import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.sqlmap import sqlmap_tool
from agent.logger import AILogger

logger = AILogger("WebAgent")
prompt_path = Path(__file__).parent.parent.parent / "prompts" / "web.yaml"
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
    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "recon_data": json.dumps(state.get("recon_data", {}))
        })
        extra = json.loads(response.content).get("findings", [])
        findings.extend(extra)
    except Exception as e:
        logger.error(f"LLM error: {e}")

    return {"findings": findings}
