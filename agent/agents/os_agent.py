import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.trivy import trivy_tool
from agent.logger import AILogger

logger = AILogger("OSAgent")
prompt_path = Path(__file__).parent.parent.parent / "prompts" / "os.yaml"
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
