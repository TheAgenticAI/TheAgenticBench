def convert_to_openai_messages(pydantic_result):
    """
    Convert Pydantic AI result format to OpenAI API message format.
    
    Args:
        pydantic_result (dict): Result object from Pydantic AI
        
    Returns:
        list: List of OpenAI API format messages
    """
    openai_messages = []
    
    for message in pydantic_result["all_messages"]:
        # Handle request messages
        if message["kind"] == "request":
            for part in message["parts"]:
                if part["part_kind"] == "system-prompt":
                    openai_messages.append({
                        "role": "system",
                        "content": part["content"]
                    })
                elif part["part_kind"] == "user-prompt":
                    openai_messages.append({
                        "role": "user",
                        "content": part["content"]
                    })
                elif part["part_kind"] == "tool-return":
                    openai_messages.append({
                        "role": "tool",
                        "content": part["content"],
                        "tool_call_id": part["tool_call_id"]
                    })
                    
        # Handle response messages 
        elif message["kind"] == "response":
            text_parts = []
            tool_calls = []
            
            for part in message["parts"]:
                if part["part_kind"] == "text":
                    text_parts.append(part["content"])
                elif part["part_kind"] == "tool-call":
                    tool_calls.append({
                        "id": part["tool_call_id"],
                        "type": "function",
                        "function": {
                            "name": part["tool_name"],
                            "arguments": part["args"]["args_json" if "args_json" in part["args"] else "args_dict"]
                        }
                    })
            
            # Create assistant message with either content or tool_calls
            assistant_message = {"role": "assistant"}
            
            if text_parts:
                assistant_message["content"] = "\n".join(text_parts)
            if tool_calls:
                assistant_message["tool_calls"] = tool_calls
                
            openai_messages.append(assistant_message)
    
    return openai_messages

