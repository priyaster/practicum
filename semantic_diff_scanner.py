import subprocess, sys
from sentence_transformers import SentenceTransformer, util

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
model = SentenceTransformer(MODEL_NAME)

def sh(cmd):
    return subprocess.check_output(cmd, text=True, errors="ignore", stderr=subprocess.DEVNULL).strip()

def changed_py_files(a, b):
    out = sh(["git", "diff", "--name-only", f"{a}..{b}"])
    return [f for f in out.splitlines() if f.endswith(".py")]

def get_file(ref, path):
    try:
        return sh(["git", "show", f"{ref}:{path}"])
    except subprocess.CalledProcessError:
        return None

def cos(a_text, b_text):
    a = model.encode(a_text, convert_to_tensor=True, normalize_embeddings=True)
    b = model.encode(b_text, convert_to_tensor=True, normalize_embeddings=True)
    return float(util.cos_sim(a, b))

def decision(avg):
    if avg >= 0.95: return "PASS"
    if avg >= 0.90: return "REVIEW"
    return "FLAG"

if len(sys.argv) != 3:
    print("Usage: python3 semantic_diff_scanner.py <from_ref> <to_ref>")
    sys.exit(2)

a, b = sys.argv[1], sys.argv[2]
files = changed_py_files(a, b)

print(f"From: {a}")
print(f"To:   {b}")

if not files:
    print("No .py files changed.")
    print("Avg semantic similarity: 1.000000")
    print("Decision: PASS")
    sys.exit(0)

sims = []
for path in files:
    a_code = get_file(a, path)
    b_code = get_file(b, path)
    if a_code is None or b_code is None:
        print(f"{path}: SKIP (missing on one side)")
        continue
    s = cos(a_code, b_code)
    sims.append(s)
    print(f"{path}: similarity={s:.6f}")

if not sims:
    print("No comparable .py files (all missing on one side).")
    print("Decision: REVIEW")
    sys.exit(0)

avg = sum(sims) / len(sims)
print(f"Avg semantic similarity: {avg:.6f}")
print("Decision:", decision(avg))

