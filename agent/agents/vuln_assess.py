import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import get_llm
from agent.tools.sqlmap import sqlmap_tool
from agent.tools.trivy import trivy_tool
from agent.tools.semgrep import semgrep_tool
from agent.logger import AILogger
from agent.normalization import normalize_tool_output
from agent.agents.schemas import LLMResponse
from utils.parser import safe_json_parse

logger = AILogger("VulnAssess")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "vuln_assess.yaml"

def vuln_assess_node(state):
    target = state["target"]
    provider = state.get("model_provider")
    logger.info(f"VULN_ANALYSIS phase started for {target} using {provider}")

    results = []

    # Run tools independently
    if target.startswith("http"):
        try:
            results.append(sqlmap_tool.invoke({"url": target}))
        except Exception as e:
            logger.error(f"SQLMap error: {e}")
            results.append({"error": str(e), "tool": "sqlmap", "target": target})
    else:
        try:
            results.append(trivy_tool.invoke({"target": target}))
        except Exception as e:
            logger.error(f"Trivy error: {e}")
            results.append({"error": str(e), "tool": "trivy", "target": target})

        try:
            results.append(semgrep_tool.invoke({"target": target}))
        except Exception as e:
            logger.error(f"Semgrep error: {e}")
            results.append({"error": str(e), "tool": "semgrep", "target": target})

    # Normalize data
    normalized_findings = []
    normalized_vulnerabilities = []

    for res in results:
        norm_state = normalize_tool_output(res)
        normalized_findings.extend([f.dict() for f in norm_state.findings])
        normalized_vulnerabilities.extend([v.dict() for v in norm_state.vulnerabilities])

    if not normalized_findings:
        logger.warning(f"No evidence found in VULN_ANALYSIS for {target}")
        return {
            "current_state": "VULN_ANALYSIS",
            "status": "empty_result",
            "evidence": [{"tool": r.get("tool"), "data": r} for r in results],
            "vuln_analysis": results
        }

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    # Prepare normalized data for LLM
    llm_input_data = {
        "vulnerabilities": normalized_vulnerabilities,
        "findings": normalized_findings
    }

    # Dynamic LLM selection
    llm = get_llm(provider)
    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "evidence_json": json.dumps(llm_input_data, indent=2)
        })
        parsed_obj = safe_json_parse(response.content, LLMResponse)
        parsed = parsed_obj.dict()

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
            "evidence": [{"tool": r.get("tool"), "data": r} for r in results],
            "vuln_analysis": parsed
        }
    except Exception as e:
        logger.error(f"LLM error in VULN_ANALYSIS: {e}")
        return {"current_state": "VULN_ANALYSIS", "status": "failed", "status_reason": str(e)}
