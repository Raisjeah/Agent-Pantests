import os
import yaml
from langchain_google_genai import ChatGoogleGenerativeAI

with open("config.yaml") as f:
    config = yaml.safe_load(f)

api_key = os.getenv(config["llm"]["api_key_env"])
if not api_key:
    raise RuntimeError(f"API key tidak ditemukan. Set env {config['llm']['api_key_env']}")

llm = ChatGoogleGenerativeAI(
    model=config["llm"]["model"],
    temperature=config["llm"]["temperature"],
    max_tokens=config["llm"]["max_tokens"],
    google_api_key=api_key
)
