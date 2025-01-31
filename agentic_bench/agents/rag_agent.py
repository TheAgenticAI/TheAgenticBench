from pydantic_ai import Agent, RunContext
from dataclasses import dataclass
from typing import List, Tuple, Any
from pydantic import Field, BaseModel
from agentic_bench.utils.initializers.graph_initializer import GraphInitializer
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
    # entities : List[str]


class RAGAgent:
    def __init__(self, agent: Agent, system_prompt: str, description: str):
        try:
            self._agent = agent
            self.name = "RAG Agent"
            self._system_prompt = system_prompt
            self.description = description
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
            response = ctx.deps.graph_rag.query(query)
            self.references = response.context
            return response.response

    async def generate_reply(
            self, user_message: str, deps: RAGDependencies
    ) -> Tuple[bool, str, List]:
        """Generate reply from the RAG agent"""
        try:
            response = await self._agent.run(user_message, deps=deps)

            # TODO: figure a way to extract the entities
            chunks = [
                {
                    "id": int(chunk[0].id),
                    "content": chunk[0].content,
                    "score": float(chunk[1]),
                }
                for chunk in self.references.chunks
            ]
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
#response.data.answer_found
            return True, str(response.data.answer), response.new_messages()

        except Exception as e:
            logfire.error(f"Failed to generate RAG reply: {e}")
            return False, str(e), []