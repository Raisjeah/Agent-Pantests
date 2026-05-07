import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.trivy import trivy_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("OSAgent")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "os.yaml"

with open(prompt_path) as f:
    prompt_cfg = yaml.safe_load(f)
prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

def os_node(state):
    target = state["target"]
    logger.info(f"OS agent memeriksa {target}")
    findings = []

    # Trivy hanya untuk host (bukan URL)
    if not target.startswith("http"):
        try:
            trivy_res = trivy_tool.invoke({"target": target})
            findings.append(trivy_res)
        except Exception as e:
            logger.error(f"Trivy error: {e}")

    # LLM analisis dari recon_data
    recon_data = state.get("recon_data")
    if recon_data:
        chain = prompt | llm
        try:
            response = chain.invoke({
                "target": target,
                "recon_data": json.dumps(recon_data, indent=2)
            })
            parsed = parse_llm_json(response.content)
            extra = []
            if isinstance(parsed, dict):
                extra = parsed.get("findings", [])
            elif isinstance(parsed, list):
                extra = parsed
            findings.extend(extra)
        except Exception as e:
            logger.error(f"LLM analysis error in OSAgent: {e}")
    else:
        logger.warning("No recon_data available for OSAgent")

    return {"findings": findings}
