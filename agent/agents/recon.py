import json
from pathlib import Path
import yaml
from langchain_core.prompts import ChatPromptTemplate
from agent.llm import get_llm
from agent.tools.nmap import nmap_tool
from agent.tools.nuclei import nuclei_tool
from agent.logger import AILogger
from agent.normalization import normalize_tool_output
from agent.agents.schemas import LLMResponse
from utils.parser import safe_json_parse

logger = AILogger("Recon")
current_dir = Path(__file__).parent.parent
prompt_path = current_dir / "prompts" / "recon.yaml"

def recon_node(state):
    target = state["target"]
    provider = state.get("model_provider")
    logger.info(f"RECON phase started for {target} using {provider}")

    # Use nmap for basic host discovery
    try:
        nmap_res = nmap_tool.invoke({"target": target, "ports": "80,443,22,21,25,53,8080"})
    except Exception as e:
        logger.error(f"nmap failed: {e}")
        nmap_res = {"error": str(e), "tool": "nmap", "target": target}

    # Use nuclei for service identification
    try:
        nuclei_res = nuclei_tool.invoke({"target": target, "template": "network/services"})
    except Exception as e:
        logger.error(f"nuclei failed: {e}")
        nuclei_res = {"error": str(e), "tool": "nuclei", "target": target}

    # Normalize data
    nmap_state = normalize_tool_output(nmap_res)
    nuclei_state = normalize_tool_output(nuclei_res)

    has_evidence = nmap_state.findings or nuclei_state.findings

    if not has_evidence:
        logger.warning(f"No evidence found in RECON for {target}")
        return {
            "current_state": "RECON",
            "status": "empty_result",
            "evidence": [
                {"tool": "nmap", "data": nmap_res},
                {"tool": "nuclei", "data": nuclei_res}
            ],
            "recon": {"nmap": nmap_res, "nuclei": nuclei_res}
        }

    with open(prompt_path) as f:
        prompt_cfg = yaml.safe_load(f)
    prompt = ChatPromptTemplate.from_messages(prompt_cfg["messages"])

    # Prepare normalized data for LLM
    llm_input_data = {
        "ports": [p.dict() for p in nmap_state.ports],
        "vulnerabilities": [v.dict() for v in nuclei_state.vulnerabilities],
        "findings": [f.dict() for f in nmap_state.findings + nuclei_state.findings]
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
            "current_state": "RECON",
            "status": parsed.get("status", "success"),
            "confidence": parsed.get("confidence", 0.5),
            "findings": parsed.get("findings", []),
            "evidence": [
                {"tool": "nmap", "data": nmap_res},
                {"tool": "nuclei", "data": nuclei_res}
            ],
            "recon": parsed
        }
    except Exception as e:
        logger.error(f"LLM error in RECON: {e}")
        return {"current_state": "RECON", "status": "failed", "status_reason": str(e)}
