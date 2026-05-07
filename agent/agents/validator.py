import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.logger import AILogger

logger = AILogger("Validator")
prompt_path = Path(__file__).parent.parent.parent / "prompts" / "validator.yaml"
with open(prompt_path) as f:
    prompt_cfg = yaml.safe_load(f)
prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

def validator_node(state):
    findings = state.get("findings", [])
    if not findings:
        report = {
            "target": state["target"],
            "findings": [],
            "summary": {"high": 0, "medium": 0, "low": 0, "total": 0}
        }
        return {"final_report": report}

    chain = prompt | llm
    try:
        response = chain.invoke({"findings": json.dumps(findings)})
        validated = json.loads(response.content).get("validated", findings)
    except Exception as e:
        logger.error(f"Validator error: {e}")
        validated = findings

    high = sum(1 for f in validated if f.get("severity") == "high")
    medium = sum(1 for f in validated if f.get("severity") == "medium")
    low = sum(1 for f in validated if f.get("severity") == "low")
    report = {
        "target": state["target"],
        "findings": validated,
        "summary": {"high": high, "medium": medium, "low": low, "total": len(validated)}
    }
    return {"final_report": report}
