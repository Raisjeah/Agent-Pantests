import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.nmap import nmap_tool
from agent.tools.nuclei import nuclei_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("Scanning")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "scanning.yaml"

def scanning_node(state):
    target = state["target"]
    logger.info(f"SCAN phase started for {target}")

    try:
        nmap_res = nmap_tool.invoke({"target": target, "ports": "1-1000"})
    except Exception as e:
        logger.error(f"nmap failed: {e}")
        nmap_res = {"error": str(e)}

    try:
        nuclei_res = nuclei_tool.invoke({"target": target, "template": "network"})
    except Exception as e:
        logger.error(f"nuclei failed: {e}")
        nuclei_res = {"error": str(e)}

    has_nmap = nmap_res and "error" not in nmap_res and nmap_res.get("services")
    has_nuclei = nuclei_res and "error" not in nuclei_res and nuclei_res.get("nuclei_results")

    if not (has_nmap or has_nuclei):
        logger.warning(f"No evidence found in SCAN for {target}")
        return {
            "current_state": "SCAN",
            "status": "empty_result",
            "scan": {"nmap": nmap_res, "nuclei": nuclei_res}
        }

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "nmap_output": json.dumps(nmap_res, indent=2),
            "nuclei_output": json.dumps(nuclei_res, indent=2)
        })
        parsed = parse_llm_json(response.content)

        return {
            "current_state": "SCAN",
            "status": parsed.get("status", "success"),
            "confidence": parsed.get("confidence", 0.5),
            "findings": parsed.get("findings", []),
            "evidence": [{"tool": "scan", "data": {"nmap": nmap_res, "nuclei": nuclei_res}}],
            "scan": parsed
        }
    except Exception as e:
        logger.error(f"LLM error in SCAN: {e}")
        return {"current_state": "SCAN", "status": "failed", "status_reason": str(e)}
