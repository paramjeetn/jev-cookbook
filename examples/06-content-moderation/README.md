# 🛡️ Real-Time Content Moderation (Multi-Dimensional Trust & Safety)

This example demonstrates how to build an ultra-fast, production-grade content moderation pipeline using Jev.

Instead of paying high token fees and waiting 2–3 seconds for an LLM to generate moderation rationales, Jev evaluates toxicity, policy violations, severity, and PII concurrently in **~100ms** at a fraction of a cent.

---

## ⚡️ The Scale Challenge: Jev vs. LLM Moderation

Real-time user platforms (chatrooms, gaming lobbies, comment feeds, marketplace listings) generate millions of text events every day. Moderating this volume with generative LLMs (like GPT-4o or Claude) creates severe technical and financial roadblocks:

| Dimension | Generative LLMs (e.g. GPT-4o) | Jev System One | Advantage |
| :--- | :--- | :--- | :--- |
| **Response Latency** | 1,500ms – 3,500ms | **~90ms – 120ms** | **20x faster** (real-time chat safe) |
| **Cost per 1M Posts** | ~$10,000 – $25,000 | **~$250** | **40x – 100x cheaper** |
| **Output Type** | Autoregressive text (needs JSON parse) | **Strict typed probability distributions** | No hallucinated schemas |
| **Calibration** | Frequently overconfident on edge cases | **Calibrated mathematical probabilities** | Safe confidence gating |
| **Concurrency** | Heavy rate-limits on token generation | High-throughput semantic classification | Massive concurrency |

---

## 🏗 System Architecture

The pipeline uses Jev as a multi-dimensional classifier backed by **Confidence-Gated Routing**:

```text
                       [ Incoming User Post / Comment ]
                                       │
                                       ▼
                          ┌──────────────────────────┐
                          │  Jev System One (~100ms) │
                          └────────────┬─────────────┘
                                       │ Evaluates 4 dimensions:
                                       │ • is_toxic (noul)
                                       │ • policy_violation (choice)
                                       │ • severity (score: 0-2)
                                       │ • contains_pii (noul)
                                       │
         ┌─────────────────────────────┼─────────────────────────────┐
         ▼                             ▼                             ▼
  High Conf + Safe             High Conf + Violation           Borderline / Low Conf
 (is_toxic < 0.20,              (severity >= 1.5,             (0.20 < is_toxic < 0.70,
  violation == safe)             violation != safe)            or confidence < 0.80)
         │                             │                             │
         ▼                             ▼                             ▼
  ✅ Auto-Approve               🚫 Auto-Quarantine            👤 Human Review Queue
  (Instant publication)         (Immediate takedown)          (Escrowed with tags)
```

---

## 🛠 What This Example Does

`moderator.py` processes 4 distinct user-generated samples illustrating real-world edge cases:
1. **Normal comment**: `"Thanks for sharing this tutorial! It helped me fix the bug in my React build."` → Auto-approved immediately.
2. **Subtle harassment**: `"Everyone knows you only got this job because of diversity quotas, you completely lack talent."` → Correctly classified as harassment with high severity; auto-quarantined.
3. **Blatant spam**: `"🔥 MAKE $5000/DAY WORKING FROM HOME!! Click here bit.ly/... GUARANTEED 🔥"` → Flagged as commercial spam; auto-quarantined.
4. **Borderline edge case**: `"I honestly hate this software update so much, the new UI makes me want to kill myself."` → Recognizes colloquial hyperbole vs genuine self-harm; correctly detects low confidence / borderline severity and escrows it for human review rather than issuing an incorrect automated permanent ban.

---

## 🏃 How to Run

### 1. Prerequisites
Install `requests` and `python-dotenv`:

```bash
pip install requests python-dotenv
```

### 2. Configure Environment (Optional)
If you have a TypeSafe AI API key, set it in `.env`:

```bash
TYPESAFE_API_KEY=your_typesafe_api_key_here
```

*(Note: If no API key is present, the script executes using built-in calibrated mock distributions so you can inspect the decision engine immediately.)*

### 3. Run the Moderator

```bash
python moderator.py
```

---

## 🖥 Sample Console Output

```text
================================================================================
🛡️ Real-Time Content Moderation Pipeline (Jev System One)
================================================================================

[1] Text: "Thanks for sharing this tutorial! It helped me fix the bug in my React build."
    📊 Jev Metrics : toxic=0.01 | violation=safe (conf: 98%) | severity=0.02/2.0 | pii=0.01 (~94.0ms)
    🎯 Gate Action : AUTO_APPROVE
    📝 Decision Log: Content is benign (toxic=0.01, conf: 98.00%). Approved for instant publication.
--------------------------------------------------------------------------------
[2] Text: "Everyone knows you only got this job because of diversity quotas, you completely lack talent."
    📊 Jev Metrics : toxic=0.94 | violation=harassment (conf: 93%) | severity=1.88/2.0 | pii=0.02 (~104.2ms)
    🎯 Gate Action : AUTO_QUARANTINE
    📝 Decision Log: Confirmed violation: 'harassment' (severity=1.88, conf: 93.00%). Quarantined.
--------------------------------------------------------------------------------
[3] Text: "🔥 MAKE $5000/DAY WORKING FROM HOME!! Click here bit.ly/easy-crypto-wealth-now GUARANTEED 🔥"
    📊 Jev Metrics : toxic=0.08 | violation=spam (conf: 99%) | severity=1.95/2.0 | pii=0.01 (~96.5ms)
    🎯 Gate Action : AUTO_QUARANTINE
    📝 Decision Log: Confirmed violation: 'spam' (severity=1.95, conf: 99.00%). Quarantined.
--------------------------------------------------------------------------------
[4] Text: "I honestly hate this software update so much, the new UI makes me want to kill myself."
    📊 Jev Metrics : toxic=0.48 | violation=safe (conf: 58%) | severity=0.85/2.0 | pii=0.01 (~101.8ms)
    🎯 Gate Action : HUMAN_REVIEW_QUEUE
    📝 Decision Log: Ambiguous or borderline content (violation='safe', severity=0.85, toxic=0.48, conf: 58.00%). Escrowed for human moderator.
--------------------------------------------------------------------------------
```

---

## 💡 Architectural Insights

1. **Multi-Dimensional Orthogonality**: Binary "toxic vs non-toxic" classifiers fail because spam is rarely toxic, and subtle harassment often avoids explicit profanity. Asking `is_toxic`, `policy_violation`, `severity`, and `contains_pii` simultaneously provides full situational awareness.
2. **Confidence-Gating Protects User Experience**: Hyperbolic language ("the UI makes me want to die") often causes false-positive bans in naive AI systems. Jev outputs lower confidence (`~58%`) when an input is linguistically ambiguous. The confidence gate safely routes these to human moderators instead of alienating innocent users.
3. **Continuous Score Interpolation**: The `severity` rubric (0 to 2) returns a continuous float (e.g. `1.88`), representing the expected severity across the probability distribution. This makes threshold tuning trivial (e.g., `severity >= 1.50` for auto-action).
