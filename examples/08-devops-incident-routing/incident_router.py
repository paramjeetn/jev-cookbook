"""DevOps Incident Alert Routing using Jev (TypeSafe AI).

This example demonstrates how to evaluate incoming telemetry alerts and
automatically route them to the correct engineering team with calibrated severity
and paging decisions in ~100ms.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY")
API_URL = "https://api.typesafe.ai/v1/systemone"

# Three production alert scenarios
INCIDENT_SCENARIOS = [
    {
        "id": "ALT-9021",
        "name": "Database Connection Pool Exhaustion (Aurora Postgres)",
        "state": (
            "CRITICAL INCIDENT ALERT: production-db-primary\n"
            "Timestamp: 2026-09-22T03:15:22Z\n"
            "Source: Datadog APM & AWS CloudWatch\n"
            "Service: pg-cluster-primary.us-east-1 (Aurora Postgres 15.4)\n"
            "Metric Alarm: DatabaseConnectionPoolExhausted\n"
            "Details: Active connections spiked to 498/500 (99.6% capacity). Log snippet: "
            "'FATAL: remaining connection slots are reserved for non-replication superuser connections'.\n"
            "Impact: Upstream service 'checkout-api' reporting 38.4% HTTP 500 failure rate. "
            "P99 latency rose from 120ms to 14,850ms. 45 container pods in CrashLoopBackOff due to "
            "failed database health checks.\n"
            "Blast Radius: Global checkout pipeline blocked; customer transactions failing at gateway step."
        ),
    },
    {
        "id": "ALT-9022",
        "name": "CSS Rendering Glitch on Mobile Safari (UI Layout Overflow)",
        "state": (
            "Sentry Bug Report [web-client-v3]\n"
            "Timestamp: 2026-09-22T10:42:01Z\n"
            "Source: Sentry Client Error Tracking\n"
            "Service: customer-storefront-spa (v2.14.8)\n"
            "Description: iOS Safari 17.2 flex-wrap CSS layout anomaly on '/checkout/summary' view. "
            "The sticky 'Complete Order' button renders 40px below the viewport fold when browser "
            "bottom address bar is expanded on iPhone 15 Pro.\n"
            "Backend Health: All REST endpoints returning 200 OK. No server exceptions.\n"
            "Business Impact: Non-fatal UI defect. Users can still scroll to tap the button, "
            "but checkout completion rate dipped 2.3% on iOS Safari over the last 2 hours."
        ),
    },
    {
        "id": "ALT-9023",
        "name": "Suspicious Login from Unusual Geography (Admin Account Takeover Risk)",
        "state": (
            "SECURITY SENTINEL ALERT: Anomalous Geo-Velocity\n"
            "Timestamp: 2026-09-22T03:38:15Z\n"
            "Source: Okta Identity & CloudTrail Threat Detection\n"
            "Account: 'alice.vance@megacorp.internal' (Role: Production DB Admin)\n"
            "Event Chain: Successful SSO login from Dublin, Ireland (IPv4 185.120.44.12) at 03:14 UTC. "
            "Subsequent login attempt 22 minutes later from St. Petersburg, Russia (IPv4 95.173.136.2) "
            "bypassing WebAuthn hardware token via legacy session token reuse.\n"
            "Target Resource: AWS Secrets Manager 'prod/db/master-credentials' decrypted via CLI.\n"
            "Threat Assessment: High probability of stolen bearer token or corporate device compromise."
        ),
    },
]

# Definition of Jev questions matching TypeSafe API schema
INCIDENT_QUESTIONS = {
    "severity": {
        "type": "score",
        "instructions": "Determine the operational incident severity tier (P4 low to P1 critical).",
        "criteria": [
            "P4 - Low: Cosmetic issue, minor internal inconvenience, or non-blocking bug with negligible customer impact.",
            "P3 - Medium: Degraded non-critical service or partial internal tooling outage with an immediate workaround available.",
            "P2 - High: Severe degradation of major customer-facing features, high latency, or partial production outage affecting multiple tenants.",
            "P1 - Critical: Complete system outage, catastrophic core workflow failure, active data loss, or severe security breach requiring emergency bridge.",
        ],
    },
    "team": {
        "type": "choice",
        "instructions": "Select the engineering domain team that owns primary resolution of this alert.",
        "criteria": {
            "backend": "Application business logic, microservice APIs, payment processing workflows, and backend service code.",
            "frontend": "Web application client UI, mobile apps, styling/CSS layout, JavaScript bundles, and browser compatibility.",
            "security": "Unauthorized access, suspicious auth geography, credential stuffing, vulnerability exploit, or data breach.",
            "infrastructure": "Cloud platforms (AWS/GCP), Kubernetes clusters, database engines/connection pools, VPC networking, and bare metal.",
            "data": "Data warehouse pipelines, ETL jobs, streaming Kafka topics, and analytical reporting models.",
        },
    },
    "is_customer_facing": {
        "type": "noul",
        "instructions": "Does this incident directly impact external customer transactions, client UI availability, or public user experience?",
    },
    "needs_page": {
        "type": "noul",
        "instructions": "Does this incident meet the threshold to immediately page on-call engineering staff outside business hours?",
    },
}


def query_jev(state: str, questions: dict, api_key: str) -> dict:
    """Send alert state and questions to Jev API."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "jev-1.13.0",
        "state": state,
        "questions": questions,
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()


