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
    logger.info(f"Scanning dimulai: {target}")

    # Run nmap and nuclei for scanning
    # Fallback logic: if a tool is missing, report it as a finding instead of crashing
    try:
        nmap_res = nmap_tool.invoke({"target": target, "ports": "1-1000"})
    except FileNotFoundError as e:
        logger.warning(f"Tool nmap tidak ditemukan: {e}")
        nmap_res = {"error": "nmap not found", "finding": "Nmap missing in Kali Linux environment"}
    except Exception as e:
        logger.error(f"nmap gagal: {e}")
        nmap_res = {"error": str(e)}

    try:
        nuclei_res = nuclei_tool.invoke({"target": target, "template": "network"})
    except FileNotFoundError as e:
        logger.warning(f"Tool nuclei tidak ditemukan: {e}")
        nuclei_res = {"error": "nuclei not found", "finding": "Nuclei missing in Kali Linux environment"}
    except Exception as e:
        logger.error(f"nuclei gagal: {e}")
        nuclei_res = {"error": str(e)}

    # Error Silence
    has_nmap = nmap_res and "error" not in nmap_res and nmap_res.get("services")
    has_nuclei = nuclei_res and "error" not in nuclei_res and nuclei_res.get("nuclei_results")

    findings = []
    if not (has_nmap or has_nuclei):
        logger.warning(f"Scanning tidak menemukan hasil valid untuk {target}.")
        return {"scanning": {"nmap": nmap_res, "nuclei": nuclei_res}}

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        return {"scanning": {"nmap": nmap_res, "nuclei": nuclei_res}}

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
        if isinstance(parsed, dict):
            findings = parsed.get("findings", [])
        elif isinstance(parsed, list):
            findings = parsed
    except Exception as e:
        logger.error(f"LLM analysis error in Scanning: {e}")

    return {"findings": findings, "scanning": {"nmap": nmap_res, "nuclei": nuclei_res, "findings": findings}}
