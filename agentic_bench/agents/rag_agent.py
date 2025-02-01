from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import List, Tuple, Any,  Optional
from pydantic import Field, BaseModel
from fastapi import WebSocket
from utils.stream_response_format import StreamResponse
from dataclasses import asdict
import json
import asyncio
import logfire
import tracemalloc
import os
from fastapi import WebSocket
from dataclasses import asdict
from utils.stream_response_format import StreamResponse
from utils.initializers.rag_constants import PDF_DIRECTORY
from utils.initializers.graph_initializer import GraphInitializer
from utils.initializers.rag_constants import DOMAIN, EXAMPLE_QUERIES, ENTITY_TYPES, WORKING_DIR, PDF_DIRECTORY, rag_system_prompt
from utils.initializers.rag_constants import AGENT_DESCRIPTION_FINANCE

tracemalloc.start()


@dataclass
class RAGDependencies:
    graph_rag: GraphInitializer
    description: str
    system_message: str
    websocket: Optional[WebSocket]
    stream_output: Optional[StreamResponse]



class RAGResult(BaseModel):
    answer_found: bool = Field(description="Whether the answer was found")
    answer: str = Field(description="Response content from RAG query")
    chunks: List[str]
    relationships: List[str]


class RAGAgent:
    def __init__(self, agent: Agent, system_prompt: str):
        try:
            self._agent: Agent = agent
            self.name = "RAG Agent"
            self._system_prompt = system_prompt
            self.websocket: Optional[WebSocket] = None
            self.stream_output: Optional[StreamResponse] = None

            all_file_names_list = [f for f in os.listdir(PDF_DIRECTORY) if os.path.isfile(os.path.join(PDF_DIRECTORY, f))]
            file_names_string = ", ".join(all_file_names_list)

            self.description = f"RAG agent which utilizes the existing data uploaded by user and can answer questions based on the provided data. The available files are: {file_names_string}"
            self.register_tool()
        except Exception as e:
            logfire.error(f"Failed to initialize RAGAgent: {e}")
            raise

    # def add_system_message(self):
    #     @self._agent.system_prompt
    #     def add_system_messages(ctx: RunContext[RAGDependencies]) -> str:
    #         return self._system_prompt

    def register_tool(self):
        @self._agent.tool
        async def query_rag(ctx: RunContext[RAGDependencies], query: str) -> dict:
            """Query the GraphRAG instance and return the parsed response."""

            if ctx.deps.stream_output and ctx.deps.websocket:
                ctx.deps.stream_output.steps.append(f"Querying RAG system with: {query}")
                await ctx.deps.websocket.send_text(json.dumps(asdict(ctx.deps.stream_output)))

            response = await ctx.deps.graph_rag.query(query)

            chunks = [
                {
                    "id": int(chunk[0].id),
                    "content": chunk[0].content,
                    "score": float(chunk[1]),
                }
                for chunk in response.context.chunks
            ]

            if ctx.deps.stream_output and ctx.deps.websocket:
                ctx.deps.stream_output.steps.append(f"Found {len(chunks)} relevant chunks")
                await ctx.deps.websocket.send_text(json.dumps(asdict(ctx.deps.stream_output)))

            relationships = []
            for item in response.context.relationships:
                for chunk_id in item[0].chunks:
                    if chunk_id in [chunk["id"] for chunk in chunks]:
                        rels = {
                            "source": item[0].source,
                            "target": item[0].target,
                            "description": item[0].description,
                            "chunks": [int(chunk_id) for chunk_id in item[0].chunks],
                            "score": float(item[1]),
                        }
                        if rels not in relationships:
                            relationships.append(rels)

            return response.response

    async def generate_reply(
            self, user_message: str, websocket: WebSocket, stream_output: StreamResponse
    ) -> Tuple[bool, str, List]:
        """Generate reply from the RAG agent"""
        try:
            self.websocket = websocket
            self.stream_output = stream_output

            graph_initializer = GraphInitializer(
                working_dir=WORKING_DIR,
                domain=DOMAIN,
                example_queries=EXAMPLE_QUERIES,
                entity_types=ENTITY_TYPES,
            )

            ingestion_status = await graph_initializer.ingest_data(pdf_dir=PDF_DIRECTORY)
            logfire.info(f"Graph memory initialization status: {ingestion_status}")

            rag_deps = RAGDependencies(
                graph_rag=graph_initializer,
                description=AGENT_DESCRIPTION_FINANCE,
                system_message=rag_system_prompt,
                websocket=self.websocket,
                stream_output=self.stream_output
            )

            if self.stream_output and self.websocket:
                self.stream_output.steps.append("Data Ingestion in Progress")
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))

                self.stream_output.steps.append("Creating Knowledge Graph")
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))

            response = await self._agent.run(user_message, deps=rag_deps)

            return (True, str(response.data), response.all_messages())

        except Exception as e:
            logfire.error(f"Failed to generate RAG reply: {e}")
            if self.stream_output and self.websocket:
                self.stream_output.status_code = 500
                self.stream_output.output = str(e)
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))
            return False, str(e), []