def simulate_jev_response(incident_id: str) -> dict:
    """Calibrated mock responses for offline execution and testing."""
    if incident_id == "ALT-9021":  # Database Pool
        return {
            "answers": {
                "severity": {
                    "type": "score",
                    "score": 2.91,
                    "confidence": 0.97,
                    "probabilities": {"0": 0.0, "1": 0.01, "2": 0.07, "3": 0.92},
                },
                "team": {
                    "type": "choice",
                    "choice": "infrastructure",
                    "confidence": 0.94,
                    "probabilities": {
                        "backend": 0.04,
                        "frontend": 0.0,
                        "security": 0.01,
                        "infrastructure": 0.94,
                        "data": 0.01,
                    },
                },
                "is_customer_facing": {"type": "noul", "noul": 0.98, "confidence": 0.99},
                "needs_page": {"type": "noul", "noul": 0.99, "confidence": 0.98},
            }
        }
    elif incident_id == "ALT-9022":  # CSS Bug
        return {
            "answers": {
                "severity": {
                    "type": "score",
                    "score": 0.45,
                    "confidence": 0.93,
                    "probabilities": {"0": 0.60, "1": 0.36, "2": 0.04, "3": 0.0},
                },
                "team": {
                    "type": "choice",
                    "choice": "frontend",
                    "confidence": 0.98,
                    "probabilities": {
                        "backend": 0.01,
                        "frontend": 0.98,
                        "security": 0.0,
                        "infrastructure": 0.01,
                        "data": 0.0,
                    },
                },
                "is_customer_facing": {"type": "noul", "noul": 0.96, "confidence": 0.95},
                "needs_page": {"type": "noul", "noul": 0.04, "confidence": 0.97},
            }
        }
    else:  # Suspicious Auth
        return {
            "answers": {
                "severity": {
                    "type": "score",
                    "score": 2.76,
                    "confidence": 0.95,
                    "probabilities": {"0": 0.0, "1": 0.02, "2": 0.20, "3": 0.78},
                },
                "team": {
                    "type": "choice",
                    "choice": "security",
                    "confidence": 0.99,
                    "probabilities": {
                        "backend": 0.0,
                        "frontend": 0.0,
                        "security": 0.99,
                        "infrastructure": 0.01,
                        "data": 0.0,
                    },
                },
                "is_customer_facing": {"type": "noul", "noul": 0.06, "confidence": 0.92},
                "needs_page": {"type": "noul", "noul": 0.96, "confidence": 0.95},
            }
        }


