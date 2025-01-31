import json
from typing import List, Optional, Tuple
from pydantic_ai.messages import ModelMessage

def get_openai_format_json_messages_from_pydantic_message_response(
    messages: List[ModelMessage],
):
    def get_role(kind, part_kind):
        if kind == "request":
            if part_kind == "system-prompt":
                return "system"
            elif part_kind == "user-prompt":
                return "user"
            elif part_kind == "tool-return":
                return "user"
            elif part_kind == "retry-prompt":
                return "user"
        elif kind == "response":
            if part_kind == "tool-call":
                return "assistant"
            elif part_kind == "retry-prompt":
                return "user"
            elif part_kind == "text":
                return "assistant"
    json_formatted_messages = []

    for message in messages:
        kind = message.kind
        parts = message.parts
        for part in parts:
            part_dict = part.__dict__
            content = part.content if "content" in part_dict else ""
            tool_name = part.tool_name if "tool_name" in part_dict else ""
            arguments = part.args if "args" in part_dict else ""
            part_kind = part.part_kind

            if content:
                json_formatted_messages.append(
                    {"role": get_role(kind, part_kind), "content": content}
                )
            if tool_name:
                json_formatted_messages.append(
                    {
                        "role": get_role(kind, part_kind),
                        "tool_name": tool_name,
                        "arguments": str(arguments),
                    }
                )

    return json_formatted_messages

def convert_json_to_string_messages(json_messages):
    string_messages = ""
    for message in json_messages:
        string_messages += (
            f"\n{message['role']}: {message['content']}\n"
            if "content" in message
            else f"{message['role']}: {message['tool_name']}\nArguments: {message['arguments']}\n"
        )
    return string_messages
