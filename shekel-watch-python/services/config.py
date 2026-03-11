"""
Reads config from Streamlit secrets (cloud) or .env (local).
Import `get` instead of os.getenv so both environments work.
"""
import os
from dotenv import load_dotenv

load_dotenv()

try:
    import streamlit as st
    _secrets = st.secrets
except Exception:
    _secrets = {}


def get(key: str) -> str:
    # Streamlit Cloud secrets take priority
    try:
        return _secrets[key]
    except Exception:
        return os.getenv(key, "")
