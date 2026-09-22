# Pattern: Hybrid Agent Loop (Jev + LLM)

## The Core Insight

Most decisions in an agent loop are **structural** — what to do next, is this safe, which tool to call. These don't need prose generation. Only a small fraction of steps require actual text output.

Jev is purpose-built for the structural layer. By surgically combining it with a text-generation LLM, you get an agent that is simultaneously:
- ⚡ Faster (Jev decisions in ~100ms vs 2–5s for LLMs)
- 💸 Cheaper (~400x less per decision)
- 🛡️ Safer (hallucination-free structure layer)
- 🔍 Debuggable (every structural decision is a typed, logged value)

## Architecture

```
┌──────────────────────────────────────────────────┐
│  USER INPUT / TASK                               │
└──────────────────┬───────────────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────────────┐
│  JEV: Intent Classification (~50ms)              │
│  · What type of task is this?                    │
│  · Simple / complex / off-topic?                 │
│  · Which agent / tool cluster to use?            │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────┼─────────┐
         ▼         ▼         ▼
      [Simple]  [Complex]  [Off-topic]
         │         │         │
  Small LLM   Frontier    Reject /
  (generate)  LLM + tools  redirect
         │         │
         ▼         ▼
┌──────────────────────────────────────────────────┐
│  JEV: Output Evaluation (~100ms)                 │
│  · Is the goal achieved?                         │
│  · Quality score (1–5)                           │
│  · Safe to return to user?                       │
└──────────────────┬───────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
   [Good enough]        [Needs retry]
   Return to user    Retry / escalate
```

## Code

```python
import requests
from openai import OpenAI

JEV_URL = "https://api.typesafe.ai/v1/systemone"
jev_key = "your-typesafe-key"
openai_client = OpenAI(api_key="your-openai-key")

def jev(state: str, questions: dict) -> dict:
    return requests.post(JEV_URL,
        headers={"Authorization": f"Bearer {jev_key}"},
        json={"model": "jev-1.13.0", "state": state, "questions": questions}
    ).json()["answers"]

def run_agent(user_input: str) -> str:
    # --- STEP 1: Jev classifies the request (fast, cheap) ---
    routing = jev(user_input, {
        "complexity": {
            "type": "choice",
            "instructions": "How complex is this request?",
            "criteria": {
                "simple":  "Single, clear question with a known factual answer.",
                "moderate":"Requires moderate reasoning or 2-3 steps.",
                "complex": "Requires deep reasoning, research, or tool use."
            }
        },
        "is_safe": {
            "type": "noul",
            "instructions": "Is this request safe and appropriate to answer?"
        },
        "needs_tools": {
            "type": "noul",
            "instructions": "Does this request require external tools (search, database, API calls)?"
        }
    })

    # Guard: reject unsafe requests immediately
    if routing["is_safe"]["noul"] < 0.5:
        return "I'm unable to help with that request."

    complexity   = routing["complexity"]["choice"]
    needs_tools  = routing["needs_tools"]["noul"] > 0.6

    # --- STEP 2: Route to appropriate LLM ---
    if complexity == "simple" and not needs_tools:
        model = "gpt-4o-mini"   # Fast + cheap
    elif complexity == "moderate":
        model = "gpt-4o"        # Balanced
    else:
        model = "claude-opus-4" # Powerful (or use with tools)

    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_input}]
    )
    output = response.choices[0].message.content

    # --- STEP 3: Jev evaluates the output (fast quality check) ---
    evaluation = jev(
        f"User asked: {user_input}\n\nAgent responded: {output}",
        {
            "goal_achieved": {
                "type": "noul",
                "instructions": "Did the response fully answer the user's question?"
            },
            "quality": {
                "type": "score",
                "instructions": "How good is this response?",
                "criteria": [
                    "Poor. Incorrect, incomplete, or off-topic.",
                    "Acceptable. Addresses the question but with gaps.",
                    "Good. Clear, complete, and accurate.",
                    "Excellent. Thorough, precise, and well-structured."
                ]
            }
        }
    )

    quality_score = evaluation["quality"]["score"]
    goal_achieved = evaluation["goal_achieved"]["noul"]

    if quality_score < 1.5 or goal_achieved < 0.6:
        # Quality too low — retry with a stronger model or flag for human review
        return run_agent_with_retry(user_input)

    return output
```

## When to Use

- Customer service bots (route simple FAQs cheaply, escalate complex issues)
- Code assistants (classify simple completions vs complex refactors)
- Research agents (triage web searches vs deep synthesis)
- Any pipeline where LLM costs at scale are a concern

## Cost Model

Assume 10,000 user queries/day:

| Approach | Avg LLM cost/query | Daily cost |
|---|---|---|
| All frontier LLM (GPT-4o) | ~$0.03 | ~$300/day |
| Hybrid (Jev routes 70% to mini) | ~$0.005 | ~$50/day |
| Jev routing overhead | ~$0.00001 | ~$0.10/day |

**~83% cost reduction with no quality loss on complex queries.**
