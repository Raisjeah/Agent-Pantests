import os
import yaml
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.globals import set_llm_cache
from langchain_community.cache import SQLiteCache

config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

api_key = os.getenv(config["llm"]["api_key_env"])
if not api_key:
    raise RuntimeError(f"API key tidak ditemukan. Set env {config['llm']['api_key_env']}")

# Setup Caching
cache_path = os.path.expanduser("~/.ai_pentest_langchain/llm_cache.db")
os.makedirs(os.path.dirname(cache_path), exist_ok=True)
set_llm_cache(SQLiteCache(database_path=cache_path))

llm = ChatGoogleGenerativeAI(
    model=config["llm"]["model"],
    temperature=config["llm"]["temperature"],
    max_tokens=config["llm"]["max_tokens"],
    google_api_key=api_key
)
