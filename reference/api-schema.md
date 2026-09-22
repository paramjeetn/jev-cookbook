# Jev API Schema Reference

> ⚠️ **Verified against the TypeSafe console validator — September 2026.**  
> The docs sometimes lag. Use these schemas to avoid validation errors.

---

## Endpoint

```
POST https://api.typesafe.ai/v1/systemone
```

## Request Body

```json
{
  "model": "jev-1.13.0",
  "state": "The context or document to evaluate. Can be plain text or structured data.",
  "questions": {
    "question_name_1": { ... },
    "question_name_2": { ... }
  }
}
```

- `model`: Use `"jev-1.13.0"` or the latest slug from the console.
- `state`: Any string. There is no hard token limit documented, but keep it focused.
- `questions`: An object where each key is your own name for the question (no reserved words).

---

## Question Schemas

### `choice` — Select one option from a defined set

```json
{
  "type": "choice",
  "instructions": "Short description of what you're asking.",
  "criteria": {
    "option_key_1": "Description of when this option applies.",
    "option_key_2": "Description of when this option applies.",
    "option_key_3": "Description of when this option applies."
  }
}
```

**Rules:**
- `criteria` is a **dictionary** (not an array). Keys become the option names.
- Keys are returned verbatim in the response — name them for your code.
- Up to 255 options supported.
- ❌ Do NOT use `options: [...]` — this will fail validation.

**Response:**
```json
{
  "type": "choice",
  "choice": "option_key_1",
  "confidence": 0.97,
  "probabilities": {
    "option_key_1": 0.97,
    "option_key_2": 0.02,
    "option_key_3": 0.01
  }
}
```

---

### `score` — Place on an ordered scale

```json
{
  "type": "score",
  "instructions": "Short description of what you're scoring.",
  "criteria": [
    "Description of the lowest level (index 0).",
    "Description of a middle level (index 1).",
    "Description of the highest level (index 2)."
  ]
}
```

**Rules:**
- `criteria` is an **ordered array** of strings, from lowest to highest.
- Min 2, max 10 levels.
- ❌ Do NOT use `min`/`max` integer bounds — this will fail validation.
- The score is a **float** representing the probability-weighted position in the array.

**Response:**
```json
{
  "type": "score",
  "score": 0.78,
  "legend": {
    "0": "Description of level 0",
    "1": "Description of level 1",
    "2": "Description of level 2"
  },
  "confidence": 0.77,
  "probabilities": {
    "0": 0.23,
    "1": 0.77,
    "2": 0.0
  }
}
```

> **How to read the score:** `score: 0.78` with 3 levels (0–2) means the model assigned 23% probability to level 0 and 77% to level 1, giving a weighted float of `(0*0.23 + 1*0.77) = 0.77` ≈ `0.78`. Use the float directly in your logic.

---

### `noul` — Probability that a statement is true

```json
{
  "type": "noul",
  "instructions": "A statement that can be true or false."
}
```

**Optional:** You can add a `criteria` dict with `true` and `false` keys to guide the model:
```json
{
  "type": "noul",
  "instructions": "Is the customer at risk of churning?",
  "criteria": {
    "true": "Customer has expressed dissatisfaction, threatened to leave, or referenced competitors.",
    "false": "Customer seems engaged and has not indicated any intent to leave."
  }
}
```

**Response:**
```json
{
  "type": "noul",
  "noul": 0.87,
  "confidence": 0.91
}
```

> **How to read:** `noul: 0.87` = 87% probability that the statement is true.

---

## Full Request Example (Tested Live)

```json
{
  "state": "Customer email: 'I've been waiting 3 weeks for my refund and nobody is responding. This is unacceptable!'",
  "questions": {
    "urgency": {
      "type": "score",
      "instructions": "How urgently does this customer need a response?",
      "criteria": [
        "Not urgent. General questions or feedback.",
        "Moderately urgent. Standard support issues.",
        "Very urgent. High frustration, threats to leave, or service outage."
      ]
    },
    "sentiment": {
      "type": "choice",
      "instructions": "What is the customer's sentiment?",
      "criteria": {
        "very_negative": "Extremely angry, frustrated, or threatening.",
        "negative": "Unhappy or disappointed.",
        "neutral": "Matter-of-fact, lacking strong emotion.",
        "positive": "Happy, satisfied, or praising."
      }
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Is this customer at risk of churning or cancelling their service?"
    },
    "category": {
      "type": "choice",
      "instructions": "What category is this support request?",
      "criteria": {
        "billing": "Issues with refunds, charges, or invoices.",
        "shipping": "Questions about delivery, tracking, or missing items.",
        "product": "Questions about how to use the product or features.",
        "general": "Any other questions that don't fit the above."
      }
    }
  }
}
```

---

## Common Validation Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `question "X" has an unexpected property "options"` | Used `options: [...]` for choice | Replace with `criteria: { key: "description" }` |
| `question "X" has an unexpected property "min"` | Used `min`/`max` for score | Remove them; use `criteria: [...]` array instead |
| `question "X" has an unexpected property "max"` | Same as above | Same fix |
| `question "X" requires criteria` | Left out `criteria` on choice or score | Add the `criteria` field |
| `question "questions" needs a "type"` | Wrapped the whole payload in `{"questions": {...}}` | Put questions directly as top-level keys |