def route_incident(scenario: dict, answers: dict) -> None:
    """Apply deterministic operational routing rules on Jev outputs."""
    severity = answers["severity"]
    team = answers["team"]
    customer_facing = answers["is_customer_facing"]
    paging = answers["needs_page"]

    score_val = severity["score"]
    assigned_team = team["choice"]
    team_conf = team["confidence"]
    is_cust = customer_facing["noul"]
    page_prob = paging["noul"]

    # Map float score (0 to 3) to standard P-tier
    if score_val >= 2.5:
        tier_label = "P1 - CRITICAL"
    elif score_val >= 1.5:
        tier_label = "P2 - HIGH"
    elif score_val >= 0.7:
        tier_label = "P3 - MEDIUM"
    else:
        tier_label = "P4 - LOW"

    print("=" * 70)
    print(f"INCIDENT CLASSIFICATION: {scenario['id']} - {scenario['name']}")
    print("=" * 70)
    print(f"Calculated Severity:   {tier_label} (Score: {score_val:.2f})")
    print(f"Assigned Team:         {assigned_team.upper()} (Confidence: {team_conf*100:.1f}%)")
    print(f"Customer Facing:       {'YES' if is_cust >= 0.50 else 'NO'} ({is_cust*100:.1f}%)")
    print(f"Page Probability:      {page_prob*100:.1f}%")

    print("\n--- Dispatch & Automated Remediation ---")

    # High-urgency pager dispatch
    if page_prob >= 0.80 or score_val >= 2.5:
        print(f"[DISPATCH: PAGERDUTY HIGH-SEVERITY] Paging {assigned_team.upper()} primary on-call.")
        print(f"  -> Generated Incident Room: #inc-20260922-{scenario['id'].lower()}")
        print(f"  -> Automated Zoom bridge provisioned and broadcast to statuspage.")
    else:
        print(f"[DISPATCH: NON-PAGING TICKET] Queued to #{assigned_team}-triage Slack channel.")
        print(f"  -> Logged Jira ticket with SLA: 8 business hours. No on-call wake-up.")

    # Domain-specific automated safety responses
    if assigned_team == "security" and page_prob > 0.85:
        print("[AUTOMATION: ACTIVE DEFENSE] Revoked active Okta sessions for affected admin account.")
        print("  -> Rotated AWS STS temporary credentials. Ingress IP quarantined in Cloudflare.")

    elif assigned_team == "infrastructure" and score_val >= 2.5:
        print("[AUTOMATION: INFRA RESILIENCE] Initiated horizontal pod autoscaler step-up.")
        print("  -> Sent kill signal to idle backend connection pools to release DB slots.")

    elif assigned_team == "frontend":
        print("[AUTOMATION: BUG TRACKER] Created UI sprint defect ticket in Linear with device context.")

    print("\n")


def main():
    print("Initializing Jev DevOps Incident Router...")
    is_simulated = False

    if not API_KEY:
        print("Note: TYPESAFE_API_KEY environment variable not detected.")
        print("Running in DEMO / SIMULATION mode using calibrated sample distributions.\n")
        is_simulated = True
    else:
        print("Connected to TypeSafe AI API (model: jev-1.13.0).\n")

    for scenario in INCIDENT_SCENARIOS:
        if is_simulated:
            resp = simulate_jev_response(scenario["id"])
        else:
            try:
                raw_resp = query_jev(scenario["state"], INCIDENT_QUESTIONS, API_KEY)
                resp = raw_resp.get("answers", raw_resp)
                if "answers" in resp:
                    resp = resp["answers"]
                else:
                    resp = {"answers": resp}
            except Exception as exc:
                print(f"API call failed for {scenario['id']}: {exc}")
                print("Falling back to simulated response for display...")
                resp = simulate_jev_response(scenario["id"])

        answers = resp["answers"] if "answers" in resp else resp
        route_incident(scenario, answers)


if __name__ == "__main__":
    main()
