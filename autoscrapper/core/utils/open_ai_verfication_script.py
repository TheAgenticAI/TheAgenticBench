# verify_conversation.py
import json
import os
from typing import List, Dict, Any
import asyncio
from openai import AsyncOpenAI
from datetime import datetime

class ConversationVerifier:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def verify_conversation(self, 
                                conversation_path: str, 
                                system_prompt: str = None,
                                model: str = "gpt-4o-2024-11-20") -> Dict[str, Any]:
        """
        Verify a conversation using OpenAI API
        
        Args:
            conversation_path: Path to the conversation JSON file
            system_prompt: Optional system prompt to prepend
            model: OpenAI model to use
            
        Returns:
            Dict containing the verification results
        """
        # Load conversation
        with open(conversation_path, 'r') as f:
            messages = json.load(f)
        
        # Add system prompt if provided
        if system_prompt:
            messages.insert(0, {
                "role": "system",
                "content": system_prompt
            })
        
        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            # Save verification result
            result = {
                "timestamp": datetime.now().isoformat(),
                "conversation_file": conversation_path,
                "model_used": model,
                "verification_response": response.choices[0].message.content,
                "status": "success"
            }
            
            # Save result to file
            result_path = f"verification_{os.path.basename(conversation_path)}"
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            return result
            
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "conversation_file": conversation_path,
                "status": "error",
                "error": str(e)
            }


