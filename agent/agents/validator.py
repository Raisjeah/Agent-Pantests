import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("Validator")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "validator.yaml"

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

    # Only send valid findings to LLM for validation
    valid_findings = [f for f in findings if isinstance(f, dict) and "error" not in f]

    if not valid_findings:
        logger.info("No valid findings to validate. Skipping LLM validation.")
        report = {
            "target": state["target"],
            "findings": findings,
            "summary": {"high": 0, "medium": 0, "low": 0, "total": len(findings)}
        }
        return {"final_report": report}

    chain = prompt | llm
    try:
        response = chain.invoke({"findings": json.dumps(valid_findings, indent=2)})
        parsed = parse_llm_json(response.content)
        if isinstance(parsed, dict):
            validated = parsed.get("validated", findings)
        elif isinstance(parsed, list):
            validated = parsed
        else:
            validated = findings
    except Exception as e:
        logger.error(f"Validator error: {e}")
        validated = findings

    # Ensure validated is a list
    if not isinstance(validated, list):
        validated = [validated] if validated else []

    high = sum(1 for f in validated if isinstance(f, dict) and f.get("severity") == "high")
    medium = sum(1 for f in validated if isinstance(f, dict) and f.get("severity") == "medium")
    low = sum(1 for f in validated if isinstance(f, dict) and f.get("severity") == "low")

    report = {
        "target": state["target"],
        "findings": validated,
        "summary": {
            "high": high,
            "medium": medium,
            "low": low,
            "total": len(validated)
        }
    }
    return {"final_report": report}
