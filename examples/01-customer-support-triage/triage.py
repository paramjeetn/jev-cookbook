"""
Customer Support Triage with Jev
================================
Triages incoming customer support communications across 5 distinct dimensions
in a single ~100ms API call:
  1. urgency (score, 3-level rubric)
  2. sentiment (choice: very_negative / negative / neutral / positive)
  3. churn_risk (noul: boolean probability)
  4. category (choice: billing / technical_outage / feature_request / account_access)
  5. is_enterprise (noul: boolean probability)

Requirements:
    pip install requests python-dotenv

Usage:
    Set TYPESAFE_API_KEY in your .env file, then run:
    python triage.py
"""

import json
import os
import sys
import time
from typing import Any, Dict
from dotenv import load_dotenv
import requests

load_dotenv()

# API Configuration
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

# Question Definitions adhering strictly to the Jev schema
TRIAGE_QUESTIONS = {
    "urgency": {
      "type": "score",
      "instructions": (
          "Rate the urgency of this support inquiry based on financial impact, "
          "system downtime, and contractual SLA breach risk."
      ),
      "criteria": [
          "Routine: Minor questions, general inquiries, or non-urgent issues that can wait for normal business hours.",
          "Elevated: Moderate business friction, non-critical degraded experience, or single-user workflow blockers.",
          "Critical emergency: Severe production outage, substantial financial losses, active SLA breach, or imminent account cancellation."
      ]
    },
    "sentiment": {
      "type": "choice",
      "instructions": "What is the primary emotional sentiment expressed by the customer in this message?",
      "criteria": {
          "very_negative": "Furious, outraged, actively threatening legal or contract cancellation, hostile tone.",
          "negative": "Dissatisfied, frustrated, impatient, or complaining about service quality.",
          "neutral": "Objective, matter-of-fact, transactional, or polite business inquiry.",
          "positive": "Appreciative, satisfied, enthusiastic, or complimentary."
      }
    },
    "churn_risk": {
      "type": "noul",
      "instructions": "Is there a high probability that this customer will churn, cancel their contract, or switch to a competitor if not resolved immediately?"
    },
    "category": {
      "type": "choice",
      "instructions": "What operational category best classifies this customer inquiry?",
      "criteria": {
          "technical_outage": "System downtime, service unavailability, 5xx server errors, or broken production APIs.",
          "billing": "Invoices, payment processing charges, credit card updates, or refund requests.",
          "feature_request": "Ideas for product enhancements, missing capabilities, or feature suggestions.",
          "account_access": "Login failures, password resets, multi-factor authentication, or SSO permissions."
      }
    },
    "is_enterprise": {
      "type": "noul",
      "instructions": "Does this inquiry originate from an enterprise or high-value customer based on corporate scale, contract mentions, or executive title?"
    }
}

