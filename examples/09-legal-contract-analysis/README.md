# Example 09: Legal Contract Clause Analysis

> Fast, calibrated semantic risk pre-screening of contract clauses using Jev by TypeSafe AI.

---

## What It Does

Reviewing enterprise contracts, MSAs, and employment agreements is often an expensive bottleneck. General counsel teams spend hundreds of hours reading boilerplate just to find a few dangerous clauses.

This example scans clauses individually to classify their type and quantify risk before attorney review.

> [!IMPORTANT]
> **Jev flags risk — human lawyers decide.** Jev is a System One semantic classifier, not an attorney. It does not provide legal advice, interpret statutory precedents, or draft final agreements. Instead, it acts as a rapid triage filter to flag high-risk terms (uncapped liabilities, aggressive non-competes, one-sided indemnities) and green-light standard market boilerplate.

---

## Questions Defined

| Question | Primitive | Purpose | Schema Details |
|---|---|---|---|
| `risk_level` | `score` | Continuous 4-level risk score (0: Negligible, 1: Low, 2: Moderate, 3: Critical). | `criteria: ["Level 0 - Negligible...", "Level 1 - Low...", "Level 2 - Moderate...", "Level 3 - High..."]` |
| `clause_type` | `choice` | Categorizes the legal domain of the provision. | `criteria: { "liability": "...", "payment": "...", "ip": "...", "non_compete": "...", "termination": "...", "indemnification": "..." }` |
| `needs_legal_review` | `noul` | Probability that the clause warrants formal attorney review or redlining. | `instructions: "Does this clause warrant mandatory escalation, negotiation, or redlining..."` |
| `is_standard` | `noul` | Probability that the clause represents standard, balanced market boilerplate. | `instructions: "Does this provision reflect standard, balanced market boilerplate..."` |

---

## Architectural Insight: Clause-by-Clause Semantic Triage

### 1. High-Throughput Pre-Screening
Enterprise procurement contracts can span 50 to 100 pages. Sending an entire 100-page document into a generative LLM context window often triggers attention dilution (lost in the middle) and costs dollars per contract. By chunking documents into sections and scanning each against Jev in ~100ms, an entire contract can be triaged in parallel in seconds for pennies.

### 2. Dual-Track Workflow Routing
Calibrated probabilities enable deterministic triage routing:
```python
# Green Track: Standard boilerplate bypasses legal queue
if is_standard >= 0.80 and risk_level < 1.0:
    auto_approve_for_signature()

# Red Track: Uncapped or non-standard provisions escalate to specialized counsel
elif needs_legal_review >= 0.75 or risk_score >= 2.0:
    escalate_to_counsel(clause_type, risk_score)
```

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
python contract_scanner.py
```

---

## Sample Output

```text
======================================================================
CLAUSE SCANNER: CLAUSE-01 - Unlimited Liability & Broad Indemnity (Vendor Agreement)
======================================================================
Clause Type:           LIABILITY (Confidence: 94.0%)
Assessed Risk Tier:    CRITICAL RISK (Score: 2.95 / 3.00)
Market Standard Term:  NO (2.0%)
Legal Review Needed:   YES (99.0%)

--- Workflow Routing Decision ---
[ROUTING: ESCALATE TO SENIOR COUNSEL]
  -> High exposure detected in 'LIABILITY' provision.
  -> Blocking contract execution until redline approval.
  -> Playbook Suggestion: Insert mutual 12-month trailing fee liability cap.


======================================================================
CLAUSE SCANNER: CLAUSE-02 - Standard Net 30 Commercial Payment Terms (Master Services Agreement)
======================================================================
Clause Type:           PAYMENT (Confidence: 99.0%)
Assessed Risk Tier:    NEGLIGIBLE RISK (Score: 0.12 / 3.00)
Market Standard Term:  YES (96.0%)
Legal Review Needed:   NO (5.0%)

--- Workflow Routing Decision ---
[ROUTING: EXPEDITED AUTO-APPROVAL]
  -> Clause conforms to company standard procurement terms.
  -> Green-pathed for digital signature; bypassed legal triage backlog.


======================================================================
CLAUSE SCANNER: CLAUSE-03 - Global Restrictive Covenant (Executive Employment Agreement)
======================================================================
Clause Type:           NON_COMPETE (Confidence: 98.0%)
Assessed Risk Tier:    CRITICAL RISK (Score: 2.78 / 3.00)
Market Standard Term:  NO (8.0%)
Legal Review Needed:   YES (97.0%)

--- Workflow Routing Decision ---
[ROUTING: ESCALATE TO SENIOR COUNSEL]
  -> High exposure detected in 'NON_COMPETE' provision.
  -> Blocking contract execution until redline approval.
  -> Playbook Suggestion: Strike worldwide territory; limit to direct competitors within 25 miles.
```

---

## Console Payload

A console-ready JSON payload for the unlimited liability clause is available in [`payload.json`](./payload.json). Paste it directly into [console.typesafe.ai](https://console.typesafe.ai) to test live against Jev.
