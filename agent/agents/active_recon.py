import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.nmap import nmap_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("ActiveRecon")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "active_recon.yaml"

def active_recon_node(state):
    target = state["target"]
    logger.info(f"Active Recon dimulai: {target}")

    # Run nmap for infrastructure mapping
    try:
        nmap_res = nmap_tool.invoke({"target": target, "ports": "80,443,22,21,25,53,8080"})
    except Exception as e:
        logger.error(f"nmap gagal: {e}")
        nmap_res = {"error": str(e)}

    # Error Silence: Only call LLM if we have some results
    has_nmap = nmap_res and "error" not in nmap_res and nmap_res.get("services")

    findings = []
    if not has_nmap:
        logger.warning(f"Active Recon tidak menemukan hasil valid untuk {target}.")
        return {"active_recon": nmap_res}

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        return {"active_recon": nmap_res}

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "nmap_output": json.dumps(nmap_res, indent=2)
        })
        parsed = parse_llm_json(response.content)
        if isinstance(parsed, dict):
            findings = parsed.get("findings", [])
        elif isinstance(parsed, list):
            findings = parsed
    except Exception as e:
        logger.error(f"LLM analysis error in ActiveRecon: {e}")

    return {"findings": findings, "active_recon": {"nmap": nmap_res, "findings": findings}}
