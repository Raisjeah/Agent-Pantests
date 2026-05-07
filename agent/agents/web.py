import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.sqlmap import sqlmap_tool
from agent.logger import AILogger
from utils.parser import parse_llm_json

logger = AILogger("WebAgent")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "web.yaml"

with open(prompt_path) as f:
    prompt_cfg = yaml.safe_load(f)
prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

def web_node(state):
    target = state["target"]
    logger.info(f"Web agent memeriksa {target}")
    findings = []

    # SQLMap hanya jika target adalah URL
    if target.startswith("http"):
        try:
            sqlmap_res = sqlmap_tool.invoke({"url": target})
            findings.append(sqlmap_res)
        except Exception as e:
            logger.error(f"SQLMap error: {e}")

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
            logger.error(f"LLM analysis error in WebAgent: {e}")
    else:
        logger.warning("No recon_data available for WebAgent")

    return {"findings": findings}
