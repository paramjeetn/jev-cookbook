<h1 align="center">
  Jev Cookbook 🧠⚡️
</h1>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License MIT">
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen.svg" alt="PRs Welcome">
  <img src="https://img.shields.io/badge/Use%20Cases-120%2B-orange.svg" alt="120+ Use Cases">
  <img src="https://img.shields.io/badge/Examples-10-blueviolet.svg" alt="10 Examples">
  <img src="https://img.shields.io/badge/Powered%20By-TypeSafe%20AI-black.svg" alt="TypeSafe AI">
</p>

<p align="center">
  <img src="assets/banner.jpg" alt="Jev Cookbook — State → Jev (~100ms) → Choice, Score, Noul" width="100%">
</p>

<p align="center">
  <strong>Production-ready examples, patterns, and theory for building with Jev — the 100ms System One AI.</strong>
  <br><br>
  <a href="#-quick-start">Quick Start</a> · <a href="#-examples">10 Examples</a> · <a href="THEORY.md">Theory</a> · <a href="USE_CASES.md">120+ Use Cases</a> · <a href="#-patterns">Patterns</a>
</p>

---

## ⚡️ What is Jev?

Jev is a "System One" AI model built by TypeSafe AI — a calibrated zero-shot semantic classifier, not a text generator. It takes a context `state` and typed `questions`, returning calibrated probability distributions instead of tokens. Because it doesn't generate text, Jev processes complex reasoning tasks in **~100ms**, operates at **400x lower cost** than traditional LLMs, and provides mathematically rigorous **calibrated confidence scores** for every decision. 

## 🏗 Architecture: Where Jev Fits

Stop waiting seconds for an LLM to output a JSON boolean. Jev acts as the ultra-fast instinct layer in your application:

```text
[ Incoming Data ] 
       │
       ▼
 ┌─────────────┐
 │  Jev (100ms)│ ──(Low Confidence)──► 🤖 Slow LLM Fallback (GPT-4 / Claude)
 └──────┬──────┘
        │ (High Confidence)
        ▼
[ Structured JSON Decision ]
        │
        ▼
  ⚙️ Application Logic (Code acts on it)
```

## 🚀 Quick Start (No SDK Required)

