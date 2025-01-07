from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI, OpenAI
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

def get_env_var(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Environment variable {key} is not set")
    return value

class OpenAIConfig:
    @staticmethod
    def get_text_config():
        return {
            "api_key": get_env_var("AUTOSCRAPER_TEXT_API_KEY"),
            "base_url": get_env_var("AUTOSCRAPER_TEXT_BASE_URL"),
            "model": get_env_var("AUTOSCRAPER_TEXT_MODEL"),
            "max_retries": 3
        }

    @staticmethod
    def get_ss_config():
        return {
            "api_key": get_env_var("AUTOSCRAPER_SS_API_KEY"),
            "base_url": get_env_var("AUTOSCRAPER_SS_BASE_URL"),
            "model": get_env_var("AUTOSCRAPER_SS_MODEL"),
            "max_retries": 3
        }

def get_client():
    """Get AsyncOpenAI client for text analysis"""
    config = OpenAIConfig.get_text_config()
    return AsyncOpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
        max_retries=config["max_retries"]
    )

def get_ss_client():
    """Get OpenAI client for screenshot analysis"""
    config = OpenAIConfig.get_ss_config()
    return OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
        max_retries=config["max_retries"]
    )

def get_text_model() -> str:
    """Get model name for text analysis"""
    return OpenAIConfig.get_text_config()["model"]

def get_ss_model() -> str:
    """Get model name for screenshot analysis"""
    return OpenAIConfig.get_ss_config()["model"]
