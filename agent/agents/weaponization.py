import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("Weaponization")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "weaponization.yaml"

def weaponization_node(state):
    target = state["target"]
    logger.info(f"Weaponization dimulai: {target}")

    findings = state.get("findings", [])
    if not findings:
        logger.warning("No findings for weaponization.")
        return {"weaponization": {"status": "skipped", "reason": "no findings"}}

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        return {"weaponization": {"error": "Prompt not found"}}

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    payloads = []
    try:
        response = chain.invoke({
            "target": target,
            "findings": json.dumps(findings, indent=2)
        })
        parsed = parse_llm_json(response.content)
        if isinstance(parsed, dict):
            payloads = parsed.get("payloads", [])
        elif isinstance(parsed, list):
            payloads = parsed
    except Exception as e:
        logger.error(f"LLM analysis error in Weaponization: {e}")

    return {"weaponization": {"payloads": payloads}}