### 1. The 30-Second Console Test
Go to [console.typesafe.ai](https://console.typesafe.ai) and paste this into the payload editor:

```json
{
  "state": "The user clicked 'Cancel Subscription' after experiencing multiple app crashes.",
  "questions": {
    "intent": {
      "type": "choice",
      "instructions": "Why is the user canceling?",
      "criteria": {
        "bug_frustration": "User encountered technical issues",
        "price": "Too expensive",
        "unknown": "Reason not specified"
      }
    }
  }
}
```

### 2. Python `requests` Implementation

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def analyze_intent():
    url = "https://api.typesafe.ai/v1/systemone"
    headers = {
        "Authorization": f"Bearer {os.getenv('TYPESAFE_API_KEY')}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "state": "The user clicked 'Cancel Subscription' after experiencing multiple app crashes.",
        "questions": {
            "intent": {
                "type": "choice",
                "instructions": "Why is the user canceling?",
                "criteria": {
                    "bug_frustration": "User encountered technical issues",
                    "price": "Too expensive",
                    "unknown": "Reason not specified"
                }
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    print(response.json())

if __name__ == "__main__":
    analyze_intent()
```

## 🧱 The 3 Core Primitives

Jev is built on three typed questions. **Always use these exact schemas.**

| Primitive | Description | Schema Structure | Example Output |
|-----------|-------------|-------------------|----------------|
| **Choice** | Categorize into exact keys | `{"type": "choice", "criteria": {"key": "desc"}}` | `{"choice": "key", "confidence": 0.98}` |
| **Score** | Rank on an ordered scale (2-10 levels) | `{"type": "score", "criteria": ["low", "med", "high"]}` | `{"score": 2.1, "confidence": 0.85}` |
| **Noul** | True/False boolean probability | `{"type": "noul", "instructions": "Is X true?"}` | `{"noul": 0.99, "confidence": 0.99}` |

## 📊 Live Results: Trading Signal Extraction

We ran an earnings call transcript through Jev. Here are the actual results from our live test:

- **`guidance_revision`**: `revised_down` (100% confidence)
- **`margin_sentiment`**: `0.78` (77% confidence)
- **`capital_allocation`**: `share_buyback` (100% confidence)
- **`signal_ambiguity`**: `2.0` (100% confidence)
- ⏱ **Evaluation Time**: `100.79ms`

## 📂 Examples Directory

Jump straight into runnable code. Every example includes a `payload.json`, a Python script, and a detailed README.

| Example | Title | Description | Pattern |
|---------|-------|-------------|---------|
| [01](./examples/01_customer_support) | 🎧 Customer Support Triage | Categorize tickets instantly before routing | Composite Scoring |
| [02](./examples/02_trading_signals) | 📈 Trading Signal Extraction | **(LIVE TESTED)** Extract market alpha from transcripts | Speculative Fan-Out |
| [03](./examples/03_agent_safety) | 🛡️ Agent Safety Guardrails | 100ms content filtering for AI agents | Confidence-Gated Routing |
| [04](./examples/04_web_agent) | 🌐 Web Agent DOM Navigation | Ported from browser-use/jev-ultrafast | Hybrid Agent Loop |
| [05](./examples/05_llm_router) | 🔀 LLM Model Router | Route easy queries to cheap models, hard ones to GPT-4 | Confidence-Gated Routing |
| [06](./examples/06_content_mod) | 🚫 Content Moderation | Multi-dimensional toxicity scoring | Composite Scoring |
| [07](./examples/07_healthcare_triage) | 🏥 Healthcare Triage | Fast patient urgency categorization | Confidence-Gated Routing |
| [08](./examples/08_devops_routing) | 📟 DevOps Incident Routing | Assign PagerDuty incidents by log severity | Speculative Fan-Out |
| [09](./examples/09_legal_contracts) | 📜 Legal Contract Analysis | Flag missing clauses and risky terms | Composite Scoring |
| [10](./examples/10_ecommerce_fraud) | 🕵️ E-commerce Fraud Detection | Analyze user behavior events for anomalies | Composite Scoring |

## 🧩 Architectural Patterns

Learn how to structure Jev in production:
- [Composite Scoring](./docs/patterns/composite-scoring.md): Combine multiple scores to create complex metrics.
- [Confidence-Gated Routing](./docs/patterns/confidence-gated-routing.md): Fallback to slower LLMs only when Jev's confidence is low.
- [Speculative Fan-Out](./docs/patterns/speculative-fan-out.md): Query 50 different properties simultaneously.
- [Hybrid Agent Loop](./docs/patterns/hybrid-agent-loop.md): Use Jev for the inner `OODA` loop and LLMs for generation.

## 📚 References & Theory

- [API Schema Reference](./docs/api-schema.md) — Exact payloads and types
- [Primitives Cheatsheet](./docs/primitives-cheatsheet.md) — Quick copy-paste snippets
- [The Theory of System One AI](./docs/THEORY.md) — Why classification beats generation
- [120+ Use Cases](./docs/USE_CASES.md) — Exhaustive list of what you can build

## ⚖️ Key Numbers: Jev vs LLMs

| Metric | Jev (System 1) | GPT-4o (System 2) |
|--------|----------------|-------------------|
| **Latency** | ~100ms | 1s - 5s+ |
| **Cost** | 400x Cheaper | Expensive |
| **Output** | Guaranteed strict JSON | Needs strict prompting / JSON mode |
| **Hallucinations** | None (Calibrated Math) | Possible (Autoregressive) |
| **Confidence** | mathematically rigorous | Often overconfident |

## ⚠️ Common Mistakes (Top 5)

1. **Using `options` instead of `criteria` in Choice.** (Fails validation!)
2. **Using `min`/`max` in Score instead of an array in `criteria`.**
3. **Expecting Jev to generate text.** It only returns probabilities based on your schema.
4. **Providing generic `state` text.** Jev needs detailed context to classify accurately.
5. **Ignoring the `confidence` score.** Always check it before routing!

## 🌍 Community & Resources

- [TypeSafe AI Console](https://console.typesafe.ai)
- [Official TypeSafe Docs](https://docs.typesafe.ai)
- [jev-ultrafast Repository](https://github.com/browser-use/jev-ultrafast)

---

<p align="center">
  <i>Explored and documented by @paramjeet — September 2026</i> <br>
  <b>If this helps you build faster, please ⭐️ Star and 🔱 Fork this repository!</b>
</p>
