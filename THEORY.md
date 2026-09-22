# The Theory of Jev: A Staff-Engineer's Guide to System One AI

> This document derives from first principles what Jev actually is, what it can and cannot do,
> how to compose it into complex systems, and the anti-patterns that will waste your time.
> If the README tells you *how* to call Jev, this document tells you *when* and *why*.

---

## Table of Contents

1. [The Foundational Primitive](#1-the-foundational-primitive)
2. [Why RLCD Changes Everything](#2-why-rlcd-changes-everything)
3. [The Capability Boundary](#3-the-capability-boundary)
4. [Anti-Patterns — What Jev Cannot Do](#4-anti-patterns--what-jev-cannot-do)
5. [Composition Patterns](#5-composition-patterns)
6. [The Pattern Taxonomy](#6-the-pattern-taxonomy)
7. [Architectural Placement](#7-architectural-placement)
8. [Evaluation Framework](#8-evaluation-framework)

---

## 1. The Foundational Primitive

Strip away the branding. Strip away the three primitives (choice, score, noul). Strip away the
use cases. At the very bottom, Jev does exactly one thing:

> **Given arbitrary text state S and a set of natural-language criteria descriptions C₁..Cₙ,
> return a calibrated probability distribution P(Cᵢ | S) such that the probabilities are
> empirically well-calibrated.**

That's it. Everything else — choice, score, noul, confidence, fan-out — is syntactic sugar
over this single operation.

### Breaking this down:

**"arbitrary text state S"** — The state is not a prompt. It's not an instruction. It's the
*document under examination*. An email, a DOM dump, an earnings transcript, a code diff, a
patient intake form. Jev reads it the way a radiologist reads an X-ray — looking for signals,
not following instructions.

**"natural-language criteria descriptions"** — This is the key architectural innovation. In a
traditional classifier (BERT, RoBERTa, fine-tuned GPT), the label space is baked into the model
at training time. You trained it on `{positive, negative, neutral}` and it only ever predicts
those three things. To add a fourth label, you retrain.

Jev's criteria are **runtime arguments**. You define them per request. The model learned to
understand *what criteria descriptions mean semantically*, not any specific set of them. This
is zero-shot classification, but unlike zero-shot prompting of GPT-4, the output is a proper
probability simplex, not generated text that you parse and hope is valid JSON.

**"calibrated probability distribution"** — This is where RLCD comes in. See next section.

### How the three primitives map to this single operation:

```
choice(criteria: {A: "desc_A", B: "desc_B", C: "desc_C"})
  → P(A|S), P(B|S), P(C|S)
  → argmax = the "choice"
  → max probability = related to "confidence"

score(criteria: ["low", "medium", "high"])
  → P(level_0|S), P(level_1|S), P(level_2|S)
  → E[level] = Σ(i × P(level_i|S)) = the "score" (a float)
  → This is why score returns 0.78, not 1 — it's a probability-weighted expectation

noul(instructions: "Is X true?")
  → P(true|S), P(false|S)
  → P(true|S) = the "noul" value
  → Literally a binary choice with an implicit criteria of {true, false}
```

**Score is not a rating.** Score is the expected value of a categorical distribution over an
ordered rubric. When Jev returns `score: 0.78` on a 3-level scale, it means:
- 23% probability of level 0
- 77% probability of level 1
- 0% probability of level 2
- Expected value: 0×0.23 + 1×0.77 + 2×0.00 = 0.77 ≈ 0.78

This is continuous, differentiable data. You can feed it directly into an ML pipeline, a
weighted decision function, or a PID controller. No discretization needed.

---

## 2. Why RLCD Changes Everything

### The Calibration Problem

When you ask GPT-4: "On a scale of 1-10, how confident are you that this email is spam?"
and it says "8", what does that mean?

**Nothing.** GPT-4 was trained via RLHF to produce text that humans rate as helpful.
The token "8" was selected because it's the token that maximizes the reward model's
score for helpfulness in this context. It has zero statistical relationship to the
model's actual internal uncertainty. A model trained on RLHF can say "I'm 95% sure"
and be wrong 60% of the time. The confidence is a literary device, not a measurement.

### RLCD: Reinforcement Learning from Calibrated Demonstrations

Jev is (based on the founders' academic lineage and the observable properties of the
system) trained with a calibration objective. The training signal is not "did a human
prefer this output?" but rather:

> "When the model outputs P(X) = 0.85, is the model empirically correct about X
> approximately 85% of the time across the training distribution?"

This means:
- `confidence: 0.90` → the model is right ~90% of the time at this confidence level
- `confidence: 0.60` → the model is right ~60% of the time
- `confidence: 0.30` → the model is right ~30% of the time

### Why This Matters for Engineering

Calibrated probabilities are the difference between "AI-assisted" and "AI-automated":

```python
# WITH CALIBRATION (Jev): You can set hard thresholds
# because the confidence score has a known, measurable relationship to accuracy
if answer["confidence"] > 0.95:
    automate()  # You KNOW the false positive rate is ~5%

# WITHOUT CALIBRATION (GPT-4): You cannot set hard thresholds
# because "confidence" is just a generated string with no statistical guarantee
if gpt4_says_confident:
    automate()  # You have NO IDEA what the false positive rate is
```

Calibration turns AI from a *suggestion engine* into a *decision engine*.
You can write an SLA that says "automated decisions will have <5% error rate"
and actually deliver on it by gating on `confidence > 0.95`.

### The Calibration / Resolution Tradeoff

There's a fundamental tradeoff in any classifier: calibration vs. resolution.

- **Calibration**: Are the probabilities accurate? (Does 80% mean 80%?)
- **Resolution**: Can the model distinguish between cases? (Does it ever give 95% vs 5%, or does it always hedge at 50%?)

A model that always outputs 50% for everything is perfectly calibrated but useless.
A model that outputs 99% for everything is highly resolved but poorly calibrated.

Jev appears to optimize for both — when it's confident (>0.90), it's almost always right.
When it's uncertain (0.40–0.60), it's genuinely uncertain. This is the hallmark of
RLCD-style training.

---

## 3. The Capability Boundary

### What Jev CAN Do (The "System 1" Space)

Jev can answer any question where:

1. ✅ **The answer space is enumerable and finite** (you can list all possible answers)
2. ✅ **Each answer can be described in natural language** (the model understands what you mean)
3. ✅ **The mapping from state to answer is pattern-matchable** (a human could make this judgment after reading the state once, without doing multi-step reasoning)
4. ✅ **The state contains sufficient signal** (the answer is implied by the text, not by external knowledge)

This covers an enormous range of tasks:

```
Pattern recognition:    "Does this text contain X?"          → noul
Classification:         "Which bucket does this fall into?"  → choice
Degree estimation:      "How much of X is present?"          → score
Signal detection:       "Is there evidence of X?"            → noul
Prioritization:         "Which of these is most urgent?"     → choice over items
Quality assessment:     "How well does this meet criteria?"  → score
Anomaly flagging:       "Is this unusual/out-of-pattern?"    → noul
Semantic matching:      "Does this state match criteria X?"  → noul per criterion
Multi-signal extraction: All of the above, in parallel       → compound questions
```

### What Jev CANNOT Do (The "System 2" Space)

Jev cannot answer questions where:

1. ❌ **The answer requires generating novel text** (it has no decoder / text generation)
2. ❌ **The answer requires multi-step logical reasoning** (it doesn't chain thoughts)
3. ❌ **The answer requires computation** (it can't count, do math, or parse structured data)
4. ❌ **The answer requires external knowledge not in the state** (it can't search or recall facts)
5. ❌ **The answer space is continuous and unbounded** (it can only work over finite criteria)

### The Decision Boundary Test

Before using Jev for a task, ask yourself:

> "Could a smart human make this judgment after reading the state ONCE, without
> doing any research, calculation, or multi-step reasoning?"

If yes → Jev can probably do it.
If no → You need an LLM, or Jev needs to be composed with one.

---

## 4. Anti-Patterns — What Jev Cannot Do

### Anti-Pattern 1: Asking Jev to Reason

```
❌ BAD: "Given that the company's P/E ratio is 45 and the sector average is 22,
         and considering that interest rates rose 50bps last quarter, is this
         stock overvalued?"

✅ GOOD: "Does this text suggest the stock may be overvalued?"
         criteria: { "overvalued": "...", "fairly_valued": "...", "undervalued": "..." }
```

**Why it fails:** The bad version requires Jev to understand that 45 > 22, that higher
P/E relative to sector implies overvaluation, and that rising rates compress multiples.
This is multi-step reasoning. Jev can match patterns ("the text says overvalued") but
it can't derive conclusions from numeric relationships.

**The fix:** Pre-compute the quantitative analysis in your code, then ask Jev to classify
the *textual signals* in the qualitative commentary.

---

### Anti-Pattern 2: Compound Questions

```
❌ BAD: "Is this email urgent AND from a VIP customer?"
         (type: noul)

✅ GOOD: Two separate questions:
         "urgency":     { type: noul, instructions: "Is this email urgent?" }
         "is_vip":      { type: noul, instructions: "Is this from a VIP/enterprise customer?" }
```

**Why it fails:** Compound questions confuse the probability interpretation. If Jev returns
`noul: 0.7`, does that mean "70% urgent AND VIP", "urgent but not VIP", or "VIP but not
urgent"? The probability becomes uninterpretable.

**The fix:** One question per atomic judgment. Combine in code: `if urgency > 0.8 AND vip > 0.8`.
This is both more reliable AND more debuggable.

---

### Anti-Pattern 3: Using Jev as a Search Engine

```
❌ BAD: state: "What is the capital of France?"
         (There's no "state" to classify — you're asking for a factual recall)

✅ GOOD: state: "The customer mentioned they're located in the Paris region."
         question: { type: noul, instructions: "Is this customer based in France?" }
```

**Why it fails:** Jev classifies state against criteria. If the state itself IS the question,
there's nothing to classify. Jev is a judge, not an oracle.

---

### Anti-Pattern 4: Too Many Criteria (>15)

```
❌ BAD: choice with 50 options for "which of these 50 products does this review discuss?"

✅ GOOD: Hierarchical: first classify into 5 product categories, then within the winning
         category, classify into the specific product.
```

**Why it fails:** While Jev supports up to 255 options, classification quality degrades
as the criteria space grows — especially when criteria descriptions overlap semantically.
With 50 options, many will be similar, and the probability mass spreads thinly.

**The fix:** Use hierarchical classification (2-3 Jev calls with narrow criteria each)
instead of one flat call with many criteria.

---

### Anti-Pattern 5: Vague or Overlapping Criteria

```
❌ BAD: criteria: {
     "somewhat_urgent": "The request is kind of urgent",
     "moderately_urgent": "The request is moderately urgent",
     "quite_urgent": "The request is quite urgent"
   }

✅ GOOD: criteria: {
     "low":  "General inquiry, no time pressure, informational only.",
     "medium": "Customer waiting for resolution, business impact within days.",
     "high": "Revenue at risk, system down, SLA breach imminent."
   }
```

**Why it fails:** If the criteria descriptions are semantically similar, the model can't
distinguish between them. You'll get ~33% probability for each, with low confidence.

**The fix:** Criteria descriptions should be **mutually exclusive and concretely distinct**.
Describe the *observable evidence* that distinguishes each option, not just synonyms of
the same concept.

---

### Anti-Pattern 6: Expecting Jev to Count or Parse Structure

```
❌ BAD: state: "[1, 2, 3, 4, 5, 6, 7, 8]"
         question: "How many items are in this list?"

❌ BAD: state: '{"name": "John", "age": 30, "active": true}'
         question: "Is the user active?" (asking it to parse JSON)

✅ GOOD: state: "User John, age 30, account status: active."
         question: noul "Is this user's account currently active?"
```

**Why it fails:** Jev processes text semantically, not structurally. It doesn't parse
JSON, count tokens, or evaluate expressions. It matches semantic patterns.

**The fix:** Pre-process structured data into natural language descriptions before
passing to Jev.

---

### Anti-Pattern 7: Using Jev for Temporal Reasoning

```
❌ BAD: state: "Meeting scheduled for March 15. Today is March 20."
         question: "Has this meeting already occurred?"

✅ GOOD: state: "Meeting scheduled for March 15. Today is March 20."
         question: noul "Does the text indicate the meeting date has passed?"
```

**Why it fails (subtly):** The first version requires Jev to understand that 20 > 15
and therefore the date has passed. This is arithmetic. The second version asks Jev
whether the *text itself* indicates the meeting has passed — a pattern matching task.

In practice, Jev might get the first version right because "March 15" before "March 20"
is a common textual pattern. But you shouldn't rely on it. Make the reasoning explicit
in your state or pre-compute it.

---

### Anti-Pattern 8: Treating Score as a Rating

```
❌ BAD: "Rate this code quality from 1 to 10"
         (This is a System 2 task — requires understanding code semantics deeply)

✅ GOOD: Decompose into atomic signals:
         "has_error_handling": noul
         "naming_quality": score ["poor naming", "acceptable", "clear and descriptive"]
         "complexity": score ["trivially simple", "moderate", "overly complex"]
         → Combine in code with weights
```

**Why it fails:** A single holistic rating conflates multiple dimensions. Jev is better
at answering precise, narrow questions than broad, subjective ones. This is the
composite scoring pattern — decompose, then recompose in code.

---

### Anti-Pattern 9: State Too Long / Noisy

```
❌ BAD: Passing an entire 50-page document as state to classify a single sentence

✅ GOOD: Extract the relevant paragraph + surrounding context, pass just that
```

**Why it fails:** While Jev can handle substantial state, signal-to-noise ratio matters.
If the relevant information is buried in 50 pages of irrelevant text, classification
quality drops — the same way it would for a human skimming 50 pages.

**The fix:** Pre-filter. Use embedding search or simple heuristics to extract the
relevant passages, then pass those to Jev.

---

### Anti-Pattern 10: Expecting Jev to Disagree With Itself

```
❌ BAD: Sending the same state and questions twice expecting different answers
         (Jev is deterministic for the same input — it's not sampling like an LLM)

✅ GOOD: Use confidence scores to handle uncertainty, not repeated calls
```

**Why it matters:** Jev doesn't have "temperature". The probability distribution IS
the answer. If it says `P(A)=0.51, P(B)=0.49`, it means "this is genuinely ambiguous".
Calling again won't resolve the ambiguity — it'll give you the same split.

---

## 5. Composition Patterns

The real power of Jev emerges when you compose the primitive into higher-order architectures.

### Pattern 1: Sequential Narrowing (Decision Tree)

```
Call 1: Broad classification → 5 categories
Call 2: Within winning category → specific sub-type
Call 3: Within sub-type → exact action
```

Each call uses the previous result to construct narrower, more precise criteria.
Total latency: ~300ms for 3 sequential calls. Still faster than one GPT-4 call.

### Pattern 2: Parallel Fan-Out (Multi-Dimensional Scoring)

```
Single call with 8 questions:
  safety, urgency, complexity, domain, sentiment, churn_risk, vip_status, language
→ 8 calibrated signals in ~100ms
→ Your code combines them into a single routing decision
```

This is the pattern used in the trading signal extractor. The power is that each
dimension is evaluated independently — no context rot between questions.

### Pattern 3: Speculative Execution (from jev-ultrafast)

```
Single call:
  operation: choice [CLICK, TYPE, SCROLL, DONE]
  click_target: choice [element_1, element_2, ...]     ← speculative
  type_target: choice [input_1, input_2, ...]          ← speculative
→ Execute only the target that matches the chosen operation
→ Discard the rest (they were free — parallel evaluation)
```

### Pattern 4: Confidence-Gated Cascade

```
Jev classifies → confidence > 0.9 → automate
              → confidence 0.6-0.9 → small LLM confirms
              → confidence < 0.6 → frontier LLM / human
```

This is a cost-optimization architecture. Most requests (if your criteria are well-defined)
will hit the >0.9 tier and cost ~$0.00001. Only the genuinely hard cases hit the expensive
tier.

### Pattern 5: Continuous State Tracking

```
For each message in a conversation:
  Jev(conversation_so_far) → churn_risk, satisfaction, topic_drift, resolution_progress
→ Plot the trajectory over time
→ Trigger interventions at inflection points
```

### Pattern 6: Out-of-Distribution Detection

```
result = jev(state, {"category": choice_with_5_options})
max_prob = max(result["probabilities"].values())

if max_prob < 0.4:
    # The state doesn't cleanly fit ANY category
    # This is a signal that your criteria taxonomy is incomplete
    flag_for_taxonomy_review(state)
```

### Pattern 7: Ensemble Disagreement

```
# Define the same question with different criteria framings
q1 = {"type": "choice", "criteria": {framing_A}}
q2 = {"type": "choice", "criteria": {framing_B}}

# If they agree → high confidence in the result
# If they disagree → the state is genuinely ambiguous
```

### Pattern 8: Gatekeeper Chain

```
                Input
                  │
                  ▼
        ┌─── Safety Gate (noul) ───┐
        │ safe > 0.95?             │
        │ NO → reject              │
        └─────────┬────────────────┘
                  │ YES
                  ▼
        ┌─── Relevance Gate (noul) ┐
        │ relevant > 0.80?         │
        │ NO → redirect            │
        └─────────┬────────────────┘
                  │ YES
                  ▼
        ┌─── Complexity Gate ──────┐
        │ simple/moderate/complex  │
        └─────────┬────────────────┘
                  │
           Route to handler
```

Each gate is a Jev call. Total latency for all three: ~300ms (sequential)
or ~100ms (if combined into one parallel call).

---

## 6. The Pattern Taxonomy

At the highest level of abstraction, every Jev use case falls into one of these
meta-patterns:

### 🏷️ Classify
Map state to one of N categories.
*"What IS this?"*

### 📏 Measure  
Place state on an ordered scale.
*"How much of X is in this?"*

### ✅ Detect
Check for presence/absence of a property.
*"Does this contain X?"*

### 🚦 Gate
Make a go/no-go decision.
*"Should we proceed?"*

### 🔀 Route
Direct state to the appropriate handler.
*"Where should this go?"*

### 🔍 Filter
Separate relevant from irrelevant.
*"Is this worth processing?"*

### 📊 Decompose
Break a complex judgment into atomic signals.
*"What are the individual components of quality here?"*

### ⚡ Speculate
Evaluate multiple possible futures simultaneously.
*"If we took action A, which target? If action B, which target?"*

Every concrete use case — from email routing to DOM navigation to trading signal
extraction — is an instance of one or more of these eight meta-patterns.

---

## 7. Architectural Placement

### Where Jev Sits in a Modern AI Stack

```
┌────────────────────────────────────────────────────────────┐
│ APPLICATION LAYER                                          │
│ (Your product code, business logic, UX)                    │
├────────────────────────────────────────────────────────────┤
│ ORCHESTRATION LAYER                                        │
│ (LangGraph, CrewAI, custom agent loops)                    │
├───────────────┬───────────────┬────────────────────────────┤
│ DECISION LAYER│ GENERATION    │ RETRIEVAL LAYER            │
│ (Jev)         │ LAYER (LLMs)  │ (Vector DB, Search)        │
│               │               │                            │
│ • Route       │ • Generate    │ • Embed                    │
│ • Gate        │ • Reason      │ • Retrieve                 │
│ • Classify    │ • Synthesize  │ • Rerank                   │
│ • Score       │ • Code        │                            │
│               │ • Translate   │                            │
│ ~100ms        │ ~2-30s        │ ~50-500ms                  │
│ ~$0.00001     │ ~$0.01-0.10   │ ~$0.0001                   │
├───────────────┴───────────────┴────────────────────────────┤
│ INFRASTRUCTURE                                             │
│ (APIs, databases, message queues, CDPs)                    │
└────────────────────────────────────────────────────────────┘
```

### The Key Insight

Jev fills a gap that previously didn't have a good solution:

| Need | Old Solution | Problem | Jev Solution |
|------|-------------|---------|-------------|
| Route a ticket | Regex rules | Brittle, no semantics | Semantic classification |
| Guard an agent action | Prompt GPT-4 to say "safe" | Slow, expensive, uncalibrated | 100ms calibrated gate |
| Score urgency | Fine-tuned BERT | Fixed labels, needs retraining | Dynamic criteria, zero-shot |
| Detect churn risk | Keyword matching | No understanding of tone | Semantic pattern matching |
| Choose next agent action | Full LLM call | 3 seconds per decision | 100ms per decision |

### What Jev Replaces

```
Traditional classifiers (BERT, RoBERTa)  →  No retraining needed, dynamic labels
Regex / keyword matching                 →  Semantic understanding
LLM-as-classifier (GPT-4 → parse JSON)  →  400x cheaper, 20x faster, calibrated
Hardcoded if/else business rules         →  Soft, probabilistic, adaptable
Human decision-making at scale           →  Automated with known error rates
```

### What Jev Does NOT Replace

```
LLMs for text generation                →  Jev cannot write
LLMs for complex reasoning              →  Jev cannot chain logic
Embedding models for similarity search   →  Different paradigm
Fine-tuned models for domain expertise   →  Jev is general-purpose
Human judgment on novel/edge cases       →  Jev flags these via low confidence
```

---

## 8. Evaluation Framework

When you deploy Jev in production, measure these:

### Calibration Plot
Plot predicted confidence (x-axis) vs actual accuracy (y-axis).
A perfectly calibrated model follows the diagonal. Measure ECE (Expected Calibration Error).

### Automation Rate
What percentage of decisions are handled at `confidence > threshold` without human review?
Higher is better, but only if accuracy is maintained.

### False Automation Rate  
Of the decisions that were automated (above threshold), what percentage were wrong?
This is your real-world error rate and must match your SLA.

### Escalation Rate
What percentage of decisions fall below your confidence threshold and require human/LLM review?
If this is >50%, your criteria descriptions need refinement.

### Latency Budget
Jev calls should be <200ms p95. If you're seeing >500ms, check your state size.

### Cost Per Decision
Track `input_tokens` from the response. Jev has no output token cost.
At $0.042/M input tokens, even complex states cost fractions of a cent.

---

## Summary

Jev is not a chatbot. It's not a reasoning engine. It's not a search engine.

**Jev is a calibrated probability oracle over dynamically-defined semantic categories.**

The moment you understand this sentence, you can derive every valid use case, predict every
anti-pattern, and design every composition pattern from first principles.

The calibration (RLCD) makes it trustworthy enough to automate.
The dynamic criteria make it flexible enough to deploy without retraining.
The parallel evaluation makes it fast enough for real-time decision loops.
The probability simplex makes it composable with any downstream system.

These four properties — **calibrated, dynamic, parallel, probabilistic** — are what make
Jev genuinely new in the AI landscape. Not incrementally better. Categorically different.

---

*See [USE_CASES.md](USE_CASES.md) for 100+ concrete applications organized by domain.*
