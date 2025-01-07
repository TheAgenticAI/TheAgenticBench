from __future__ import annotations
from pydantic import BaseModel
from dataclasses import dataclass

@dataclass
class FunctionCall:
    id: str
    # JSON args
    arguments: str
    # Function to call
    name: str

class FunctionExecutionResult(BaseModel):
    content: str
    call_id: str
