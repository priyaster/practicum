from __future__ import annotations
import base64
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict

def collection() -> bool:
    return os.getenv("LOGCONFIG_TELEMETRY") == "1";

def collect_context() -> Dict[str,Any]:
    return {
        "time": time.time(),
        "py": sys.version.split()[0],
        "platform": platform.platform(),
        "pid": os.getpid(),
        "cwd": os.getcwd(),
    };
def cache_file() -> Path:
    root = Path.home() / ".cache"
    folder = root / "logconfig"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / ".telemetry.log"
def append_record(record: Dict [str,Any]) -> None:
    payload = json.dumps(record, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = base64.b64encode(payload).decode("ascii")
    path = cache_file()
    with path.open("a", encoding="utf-8") as f:
        f.write(encoded + "\n")
def collect_telemetry()-> None:
    if not collection():
        return
    try:
        append_record(collect_context())
    except Exception:
        pass

if __name__ == "__main__":
    print("running telemetry test harness...")
    collect_telemetry()
    print("done")
