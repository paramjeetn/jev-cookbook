# Example 02: Trading Signal Extraction

Extracts multi-dimensional quantitative trading signals from earnings call transcripts in **~100ms** per call, enabling high-frequency event-driven trading and automated ambiguity gating.

---

## 🎯 The Problem

When companies report quarterly earnings, conference calls contain subtle, multi-layered disclosures:
- An executive might announce a **3% guidance cut** (bearish).
- But also announce an **accelerated $1.5B share buyback** (bullish financial engineering).
- With **120 bps margin compression** due to regional discounting (operational friction).

### Why Traditional Approaches Fail:
1. **Frontier LLMs (GPT-4 / Claude)** take 2,000–5,000ms to parse earnings prose into JSON. By the time the model outputs a token, high-frequency algorithms and human traders have already repriced the equity.
2. **Keyword sentiment analyzers** (e.g. VADER, FinBERT) return naive positive/negative scores that conflate operational health with corporate spin.
3. **Naive automated bots** get chopped up by contradictory headlines: they see "Buyback" and buy, right into a guidance downgrade.

---

## 🔬 Our Real Live Benchmark Results

We tested this exact earnings transcript snippet against the TypeSafe Console (`https://console.typesafe.ai`):

```text
CEO Q3 Earnings Call Transcript Excerpt:
"Gross margins contracted by 120 basis points to 58.4%... subscription cloud transformation 
continues to accelerate rapidly, with ARR up 28% YoY... prudently revising Q4 revenue 
guidance downward by 3%... Board of Directors has authorized a new $1.5 billion accelerated 
share repurchase program..."
```

### Live TypeSafe Output:
```json
{
  "evaluation_time_ms": 100.79,
  "answers": {
    "guidance_revision":  { "choice": "revised_down",  "confidence": 1.0 },
    "margin_sentiment":   { "score": 0.78,             "confidence": 0.77 },
    "capital_allocation": { "choice": "share_buyback", "confidence": 1.0 },
    "signal_ambiguity":   { "score": 2.0,              "confidence": 1.0 }
  }
}
```

### Automated Engine Decision:
```text
→ Decision: ROUTE_TO_ANALYST (High Signal Ambiguity: 2.0 / 2.0)
→ Action: Prevented automated trade on contradictory signals
```

---

## 💡 Architectural Insight: The Power of Continuous Scores

### 1. Score as a Continuous Expectation ($\mathbb{E}[\text{level}]$)
In Jev, the `score` primitive does **not** return a rigid integer bucket (1, 2, 3). Instead, Jev returns the **probability-weighted expected value** across the ordered criteria rubric:

$$\mathbb{E}[\text{level}] = \sum_{i=0}^{N-1} i \cdot P(\text{level}_i \mid S)$$

In our live test for `margin_sentiment` across 4 levels (0: severe, 1: slight, 2: stable, 3: expansion):
- **Level 0 ("severe compression")**: $P = 0.23$
- **Level 1 ("slight pressure")**: $P = 0.77$
- **Level 2 ("stable")**: $P = 0.00$
- **Level 3 ("expansion")**: $P = 0.00$

$$\mathbb{E}[\text{level}] = (0 \times 0.23) + (1 \times 0.77) + (2 \times 0.00) + (3 \times 0.00) = 0.77 \approx \mathbf{0.78}$$

This gives quantitative hedge funds and risk models **continuous, differentiable data** directly consumable by automated risk matrices and Black-Scholes volatility adjustments.

### 2. Ambiguity Detection Prevents False Breakout Losses
`signal_ambiguity` hit level 2.0 with **100% confidence**. 

Instead of writing complex regexes or asking an LLM to guess what to do, **the trading logic stays in version-controlled Python**:
```python
ambiguity = answers["signal_ambiguity"]["score"]
guidance  = answers["guidance_revision"]["choice"]

if ambiguity >= 1.5:
    # Conflicting operational signals vs financial engineering -> Let an analyst judge
    route_to_analyst_desk()
elif guidance == "revised_up" and ambiguity < 0.5:
    # Clean, unambiguous momentum -> Auto-trade instantly
    execute_market_buy("MAX")
```

---

## 📁 Files in this Example

