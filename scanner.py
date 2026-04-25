import re, subprocess, sys

FEATURES = {
    "env_trigger": re.compile(r"\+.*os\.getenv\("),
    "hidden_path": re.compile(r"\+.*(\.cache|Library/Caches|AppData)"),
    "encoding": re.compile(r"\+.*base64\.(b64encode|b64decode)"),
    "file_write": re.compile(r"\+.*\b(open\(|write\(|mkdir\(|chmod\()\b"),
    "telemetry_words": re.compile(r"\+.*(collection\(|telemetry|collect_context|append_record|exfil|beacon)"),
    "conditional_gate": re.compile(r"\+\s*if\s+not\s+collection\(\):"),
}



def git_diff(a: str, b: str) -> str:
    return subprocess.check_output(["git", "diff", f"{a}..{b}"], text=True, errors="ignore")

def detect(diff_text: str):
    feats = {k: bool(p.search(diff_text)) for k, p in FEATURES.items()}
    hits = [f"D_{k}" for k, v in feats.items() if v]

    combo = 0
    if feats["env_trigger"] and feats["file_write"] and (feats["hidden_path"] or feats["encoding"]):
        hits.append("D_combo_env_write_hide_or_encode")
        combo = 1

    score = len(hits) + combo
    return hits, score

if len(sys.argv) != 3:
    print("Usage: python3 scanner.py <from_ref> <to_ref>")
    sys.exit(2)

a, b = sys.argv[1], sys.argv[2]
diff_text = git_diff(a, b)
hits, score = detect(diff_text)

print("From:", a)
print("To:", b)
print("Triggered rules:", hits)
print("Risk score:", score)

if score >= 3:
    print("BLOCK")
elif score >= 1:
    print("REVIEW")
else:
    print("PASS")

