"""
Reads config from environment variables / .env file.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def get(key: str) -> str:
    return os.getenv(key, "")
