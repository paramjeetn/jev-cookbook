"""
Jev Cookbook — Quick Start
=========================
Verify your API key works with a simple Jev call.

Usage:
    pip install requests python-dotenv
    cp .env.example .env
    # Add your TYPESAFE_API_KEY or OPENROUTER_API_KEY to .env
    python quickstart.py
"""

import os, time, json, requests
from dotenv import load_dotenv

load_dotenv()

# Auto-detect API key
TYPESAFE_KEY = os.getenv("TYPESAFE_API_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

if TYPESAFE_KEY:
    API_KEY, BASE_URL, MODEL = TYPESAFE_KEY, "https://api.typesafe.ai/v1", "jev-1.13.0"
    print("✅ Using TypeSafe API")
elif OPENROUTER_KEY:
    API_KEY, BASE_URL, MODEL = OPENROUTER_KEY, "https://openrouter.ai/api/v1", "typesafe/jev-latest"
    print("✅ Using OpenRouter")
else:
    print("❌ Set TYPESAFE_API_KEY or OPENROUTER_API_KEY in .env")
    exit(1)

# --- The simplest possible Jev call ---
state = "The customer wrote: 'Your product is amazing, I just referred 3 friends!'"

questions = {
    "sentiment": {
        "type": "choice",
        "instructions": "What is the customer's sentiment?",
        "criteria": {
            "positive": "Happy, satisfied, praising the product.",
            "neutral": "Matter-of-fact, no strong emotion.",
            "negative": "Unhappy, frustrated, or angry."
        }
    },
    "is_promoter": {
        "type": "noul",
        "instructions": "Is this customer actively promoting the product to others?"
    },
    "engagement": {
        "type": "score",
        "instructions": "How engaged is this customer with the product?",
        "criteria": [
            "Passive. Using it but not enthusiastic.",
            "Active. Regularly engaged and satisfied.",
            "Champion. Actively promoting and referring others."
        ]
    }
}

print(f"\n📄 State: {state}")
print(f"❓ Questions: {list(questions.keys())}\n")

start = time.time()
resp = requests.post(
    f"{BASE_URL}/systemone",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={"model": MODEL, "state": state, "questions": questions}
)
elapsed = (time.time() - start) * 1000

if resp.status_code != 200:
    print(f"❌ Error {resp.status_code}: {resp.text}")
    exit(1)

data = resp.json()
answers = data.get("answers", data)

print(f"⚡ Response in {elapsed:.0f}ms\n")
print("📊 Results:")

# Choice
s = answers["sentiment"]
print(f"  🎯 sentiment    : {s['choice']}  (confidence: {s['confidence']:.0%})")

# Noul
p = answers["is_promoter"]
emoji = "✅" if p["noul"] > 0.7 else "❌"
print(f"  {emoji} is_promoter  : {p['noul']:.0%} probability")

# Score
e = answers["engagement"]
print(f"  📊 engagement   : {e['score']:.2f}  (confidence: {e['confidence']:.0%})")

print(f"\n{'─'*50}")
print("🎉 Jev is working! Explore the /examples folder next.")
print(f"   Tokens used: {data.get('usage', {}).get('input_tokens', 'N/A')} input")
