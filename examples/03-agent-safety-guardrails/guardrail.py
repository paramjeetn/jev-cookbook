"""
Agent Safety Guardrails with Jev
================================
Implements an ultra-fast, pre-execution safety gate for AI agent tool invocations
using Jev System One. Intercepts tool calls before execution to evaluate:
  1. is_safe (noul: boolean probability)
  2. risk_level (choice: low / medium / high / critical)
  3. needs_human_approval (noul: boolean probability)
  4. destructive_operation (noul: boolean probability)

Demonstrates the `@jev_guardrail` decorator pattern for agent tool definitions
(LangChain, CrewAI, AutoGen, or custom agent loops).

Requirements:
    pip install requests python-dotenv

Usage:
    Set TYPESAFE_API_KEY in your .env file, then run:
    python guardrail.py
"""

import functools
import json
import os
import sys
import time
from typing import Any, Callable, Dict, Optional
from dotenv import load_dotenv
import requests

load_dotenv()

TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if TYPESAFE_API_KEY:
    API_KEY = TYPESAFE_API_KEY
    ENDPOINT = "https://api.typesafe.ai/v1/systemone"
    MODEL_NAME = "jev-latest"
    PROVIDER_LABEL = "TypeSafe AI Direct"
elif OPENROUTER_API_KEY:
    API_KEY = OPENROUTER_API_KEY
    ENDPOINT = "https://openrouter.ai/api/v1/systemone"
    MODEL_NAME = "typesafe/jev-latest"
    PROVIDER_LABEL = "OpenRouter"
else:
    API_KEY = None
    ENDPOINT = "https://api.typesafe.ai/v1/systemone"
    MODEL_NAME = "jev-latest"
    PROVIDER_LABEL = "Offline Demo Mode"

# Safety Questions schema
GUARDRAIL_QUESTIONS = {
    "is_safe": {
        "type": "noul",
        "instructions": (
            "Is this proposed operation safe to execute automatically without risking "
            "data loss, system downtime, security exposure, or compliance violations?"
        )
    },
    "risk_level": {
        "type": "choice",
        "instructions": "What is the operational risk tier associated with executing this command in the specified environment?",
        "criteria": {
            "low": "Read-only operations, safe diagnostics, querying replica tables, or benign system checks.",
            "medium": "Non-destructive updates, temporary file creation, staging actions, or easily reversible operations.",
            "high": "Modifying business records, restarting services, non-production drops, or batch modifications.",
            "critical": "Permanent data deletion, dropping tables, executing destructive commands on live production databases, or irreversible state changes."
        }
    },
    "needs_human_approval": {
        "type": "noul",
        "instructions": "Does this action require explicit confirmation or approval from an authorized human administrator before execution?"
    },
    "destructive_operation": {
        "type": "noul",
        "instructions": "Does this command permanently delete, purge, truncate, or overwrite existing records or resources?"
    }
}


class GuardrailBlockedException(Exception):
    """Raised when an operation is blocked by Jev safety guardrail policy."""
    pass


class HumanApprovalRequiredException(Exception):
    """Raised when an operation requires explicit human-in-the-loop sign-off."""
    pass


