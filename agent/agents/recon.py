import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.nmap import nmap_tool
from agent.tools.nuclei import nuclei_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("Recon")

# Load prompt with absolute path relative to this file
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "recon.yaml"

with open(prompt_path) as f:
    prompt_cfg = yaml.safe_load(f)
prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

def recon_node(state):
    target = state["target"]
    logger.info(f"Recon dimulai: {target}")

    # Run nmap
    try:
        nmap_res = nmap_tool.invoke({"target": target})
    except Exception as e:
        logger.error(f"nmap gagal: {e}")
        nmap_res = {"error": str(e)}

    # Run nuclei
    try:
        nuclei_res = nuclei_tool.invoke({"target": target, "template": "services"})
    except Exception as e:
        logger.error(f"nuclei gagal: {e}")
        nuclei_res = {"error": str(e)}

    # LLM analysis - Check if we have valid results to analyze
    has_nmap = nmap_res and "error" not in nmap_res and nmap_res.get("services")
    has_nuclei = nuclei_res and "error" not in nuclei_res and nuclei_res.get("nuclei_results")

    findings = []
    if not (has_nmap or has_nuclei):
        logger.warning(f"Recon tidak menemukan hasil valid dari nmap atau nuclei untuk {target}. Skip LLM analysis.")
        recon_data = {"nmap": nmap_res, "nuclei": nuclei_res}
        return {"findings": [], "recon_data": recon_data}

    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "nmap_output": json.dumps(nmap_res, indent=2),
            "nuclei_output": json.dumps(nuclei_res, indent=2)
        })
        parsed = parse_llm_json(response.content)
        if isinstance(parsed, dict):
            findings = parsed.get("findings", [])
        elif isinstance(parsed, list):
            findings = parsed
    except Exception as e:
        logger.error(f"LLM analysis error in Recon: {e}")

    recon_data = {"nmap": nmap_res, "nuclei": nuclei_res}
    logger.info(f"Recon selesai: {len(findings)} temuan mentah")
    return {"findings": findings, "recon_data": recon_data}
