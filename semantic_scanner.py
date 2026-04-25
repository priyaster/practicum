import subprocess, sys
from sentence_transformers import SentenceTransformer, util

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

def sh(cmd):
    return subprocess.check_output(
        cmd,
        text=True,
        errors="ignore",
        stderr=subprocess.DEVNULL
    ).strip()

def changed_py_files(a, b):
    out = sh(["git", "diff", "--name-only", f"{a}..{b}"])
    files = [f for f in out.splitlines() if f.endswith(".py")]
    return files

def get_file(ref, path):
    try:
        return sh(["git", "show", f"{ref}:{path}"])
    except subprocess.CalledProcessError:
        return ""

def score_text(a_text, b_text):
    a_emb = model.encode(a_text, convert_to_tensor=True, normalize_embeddings=True)
    b_emb = model.encode(b_text, convert_to_tensor=True, normalize_embeddings=True)
    return float(util.cos_sim(a_emb, b_emb))

def decision(sim):
    if sim >= 0.95:
        return "PASS"
    if sim >= 0.90:
        return "REVIEW"
    return "FLAG"

if len(sys.argv) != 3:
    print("Usage: python3 semantic_scanner.py <from_ref> <to_ref>")
    sys.exit(2)

a, b = sys.argv[1], sys.argv[2]
files = changed_py_files(a, b)

print(f"From: {a}")
print(f"To:   {b}")

if not files:
    print("No .py files changed.")
    print("Semantic similarity: 1.000")
    print("Decision: PASS")
    sys.exit(0)

sims = []
for path in files:
    a_code = get_file(a, path)
    b_code = get_file(b, path)
    if a_code is None or b_code is None:
        continue
    sim = score_text(a_code, b_code)
    sims.append(sim)
    print(f"{path}: similarity={sim:.3f}")

if not sims:
    print("No comparable files (missing on one side).")
    print("Decision: REVIEW")
    sys.exit(0)

avg = sum(sims) / len(sims)
print(f"Avg semantic similarity: {avg:.3f}")
print("Decision:", decision(avg))

