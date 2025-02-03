from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

def get_client():
    api_key = os.getenv("AGENTIC_BENCH_MODEL_API_KEY")
    base_url = os.getenv("AGENTIC_BENCH_MODEL_BASE_URL")

    client = AsyncOpenAI(api_key=api_key, 
                         base_url=base_url,
                         max_retries=3,
                         timeout=10000)
    return client