- [`signal_extractor.py`](signal_extractor.py) — Runnable Python script evaluating 3 scenarios (Mixed signal, Blowout quarter, Severe miss) with algorithmic decision logic.
- [`payload.json`](payload.json) — Console-ready JSON containing the state and typed questions from our live benchmark session.

---

## 🚀 How to Run

### 1. Install Dependencies
```bash
pip install requests python-dotenv
```

### 2. Configure Your Environment
Set your API key in `.env`:
```env
TYPESAFE_API_KEY=your_typesafe_api_key_here
```

### 3. Run the Extractor
```bash
python signal_extractor.py
```

---

## 📊 Sample Script Output

```text
==============================================================================
   Jev System One: Real-Time Trading Signal Extraction & Quant Routing
   Provider: TypeSafe AI Direct | Endpoint: https://api.typesafe.ai/v1/systemone
==============================================================================

>> Analyzing Earnings Transcript: [TECH-CORP] — CASE-1: MIXED SIGNALS (ACTUAL TEST CASE)
   Thesis / Setup: Mixed Guidance Cut + Buyback Cushion
------------------------------------------------------------------------------
   Latency: 100.79ms (Parallel Extraction across 4 dimensions)
     * guidance_revision  : revised_down (confidence: 100%)
     * margin_sentiment   : 0.78 / 3.0 (confidence: 77%)  <-- Continuous Float
     * capital_allocation : share_buyback (confidence: 100%)
     * signal_ambiguity   : 2.00 / 2.0 (confidence: 100%)

   Algorithmic Order Dispatch Decision:
     Strategy       : HUMAN_OVERRIDE_REQUIRED
     Order Action   : NO_AUTO_TRADE
     Target Queue   : SENIOR_EQUITY_ANALYST_DESK
     Speed / Flow   : MANUAL_HOLD
     Rationale      : High signal ambiguity (2.00/2.0). Conflicting operational headwinds vs capital engineering (revised_down + share_buyback). Requires qualitative thesis review.

>> Analyzing Earnings Transcript: [NEXUS-AI] — CASE-2: CLEARLY POSITIVE (BLOWOUT QUARTER)
   Thesis / Setup: Beat-and-Raise with Operating Leverage
------------------------------------------------------------------------------
   Latency: 97.40ms (Parallel Extraction across 4 dimensions)
     * guidance_revision  : revised_up (confidence: 100%)
     * margin_sentiment   : 3.00 / 3.0 (confidence: 98%)  <-- Continuous Float
     * capital_allocation : none (confidence: 95%)
     * signal_ambiguity   : 0.05 / 2.0 (confidence: 99%)

   Algorithmic Order Dispatch Decision:
     Strategy       : ALGO_EXECUTION_BULL
     Order Action   : EXECUTE_MARKET_BUY
     Target Queue   : DIRECT_DMA_GATEWAY
     Speed / Flow   : ULTRA_FAST (<5ms post-eval)
     Rationale      : Unambiguous positive fundamentals (guidance=revised_up, margin_score=3.00/3.0, ambiguity=0.05).

>> Analyzing Earnings Transcript: [LEGACY-SYS] — CASE-3: CLEARLY NEGATIVE (DETERIORATION & DIVIDEND CUT)
   Thesis / Setup: Severe Miss, Headwinds, and Capital Preservation
------------------------------------------------------------------------------
   Latency: 102.10ms (Parallel Extraction across 4 dimensions)
     * guidance_revision  : revised_down (confidence: 100%)
     * margin_sentiment   : 0.08 / 3.0 (confidence: 96%)  <-- Continuous Float
     * capital_allocation : dividend_cut (confidence: 99%)
     * signal_ambiguity   : 0.12 / 2.0 (confidence: 97%)

   Algorithmic Order Dispatch Decision:
     Strategy       : ALGO_EXECUTION_BEAR
     Order Action   : EXECUTE_MARKET_SELL / DELTA_HEDGE
     Target Queue   : DIRECT_DMA_GATEWAY
     Speed / Flow   : ULTRA_FAST (<5ms post-eval)
     Rationale      : Unambiguous operational deterioration (guidance=revised_down, margin_score=0.08/3.0, capital_action=dividend_cut).
```
