# Example 08: DevOps Incident Routing

> Automated incident severity scoring, domain team assignment, and on-call paging decisions in ~100ms using Jev by TypeSafe AI.

---

## What It Does

When an incident strikes, seconds matter. Traditional regex alerting rules are brittle across microservices, while generative LLMs take 3–5 seconds and often hallucinate severity levels or non-existent teams.

This example processes raw APM, cloud monitoring, and security telemetry through Jev to determine:
1. **Severity score** on an ordered P4 to P1 scale.
2. **Owning engineering team** (`backend`, `frontend`, `security`, `infrastructure`, or `data`).
3. **Customer impact** (whether end users are actively affected).
4. **Paging urgency** (whether to wake up an on-call engineer or file a quiet ticket).

---

## Questions Defined

| Question | Primitive | Purpose | Schema Details |
|---|---|---|---|
| `severity` | `score` | Calibrated continuous score across 4 ordered levels (0: P4 Low, 1: P3 Medium, 2: P2 High, 3: P1 Critical). | `criteria: ["P4 - Low...", "P3 - Medium...", "P2 - High...", "P1 - Critical..."]` |
| `team` | `choice` | Determines which functional team owns primary remediation. | `criteria: { "backend": "...", "frontend": "...", "security": "...", "infrastructure": "...", "data": "..." }` |
| `is_customer_facing` | `noul` | Probability that public traffic, UI, or external transactions are impacted. | `instructions: "Does this incident directly impact external customer transactions..."` |
| `needs_page` | `noul` | Probability that an on-call engineer must be paged immediately. | `instructions: "Does this incident meet the threshold to immediately page on-call staff..."` |

---

## Architectural Insight: Guarding the Pager with Calibrated Probabilities

### 1. Alert Noise vs. Pager Fatigue
On-call burnout is primarily caused by uncalibrated alerts waking engineers up for cosmetic CSS bugs or transient metrics. By using Jev's `needs_page` probability and `severity` score as strict gates in code, you decouple semantic classification from operational policy:

```python
# Guardrail: Programmatic paging policy in version-controlled Python
if needs_page >= 0.80 or severity_score >= 2.5:
    trigger_pagerduty_incident(team)
else:
    queue_slack_ticket(team)  # Business hours review
```

### 2. Zero-Latency Pipeline Integration
Monitoring platforms like Datadog, Prometheus, AWS CloudWatch, and PagerDuty post webhooks that expect responses within 500ms. Jev evaluates all 4 questions in parallel within ~100ms, making it ideal for inline webhook middleware before alerts hit the notification bus.

---

## How to Run

### 1. Install Dependencies
```bash
pip install requests python-dotenv
```

### 2. Configure Environment
Set your API key in a `.env` file or export it:
```bash
TYPESAFE_API_KEY=your_api_key_here
```
*(If no API key is provided, the script runs in simulation mode with calibrated distributions.)*

### 3. Execute Script
```bash
python incident_router.py
```

---

## Sample Output

```text
======================================================================
INCIDENT CLASSIFICATION: ALT-9021 - Database Connection Pool Exhaustion (Aurora Postgres)
======================================================================
Calculated Severity:   P1 - CRITICAL (Score: 2.91)
Assigned Team:         INFRASTRUCTURE (Confidence: 94.0%)
Customer Facing:       YES (98.0%)
Page Probability:      99.0%

--- Dispatch & Automated Remediation ---
[DISPATCH: PAGERDUTY HIGH-SEVERITY] Paging INFRASTRUCTURE primary on-call.
  -> Generated Incident Room: #inc-20260922-alt-9021
  -> Automated Zoom bridge provisioned and broadcast to statuspage.
[AUTOMATION: INFRA RESILIENCE] Initiated horizontal pod autoscaler step-up.
  -> Sent kill signal to idle backend connection pools to release DB slots.


======================================================================
INCIDENT CLASSIFICATION: ALT-9022 - CSS Rendering Glitch on Mobile Safari (UI Layout Overflow)
======================================================================
Calculated Severity:   P4 - LOW (Score: 0.45)
Assigned Team:         FRONTEND (Confidence: 98.0%)
Customer Facing:       YES (96.0%)
Page Probability:      4.0%

--- Dispatch & Automated Remediation ---
[DISPATCH: NON-PAGING TICKET] Queued to #frontend-triage Slack channel.
  -> Logged Jira ticket with SLA: 8 business hours. No on-call wake-up.
[AUTOMATION: BUG TRACKER] Created UI sprint defect ticket in Linear with device context.


======================================================================
INCIDENT CLASSIFICATION: ALT-9023 - Suspicious Login from Unusual Geography (Admin Account Takeover Risk)
======================================================================
Calculated Severity:   P1 - CRITICAL (Score: 2.76)
Assigned Team:         SECURITY (Confidence: 99.0%)
Customer Facing:       NO (6.0%)
Page Probability:      96.0%

--- Dispatch & Automated Remediation ---
[DISPATCH: PAGERDUTY HIGH-SEVERITY] Paging SECURITY primary on-call.
  -> Generated Incident Room: #inc-20260922-alt-9023
  -> Automated Zoom bridge provisioned and broadcast to statuspage.
[AUTOMATION: ACTIVE DEFENSE] Revoked active Okta sessions for affected admin account.
  -> Rotated AWS STS temporary credentials. Ingress IP quarantined in Cloudflare.
```

---

## Console Payload

A console-ready JSON payload for the database exhaustion scenario is available in [`payload.json`](./payload.json). Paste it directly into [console.typesafe.ai](https://console.typesafe.ai) to test live against Jev.
