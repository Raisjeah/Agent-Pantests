import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import get_llm
from agent.tools.nuclei import nuclei_tool
from agent.logger import AILogger
from agent.normalization import normalize_tool_output
from agent.agents.schemas import LLMResponse
from utils.parser import safe_json_parse

logger = AILogger("Enumeration")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "enumeration.yaml"

def enumeration_node(state):
    target = state["target"]
    provider = state.get("model_provider")
    logger.info(f"ENUM phase started for {target} using {provider}")

    # Run specific nuclei templates for deep enumeration
    try:
        nuclei_res = nuclei_tool.invoke({"target": target, "template": "http,config,cves"})
    except Exception as e:
        logger.error(f"nuclei failed: {e}")
        nuclei_res = {"error": str(e), "tool": "nuclei", "target": target}

    # Normalize data
    nuclei_state = normalize_tool_output(nuclei_res)

    if not nuclei_state.findings:
        logger.warning(f"No evidence found in ENUM for {target}")
        return {
            "current_state": "ENUM",
            "status": "empty_result",
            "evidence": [{"tool": "nuclei", "data": nuclei_res}],
            "enum": {"nuclei": nuclei_res}
        }

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    # Prepare normalized data for LLM
    llm_input_data = {
        "vulnerabilities": [v.dict() for v in nuclei_state.vulnerabilities],
        "findings": [f.dict() for f in nuclei_state.findings]
    }

    # Dynamic LLM selection
    llm = get_llm(provider)
    chain = prompt | llm
    try:
        response = chain.invoke({
            "target": target,
            "evidence_json": json.dumps(llm_input_data, indent=2)
        })
        parsed_obj = safe_json_parse(response.content, LLMResponse)
        parsed = parsed_obj.dict()

        return {
            "current_state": "ENUM",
            "status": parsed.get("status", "success"),
            "confidence": parsed.get("confidence", 0.5),
            "findings": parsed.get("findings", []),
            "evidence": [{"tool": "nuclei", "data": nuclei_res}],
            "enum": parsed
        }
    except Exception as e:
        logger.error(f"LLM error in ENUM: {e}")
        return {"current_state": "ENUM", "status": "failed", "status_reason": str(e)}