# 3 Realistic Customer Scenarios
SCENARIOS = [
    {
        "id": "TICKET-101",
        "name": "Enterprise Production Outage",
        "state": (
            "From: james.chen@globaltech-industries.com\n"
            "To: enterprise-support@typesafe-demo.com\n"
            "Date: Mon, 22 Sep 2026 02:47:18 GMT\n"
            "Subject: URGENT - Production API Outage costing $10k/hr - SLA Breach\n\n"
            "I am writing to express extreme dissatisfaction. Our entire customer-facing "
            "checkout system has been failing for over 3 hours due to 502 Bad Gateway "
            "responses from your v2/payments endpoint. We estimate our revenue loss at "
            "approximately $10,000 per hour. Your status dashboard reports 'All Systems Operational', "
            "which is completely untrue. Our Tier-1 Enterprise contract promises a 15-minute response SLA, "
            "yet our tickets have gone unanswered and phone lines keep disconnecting. If this is not "
            "escalated to engineering leadership and resolved within the hour, we will be forced to "
            "failover to our secondary provider and invoke our contract cancellation clause.\n\n"
            "James Chen\n"
            "Chief Technology Officer, GlobalTech Industries (Enterprise Tier ID: #GT-88491)"
        ),
        "mock_fallback": {
            "urgency": {"score": 2.85, "confidence": 0.94},
            "sentiment": {"choice": "very_negative", "confidence": 0.98},
            "churn_risk": {"noul": 0.92, "confidence": 0.90},
            "category": {"choice": "technical_outage", "confidence": 0.99},
            "is_enterprise": {"noul": 0.96, "confidence": 0.95}
        }
    },
    {
        "id": "TICKET-102",
        "name": "Standard Billing Invoice Inquiry",
        "state": (
            "From: accounting@creativepulse.io\n"
            "To: billing@typesafe-demo.com\n"
            "Date: Mon, 22 Sep 2026 08:15:30 GMT\n"
            "Subject: Request for updated VAT invoice for August 2026 (#INV-9921)\n\n"
            "Hi Support Team,\n\n"
            "Could you please re-issue invoice INV-9921 to include our newly registered "
            "European VAT identification number: EU984124982? Our accounting department requires "
            "the updated PDF for month-end tax filing. Everything else with our Team plan is working "
            "splendidly. No rush on this, by end of week is completely fine.\n\n"
            "Warm regards,\n"
            "Sarah Lindqvist\n"
            "Finance Operations, CreativePulse Media"
        ),
        "mock_fallback": {
            "urgency": {"score": 0.15, "confidence": 0.92},
            "sentiment": {"choice": "positive", "confidence": 0.88},
            "churn_risk": {"noul": 0.03, "confidence": 0.96},
            "category": {"choice": "billing", "confidence": 0.99},
            "is_enterprise": {"noul": 0.12, "confidence": 0.89}
        }
    },
    {
        "id": "TICKET-103",
        "name": "Developer Feature Request",
        "state": (
            "From: dev-sarah@cloudstride.dev\n"
            "To: feedback@typesafe-demo.com\n"
            "Date: Mon, 22 Sep 2026 11:20:05 GMT\n"
            "Subject: Feature Suggestion: Webhook event for workspace member invitations\n\n"
            "Hey folks!\n\n"
            "Really impressed with the API response times since the last release. We are currently "
            "building an internal automated employee onboarding script and noticed that while we can "
            "poll the /members endpoint, there is no webhook event triggered when a new workspace "
            "invitation is accepted. Adding an `invitation.accepted` webhook event would save us a ton "
            "of polling overhead.\n\n"
            "Would love to know if this is on your Q4 roadmap!\n\n"
            "Best,\n"
            "Sarah Jenkins\n"
            "Lead Backend Engineer, CloudStride"
        ),
        "mock_fallback": {
            "urgency": {"score": 0.20, "confidence": 0.90},
            "sentiment": {"choice": "positive", "confidence": 0.93},
            "churn_risk": {"noul": 0.05, "confidence": 0.95},
            "category": {"choice": "feature_request", "confidence": 0.97},
            "is_enterprise": {"noul": 0.28, "confidence": 0.85}
        }
    }
]


