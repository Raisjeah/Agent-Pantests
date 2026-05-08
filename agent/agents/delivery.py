import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("Delivery")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "delivery.yaml"

def delivery_node(state):
    target = state["target"]
    logger.info(f"Delivery strategy dimulai: {target}")

    weaponization_data = state.get("weaponization", {})
    payloads = weaponization_data.get("payloads", [])

    if not payloads:
        logger.warning("No payloads for delivery.")
        return {"delivery": {"status": "skipped", "reason": "no payloads"}}

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        return {"delivery": {"error": "Prompt not found"}}

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    strategies = []
    try:
        response = chain.invoke({
            "target": target,
            "payloads": json.dumps(payloads, indent=2)
        })
        parsed = parse_llm_json(response.content)
        if isinstance(parsed, dict):
            strategies = parsed.get("strategies", [])
        elif isinstance(parsed, list):
            strategies = parsed
    except Exception as e:
        logger.error(f"LLM analysis error in Delivery: {e}")

    return {"delivery": {"strategies": strategies}}
