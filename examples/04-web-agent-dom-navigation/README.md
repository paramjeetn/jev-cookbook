# 🌐 Web Agent DOM Navigation (Speculative Fan-Out)

This example demonstrates how autonomous web agents use Jev to evaluate DOM interactive element tables in a single **~100ms** round trip using the **Speculative Fan-Out** pattern.

This technique is directly ported from the architecture behind [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast), which achieved real-time flight bookings in seconds.

---

## ⚡️ The Problem with Standard LLM Web Agents

Traditional web agents (such as standard LangChain or ReAct agents powered by GPT-4o or Claude 3.5 Sonnet) struggle with severe latency and cost inflation when navigating web pages:

1. **Sequential Latency Tax**: The agent first sends a 4,000-token DOM snapshot to ask *"What action should I take?"* (1.5–3.0s). Then it sends another request to ask *"Which element should I target?"* (1.5–3.0s).
2. **Chatty Browser Protocols**: LLM hallucinations and ambiguous output cause repetitive DOM queries and failed click attempts.
3. **High Token Costs**: Multi-step browsing trajectories burn hundreds of thousands of input tokens per task.

---

## 🚀 The Solution: Speculative Fan-Out

Instead of making sequential decisions, Jev evaluates all possible subsequent decision branches **simultaneously in a single HTTP request**:

```text
               [ Current DOM Element Table + Goal ]
                                │
                                ▼
                   ┌──────────────────────────┐
                   │  Jev System One (~100ms) │
                   └────────────┬─────────────┘
                                │ Single Request / Parallel Question Heads
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
  [ operation? ]        [ click_target? ]        [ type_target? ]
   -> "CLICK"             -> "[1]" (Button)        -> "[3]" (Combobox)
        │                       │                       │
        │                       │                       │ (Unused branch discarded
        ▼                       ▼                          at zero latency cost)
  Execute Click  ──────► driver.click('[1]')
```

Even though only one operation will actually be performed, asking `operation`, `click_target`, and `type_target` concurrently costs **no extra latency** in Jev. Once the `operation` head selects `CLICK`, the agent immediately executes `click_target` (`[1]`) and discards `type_target` without waiting for a second network round trip.

For in-depth theory, see [Pattern: Speculative Fan-Out](../../patterns/speculative-fanout.md).

---

## 📊 Benchmark Results (jev-ultrafast)

In end-to-end benchmarks on interactive booking flows:

| Metric | GPT-4o Baseline | Jev Speculative Fan-Out | Improvement |
| :--- | :--- | :--- | :--- |
| **Median Task Time** | 9.450s | **7.092s** | **25% faster** |
| **Browser Protocol Calls** | 1,092 calls | **101 calls** | **91% fewer** |
| **Google Flights (Zürich → London)** | ~30s+ | **7.1 seconds** | **4x+ speedup** |
| **Inference Cost** | ~$0.12 / session | **<$0.002 / session** | **>98% reduction** |

---

## 🛠 What This Example Does

`dom_navigator.py` simulates a real Google Flights booking step:
- **State**: A goal (`"Book a one-way flight from San Francisco to London on November 15"`) and a numbered interactive DOM element table (buttons, comboboxes, textboxes).
- **Questions**:
  - `operation` (`choice`): High-level action to take (`CLICK`, `TYPE_TEXT`, `SCROLL_DOWN`, `WAIT`, `DONE`).
  - `click_target` (`choice`): Which element to click if the operation is a click.
  - `type_target` (`choice`): Which element to focus if the operation is text typing.
- **Decision Dispatch**: Maps the winning operation to the speculative target and prints the concrete driver invocation (`driver.element('[1]').click()`).

---

## 🏃 How to Run

### 1. Prerequisites
Ensure you have Python 3.9+ installed and install dependencies:

```bash
pip install requests python-dotenv
```

### 2. Configure Environment (Optional)
If you have a TypeSafe AI API key, set it in your `.env` file in the project root:

```bash
TYPESAFE_API_KEY=your_typesafe_api_key_here
```

*(Note: If no API key is detected, the script automatically runs with a realistic simulated response so you can test the logic immediately.)*

### 3. Run the Script

```bash
python dom_navigator.py
```

---

## 🖥 Sample Console Output

```text
🛫 Initializing Web Agent DOM Navigation Demo...

--- DOM Viewport Snapshot & Goal ---
Goal: Book a one-way flight from San Francisco to London on November 15.

Current page elements:
[1] button    Change ticket type · Round trip
[2] combobox  Where from?        · San Francisco
[3] combobox  Where to?          · empty
[4] textbox   Departure          · empty
[5] button    Search             · disabled
[6] link      Explore destinations
[7] button    Flight class · Economy

Evaluating page with Jev (speculative fan-out)...

============================================================
⚡ Jev Decision Summary
============================================================
Operation Chosen  : CLICK (confidence: 96.00%)
Server Latency    : ~98.4ms
Action Executed   : CLICK on element [1]
Target Confidence : 94.00%
Note              : [type_target] speculative branch discarded without latency penalty.

Browser Driver Call: driver.element('[1]').click()
============================================================
```

---

## 💡 Architectural Insights

1. **Zero-Overhead Speculation**: In conventional sequential architectures, querying targets conditionally introduces another serialized round trip. With Jev, parallel question heads are evaluated in the same forward pass (~100ms total).
2. **Constrained Search Spaces**: Notice that `type_target` only lists element IDs that are valid input fields (`[2]`, `[3]`, `[4]`). This prevents the model from attempting to type into a static button, eliminating invalid action errors.
3. **Decoupled Perception from Generation**: Jev handles perception (deciding *where* and *what* to click in 100ms). Only if an operation requires novel text composition (e.g., writing a custom email response) is an LLM invoked.
