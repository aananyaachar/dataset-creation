import pandas as pd
import requests
import sys
import re

INPUT_FILE  = "influencer_master.csv"
OUTPUT_FILE = "final.csv"
OLLAMA_URL  = "http://localhost:11434/api/generate"
MODEL       = "llama3.2"
BATCH_SAVE  = 200


CATEGORY_AGE_MAP = {
    "beauty":   {"min": 16, "max": 30},
    "fashion":  {"min": 18, "max": 35},
    "fitness":  {"min": 18, "max": 34},
    "food":     {"min": 20, "max": 40},
    "travel":   {"min": 24, "max": 40},
    "family":   {"min": 25, "max": 44},
    "interior": {"min": 28, "max": 45},
    "pet":      {"min": 20, "max": 40},
    "other":    {"min": 18, "max": 40},
    "fsa":      {"min": 18, "max": 40},
}

NAME_KEYWORD_MAP = [
    (r"\bteen\b|\bstudent\b",          18,  40),
    (r"\bjunior\b|\bkid\b|\bchild\b",  18,  40),
    (r"\bmum\b|\bmom\b|\bmother\b|\bmummy\b|\bdad\b|\bfather\b|\bparent\b", 25, 40),
    (r"\bgrandma\b|\bgrandpa\b|\bnana\b|\bgran\b",  18,  40),
    (r"\bwife\b|\bhusband\b|\bmarried\b",            25,  40),
    (r"\bbride\b|\bwedding\b",                       22,  35),
    (r"\bsenior\b|\bretired\b",                      18,  40),
    (r"\buniversity\b|\bcollege\b|\buni\b",          18,  25),
    (r"\btoddler\b|\bnewborn\b|\bbaby\b",            25,  38),
]
def proxy_from_name(full_name: str):
    if not full_name or pd.isna(full_name):
        return None
    text = str(full_name).lower()
    for pattern, mn, mx in NAME_KEYWORD_MAP:
        if re.search(pattern, text):
            return {"min": mn, "max": mx, "source": "name_keyword"}
    return None

def proxy_from_category(category: str):
    cat = (str(category) if category and not pd.isna(category) else "other").lower().strip()
    mapping = CATEGORY_AGE_MAP.get(cat, CATEGORY_AGE_MAP["other"])
    return {"min": mapping["min"], "max": mapping["max"], "source": "category_proxy"}


def normalize_age_range(result: dict) -> dict:
    mn = max(result["min"], 18)
    mx = min(result["max"], 40)
    if mn >= mx:
        mn, mx = 18, 40
    return {"min": mn, "max": mx, "source": result.get("source", "unknown")}


def get_age_from_ollama(user: dict):
    try:
        prompt = f"""
You are analyzing an Instagram influencer profile.
Based ONLY on the name and username below, estimate the likely AUDIENCE age range.

Username : {user.get("username", "")}
Full name: {user.get("full_name", "")}

Reply with ONLY two numbers separated by a dash, like: 18-35
If you cannot determine it at all, reply: Unknown
Do NOT include any explanation.
"""
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        raw = response.json()["response"].strip().split("\n")[0].strip()

        match = re.match(r"(\d{1,3})\s*[-–]\s*(\d{1,3})", raw)
        if match:
            mn, mx = int(match.group(1)), int(match.group(2))
            if 10 <= mn < mx <= 80:
                return {"min": mn, "max": mx, "source": "ollama"}

        return None

    except Exception:
        return None

def get_age_range(user: dict):
    result = get_age_from_ollama(user)
    if result:
        return normalize_age_range(result)

    result = proxy_from_name(user.get("full_name", ""))
    if result:
        return normalize_age_range(result)

    return normalize_age_range(proxy_from_category(user.get("category", "other")))

def run_proxy_only(users: list):
    print(" Running proxy-only mode")
    for user in users:
        result = proxy_from_name(user.get("full_name", ""))
        if not result:
            result = proxy_from_category(user.get("category", "other"))
        result = normalize_age_range(result)
        user["age_min"]   = result["min"]
        user["age_max"]   = result["max"]
        user["age_label"] = f"{result['min']}-{result['max']}"
    return users

def main():
    print("Hybrid Age Range Extractor")
    print(f"Input : {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}\n")

    try:
        df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
        users = df.to_dict(orient="records")
        print(f" Loaded {len(users)} users")
    except Exception as e:
        print(f" Failed to load: {e}")
        sys.exit(1)

    print("\nChoose mode:")
    print("  1 — Proxy only      (instant, no Ollama, recommended)")
    print("  2 — Ollama + proxy  (slower but tries LLM first)")
    choice = input("\nEnter 1 or 2: ").strip()

    if choice == "1":
        users = run_proxy_only(users)
        pd.DataFrame(users).to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
        print("\nDone.")
        _print_summary(users)
        return

    print("\n Running Ollama + proxy hybrid mode...")
    processed = 0
    ollama_success = 0
    name_success   = 0
    proxy_used     = 0

    for index, user in enumerate(users):
        print(f"[{index+1}/{len(users)}] {user.get('username', '')}", end=" → ")

        result = get_age_range(user)
        user["age_min"]   = result["min"]
        user["age_max"]   = result["max"]
        user["age_label"] = f"{result['min']}-{result['max']}"
        processed += 1

        src = result["source"]
        if src == "ollama":
            ollama_success += 1
            print(f" Ollama: {user['age_label']}")
        elif src == "name_keyword":
            name_success += 1
            print(f"Name:   {user['age_label']}")
        else:
            proxy_used += 1
            print(f"Proxy:  {user['age_label']}")

        if processed % BATCH_SAVE == 0:
            pd.DataFrame(users).to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
            print(f" Progress saved at {processed} processed...")

    pd.DataFrame(users).to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

    print(f"\n Done. Saved to {OUTPUT_FILE}")
    print(f"\n Source breakdown:")
    print(f"   Ollama extracted : {ollama_success}")
    print(f" Name keywords    : {name_success}")
    print(f" Category proxy   : {proxy_used}")
    _print_summary(users)

def _print_summary(users):
    from collections import Counter
    labels = [u.get("age_label", "?") for u in users]
    counts = Counter(labels)
    print(f"\n Age label distribution (top 10):")
    for label, count in counts.most_common(10):
        print(f"   {label}: {count}")

if __name__ == "__main__":
    main()