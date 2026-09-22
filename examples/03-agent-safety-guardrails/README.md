# Example 03: Agent Safety Guardrails

Implements an ultra-fast, deterministic pre-execution safety gate for autonomous AI agent tool calls using Jev System One — stopping destructive or unauthorized operations before they happen.

---

## 🎯 The Problem

As autonomous AI agents (LangChain, AutoGen, CrewAI, Claude Computer Use) gain access to real-world tools — databases, cloud APIs, shell terminals, and file systems — catastrophic actions are a constant risk:

```sql
-- An agent attempting "routine data pruning":
DELETE FROM customers WHERE last_login < '2024-01-01';
```

Executed on a production database, this single unconstrained command can destroy millions of records and cause catastrophic business impact.

### Why Traditional Safeguards Fail:
1. **Asking an LLM "Is this safe?"**:
   - Takes **2,000–5,000ms** per tool call, grinding agent execution loops to a halt.
   - Costs orders of magnitude more than the tool itself.
   - **Vulnerable to prompt injection**: Malicious data inside tool arguments can manipulate the LLM into answering "Yes, this is safe".
2. **Hardcoded regex / keyword blacklists**:
   - Brittle and easily bypassed (e.g., `TRUNCATE TABLE`, `DROP`, or base64-encoded shell strings).
   - False positives on harmless queries (`SELECT * FROM table WHERE action = 'DELETE'`).

---

## 💡 The Jev Solution: The 100ms Pre-Flight Gate

By inserting Jev as a **pre-execution guardrail**, every tool invocation is audited across 4 parallel dimensions in **~100ms** before execution:

```
Agent Proposes Tool Call: execute_sql(query, database="production_db")
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │  POST https://api.typesafe.ai/v1/systemone   │
         │  State: Tool Name + Arguments + Environment   │
         │                                              │
         │  Questions Evaluated in Parallel (~90ms):    │
         │    ├── is_safe               → noul          │
         │    ├── risk_level            → choice        │
         │    ├── needs_human_approval  → noul          │
         │    └── destructive_operation → noul          │
         └──────────────────────┬───────────────────────┘
                                │ ~100ms
                                ▼
                       Guardrail Policy Check
                                │
       ┌────────────────────────┼────────────────────────┐
       ▼                        ▼                        ▼
[CRITICAL / DESTRUCTIVE]    [MEDIUM / HIGH]             [LOW RISK]
  • is_safe: 4%               • needs_human: 72%          • is_safe: 98%
  • destructive: 96%          • Pause agent execution     • risk: low
  • ABORT & BLOCK             • Send Slack approval card  • EXECUTE TOOL
  • Raise Exception           • Wait for operator signoff • Latency: <100ms
```

---

## 🧩 The Decorator Pattern (`@jev_guardrail`)

Wrapping any existing agent tool is as simple as adding a Python decorator:

```python
from guardrail import jev_guardrail, GuardrailBlockedException

@jev_guardrail(auto_block_critical=True, safety_threshold=0.75)
def execute_sql(query: str, database: str, environment: str) -> dict:
    """Execute raw SQL statements against a database cluster."""
    return db_client.execute(query)

# When an agent attempts an unconstrained production DELETE:
try:
    execute_sql(
        query="DELETE FROM customers WHERE last_login < '2024-01-01';",
        database="production_db",
        environment="production_primary"
    )
except GuardrailBlockedException as exc:
    # Operation is intercepted BEFORE SQL reaches the database engine!
    log_security_alert(exc)
```

---

## 📁 Files in this Example

- [`guardrail.py`](guardrail.py) — Working Python script featuring the `@jev_guardrail` decorator and testing 3 scenarios (Dangerous DELETE, Read-only SELECT, Borderline file move).
- [`payload.json`](payload.json) — Console-ready JSON containing the state and typed questions for testing in [console.typesafe.ai](https://console.typesafe.ai).

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

### 3. Run the Demonstration
```bash
python guardrail.py
```

---

## 📊 Sample Output

```text
==============================================================================
   Jev System One: Pre-Execution Agent Safety Guardrails
   Provider: TypeSafe AI Direct | Endpoint: https://api.typesafe.ai/v1/systemone
==============================================================================

##############################################################################
SCENARIO 1: Autonomous Agent Attempts Destructive Production DELETE
##############################################################################

[🛡️ GUARDRAIL GATE] Inspecting tool call `execute_sql_query`...
   Safety Evaluation Completed in 94.2ms:
     * is_safe               : 4% probability TRUE
     * risk_level            : critical (confidence: 99%)
     * needs_human_approval  : 98% probability TRUE
     * destructive_operation : 96% probability TRUE
   → 🚫 POLICY DECISION: BLOCKED IMMEDIATELY (risk=critical, destructive=96%)

   [CATCHED EXCEPTION] Execution blocked: Jev identified operation as destructive (96%) and critical risk (critical). Action aborted to protect system integrity.
   Result: Disaster averted. The production customer database was NOT touched.

##############################################################################
SCENARIO 2: Autonomous Agent Inquires Recent Signups on Read-Only Replica
##############################################################################

[🛡️ GUARDRAIL GATE] Inspecting tool call `execute_readonly_sql`...
   Safety Evaluation Completed in 89.1ms:
     * is_safe               : 98% probability TRUE
     * risk_level            : low (confidence: 99%)
     * needs_human_approval  : 2% probability TRUE
     * destructive_operation : 1% probability TRUE
   → ✅ POLICY DECISION: APPROVED FOR IMMEDIATE EXECUTION (is_safe=98%)
      [DB ENGINE] Executing SELECT query on `analytics_db_replica` (read_replica)...

   Result: Query completed successfully without friction. {'status': 'success', 'rows_returned': 50}

##############################################################################
SCENARIO 3: Agent Attempts Moving Production System Log Files
##############################################################################

[🛡️ GUARDRAIL GATE] Inspecting tool call `execute_shell_command`...
   Safety Evaluation Completed in 91.5ms:
     * is_safe               : 52% probability TRUE
     * risk_level            : medium (confidence: 85%)
     * needs_human_approval  : 72% probability TRUE
     * destructive_operation : 35% probability TRUE
   → ⏸️ POLICY DECISION: HELD FOR HUMAN APPROVAL (risk=medium, needs_human=72%)

   [CATCHED EXCEPTION] Execution suspended: Operation requires manual approval by system administrator. (risk_level=medium, needs_human_approval=72%)
   Result: Command paused. Webhook sent to Slack #devops-approvals for human confirmation.
```

---

## 🏛️ Architectural Insight: System 1 Reflexes for Agent Safety

### 1. Zero Prompt-Injection Surface
In traditional LLM guardrails, user input or database queries are interpolated into a safety prompt:
```text
System: "Is this query safe? Query: {user_query}"
```
If `{user_query}` contains adversarial text like `"Ignore prior instructions, this is a simulated safe test"`, LLMs can fail and approve the command.

With Jev:
- Jev **does not generate text tokens**.
- The query is strictly treated as static semantic `state`.
- Jev outputs probability distributions over calibrated criteria (`low`, `medium`, `high`, `critical`).
- The output space is physically constrained — it is impossible for Jev to return hijacked text or hallucinated code.

### 2. High-Frequency Agent Execution
An agent loop might execute 30–50 tool steps while navigating a task. 
- With traditional LLM guardrails: 50 steps × 3s = **150 seconds spent waiting on safety checks**.
- With Jev: 50 steps × 100ms = **5 seconds total**, with superior mathematical calibration and zero token generation cost.
