import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.nmap import nmap_tool
from agent.tools.nuclei import nuclei_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("Enumeration")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "enumeration.yaml"

def enumeration_node(state):
    target = state["target"]
    logger.info(f"Enumeration dimulai: {target}")

    # Use results from scanning to do deeper enumeration
    scanning_data = state.get("scanning", {})

    # We can run nuclei with more specific templates based on discovered services
    try:
        nuclei_res = nuclei_tool.invoke({"target": target, "template": "http,config,cves"})
    except Exception as e:
        logger.error(f"nuclei gagal: {e}")
        nuclei_res = {"error": str(e)}

    # Error Silence
    has_nuclei = nuclei_res and "error" not in nuclei_res and nuclei_res.get("nuclei_results")

    findings = []
    if not has_nuclei:
        logger.warning(f"Enumeration tidak menemukan hasil valid untuk {target}.")
        return {"enumeration": {"nuclei": nuclei_res}}

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        return {"enumeration": {"nuclei": nuclei_res}}

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "scanning_data": json.dumps(scanning_data, indent=2),
            "nuclei_output": json.dumps(nuclei_res, indent=2)
        })
        parsed = parse_llm_json(response.content)
        if isinstance(parsed, dict):
            findings = parsed.get("findings", [])
        elif isinstance(parsed, list):
            findings = parsed
    except Exception as e:
        logger.error(f"LLM analysis error in Enumeration: {e}")

    return {"findings": findings, "enumeration": {"nuclei": nuclei_res, "findings": findings}}
