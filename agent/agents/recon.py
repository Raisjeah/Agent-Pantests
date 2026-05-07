import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.nmap import nmap_tool
from agent.tools.nuclei import nuclei_tool
from agent.logger import AILogger

logger = AILogger("Recon")

prompt_path = Path(__file__).parent.parent.parent / "prompts" / "recon.yaml"
with open(prompt_path) as f:
    prompt_cfg = yaml.safe_load(f)
prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

def recon_node(state):
    target = state["target"]
    logger.info(f"Recon dimulai: {target}")
    findings = []

    # nmap
    try:
        nmap_res = nmap_tool.invoke({"target": target})
    except Exception as e:
        logger.error(f"nmap gagal: {e}")
        nmap_res = {"error": str(e)}

    # nuclei
    try:
        nuclei_res = nuclei_tool.invoke({"target": target, "template": "services"})
    except Exception as e:
        logger.error(f"nuclei gagal: {e}")
        nuclei_res = {"error": str(e)}

    # LLM analysis
    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "nmap_output": json.dumps(nmap_res),
            "nuclei_output": json.dumps(nuclei_res)
        })
        parsed = json.loads(response.content)
        findings = parsed.get("findings", [])
    except Exception as e:
        logger.error(f"LLM parsing error: {e}")

    recon_data = {"nmap": nmap_res, "nuclei": nuclei_res}
    logger.info(f"Recon selesai: {len(findings)} temuan mentah")
    return {"findings": findings, "recon_data": recon_data}
