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

def validator_node(state):
    target = state["target"]
    logger.info(f"REPORT phase started for {target}")

    findings = state.get("findings", [])
    evidence = state.get("evidence", [])

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "findings": json.dumps(findings, indent=2)
        })
        report = parse_llm_json(response.content)

        # Merge tool evidence into report
        report["raw_evidence"] = evidence
        report["status"] = state.get("status")
        report["status_reason"] = state.get("status_reason")

        return {
            "current_state": "REPORT",
            "report": report,
            "final_report": report # For backward compatibility
        }
    except Exception as e:
        logger.error(f"LLM error in REPORT: {e}")
        return {
            "current_state": "REPORT",
            "report": {"error": str(e), "target": target}
        }
