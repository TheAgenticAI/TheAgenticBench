from datetime import datetime, timezone
from typing import List, Dict, Any, Union
from dataclasses import dataclass
from openai.types.chat import ChatCompletionMessageParam
import uuid
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from openai.types.chat import ChatCompletionMessageParam

from config import SOURCE_LOG_FOLDER_PATH
from datetime import datetime, timezone
from typing import List, Dict, Any, Union
from dataclasses import dataclass
from openai.types.chat import ChatCompletionMessageParam
import uuid
import json
import os

@dataclass
class AgentConversationHandler:
    """Handles conversion and storage of agent conversations in OpenAI format"""
    
    def __init__(self):
        self.conversation_history: List[ChatCompletionMessageParam] = []

    def _extract_tool_call(self, response_part: Any) -> Dict[str, Any]:
        """Extract tool call information from a response part"""
        tool_call_id = getattr(response_part, 'tool_call_id', str(uuid.uuid4()))
        tool_name = getattr(response_part, 'tool_name', '')
        args = {}
        
        if hasattr(response_part, 'args') and hasattr(response_part.args, 'args_json'):
            try:
                args = json.loads(response_part.args.args_json)
            except json.JSONDecodeError:
                args = {'raw_args': response_part.args.args_json}
                
        return {
            'id': tool_call_id,
            'type': 'function',
            'function': {
                'name': tool_name,
                'arguments': json.dumps(args)
            }
        }

    def _format_content(self, content: Any) -> str:
        """Format content into a string, handling various input types"""
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            return json.dumps(content, indent=2)
        elif content is None:
            return ""
        else:
            try:
                return json.dumps(content, indent=2)
            except:
                return str(content)

    def _extract_from_model_request(self, response: Any) -> List[Dict[str, Any]]:
        """Extract all message components from a model response"""
        messages = []
        
        if not hasattr(response, '_all_messages'):
            return messages

        for msg in response._all_messages:
            if not hasattr(msg, 'parts'):
                continue
                
            for part in msg.parts:
                part_kind = getattr(part, 'part_kind', '')
                
                if part_kind == 'tool-call':
                    messages.append({
                        'role': 'assistant',
                        'content': None,
                        'tool_calls': [self._extract_tool_call(part)]
                    })
                
                elif part_kind == 'tool-return':
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': getattr(part, 'tool_call_id', ''),
                        'name': getattr(part, 'tool_name', ''),
                        'content': self._format_content(getattr(part, 'content', ''))
                    })
                
                elif part_kind == 'text':
                    messages.append({
                        'role': 'assistant',
                        'content': getattr(part, 'content', ''),
                        'name': 'browser_nav_agent'
                    })
                    
        return messages

    def add_browser_nav_message(self, browser_response: Any) -> None:
        """Convert and store browser navigation agent messages"""
        messages = self._extract_from_model_request(browser_response)
        self.conversation_history.extend(messages)

    def add_planner_message(self, planner_response: Any) -> None:
        """Convert and store planner agent messages"""
        plan = ''
        next_step = ''
        
        if hasattr(planner_response, 'data'):
            data = planner_response.data
            plan = str(getattr(data, 'plan', ''))
            next_step = str(getattr(data, 'next_step', ''))
        
        tool_call_id = str(uuid.uuid4())
        
        assistant_message = {
            'role': 'assistant',
            'content': None,
            'tool_calls': [{
                'id': tool_call_id,
                'type': 'function',
                'function': {
                    'name': 'planner_agent',
                    'arguments': json.dumps({
                        'plan': plan,
                        'next_step': next_step
                    })
                }
            }]
        }
        self.conversation_history.append(assistant_message)
        
        tool_message = {
            'role': 'tool',
            'tool_call_id': tool_call_id,
            'name': 'planner_agent',
            'content': json.dumps({
                'plan': plan,
                'next_step': next_step
            })
        }
        self.conversation_history.append(tool_message)

    def add_dom_analysis_message(self, dom_analysis_response: Any) -> None:
        """Convert and store DOM analysis messages"""
        tool_call_id = str(uuid.uuid4())
        
        assistant_message = {
            'role': 'assistant',
            'content': None,
            'tool_calls': [{
                'id': tool_call_id,
                'type': 'function',
                'function': {
                    'name': 'dom_analyzer',
                    'arguments': json.dumps({
                        'analysis_request': 'analyze_dom'
                    })
                }
            }]
        }
        self.conversation_history.append(assistant_message)

        # Convert DOM content to string if it's not already
        content = self._format_content(dom_analysis_response)

        tool_message = {
            'role': 'tool',
            'tool_call_id': tool_call_id,
            'name': 'dom_analyzer',
            'content': content
        }
        self.conversation_history.append(tool_message)

    def add_critique_message(self, critique_response: Any) -> None:
        """Convert and store critique agent messages"""
        if hasattr(critique_response, 'data'):
            data = critique_response.data
            feedback = str(getattr(data, 'feedback', ''))
            final_response = str(getattr(data, 'final_response', ''))
        else:
            feedback = ''
            final_response = ''
            
        content = json.dumps({
            'feedback': feedback,
            'final_response': final_response
        })
        
        critique_message = {
            'role': 'assistant',
            'content': content,
            'name': 'critique_agent'
        }
        self.conversation_history.append(critique_message)

    def add_user_message(self, command: str) -> None:
        """Add user input messages"""
        user_message = {
            'role': 'user',
            'content': command
        }
        self.conversation_history.append(user_message)

    def add_system_message(self, content: str) -> None:
        """Add system messages"""
        system_message = {
            'role': 'system',
            'content': content
        }
        self.conversation_history.append(system_message)

    def get_conversation_history(self) -> List[ChatCompletionMessageParam]:
        """Get the full conversation history in OpenAI format"""
        return self.conversation_history


