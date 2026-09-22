# Example 01: Customer Support Triage

Triages incoming support emails across **5 distinct dimensions** — urgency, customer sentiment, churn probability, operational category, and enterprise tier — in a single **~100ms** System One API call.

---

## 🎯 The Problem

Customer support queues in high-volume SaaS environments struggle with two failure modes:
1. **Rule-based keyword routing**: Brittle regex systems that miss nuances (e.g., mistaking a polite cancellation request for a standard account question).
2. **Generative LLM classification**: Passing emails to GPT-4/Claude requires 2,000–5,000ms of token generation, costs $0.01–$0.05 per ticket, and frequently breaks JSON schemas or hallucinates tags.

When an enterprise customer experiences a production outage costing $10,000/hour, waiting 4 seconds for an LLM to generate prose triage — or letting it sit in a general Zendesk queue for 45 minutes — breaches SLAs and triggers contract terminations.

---

## 💡 The Jev Solution

With **Jev**, triage is a **System One reflex**:
- **Zero text generation**: Evaluates probability distributions over predefined criteria.
- **Ultra-low latency**: Returns all 5 dimensions in **~100ms**.
- **Deterministic types**: Direct Python primitives (`float`, `str`, probabilities).
- **Cost effective**: At ~$0.042 per million tokens, you can triage 100,000 tickets for less than $0.50.

```
Incoming Support Email
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  POST https://api.typesafe.ai/v1/systemone                  │
│                                                             │
│  State: Full Email Body + Metadata                          │
│  Questions (Evaluated in Parallel):                         │
│    ├── urgency        → score (3-level rubric: 0 to 2)      │
│    ├── sentiment      → choice (very_neg/neg/neutral/pos)   │
│    ├── churn_risk     → noul (boolean probability 0.0–1.0)  │
│    ├── category       → choice (outage/billing/feature/auth)│
│    └── is_enterprise  → noul (boolean probability 0.0–1.0)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ ~100ms
                               ▼
               Clean Typed JSON Results in Python
                               │
       ┌───────────────────────┼────────────────────────┐
       ▼                       ▼                        ▼
[Enterprise Outage]    [Routine Billing]       [Feature Request]
  • Page On-Call Eng     • Dispatch to Invoicing • Ingest to Productboard
  • Alert VP of CS       • Auto-send VAT receipt • Tag PM Backlog
  • Open War Room        • SLA: 24 hours         • SLA: 48 hours
```

---

## 📁 Files in this Example

