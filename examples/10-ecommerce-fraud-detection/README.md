# Example 10: Real-Time E-Commerce Fraud Detection

> Sub-100ms synchronous transaction risk classification, anomaly scoring, and dynamic authentication gating using Jev by TypeSafe AI.

---

## What It Does

Online merchants face an unrelenting dilemma: block fraud aggressively and alienate legitimate customers with false declines, or ease checkout friction and absorb catastrophic chargebacks.

This example scores incoming checkout orders in real time to:
1. Detect **fraudulent patterns** (disposable emails, card testing, datacenter proxies).
2. Assign orders to an operational **risk tier** (`low`, `medium`, `high`, `block`).
3. Compute a continuous **anomaly score** on a 3-level scale.
4. Flag borderline orders for **manual investigator review**.

---

## The Speed Advantage: 100ms vs. Gateway Timeout

Payment gateways (Stripe, Adyen, Cybersource) enforce strict **sub-2-second timeouts** on authorization webhooks. If your fraud evaluation service fails to respond within that window, the gateway aborts the transaction, triggering cart abandonment.

```
Traditional Generative LLM (2,000 – 8,000 ms):
[Customer Clicks "Pay"] ───▶ [Stripe Auth] ───▶ [LLM Prompt ...] ───▶ 💥 GATEWAY TIMEOUT / DROPPED CART

Jev System One AI (~100 ms):
[Customer Clicks "Pay"] ───▶ [Stripe Auth] ───▶ [Jev: 100ms] ───▶ [Approve / 3DS / Block] (Total < 250ms)
```

Generative LLMs cannot safely sit inline in high-throughput checkout paths. Jev delivers calibrated semantic classification in **~100ms**, executing well within payment gateway SLA budgets.

---

## Questions Defined

| Question | Primitive | Purpose | Schema Details |
|---|---|---|---|
| `is_fraudulent` | `noul` | Calibrated probability that the transaction is unauthorized or syndicate fraud. | `instructions: "Does this transaction exhibit high-confidence markers..."` |
| `risk_tier` | `choice` | Assigns transaction to an operational fraud mitigation tier. | `criteria: { "low": "...", "medium": "...", "high": "...", "block": "..." }` |
| `anomaly_score` | `score` | Continuous 3-level anomaly scale (0: Nominal, 1: Elevated, 2: Severe). | `criteria: ["Nominal...", "Elevated...", "Severe..."]` |
| `needs_manual_review` | `noul` | Probability that an order requires human risk analyst review prior to fulfillment. | `instructions: "Does this transaction warrant placing an order hold..."` |

---

## Architectural Insight: Adaptive Friction via Calibrated Probabilities

Rather than a crude binary decision (approve vs block), Jev's calibrated probabilities enable **dynamic friction**:

```python
# Low Risk (prob < 0.30): Frictionless one-click checkout
if is_fraudulent < 0.30 and risk_tier == "low":
    approve_instantly()

# Borderline / Medium Risk (0.30 <= prob < 0.85): Trigger Step-Up 3DS
elif risk_tier == "medium" or (0.30 <= is_fraudulent < 0.85):
    request_step_up_3ds_biometric_challenge()

# Extreme Risk (prob >= 0.85): Immediate decline & IP blacklist
elif risk_tier == "block" or is_fraudulent >= 0.85:
    decline_and_blacklist()
```

Legitimate customers enjoy instant checkout, while high-risk orders encounter step-up verification (SMS OTP or 3D Secure 2.0 biometric auth), eliminating both chargebacks and cart abandonment.

---

## How to Run

### 1. Install Dependencies
```bash
pip install requests python-dotenv
```

### 2. Configure Environment
Set your API key in `.env`:
```bash
TYPESAFE_API_KEY=your_api_key_here
```
*(If no API key is set, the script runs in simulation mode with calibrated distributions.)*

### 3. Execute Script
```bash
python fraud_detector.py
```

---

## Sample Output

```text
========================================================================
CHECKOUT FRAUD EVALUATION: TX-7011 - Normal Repeat Customer Purchase (Low Risk)
Gateway Decision Latency:  94.2 ms (Deadline: 2,000 ms)
========================================================================
Fraud Probability:         1.0%
Assigned Risk Tier:        LOW (Confidence: 98.0%)
Anomaly Score (0-2 scale): 0.04
Manual Review Probability: 2.0%

--- Inline Gateway Action ---
[GATEWAY RESPONSE: INSTANT AUTHORIZATION APPROVED]
  -> Zero checkout friction. Payment captured successfully.
  -> Order immediately dispatched to fulfillment pipeline.


========================================================================
CHECKOUT FRAUD EVALUATION: TX-7012 - Suspicious Bulk Digital Gift Cards at 3am (High Risk / Syndicate)
Gateway Decision Latency:  98.6 ms (Deadline: 2,000 ms)
========================================================================
Fraud Probability:         98.0%
Assigned Risk Tier:        BLOCK (Confidence: 96.0%)
Anomaly Score (0-2 scale): 1.96
Manual Review Probability: 5.0%

--- Inline Gateway Action ---
[GATEWAY RESPONSE: DECLINED / BLOCKED]
  -> Immediate transaction rejection (HTTP 402 Payment Declined).
  -> Blacklisted originating IP subnet and browser canvas fingerprint.
  -> Card issuer alerted: Stolen Card / Account Takeover pattern.


========================================================================
CHECKOUT FRAUD EVALUATION: TX-7013 - High-Value Purchase While Traveling (Borderline Case)
Gateway Decision Latency:  102.1 ms (Deadline: 2,000 ms)
========================================================================
Fraud Probability:         36.0%
Assigned Risk Tier:        MEDIUM (Confidence: 81.0%)
Anomaly Score (0-2 scale): 1.18
Manual Review Probability: 72.0%

--- Inline Gateway Action ---
[GATEWAY RESPONSE: STEP-UP AUTHENTICATION (3D SECURE 2.0)]
  -> Borderline risk / travel anomaly detected.
  -> Dispatched frictionless biometric / SMS-OTP challenge to cardholder's mobile.
  -> Fulfillment status set to HOLD pending 3DS confirmation.
```

---

## Console Payload

A console-ready JSON payload for the suspicious gift card purchase is available in [`payload.json`](./payload.json). Paste it directly into [console.typesafe.ai](https://console.typesafe.ai) to test live against Jev.