def evaluate_ticket(state: str, questions: Dict[str, Any], fallback: Dict[str, Any]) -> tuple[Dict[str, Any], float]:
    """
    Call the Jev API to evaluate all questions in parallel.
    Falls back gracefully to calibrated mock values if API key is not configured.
    """
    if not API_KEY:
        time.sleep(0.10)  # Simulate ~100ms evaluation latency
        return fallback, 100.0

    payload = {
        "model": MODEL_NAME,
        "state": state,
        "questions": questions,
    }

    start_time = time.perf_counter()
    try:
        response = requests.post(
            ENDPOINT,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000

        if response.status_code == 200:
            data = response.json()
            # Standardize structure whether returned as {"answers": {...}} or top-level keys
            answers = data.get("answers", data)
            return answers, latency_ms
        else:
            print(f"  [!] API returned status {response.status_code}: {response.text}")
            print("      Falling back to calibrated demo data...")
            return fallback, latency_ms

    except Exception as exc:
        print(f"  [!] Network error: {exc}")
        print("      Falling back to calibrated demo data...")
        return fallback, 100.0


def apply_routing_rules(answers: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply automated business decision rules to Jev's typed classification.
    All business logic remains in Python, completely decoupled from prompts.
    """
    urgency_val = answers.get("urgency", {}).get("score", 0.0)
    sentiment_val = answers.get("sentiment", {}).get("choice", "neutral")
    sentiment_conf = answers.get("sentiment", {}).get("confidence", 1.0)
    churn_prob = answers.get("churn_risk", {}).get("noul", 0.0)
    category_val = answers.get("category", {}).get("choice", "general")
    category_conf = answers.get("category", {}).get("confidence", 1.0)
    is_ent_prob = answers.get("is_enterprise", {}).get("noul", 0.0)

    # 1. Confidence-gated safeguard
    if category_conf < 0.70 or sentiment_conf < 0.65:
        return {
            "tier": "TIER-0: AMBIGUOUS",
            "action": "ROUTE_TO_HUMAN_TRIAGE",
            "reason": f"Low model confidence (category={category_conf:.0%}, sentiment={sentiment_conf:.0%})",
            "priority": "P3",
            "sla_target": "2 hours"
        }

    # 2. Critical Enterprise Emergency
    if is_ent_prob >= 0.70 and urgency_val >= 1.8 and category_val == "technical_outage":
        return {
            "tier": "TIER-1: CRITICAL INCIDENT",
            "action": "PAGE_ONCALL_ENG + ALERT_VP_CUSTOMER_SUCCESS",
            "reason": (
                f"Enterprise account (p={is_ent_prob:.0%}) suffering critical outage "
                f"(urgency={urgency_val:.2f}/2.0, sentiment={sentiment_val})"
            ),
            "priority": "P1-CRITICAL",
            "sla_target": "15 minutes (Enterprise War Room)",
            "retention_flag": churn_prob >= 0.60
        }

    # 3. Churn risk escalation without immediate outage
    if churn_prob >= 0.75:
        return {
            "tier": "TIER-2: RETENTION RISK",
            "action": "ASSIGN_CSM_EXECUTIVE_OUTREACH",
            "reason": f"Elevated churn likelihood detected ({churn_prob:.0%})",
            "priority": "P2-HIGH",
            "sla_target": "1 hour",
            "retention_flag": True
        }

    # 4. Standard Operational Queues
    if category_val == "billing":
        return {
            "tier": "STANDARD QUEUE: BILLING",
            "action": "DISPATCH_TO_INVOICE_SUPPORT",
            "reason": f"Routine billing/tax adjustment (urgency={urgency_val:.2f})",
            "priority": "P4-LOW",
            "sla_target": "24 hours",
            "retention_flag": False
        }
    elif category_val == "feature_request":
        return {
            "tier": "STANDARD QUEUE: PRODUCT FEEDBACK",
            "action": "INGEST_TO_PRODUCTBOARD_BACKLOG",
            "reason": "Feature suggestion from active user; auto-acknowledge with appreciation note",
            "priority": "P4-ROUTINE",
            "sla_target": "48 hours",
            "retention_flag": False
        }
    elif category_val == "account_access":
        return {
            "tier": "STANDARD QUEUE: SECURITY & AUTH",
            "action": "TRIGGER_IDENTITY_VERIFICATION_FLOW",
            "reason": "Account access or credential request",
            "priority": "P2-HIGH",
            "sla_target": "30 minutes",
            "retention_flag": False
        }

    # Default fallback
    return {
        "tier": "GENERAL QUEUE",
        "action": "STANDARD_AGENT_DISPATCH",
        "reason": f"Category: {category_val}",
        "priority": "P3-NORMAL",
        "sla_target": "8 hours",
        "retention_flag": churn_prob >= 0.50
    }


def main():
    print("=" * 75)
    print("   Jev System One: Automated Customer Support Triage Demo")
    print(f"   Provider: {PROVIDER_LABEL} | Endpoint: {ENDPOINT}")
    print("=" * 75)

    if not API_KEY:
        print("\n[NOTE] No TYPESAFE_API_KEY found in environment or .env.")
        print("       Running with calibrated benchmark responses for offline demonstration.\n")

    for scenario in SCENARIOS:
        ticket_id = scenario["id"]
        ticket_name = scenario["name"]
        state_text = scenario["state"]
        fallback = scenario["mock_fallback"]

        print(f"\n>> Processing: [{ticket_id}] {ticket_name}")
        print("-" * 75)
        # Show first 160 characters of incoming email
        first_line = state_text.strip().split("\n")[0]
        subject_line = [line for line in state_text.split("\n") if "Subject:" in line][0]
        print(f"   Header: {first_line}")
        print(f"   {subject_line}")

        # Send state + all 5 questions to Jev in ONE call
        answers, latency_ms = evaluate_ticket(state_text, TRIAGE_QUESTIONS, fallback)

        # Print extracted signals
        print(f"\n   Evaluated in {latency_ms:.1f}ms across 5 typed dimensions:")
        
        urgency = answers.get("urgency", {})
        print(f"     [Score]     urgency        : {urgency.get('score', 0):.2f}/2.0  (confidence: {urgency.get('confidence', 0):.0%})")
        
        sentiment = answers.get("sentiment", {})
        print(f"     [Choice]    sentiment      : {sentiment.get('choice', 'N/A')}  (confidence: {sentiment.get('confidence', 0):.0%})")
        
        churn = answers.get("churn_risk", {})
        print(f"     [Noul]      churn_risk     : {churn.get('noul', 0):.0%} probability TRUE")
        
        category = answers.get("category", {})
        print(f"     [Choice]    category       : {category.get('choice', 'N/A')}  (confidence: {category.get('confidence', 0):.0%})")
        
        is_ent = answers.get("is_enterprise", {})
        print(f"     [Noul]      is_enterprise  : {is_ent.get('noul', 0):.0%} probability TRUE")

        # Execute decision logic
        decision = apply_routing_rules(answers)

        print("\n   Automated Routing Action:")
        print(f"     Tier      : {decision['tier']}")
        print(f"     Action    : {decision['action']}")
        print(f"     SLA Target: {decision['sla_target']} [{decision['priority']}]")
        print(f"     Rationale : {decision['reason']}")
        if decision.get("retention_flag"):
            print("     Retention : [WARNING] Customer Success alert triggered (high churn risk)")

    print("\n" + "=" * 75)
    print("Demo completed successfully.")
    print("=" * 75)


if __name__ == "__main__":
    main()
