from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import List, Tuple, Any,  Optional
from pydantic import Field, BaseModel
from agentic_bench.utils.initializers.graph_initializer import GraphInitializer
from fastapi import WebSocket
from agentic_bench.utils.stream_response_format import StreamResponse
from agentic_bench.utils.initializers.rag_constants import AGENT_DESCRIPTION_FINANCE
from dataclasses import asdict
import json
import asyncio
import logfire
import tracemalloc

tracemalloc.start()


@dataclass
class RAGDependencies:
    graph_rag: GraphInitializer
    description: str
    system_message: str



class RAGResult(BaseModel):
    answer_found: bool = Field(description="Whether the answer was found")
    answer: str = Field(description="Response content from RAG query")
    chunks: List[str]
    relationships: List[str]


class RAGAgent:
    def __init__(self, agent: Agent, system_prompt: str):
        try:
            self._agent = agent
            self.name = "RAG Agent"
            self._system_prompt = system_prompt
            self.websocket: Optional[WebSocket] = None
            self.stream_output: Optional[StreamResponse] = None
            self.description = AGENT_DESCRIPTION_FINANCE
            self.register_tool()
        except Exception as e:
            logfire.error(f"Failed to initialize RAGAgent: {e}")
            raise

    def add_system_message(self):
        @self._agent.system_prompt
        def add_system_messages(ctx: RunContext[RAGDependencies]) -> str:
            return self._system_prompt

    def register_tool(self):
        @self._agent.tool
        def query_rag(ctx: RunContext[RAGDependencies], query: str) -> dict:
            """Query the GraphRAG instance and return the parsed response."""
            if self.stream_output and self.websocket:
                self.stream_output.steps.append(f"Querying RAG system with: {query}")
                asyncio.run(self.websocket.send_text(json.dumps(asdict(self.stream_output))))

            response = ctx.deps.graph_rag.query(query)
            self.references = response.context

            if self.stream_output and self.websocket:
                asyncio.run(self.websocket.send_text(json.dumps(asdict(self.stream_output))))

            return response.response

    async def generate_reply(
            self, user_message: str, deps: RAGDependencies, websocket: WebSocket = None,
            stream_output: StreamResponse = None
    ) -> Tuple[bool, str, List]:
        """Generate reply from the RAG agent"""
        try:
            self.websocket = websocket
            self.stream_output = stream_output

            if self.stream_output and self.websocket:
                self.stream_output.steps.append("Data Ingestion in Progress")
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))

                # Add sleep after data ingestion step
                await asyncio.sleep(5)  # 2 second delay, adjust as needed

                self.stream_output.steps.append("Creating Knowledge Graph")
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))

            response = await self._agent.run(user_message, deps=deps)

            chunks = [
                {
                    "id": int(chunk[0].id),
                    "content": chunk[0].content,
                    "score": float(chunk[1]),
                }
                for chunk in self.references.chunks
            ]

            if self.stream_output and self.websocket:
                self.stream_output.steps.append(f"Found {len(chunks)} relevant chunks")
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))

            relationships = []
            for item in self.references.relationships:
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

            if self.stream_output and self.websocket:
                self.stream_output.output = str(response.data.answer)
                self.stream_output.status_code = 200
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))

            return True, str(response.data.answer), response.new_messages()

        except Exception as e:
            logfire.error(f"Failed to generate RAG reply: {e}")
            if self.stream_output and self.websocket:
                self.stream_output.status_code = 500
                self.stream_output.output = str(e)
                await self.websocket.send_text(json.dumps(asdict(self.stream_output)))
            return False, str(e), []