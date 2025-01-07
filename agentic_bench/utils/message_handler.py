from pydantic import BaseModel

class BroadcastMessage(BaseModel):
    message: str
    request_halt: bool = False
