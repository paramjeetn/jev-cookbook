# Pattern: Speculative Fan-Out (from browser-use/jev-ultrafast)

## The Insight

This pattern was extracted from analysing [jev-ultrafast](https://github.com/browser-use/jev-ultrafast) — a web agent that cuts task completion time by **25%** and browser protocol calls by **91%** compared to a GPT-4-only baseline.

## Problem

In a web agent loop, after observing the page you need to decide:
1. What operation to perform? (CLICK, TYPE, SCROLL, WAIT, DONE)
2. Which element to act on?

The naive approach is to ask an LLM: "What should I do next?" But that's one sequential round-trip per decision — expensive and slow.

## Solution: Ask All Questions at Once

Instead of one sequential decision, you ask Jev multiple questions **in a single request**. These "speculative" target questions are all answered in parallel, even though only one will be used.

```
Page DOM → Numbered element table → Single Jev request →
    ├── operation?     → CLICK
    ├── click_target?  → [7] (won't be used if op isn't CLICK)  ← speculative
    ├── type_target?   → [3] (won't be used if op isn't TYPE)   ← speculative
    └── select_target? → [5] (won't be used if op isn't SELECT) ← speculative

Pick the target that matches the chosen operation → Execute
```

## Key Properties

- **One network round trip** for what would otherwise be 2–4 sequential calls
- Targets that don't match the chosen operation are discarded (not a waste — they're free given parallelism)
- Each target head only receives elements compatible with that operation (no confusion)

## Code Sketch

```python
def decide_next_action(element_table: str, goal: str, api_key: str) -> dict:
    """One Jev call → full action decision."""
    resp = requests.post(
        "https://api.typesafe.ai/v1/systemone",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": "jev-1.13.0",
            "state": f"Goal: {goal}\n\nCurrent page elements:\n{element_table}",
            "questions": {
                "operation": {
                    "type": "choice",
                    "instructions": "What is the best next operation to advance the goal?",
                    "criteria": {
                        "CLICK":       "Click a button, link, or interactive element.",
                        "TYPE_TEXT":   "Type text into an input field or search box.",
                        "SELECT":      "Select an option from a dropdown.",
                        "SCROLL_DOWN": "Scroll down to reveal more content.",
                        "SCROLL_UP":   "Scroll up to access previous content.",
                        "WAIT":        "Wait for content to load.",
                        "DONE":        "The goal has been fully achieved.",
                        "BLOCKED":     "No available operation can make progress."
                    }
                },
                "click_target": {
                    "type": "choice",
                    "instructions": "If the operation is CLICK, which element should be clicked?",
                    "criteria": {
                        # Populated dynamically from the element table
                        # "[1]": "Change ticket type · Round trip",
                        # "[4]": "Search button",
                        # ...
                    }
                },
                "type_target": {
                    "type": "choice",
                    "instructions": "If the operation is TYPE_TEXT, which input field should receive text?",
                    "criteria": {
                        # Only text inputs from the element table
                    }
                }
            }
        }
    ).json()

    op = resp["answers"]["operation"]["choice"]
    
    if op == "CLICK":
        target = resp["answers"]["click_target"]["choice"]
        execute_click(target)
    elif op == "TYPE_TEXT":
        target = resp["answers"]["type_target"]["choice"]
        text = generate_text_with_llm(target, goal)  # Only call LLM for text generation!
        execute_type(target, text)
    elif op == "DONE":
        return {"status": "done"}
    
    return {"operation": op}
```

## When to Use

- Web browsing agents
- RPA (Robotic Process Automation) pipelines
- Any agent where the action space has a fixed set of operations

## Results from jev-ultrafast

| Metric | LLM-only | Jev Speculative Fan-Out |
|--------|----------|------------------------|
| Median task time | 9.450s | 7.092s (**25% faster**) |
| Browser protocol calls | 1,092 | 101 (**91% fewer**) |
| Google Flights (Zürich→London) | — | **7.1 seconds** |

## Why "Speculative"?

The word comes from CPU architecture — speculative execution means starting work on multiple possible paths before knowing which one is correct. You discard the unused ones, but the latency is dominated by the longest, not the sum. Jev makes this free because parallel questions don't add latency.
