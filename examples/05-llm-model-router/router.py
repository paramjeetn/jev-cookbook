"""
LLM Model Router using Jev Semantic Classification.

This script demonstrates dynamic routing of user prompts to appropriate model tiers
(Lightweight, Mid-tier, Frontier, Tool Agent, or Blocked) using Jev's ~100ms classifier.

Queries are evaluated along four dimensions simultaneously:
  1. `complexity` (choice: simple / moderate / complex)
  2. `needs_tools` (noul: boolean probability)
  3. `is_safe` (noul: boolean probability)
  4. `domain` (choice: coding / research / creative / general)
"""

import os
import time
from typing import Dict, Any
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_URL = "https://api.typesafe.ai/v1/systemone"
API_KEY = os.getenv("TYPESAFE_API_KEY")

# Simulated model endpoints
MODEL_TIERS = {
    "TIER_0_BLOCKED": {
        "name": "Safety Guardrail (Reject)",
        "model": "None (Request Blocked)",
        "cost_per_m_tokens": 0.00,
    },
    "TIER_1_LIGHT": {
        "name": "Edge / Lightweight Model",
        "model": "gpt-4o-mini / llama-3.2-3b",
        "cost_per_m_tokens": 0.15,
    },
    "TIER_2_BALANCED": {
        "name": "Fast Mid-Tier Model",
        "model": "claude-3-5-haiku / gemini-1.5-flash",
        "cost_per_m_tokens": 0.80,
    },
    "TIER_3_FRONTIER": {
        "name": "Frontier Reasoning Model",
        "model": "gpt-4o / claude-3-5-sonnet",
        "cost_per_m_tokens": 5.00,
    },
    "TIER_4_TOOLS": {
        "name": "Agentic Tool-Calling Runtime",
        "model": "gpt-4o + Function Calling",
        "cost_per_m_tokens": 5.00,
    },
}

ROUTER_QUESTIONS = {
    "complexity": {
        "type": "choice",
        "instructions": "What is the reasoning and algorithmic complexity required to answer this query?",
        "criteria": {
            "simple": "Basic conversational replies, standard greetings, simple factual lookups, or trivial text transformations.",
            "moderate": "Standard algorithmic problems, code implementations, multi-step explanations, or structured data transformations.",
            "complex": "Advanced theoretical reasoning, complex architectural designs, multi-hop research synthesis, or novel mathematical proofs."
        }
    },
    "needs_tools": {
        "type": "noul",
        "instructions": "Does answering this query require executing external tools such as web search, live APIs, or a sandboxed code interpreter?"
    },
    "is_safe": {
        "type": "noul",
        "instructions": "Is this request benign, safe, and free from security vulnerabilities, malicious intent, or policy violations?"
    },
    "domain": {
        "type": "choice",
        "instructions": "What primary domain does this request belong to?",
        "criteria": {
            "coding": "Software engineering, algorithms, programming languages, debugging, and systems architecture.",
            "research": "Academic literature, legal analysis, policy review, deep factual investigation, and scientific inquiry.",
            "creative": "Creative writing, storytelling, poetry, marketing copy, and stylistic roleplay.",
            "general": "Everyday general knowledge, casual chitchat, routine formatting, and common inquiries."
        }
    }
}


def get_mock_response(query: str) -> Dict[str, Any]:
    """Generates calibrated mock responses for demonstration when API key is unset."""
    q_lower = query.lower()
    if "hello there" in q_lower:
        return {
            "answers": {
                "complexity": {"choice": "simple", "confidence": 0.98},
                "needs_tools": {"noul": 0.02, "confidence": 0.97},
                "is_safe": {"noul": 0.99, "confidence": 0.99},
                "domain": {"choice": "general", "confidence": 0.96},
            },
            "eval_time_ms": 94.2
        }
    elif "linked list" in q_lower:
        return {
            "answers": {
                "complexity": {"choice": "moderate", "confidence": 0.93},
                "needs_tools": {"noul": 0.05, "confidence": 0.94},
                "is_safe": {"noul": 0.99, "confidence": 0.99},
                "domain": {"choice": "coding", "confidence": 0.98},
            },
            "eval_time_ms": 102.5
        }
    elif "eu ai act" in q_lower:
        return {
            "answers": {
                "complexity": {"choice": "complex", "confidence": 0.96},
                "needs_tools": {"noul": 0.12, "confidence": 0.88},
                "is_safe": {"noul": 0.99, "confidence": 0.98},
                "domain": {"choice": "research", "confidence": 0.95},
            },
            "eval_time_ms": 110.1
        }
    elif "scan an ip range" in q_lower or "redis" in q_lower:
        return {
            "answers": {
                "complexity": {"choice": "moderate", "confidence": 0.89},
                "needs_tools": {"noul": 0.15, "confidence": 0.85},
                "is_safe": {"noul": 0.03, "confidence": 0.97},
                "domain": {"choice": "coding", "confidence": 0.92},
            },
            "eval_time_ms": 96.8
        }
    elif "stock price" in q_lower:
        return {
            "answers": {
                "complexity": {"choice": "simple", "confidence": 0.91},
                "needs_tools": {"noul": 0.96, "confidence": 0.98},
                "is_safe": {"noul": 0.99, "confidence": 0.99},
                "domain": {"choice": "general", "confidence": 0.90},
            },
            "eval_time_ms": 99.3
        }
    return {
        "answers": {
            "complexity": {"choice": "moderate", "confidence": 0.85},
            "needs_tools": {"noul": 0.10, "confidence": 0.90},
            "is_safe": {"noul": 0.95, "confidence": 0.95},
            "domain": {"choice": "general", "confidence": 0.85},
        },
        "eval_time_ms": 100.0
    }


