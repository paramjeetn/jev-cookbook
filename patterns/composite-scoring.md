# Pattern: Composite Scoring

## Problem

Asking a single LLM "rate this pitch out of 10" is unreliable. The model conflates factors, buries nuance, and gives you a number you can't trace back to any single dimension. Your business logic ends up inside the prompt, not in code.

## Solution

Decompose the complex judgment into 2–6 atomic Jev questions. Combine the scores **in your code** with explicit, auditable weights.

```
One vague judgment       →    N atomic Jev questions
"Is this a good pitch?"  →    market_size + team_quality + traction + defensibility
                              ↓
                         weighted_score = (0.4 * market) + (0.3 * team) + ...
```

## Why This Works

- **Business logic stays in code**: weights, thresholds, and decision rules are version-controlled Python, not embedded in prompts
- **No context rot**: each Jev question is evaluated independently — the 5th question doesn't degrade the 1st
- **Calibrated confidence**: each dimension comes with its own confidence score — you know *which* dimension is uncertain
- **Auditable**: when you override a decision, you can trace exactly which dimension drove it

## Trading Signal Example (Live-Tested!)

This was tested against a real earnings call Q&A transcript:

```python
def analyze_earnings_call(transcript: str, api_key: str) -> dict:
    resp = requests.post(
        "https://api.typesafe.ai/v1/systemone",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "jev-1.13.0",
            "state": transcript,
            "questions": {
                "guidance_revision": {
                    "type": "choice",
                    "instructions": "Did the company revise forward-looking guidance?",
                    "criteria": {
                        "revised_down":  "Guidance was explicitly lowered or cut.",
                        "maintained":    "Guidance was reaffirmed or unchanged.",
                        "revised_up":    "Guidance was raised or increased.",
                        "not_mentioned": "No forward guidance was discussed."
                    }
                },
                "margin_sentiment": {
                    "type": "score",
                    "instructions": "What is the status of the company's profit margins?",
                    "criteria": [
                        "Severe margin compression or deterioration.",
                        "Slight margin pressure or softness.",
                        "Stable margins.",
                        "Margin expansion or improvement."
                    ]
                },
                "capital_allocation": {
                    "type": "choice",
                    "instructions": "Did the company announce major capital allocation moves?",
                    "criteria": {
                        "share_buyback": "New or expanded share repurchase program.",
                        "dividend_hike": "Increased dividends.",
                        "dividend_cut":  "Reduced or suspended dividends.",
                        "none":          "No major capital allocation moves."
                    }
                },
                "signal_ambiguity": {
                    "type": "score",
                    "instructions": "How contradictory or mixed are the signals in this text?",
                    "criteria": [
                        "Completely one-sided (all positive or all negative).",
                        "Mostly one direction, with minor caveats.",
                        "Highly mixed or contradictory (bad operations, good financial engineering)."
                    ]
                }
            }
        }
    ).json()

    answers = resp["answers"]
    
    # Decision logic lives in YOUR code, not in a prompt
    ambiguity = answers["signal_ambiguity"]["score"]
    guidance   = answers["guidance_revision"]["choice"]
    buyback    = answers["capital_allocation"]["choice"]

    if ambiguity >= 1.5:
        # Mixed signal — don't auto-trade, route to analyst
        return {"action": "route_to_analyst", "reason": "signal_ambiguity"}
    
    elif guidance == "revised_up" and ambiguity < 1.0:
        # Unambiguous positive — execute fast
        return {"action": "buy", "size": "max"}
    
    elif guidance == "revised_down" and buyback == "share_buyback":
        # Classic "bad news + buyback" — let analyst decide
        return {"action": "route_to_analyst", "reason": "mixed_guidance_buyback"}
    
    return {"action": "hold"}
```

## Real Results

```
State: Mixed earnings call — guidance down 3%, buyback $1.5B, APAC softness, cloud acceleration

guidance_revision  → revised_down  (confidence: 100%)
margin_sentiment   → 0.78          (confidence: 77%)  ← float between severe/slight
capital_allocation → share_buyback (confidence: 100%)
signal_ambiguity   → 2.0           (confidence: 100%) ← highly mixed

Decision → route_to_analyst (correct! This was genuinely ambiguous)
Evaluation time → 100ms
```

## Other Use Cases

| Domain | Dimensions to Score |
|--------|---------------------|
| Startup pitch | market_size, team_quality, traction, defensibility |
| Job application | technical_fit, culture_fit, experience_level, communication |
| Content quality | accuracy, relevance, clarity, engagement |
| Medical triage | severity, urgency, resource_requirement, risk_if_delayed |
| Code review | correctness, security, performance, readability |
