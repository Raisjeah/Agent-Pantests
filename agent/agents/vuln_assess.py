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
    logger.info(f"Vulnerability Assessment dimulai: {target}")

    results = {}

    # SQLMap for URLs
    if target.startswith("http"):
        try:
            results["sqlmap"] = sqlmap_tool.invoke({"url": target})
        except FileNotFoundError:
            logger.warning("sqlmap not found. Consider using ghauri if available.")
            results["sqlmap"] = {"error": "sqlmap not found"}
        except Exception as e:
            logger.error(f"SQLMap error: {e}")
            results["sqlmap"] = {"error": str(e)}

    # Trivy for files/hosts
    if not target.startswith("http"):
        try:
            results["trivy"] = trivy_tool.invoke({"target": target})
        except FileNotFoundError:
            logger.warning("trivy not found.")
            results["trivy"] = {"error": "trivy not found"}
        except Exception as e:
            logger.error(f"Trivy error: {e}")
            results["trivy"] = {"error": str(e)}

    # Semgrep - SKIP if it starts with http
    if not target.startswith("http"):
        try:
            results["semgrep"] = semgrep_tool.invoke({"target": target})
        except FileNotFoundError:
            logger.warning("semgrep not found.")
            results["semgrep"] = {"error": "semgrep not found"}
        except Exception as e:
            logger.error(f"Semgrep error: {e}")
            results["semgrep"] = {"error": str(e)}
    else:
        logger.info("Skipping Semgrep for URL target")

    # Error Silence: check if any tool returned valid data
    has_data = any(res for res in results.values() if res and "error" not in res)

    findings = []
    if not has_data:
        logger.warning(f"VulnAssess tidak menemukan hasil valid untuk {target}.")
        return {"vuln_assess": results}

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        return {"vuln_assess": results}

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
        if isinstance(parsed, dict):
            findings = parsed.get("findings", [])
        elif isinstance(parsed, list):
            findings = parsed
    except Exception as e:
        logger.error(f"LLM analysis error in VulnAssess: {e}")

    return {"findings": findings, "vuln_assess": {"results": results, "findings": findings}}