class ConversationStorage:
    def __init__(self, storage_dir: str = None):
        """
        Initialize conversation storage with configurable directory.
        If no storage_dir is provided, it will use SOURCE_LOG_FOLDER_PATH from config.
        """
        
        self.storage_dir = storage_dir if storage_dir else SOURCE_LOG_FOLDER_PATH
        os.makedirs(self.storage_dir, exist_ok=True)
        self.current_filepath = None
        
    def _get_filepath(self, prefix: str = "") -> str:
        """Get the filepath for the conversation, creating it if it doesn't exist"""
        if self.current_filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}_conversation_{timestamp}.json" if prefix else f"conversation_{timestamp}.json"
            self.current_filepath = os.path.join(self.storage_dir, filename)
        return self.current_filepath
    
    def _read_existing_messages(self, filepath: str) -> List[Dict]:
        """Read existing messages from the file if it exists"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            # If file is corrupted or empty, return empty list
            return []
        return []
    
    def save_conversation(self, messages: List[ChatCompletionMessageParam], prefix: str = "") -> str:
        """
        Append conversation messages to a single JSON file
        
        Args:
            messages: List of conversation messages
            prefix: Optional prefix for the filename
            
        Returns:
            str: Path to the saved file
        """
        filepath = self._get_filepath(prefix)
        
        # Convert new messages to serializable format
        serializable_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                serializable_messages.append(msg)
            else:
                # Handle any custom objects by converting to dict
                serializable_messages.append({
                    'role': msg.role,
                    'content': msg.content,
                    'name': getattr(msg, 'name', None)
                })
        
        # Read existing messages
        existing_messages = self._read_existing_messages(filepath)
        
        # Find new messages that aren't already in the file
        last_message_index = len(existing_messages)
        new_messages = serializable_messages[last_message_index:]
        
        # Append new messages to existing ones
        updated_messages = existing_messages + new_messages
        
        # Write all messages back to file
        with open(filepath, 'w') as f:
            json.dump(updated_messages, f, indent=2)
            
        return filepath

    def reset_file(self):
        """Reset the current file path to create a new file for a new conversation"""
        self.current_filepath = None