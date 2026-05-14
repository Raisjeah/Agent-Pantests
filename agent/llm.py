import os
import yaml
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

config_path = Path(__file__).parent / "config.yaml"
with open(config_path) as f:
    config = yaml.safe_load(f)

def get_llm(provider: str = None):
    if provider is None:
        provider = config["llm"]["default_provider"]

    if provider == "google":
        provider_cfg = config["llm"]["google"]
        api_key = os.getenv(provider_cfg["api_key_env"])
        if not api_key:
             # Fallback or error
             raise RuntimeError(f"API key tidak ditemukan. Set env {provider_cfg['api_key_env']}")
        return ChatGoogleGenerativeAI(
            model=provider_cfg["model"],
            temperature=provider_cfg["temperature"],
            max_tokens=provider_cfg["max_tokens"],
            google_api_key=api_key
        )
    elif provider == "anthropic":
        provider_cfg = config["llm"]["anthropic"]
        api_key = os.getenv(provider_cfg["api_key_env"])
        if not api_key:
             raise RuntimeError(f"API key tidak ditemukan. Set env {provider_cfg['api_key_env']}")
        return ChatAnthropic(
            model=provider_cfg["model"],
            temperature=provider_cfg["temperature"],
            max_tokens=provider_cfg["max_tokens"],
            anthropic_api_key=api_key
        )
    else:
        raise ValueError(f"Provider LLM tidak didukung: {provider}")

# Default LLM for backward compatibility if needed, though nodes should use get_llm()
llm = get_llm()
