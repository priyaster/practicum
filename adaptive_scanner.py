import subprocess
import re
import sys
from sentence_transformers import SentenceTransformer, util

MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

STATIC_FEATURES = {
    "env_trigger": re.compile(r"\+.*os\.getenv\("),
    "hidden_path": re.compile(r"\+.*(\.cache|Library/Caches|AppData)"),
    "encoding": re.compile(r"\+.*base64\.(b64encode|b64decode)"),
    "file_write": re.compile(r"\+.*\b(open\(|write\(|mkdir\(|chmod\()\b"),
    "telemetry_words": re.compile(r"\+.*(collection\(|collect_context|append_record|exfil|beacon)"),
}

def sh(cmd):
    return subprocess.check_output(
        cmd,
        text=True,
        errors="ignore",
        stderr=subprocess.DEVNULL
    )

def git_diff(a, b):
    return sh(["git", "diff", f"{a}..{b}"])

def semantic_score(a, b):
    """
    Compute semantic similarity of telemetry.py between two refs.
    Returns None if file missing in either ref.
    """
    try:
        a_text = sh(["git", "show", f"{a}:telemetry.py"])
        b_text = sh(["git", "show", f"{b}:telemetry.py"])
    except subprocess.CalledProcessError:
        return None

    a_emb = MODEL.encode(a_text, convert_to_tensor=True, normalize_embeddings=True)
    b_emb = MODEL.encode(b_text, convert_to_tensor=True, normalize_embeddings=True)

    return float(util.cos_sim(a_emb, b_emb))

if len(sys.argv) != 3:
    print("Usage: python3 adaptive_scanner.py <from> <to>")
    sys.exit(2)

a, b = sys.argv[1], sys.argv[2]
diff = git_diff(a, b)

static_hits = [k for k, r in STATIC_FEATURES.items() if r.search(diff)]
static_score = len(static_hits)

combo_penalty = 0
if ("env_trigger" in static_hits and
    "file_write" in static_hits and
    "hidden_path" in static_hits):
    combo_penalty = 2


sim = semantic_score(a, b)

semantic_weight = 0
has_change = diff.strip() != ""

if has_change and sim is not None:
    if sim >= 0.95 and static_score >= 1:
        semantic_weight = 2
    elif sim >= 0.90 and static_score >= 1:
        semantic_weight = 1

total = static_score + semantic_weight + combo_penalty

print("From:", a)
print("To:", b)
print("Static hits:", static_hits)
print("Static score:", static_score)

if sim is not None:
    print("Semantic similarity:", round(sim, 3))
else:
    print("Semantic similarity: N/A (file missing)")

print("Semantic weight:", semantic_weight)
print("Combo penalty:", combo_penalty)
print("Total risk:", total)

if total >= 4:
    print("FINAL DECISION: BLOCK")
elif total >= 2:
    print("FINAL DECISION: REVIEW")
else:
    print("FINAL DECISION: PASS")

