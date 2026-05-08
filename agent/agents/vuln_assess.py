import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.sqlmap import sqlmap_tool
from agent.tools.trivy import trivy_tool
from agent.tools.semgrep import semgrep_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("VulnAssess")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "vuln_assess.yaml"

def vuln_assess_node(state):
    target = state["target"]
    logger.info(f"VULN_ANALYSIS phase started for {target}")

    results = {}

    # Run tools independently
    if target.startswith("http"):
        try:
            results["sqlmap"] = sqlmap_tool.invoke({"url": target})
        except Exception as e:
            logger.error(f"SQLMap error: {e}")
            results["sqlmap"] = {"error": str(e)}
    else:
        try:
            results["trivy"] = trivy_tool.invoke({"target": target})
        except Exception as e:
            logger.error(f"Trivy error: {e}")
            results["trivy"] = {"error": str(e)}

        try:
            results["semgrep"] = semgrep_tool.invoke({"target": target})
        except Exception as e:
            logger.error(f"Semgrep error: {e}")
            results["semgrep"] = {"error": str(e)}

    has_data = any(res for res in results.values() if res and "error" not in res)

    if not has_data:
        logger.warning(f"No evidence found in VULN_ANALYSIS for {target}")
        return {
            "current_state": "VULN_ANALYSIS",
            "status": "empty_result",
            "vuln_analysis": results
        }

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "tool_results": json.dumps(results, indent=2)
        })
        parsed = parse_llm_json(response.content)

        # Enforce confidence threshold for status
        status = parsed.get("status", "success")
        confidence = parsed.get("confidence", 0.0)
        if confidence < 0.7 and status == "success":
            status = "blocked"
            logger.warning(f"Confidence {confidence} below 0.7. Blocking exploitation.")

        return {
            "current_state": "VULN_ANALYSIS",
            "status": status,
            "confidence": confidence,
            "findings": parsed.get("findings", []),
            "evidence": [{"tool": "vuln_analysis", "data": results}],
            "vuln_analysis": parsed
        }
    except Exception as e:
        logger.error(f"LLM error in VULN_ANALYSIS: {e}")
        return {"current_state": "VULN_ANALYSIS", "status": "failed", "status_reason": str(e)}