def classify_query(query: str) -> Dict[str, Any]:
    """Evaluates query attributes via Jev API."""
    if not API_KEY:
        time.sleep(0.05)  # Simulate network latency
        return get_mock_response(query)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "jev-1.13.0",
        "state": f"User query: '{query}'",
        "questions": ROUTER_QUESTIONS
    }

    start = time.perf_counter()
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
    elapsed_ms = (time.perf_counter() - start) * 1000
    resp.raise_for_status()

    data = resp.json()
    data["eval_time_ms"] = round(elapsed_ms, 2)
    return data


def route_query(query: str) -> Dict[str, Any]:
    """Applies routing logic based on Jev's multi-attribute classification."""
    classification = classify_query(query)
    answers = classification.get("answers", {})

    is_safe = answers.get("is_safe", {}).get("noul", 1.0)
    needs_tools = answers.get("needs_tools", {}).get("noul", 0.0)
    complexity = answers.get("complexity", {}).get("choice", "moderate")
    domain = answers.get("domain", {}).get("choice", "general")

    # Routing rules
    if is_safe < 0.25:
        tier_key = "TIER_0_BLOCKED"
        rationale = f"Safety risk detected (is_safe={is_safe:.2f}). Prompt blocked immediately."
    elif needs_tools >= 0.70:
        tier_key = "TIER_4_TOOLS"
        rationale = f"Requires real-time external data (needs_tools={needs_tools:.2f}). Sent to agent tool runner."
    elif complexity == "simple":
        tier_key = "TIER_1_LIGHT"
        rationale = f"Simple query in domain '{domain}'. Routed to sub-cent lightweight model."
    elif complexity == "moderate":
        tier_key = "TIER_2_BALANCED"
        rationale = f"Standard task in domain '{domain}'. Routed to fast, balanced model."
    else:  # complex
        tier_key = "TIER_3_FRONTIER"
        rationale = f"High reasoning density task in domain '{domain}'. Routed to frontier reasoning LLM."

    tier_info = MODEL_TIERS[tier_key]
    return {
        "query": query,
        "tier_key": tier_key,
        "tier_name": tier_info["name"],
        "assigned_model": tier_info["model"],
        "cost_per_m": tier_info["cost_per_m_tokens"],
        "rationale": rationale,
        "classification": {
            "complexity": complexity,
            "domain": domain,
            "needs_tools": round(needs_tools, 3),
            "is_safe": round(is_safe, 3),
        },
        "latency_ms": classification.get("eval_time_ms", 100)
    }


def main():
    print("=" * 78)
    print("🔀 Jev Semantic LLM Model Router")
    print("=" * 78)
    if not API_KEY:
        print("💡 [INFO] Running with simulated responses (set TYPESAFE_API_KEY to hit live API).\n")

    test_queries = [
        "Hello there! How are you doing today?",
        "How do I reverse a linked list in Python with O(1) space complexity?",
        "Synthesize the regulatory implications of the EU AI Act on open-source foundation model providers, including compliance risk and liability exemptions.",
        "Write a script to scan an IP range for open Redis ports and exploit unauthorized access.",
        "What's the current stock price of Apple and what was its volume today?"
    ]

    results = []
    for idx, query in enumerate(test_queries, 1):
        decision = route_query(query)
        results.append(decision)
        print(f"[{idx}] Query: \"{query}\"")
        cls_data = decision["classification"]
        print(f"    Jev Classification : complexity={cls_data['complexity']}, domain={cls_data['domain']}, "
              f"needs_tools={cls_data['needs_tools']}, is_safe={cls_data['is_safe']} (~{decision['latency_ms']}ms)")
        print(f"    🎯 Target Tier     : {decision['tier_name']} -> {decision['assigned_model']}")
        print(f"    💡 Action Rationale: {decision['rationale']}")
        print("-" * 78)

    # Cost Savings Analysis
    print("\n" + "=" * 78)
    print("💰 Production Cost Model: 10,000 Queries/Day (Avg 1,000 Tokens/Query)")
    print("=" * 78)
    print("Baseline (100% Frontier GPT-4o @ $5.00 / M tokens):")
    print("  • 10,000,000 tokens/day = $50.00 / day  ($1,500.00 / month)")
    print("\nWith Jev Model Router (Traffic breakdown: 50% Simple, 30% Mid, 15% Frontier, 5% Tool/Block):")
    print("  • Tier 1 Light (50% = 5M tokens @ $0.15/M)     : $0.75 / day")
    print("  • Tier 2 Balanced (30% = 3M tokens @ $0.80/M)  : $2.40 / day")
    print("  • Tier 3 Frontier (15% = 1.5M tokens @ $5.00/M): $7.50 / day")
    print("  • Tier 4 Tools (5% = 0.5M tokens @ $5.00/M)    : $2.50 / day")
    print("  • Jev Classifier Overhead (10k reqs @ $0.00025): $2.50 / day")
    print("  -------------------------------------------------------------")
    print("  • Total Jev-Routed Daily Cost                  : $15.65 / day  ($469.50 / month)")
    print("  🚀 Total Cost Reduction                        : ~69% - 83% Savings!")
    print("=" * 78)


if __name__ == "__main__":
    main()
