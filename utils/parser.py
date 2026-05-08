import json
import re
from typing import Any, Dict, Union
from urllib.parse import urlparse

def extract_host(target: str) -> str:
    """
    Ekstrak hostname atau IP dari target (URL, IP, atau domain).
    Contoh: http://182.23.82.141/phpmyadmin/ -> 182.23.82.141
    """
    if not target:
        return ""

    # Handle protocol-less URL patterns like example.com/path
    if "/" in target and not (target.startswith("http://") or target.startswith("https://")):
        # Simple heuristic: if it has a slash but no protocol, it might be a path
        # Check if it looks like an IP/domain before the slash
        parts = target.split("/", 1)
        potential_host = parts[0]
        # Very basic check for domain/IP: contains dot and no space
        if "." in potential_host and " " not in potential_host:
             target = "http://" + target

    if target.startswith("http://") or target.startswith("https://"):
        try:
            parsed = urlparse(target)
            return parsed.hostname or target
        except Exception:
            return target

    return target

def parse_llm_json(content: str) -> Union[Dict[str, Any], list]:
    """
    Ekstrak dan parse JSON dari output LLM secara robust.
    Mendukung format markdown ```json ... ```, string JSON mentah,
    dan membersihkan artefak markdown/teks narasi yang sering dikirim LLM.
    """
    if not content:
        return {}

    # Bersihkan whitespace
    json_str = content.strip()

    # 1. Coba cari blok kode markdown (handle unclosed blocks dan case-insensitive)
    # Menggunakan findall untuk menangani multiple blocks
    markdown_blocks = re.findall(r"```(?:json)?\s*(.*?)\s*(?:```|$)", json_str, re.DOTALL | re.IGNORECASE)

    if markdown_blocks:
        for block in markdown_blocks:
            cleaned_block = block.strip()
            if not cleaned_block:
                continue
            try:
                return json.loads(cleaned_block)
            except json.JSONDecodeError:
                # Coba cari JSON di dalam blok ini
                m = re.search(r"(\{.*\}|\[.*\])", cleaned_block, re.DOTALL)
                if m:
                    try:
                        return json.loads(m.group(1))
                    except json.JSONDecodeError:
                        pass
        # Jika semua blok gagal secara direct, gunakan blok pertama untuk pembersihan lebih lanjut
        json_str = markdown_blocks[0].strip()

    # 2. Pembersihan manual: hapus kata 'json' di awal dan backticks (permintaan user)
    json_str = re.sub(r"^\s*json\s*", "", json_str, flags=re.IGNORECASE).strip()
    json_str = json_str.replace("`", "").strip()

    # 3. Coba parse hasil pembersihan
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # 4. Fallback final: Cari pattern { ... } atau [ ... ] yang paling luar (greedy)
    # Ini menangani kasus di mana LLM menyisipkan JSON di tengah narasi tanpa blok kode
    patterns = [r"(\{.*\})", r"(\[.*\])"]
    for pattern in patterns:
        match = re.search(pattern, json_str, re.DOTALL)
        if match:
            candidate = match.group(1)
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                # Terakhir: coba hapus trailing commas yang sering dihasilkan LLM
                fixed = re.sub(r",\s*([\]}])", r"\1", candidate)
                try:
                    return json.loads(fixed)
                except json.JSONDecodeError:
                    pass

    # Jika gagal semua, raise error yang lebih deskriptif
    raise ValueError(f"Gagal mem-parse JSON dari content ({len(content)} chars): {content}")
