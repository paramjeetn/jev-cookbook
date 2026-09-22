# Example 07: Healthcare Patient Intake Triage

> Fast, calibrated clinical acuity classification and intake routing using Jev by TypeSafe AI.

---

## What It Does

This example classifies patient intake forms and triage narratives to determine clinical urgency and route the patient to the appropriate care level (Primary Care, Urgent Care, Emergency Room, or 911 dispatch).

> [!IMPORTANT]
> **Jev does NOT diagnose disease.** Clinical diagnosis requires multi-step deductive reasoning, lab analysis, and physician judgment (System Two). Jev is a **System One** semantic classifier: it rapidly evaluates intake text against standardized clinical acuity rubrics (such as the Emergency Severity Index / ESI) to prioritize queues and direct patients to the right medical setting in ~100ms.

---

## Questions Defined

| Question | Primitive | Purpose | Schema Details |
|---|---|---|---|
| `urgency` | `score` | Measures clinical acuity on a 4-level scale (0: Routine, 1: Semi-urgent, 2: Urgent, 3: Emergency). | `criteria: ["Routine...", "Semi-urgent...", "Urgent...", "Emergency..."]` |
| `care_level` | `choice` | Selects recommended care destination. | `criteria: { "primary_care": "...", "urgent_care": "...", "emergency_room": "...", "call_911": "..." }` |
| `follow_up_needed` | `noul` | Probability that patient requires scheduled continuity of care. | `instructions: "Will this clinical condition require mandatory structured follow-up care..."` |
| `mental_health_flag` | `noul` | Critical safety sentinel for active self-harm or psychiatric crisis. | `instructions: "Does this patient intake indicate an acute psychological crisis..."` |

---

## Architectural Insight: Why System One for Medical Triage?

### 1. Zero Hallucination Risk in Routing
Generative LLMs (GPT-4, Claude) generate tokens probabilistically. When prompted for triage, an LLM might generate plausible-sounding medical advice or invent non-existent contraindications. Jev **never generates text**. Its output is strictly bounded to the probability simplex over the criteria you specify.

### 2. Sub-100ms Intake at Scale
During surges (e.g., flu season, ED saturation, telehealth spikes), synchronous intake queues cannot tolerate 3–8 second generative LLM latency. Jev evaluates all questions in parallel in ~100ms, enabling real-time routing directly inside digital registration kiosks and call centers.

### 3. Programmatic Safety Guardrails
Because Jev outputs true calibrated probabilities, safety logic lives in deterministic code, not prompts:
```python
# Guardrail: Immediate psychiatric crisis escalation
if mental_health_flag > 0.60:
    route_to_crisis_counselor()

# Guardrail: Emergency threshold gating
if urgency_score >= 2.5 or care_level == "emergency_room":
    dispatch_emergency_bay()
```

---

## How to Run

### 1. Install Dependencies
```bash
pip install requests python-dotenv
```

### 2. Configure Environment
Create a `.env` file in your working directory (or set the variable in your shell):
```bash
TYPESAFE_API_KEY=your_api_key_here
```
*(Note: If no API key is provided, the script runs in simulation mode with realistic calibrated distributions so you can test the pipeline immediately.)*

### 3. Execute Script
```bash
python triage.py
```

---

## Sample Output

```text
======================================================================
PATIENT INTAKE EVALUATION: PT-10492 - Chest Pain & Dyspnea (Suspected Acute Coronary Syndrome)
======================================================================
Urgency Score (0-3 scale): 2.94 (Confidence: 98.0%)
Care Disposition:          EMERGENCY_ROOM (Confidence: 96.0%)
Follow-up Probability:     99.0%
Mental Health Alert Flag:  2.0%

--- Operational Action Taken ---
[ACTION: RED PATHWAY - IMMEDIATE EMERGENCY]
  -> Dispatched Code Triage alert to Emergency Resuscitation Bay.
  -> Prep: 12-lead ECG, continuous telemetry, oxygen, intravenous access.
  -> Directing patient/EMS to Acute Trauma/Cardiac Suite.
  -> Automated Continuity: Flagged for mandatory 48-hour follow-up callback.


======================================================================
PATIENT INTAKE EVALUATION: PT-10493 - Mild Headache for 2 Days (Non-emergent Tension Headache)
======================================================================
Urgency Score (0-3 scale): 0.15 (Confidence: 94.0%)
Care Disposition:          PRIMARY_CARE (Confidence: 93.0%)
Follow-up Probability:     28.0%
Mental Health Alert Flag:  1.0%

--- Operational Action Taken ---
[ACTION: GREEN PATHWAY - PRIMARY CARE]
  -> Telehealth / Primary Care consult scheduled within 48-72 hours.
  -> Digital self-care packet and red-flag escalation instructions sent via SMS.


======================================================================
PATIENT INTAKE EVALUATION: PT-10494 - Twisted Ankle While Jogging (Acute Musculoskeletal Sprain)
======================================================================
Urgency Score (0-3 scale): 1.88 (Confidence: 91.0%)
Care Disposition:          URGENT_CARE (Confidence: 92.0%)
Follow-up Probability:     82.0%
Mental Health Alert Flag:  1.0%

--- Operational Action Taken ---
[ACTION: YELLOW PATHWAY - SAME-DAY URGENT CARE]
  -> Scheduled immediate walk-in slot at Partner Urgent Care Clinic.
  -> Auto-requisitioned right ankle weight-bearing X-ray (Ottawa Ankle Rules).
  -> Issued digital check-in token and wait-time estimate (15 mins).
  -> Automated Continuity: Flagged for mandatory 48-hour follow-up callback.
```

---

## Console Payload

A console-ready JSON payload for the chest pain scenario is available in [`payload.json`](./payload.json). You can paste it directly into [console.typesafe.ai](https://console.typesafe.ai) to inspect the probability distributions interactively.
