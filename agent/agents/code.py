import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import llm
from agent.tools.semgrep import semgrep_tool
from agent.logger import AILogger

logger = AILogger("CodeAgent")
prompt_path = Path(__file__).parent.parent.parent / "prompts" / "code.yaml"
with open(prompt_path) as f:
    prompt_cfg = yaml.safe_load(f)
prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

def code_node(state):
    target = state["target"]  # path ke direktori source code
    logger.info(f"Code agent memeriksa {target}")
    findings = []

    try:
        semgrep_res = semgrep_tool.invoke({"target": target})
        findings.append(semgrep_res)
    except Exception as e:
        logger.error(f"Semgrep error: {e}")

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
