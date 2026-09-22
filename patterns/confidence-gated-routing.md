# Pattern: Confidence-Gated Routing

## Problem

You want to automate decisions, but you don't want to blindly trust every answer from Jev. Some inputs are ambiguous — for those, you want a human or a more powerful LLM in the loop.

## Solution

Use Jev's `confidence` score (available on all three primitive types) as a gate to choose between automation, human-assist, and full escalation.

```
High confidence → Automate fully
Mid confidence  → Suggest to human (human confirms or overrides)
Low confidence  → Full human review
```

## Code

```python
import requests, os

def route_with_confidence(state: str, api_key: str) -> dict:
    resp = requests.post(
        "https://api.typesafe.ai/v1/systemone",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "jev-1.13.0",
            "state": state,
            "questions": {
                "category": {
                    "type": "choice",
                    "instructions": "Which support team should handle this ticket?",
                    "criteria": {
                        "billing":    "Questions about invoices, charges, refunds.",
                        "technical":  "Product bugs, API errors, integration issues.",
                        "sales":      "Pricing, upgrades, enterprise plans.",
                        "general":    "Everything else."
                    }
                }
            }
        }
    ).json()

    answer = resp["answers"]["category"]
    category   = answer["choice"]
    confidence = answer["confidence"]

    if confidence >= 0.90:
        # High confidence — route automatically, no human needed
        auto_route(category)
        return {"action": "auto_routed", "category": category, "confidence": confidence}

    elif confidence >= 0.60:
        # Mid confidence — show suggestion to human agent
        suggest_to_human(category, confidence)
        return {"action": "suggested", "category": category, "confidence": confidence}

    else:
        # Low confidence — don't guess, put in review queue
        human_review_queue.add(state)
        return {"action": "escalated", "confidence": confidence}
```

## When to Use

- Email/ticket routing systems
- Any classification step in an automated pipeline
- Fraud detection (act on high confidence, review mid confidence)
- Content moderation (auto-approve/reject extremes, human review the gray zone)

## Tuning the Thresholds

Start with `0.90 / 0.60` and measure:
- **False automation rate** (routed wrong without human review)
- **Escalation rate** (how often you're punting to humans)

Move the upper threshold up to reduce false automation. Move the lower threshold down to reduce unnecessary escalations.
