import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.mobsf import mobsf_tool
from agent.logger import AILogger

logger = AILogger("MobileAgent")
prompt_path = Path(__file__).parent.parent.parent / "prompts" / "mobile.yaml"
with open(prompt_path) as f:
    prompt_cfg = yaml.safe_load(f)
prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

def mobile_node(state):
    target = state["target"]
    logger.info(f"Mobile agent memeriksa {target}")
    findings = []

    if target.endswith(".apk") or target.endswith(".ipa"):
        try:
            mobsf_res = mobsf_tool.invoke({"file_path": target})
            findings.append(mobsf_res)
        except Exception as e:
            logger.error(f"MobSF error: {e}")

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

