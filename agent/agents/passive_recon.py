import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("PassiveRecon")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "passive_recon.yaml"

def passive_recon_node(state):
    target = state["target"]
    logger.info(f"Passive Recon dimulai: {target}")

    # Passive recon typically doesn't use active tools.
    # We might use some OSINT APIs if available, but for now LLM analysis of the target.

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        return {"passive_recon": {"error": "Prompt not found"}}

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    findings = []
    try:
        response = chain.invoke({"target": target})
        parsed = parse_llm_json(response.content)
        if isinstance(parsed, dict):
            findings = parsed.get("findings", [])
        elif isinstance(parsed, list):
            findings = parsed
    except Exception as e:
        logger.error(f"LLM analysis error in PassiveRecon: {e}")

    return {"findings": findings, "passive_recon": {"findings": findings}}
