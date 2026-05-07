import subprocess
import shutil
import os
from typing import Tuple

def run_command(cmd: list, timeout: int = 120, sudo: bool = False) -> Tuple[str, str]:
    """Jalankan perintah shell, return (stdout, stderr)."""
    if sudo:
        cmd = ["sudo"] + cmd
    binary = cmd[0]
    if binary != "sudo" and shutil.which(binary) is None:
        raise FileNotFoundError(f"Tool '{binary}' tidak ditemukan di PATH.")
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=os.environ.copy()
        )
        return proc.stdout, proc.stderr
    except subprocess.TimeoutExpired:
        return "", f"Timeout setelah {timeout} detik"
    except Exception as e:
        return "", str(e)
