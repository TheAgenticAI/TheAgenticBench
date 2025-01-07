from typing import List, Union
from utils.types import FunctionCall, FunctionExecutionResult
from utils.image import Image

# Convenience type
UserContent = Union[str, List[Union[str, Image]]]
AssistantContent = Union[str, List[FunctionCall]]
FunctionExecutionContent = List[FunctionExecutionResult]
SystemContent = str

# Convert UserContent to a string
def message_content_to_str(
    message_content: (
        UserContent | AssistantContent | SystemContent | FunctionExecutionContent
    ),
) -> str:
    if isinstance(message_content, str):
        return message_content
    elif isinstance(message_content, List):
        converted: List[str] = list()
        for item in message_content:
            if isinstance(item, str):
                converted.append(item.rstrip())
            elif isinstance(item, Image):
                converted.append("<Image>")
            else:
                converted.append(str(item).rstrip())
        return "\n".join(converted)
    else:
        raise AssertionError("Unexpected response type.")