- [`triage.py`](triage.py) — Runnable Python script demonstrating 3 customer scenarios (Enterprise outage, routine billing, feature request) with automated dispatch logic.
- [`payload.json`](payload.json) — Console-ready JSON containing the state and typed questions for testing in [console.typesafe.ai](https://console.typesafe.ai).

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install requests python-dotenv
```

### 2. Configure Your Environment
Create a `.env` file in the project root or parent directory with your API key:
```env
TYPESAFE_API_KEY=your_typesafe_api_key_here
```
*(Alternatively, you can provide `OPENROUTER_API_KEY` for OpenRouter access).*

### 3. Execute the Script
```bash
python triage.py
```

---

## 📊 Sample Output

```text
===========================================================================
   Jev System One: Automated Customer Support Triage Demo
   Provider: TypeSafe AI Direct | Endpoint: https://api.typesafe.ai/v1/systemone
===========================================================================

>> Processing: [TICKET-101] Enterprise Production Outage
---------------------------------------------------------------------------
   Header: From: james.chen@globaltech-industries.com
   Subject: URGENT - Production API Outage costing $10k/hr - SLA Breach

   Evaluated in 98.4ms across 5 typed dimensions:
     [Score]     urgency        : 2.85/2.0  (confidence: 94%)
     [Choice]    sentiment      : very_negative  (confidence: 98%)
     [Noul]      churn_risk     : 92% probability TRUE
     [Choice]    category       : technical_outage  (confidence: 99%)
     [Noul]      is_enterprise  : 96% probability TRUE

   Automated Routing Action:
     Tier      : TIER-1: CRITICAL INCIDENT
     Action    : PAGE_ONCALL_ENG + ALERT_VP_CUSTOMER_SUCCESS
     SLA Target: 15 minutes (Enterprise War Room) [P1-CRITICAL]
     Rationale : Enterprise account (p=96%) suffering critical outage (urgency=2.85/2.0, sentiment=very_negative)
     Retention : [WARNING] Customer Success alert triggered (high churn risk)

>> Processing: [TICKET-102] Standard Billing Invoice Inquiry
---------------------------------------------------------------------------
   Header: From: accounting@creativepulse.io
   Subject: Request for updated VAT invoice for August 2026 (#INV-9921)

   Evaluated in 95.1ms across 5 typed dimensions:
     [Score]     urgency        : 0.15/2.0  (confidence: 92%)
     [Choice]    sentiment      : positive  (confidence: 88%)
     [Noul]      churn_risk     : 3% probability TRUE
     [Choice]    category       : billing  (confidence: 99%)
     [Noul]      is_enterprise  : 12% probability TRUE

   Automated Routing Action:
     Tier      : STANDARD QUEUE: BILLING
     Action    : DISPATCH_TO_INVOICE_SUPPORT
     SLA Target: 24 hours [P4-LOW]
     Rationale : Routine billing/tax adjustment (urgency=0.15)

>> Processing: [TICKET-103] Developer Feature Request
---------------------------------------------------------------------------
   Header: From: dev-sarah@cloudstride.dev
   Subject: Feature Suggestion: Webhook event for workspace member invitations

   Evaluated in 101.2ms across 5 typed dimensions:
     [Score]     urgency        : 0.20/2.0  (confidence: 90%)
     [Choice]    sentiment      : positive  (confidence: 93%)
     [Noul]      churn_risk     : 5% probability TRUE
     [Choice]    category       : feature_request  (confidence: 97%)
     [Noul]      is_enterprise  : 28% probability TRUE

   Automated Routing Action:
     Tier      : STANDARD QUEUE: PRODUCT FEEDBACK
     Action    : INGEST_TO_PRODUCTBOARD_BACKLOG
     SLA Target: 48 hours [P4-ROUTINE]
     Rationale : Feature suggestion from active user; auto-acknowledge with appreciation note
```

---

## 🏛️ Architectural Insight: Parallel Evaluation & Zero Latency Penalty

### 1. The O(1) Latency Scaling of System One
When asking an autoregressive generative model 5 distinct questions about a document, traditional architectures either:
- **Chain 5 separate LLM calls**: 5 × 1,500ms = 7,500ms total wall time.
- **Instruct one LLM to output a complex JSON dictionary**: 2,500ms generating 150+ tokens, subject to syntax parsing errors and hallucinations.

With Jev, **all questions are evaluated concurrently against the same state representation**:
$$\text{Latency}(Q_1, Q_2, Q_3, Q_4, Q_5) \approx \text{Latency}(Q_1) \approx 100\text{ms}$$

The model performs a single forward evaluation pass. Adding questions to the request does not add token-generation cycles because no text is generated.

### 2. Calibrated Confidence Gating
Unlike traditional LLMs where confidence values are fabricated text tokens ("I am 90% sure"), Jev's `confidence` is a mathematically calibrated probability over the criteria simplex.

This enables production-grade **confidence-gated routing**:
```python
# If the classifier encounters ambiguous text, do not guess
if result["category"]["confidence"] < 0.70:
    escalate_to_human_triage(ticket)
else:
    auto_route(result["category"]["choice"])
```

### 3. Continuous Urgency Scoring
Notice `urgency` returns `2.85` on a 3-level scale (0, 1, 2). Jev's `score` primitive calculates the expected value:
$$\mathbb{E}[\text{level}] = \sum_{i=0}^{N-1} i \cdot P(\text{level}_i \mid S)$$

This provides continuous gradient values that seamlessly plug into priority queues and sorting algorithms without arbitrary binning.
