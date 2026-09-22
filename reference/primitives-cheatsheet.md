# Jev Primitives — Quick Reference Card

## When to use what

| I want to... | Use | Returns |
|---|---|---|
| Classify into categories | `choice` | The winning key + probability per option |
| Rate on a scale | `score` | Float (probability-weighted position in criteria array) |
| Check if something is true | `noul` | Float 0.0–1.0 (probability of true) |

---

## choice

```json
{
  "type": "choice",
  "instructions": "...",
  "criteria": { "key": "when this applies", ... }
}
```
**Output key:** `answer["choice"]` → string  
**Confidence key:** `answer["confidence"]` → float  
**All probs:** `answer["probabilities"]` → `{ "key": float, ... }`

---

## score

```json
{
  "type": "score",
  "instructions": "...",
  "criteria": ["lowest level desc", "...", "highest level desc"]
}
```
**Output key:** `answer["score"]` → float (e.g. `1.78` for a 3-level scale)  
**Legend:** `answer["legend"]` → `{ "0": "desc", "1": "desc", ... }`  
**Probs:** `answer["probabilities"]` → `{ "0": float, "1": float, ... }`

---

## noul

```json
{
  "type": "noul",
  "instructions": "Is X true?"
}
```
**Output key:** `answer["noul"]` → float 0–1  
**Read as:** `>0.7` → likely true | `0.3–0.7` → uncertain | `<0.3` → likely false

---

## Decision Thresholds (recommended starting points)

```python
# noul
if answer["noul"] > 0.85:   # act on it — high confidence TRUE
if answer["noul"] > 0.50:   # probably true — consider acting
if answer["noul"] < 0.20:   # very likely false

# choice
if answer["confidence"] > 0.90:   # automate
if answer["confidence"] > 0.60:   # suggest to human
if answer["confidence"] < 0.60:   # escalate / human review

# score (3-level, 0-indexed)
# score ≈ 0.0  → level 0
# score ≈ 1.0  → level 1
# score ≈ 2.0  → level 2
```
