import json
import re
from typing import Any, Dict, Union

def parse_llm_json(content: str) -> Union[Dict[str, Any], list]:
    """
    Ekstrak dan parse JSON dari output LLM.
    Mendukung format markdown ```json ... ``` atau string JSON mentah.
    """
    # Bersihkan whitespace
    content = content.strip()

    # Cari blok kode markdown
    json_match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = content

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Percobaan terakhir: cari pattern { ... } atau [ ... ]
        pattern_match = re.search(r"(\{.*\}|\[.*\])", json_str, re.DOTALL)
        if pattern_match:
            try:
                return json.loads(pattern_match.group(1))
            except json.JSONDecodeError:
                pass

        # Jika gagal semua, raise error yang lebih deskriptif
        raise ValueError(f"Gagal mem-parse JSON dari content: {content[:100]}...")
