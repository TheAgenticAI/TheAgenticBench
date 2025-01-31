from dataclasses import dataclass
from typing import List

@dataclass
class StreamResponse:
    agent_name: str
    instructions: str
    steps: List[str]
    status_code: int
    output: str
