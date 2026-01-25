import re
import subprocess
import sys

RULES = {
    "D1_new_env_trigger": r"\+.*os\.getenv\(",
    "D2_new_hidden_cache_path": r"\+.*(\.cache|Library/Caches|AppData)",
    "D3_new_encoded_exfil": r"\+.*base64\.(b64encode|b64decode)",
    "D4_new_file_write": r"\+.*\b(open\(|write\(|mkdir\(|chmod\()\b",
    "D5_new_telemetry_keywords": r"\+.*(telemetry|collect_context|append_record|exfil|beacon)",
}

def git_diff(a: str, b: str) -> str:
    out = subprocess.check_output(["git", "diff", f"{a}..{b}"], text=True, errors="ignore")
    return out

def scan(diff_text: str):
    hits = []
    for name, pat in RULES.items():
        if re.search(pat, diff_text):
            hits.append(name)
    return sorted(set(hits))

if len(sys.argv) != 3:
    print("Usage: python3 scanner.py <from_ref> <to_ref>")
    print("Example: python3 scanner.py baseline-benign baseline-malicious")
    sys.exit(2)

a, b = sys.argv[1], sys.argv[2]
diff_text = git_diff(a, b)
hits = scan(diff_text)
score = len(hits)

print("From:", a)
print("To:", b)
print("Triggered rules:", hits)
print("Risk score:", score)

if score >= 3:
    print("BLOCK")
elif score >= 1:
    print("REVIEW")
else:
    print(" PASS")