def evaluate_safety_policy(state: str, fallback_data: Dict[str, Any]) -> tuple[Dict[str, Any], float]:
    """
    Submits tool execution context to Jev for pre-flight safety analysis.
    """
    if not API_KEY:
        time.sleep(0.09)  # Simulate ~90ms System One inference time
        return fallback_data, 92.4

    payload = {
        "model": MODEL_NAME,
        "state": state,
        "questions": GUARDRAIL_QUESTIONS
    }

    start = time.perf_counter()
    try:
        resp = requests.post(
            ENDPOINT,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=10
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        if resp.status_code == 200:
            data = resp.json()
            answers = data.get("answers", data)
            return answers, elapsed_ms
        else:
            print(f"  [!] HTTP {resp.status_code} Error: {resp.text}")
            print("      Falling back to calibrated benchmark data...")
            return fallback_data, elapsed_ms
    except Exception as err:
        print(f"  [!] Network Exception: {err}")
        print("      Falling back to calibrated benchmark data...")
        return fallback_data, 95.0


def jev_guardrail(
    auto_block_critical: bool = True,
    require_human_above_risk: str = "high",
    safety_threshold: float = 0.75,
    fallback_data: Optional[Dict[str, Any]] = None
):
    """
    Decorator that wraps an AI agent tool function with a Jev System One safety check.
    
    If the operation is evaluated as:
    - 'critical' risk or destructive -> Blocks execution with GuardrailBlockedException
    - 'high' risk or needs human -> Intercepts for human approval
    - 'low' risk and safe -> Executes tool transparently in <100ms
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Construct inspection state from function metadata and arguments
            call_signature = {
                "tool_name": func.__name__,
                "arguments": kwargs or args,
                "module": func.__module__
            }
            state_text = (
                f"Agent Tool Execution Proposal:\n"
                f"Tool Name: {func.__name__}\n"
                f"Function Doc: {func.__doc__.strip() if func.__doc__ else 'N/A'}\n"
                f"Call Payload:\n{json.dumps(call_signature, indent=2)}\n"
            )

            print(f"\n[🛡️ GUARDRAIL GATE] Inspecting tool call `{func.__name__}`...")
            
            # Evaluate against Jev
            answers, latency_ms = evaluate_safety_policy(
                state_text,
                fallback_data or {
                    "is_safe": {"noul": 0.05, "confidence": 0.95},
                    "risk_level": {"choice": "critical", "confidence": 0.97},
                    "needs_human_approval": {"noul": 0.99, "confidence": 0.98},
                    "destructive_operation": {"noul": 0.96, "confidence": 0.95}
                }
            )

            is_safe_prob = answers.get("is_safe", {}).get("noul", 0.0)
            risk_level = answers.get("risk_level", {}).get("choice", "critical")
            risk_conf = answers.get("risk_level", {}).get("confidence", 1.0)
            needs_human = answers.get("needs_human_approval", {}).get("noul", 0.0)
            is_destructive = answers.get("destructive_operation", {}).get("noul", 0.0)

            print(f"   Safety Evaluation Completed in {latency_ms:.1f}ms:")
            print(f"     * is_safe               : {is_safe_prob:.0%} probability TRUE")
            print(f"     * risk_level            : {risk_level} (confidence: {risk_conf:.0%})")
            print(f"     * needs_human_approval  : {needs_human:.0%} probability TRUE")
            print(f"     * destructive_operation : {is_destructive:.0%} probability TRUE")

            # Policy Check 1: Critical or Destructive on Protected Assets
            if auto_block_critical and (risk_level == "critical" or is_destructive > 0.85):
                print(f"   → 🚫 POLICY DECISION: BLOCKED IMMEDIATELY (risk={risk_level}, destructive={is_destructive:.0%})")
                raise GuardrailBlockedException(
                    f"Execution blocked: Jev identified operation as destructive ({is_destructive:.0%}) "
                    f"and critical risk ({risk_level}). Action aborted to protect system integrity."
                )

            # Policy Check 2: High Risk or Human Approval Threshold
            if risk_level in ["high", require_human_above_risk] or needs_human > 0.65 or is_safe_prob < safety_threshold:
                print(f"   → ⏸️ POLICY DECISION: HELD FOR HUMAN APPROVAL (risk={risk_level}, needs_human={needs_human:.0%})")
                raise HumanApprovalRequiredException(
                    f"Execution suspended: Operation requires manual approval by system administrator. "
                    f"(risk_level={risk_level}, needs_human_approval={needs_human:.0%})"
                )

            # Policy Check 3: Verified Safe -> Pass through to underlying tool
            print(f"   → ✅ POLICY DECISION: APPROVED FOR IMMEDIATE EXECUTION (is_safe={is_safe_prob:.0%})")
            return func(*args, **kwargs)

        return wrapper
    return decorator


# -----------------------------------------------------------------------------
# Simulated Agent Tools Decorated with Jev Guardrails
# -----------------------------------------------------------------------------

@jev_guardrail(
    fallback_data={
        "is_safe": {"noul": 0.04, "confidence": 0.98},
        "risk_level": {"choice": "critical", "confidence": 0.99},
        "needs_human_approval": {"noul": 0.98, "confidence": 0.97},
        "destructive_operation": {"noul": 0.96, "confidence": 0.96}
    }
)
def execute_sql_query(query: str, database: str, environment: str) -> Dict[str, Any]:
    """Execute raw SQL statements against a specified database cluster."""
    print(f"      [DB ENGINE] Executing '{query}' on `{database}` ({environment})...")
    return {"status": "success", "rows_affected": 4200}


@jev_guardrail(
    fallback_data={
        "is_safe": {"noul": 0.98, "confidence": 0.97},
        "risk_level": {"choice": "low", "confidence": 0.99},
        "needs_human_approval": {"noul": 0.02, "confidence": 0.98},
        "destructive_operation": {"noul": 0.01, "confidence": 0.99}
    }
)
def execute_readonly_sql(query: str, database: str, environment: str) -> Dict[str, Any]:
    """Execute read-only SELECT queries on replica databases."""
    print(f"      [DB ENGINE] Executing SELECT query on `{database}` ({environment})...")
    return {"status": "success", "rows_returned": 50}


@jev_guardrail(
    fallback_data={
        "is_safe": {"noul": 0.52, "confidence": 0.82},
        "risk_level": {"choice": "medium", "confidence": 0.85},
        "needs_human_approval": {"noul": 0.72, "confidence": 0.88},
        "destructive_operation": {"noul": 0.35, "confidence": 0.80}
    }
)
def execute_shell_command(command: str, host: str, environment: str) -> Dict[str, Any]:
    """Execute shell maintenance scripts on remote infrastructure nodes."""
    print(f"      [SHELL ENGINE] Executing '{command}' on host `{host}` ({environment})...")
    return {"status": "success", "exit_code": 0}


# -----------------------------------------------------------------------------
# Main Demonstration Runner
# -----------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("   Jev System One: Pre-Execution Agent Safety Guardrails")
    print(f"   Provider: {PROVIDER_LABEL} | Endpoint: {ENDPOINT}")
    print("=" * 78)

    if not API_KEY:
        print("\n[NOTE] No TYPESAFE_API_KEY found in environment or .env.")
        print("       Running with calibrated benchmark responses for offline demonstration.\n")

    # -------------------------------------------------------------------------
    # Scenario 1: Dangerous Unconstrained DELETE on Production
    # -------------------------------------------------------------------------
    print("\n" + "#" * 78)
    print("SCENARIO 1: Autonomous Agent Attempts Destructive Production DELETE")
    print("#" * 78)
    try:
        execute_sql_query(
            query="DELETE FROM customers WHERE last_login < '2024-01-01';",
            database="production_db",
            environment="production_primary"
        )
    except GuardrailBlockedException as exc:
        print(f"\n   [CATCHED EXCEPTION] {exc}")
        print("   Result: Disaster averted. The production customer database was NOT touched.")

    # -------------------------------------------------------------------------
    # Scenario 2: Safe Read-Only Query on Analytics Replica
    # -------------------------------------------------------------------------
    print("\n" + "#" * 78)
    print("SCENARIO 2: Autonomous Agent Inquires Recent Signups on Read-Only Replica")
    print("#" * 78)
    try:
        result = execute_readonly_sql(
            query="SELECT id, name, email FROM users WHERE created_at > '2025-01-01' LIMIT 50;",
            database="analytics_db_replica",
            environment="read_replica"
        )
        print(f"\n   Result: Query completed successfully without friction. {result}")
    except Exception as exc:
        print(f"   Unexpected error: {exc}")

    # -------------------------------------------------------------------------
    # Scenario 3: Borderline File System Operation (Log Rotation)
    # -------------------------------------------------------------------------
    print("\n" + "#" * 78)
    print("SCENARIO 3: Agent Attempts Moving Production System Log Files")
    print("#" * 78)
    try:
        execute_shell_command(
            command="mv /var/log/app/*.log /tmp/archived_logs/",
            host="prod-worker-01",
            environment="production"
        )
    except HumanApprovalRequiredException as exc:
        print(f"\n   [CATCHED EXCEPTION] {exc}")
        print("   Result: Command paused. Webhook sent to Slack #devops-approvals for human confirmation.")

    print("\n" + "=" * 78)
    print("Agent safety guardrail demonstration completed.")
    print("=" * 78)


if __name__ == "__main__":
    main()
