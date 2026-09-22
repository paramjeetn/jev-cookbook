"""Legal Contract Clause Risk Scanner using Jev (TypeSafe AI).

This example demonstrates high-speed semantic risk pre-screening of contract
clauses during enterprise procurement, vendor onboarding, and M&A due diligence.

IMPORTANT LEGAL DISCLAIMER:
    Jev is a System One AI classifier, NOT an attorney. Jev flags legal risk
    indicators and classifies contractual terms against company playbooks in ~100ms.
    It does NOT provide legal advice or draft definitive legal opinions.
    Human attorneys must always decide and approve contract redlines.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY")
API_URL = "https://api.typesafe.ai/v1/systemone"

# Three representative contract clause scenarios
CONTRACT_CLAUSES = [
    {
        "id": "CLAUSE-01",
        "title": "Unlimited Liability & Broad Indemnity (Vendor Agreement)",
        "state": (
            "CONTRACT SECTION 12.4: LIMITATION OF LIABILITY & INDEMNIFICATION\n"
            "'NOTWITHSTANDING ANYTHING TO THE CONTRARY IN THIS AGREEMENT OR ANY SOW, "
            "CUSTOMER'S AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THIS AGREEMENT, "
            "WHETHER IN CONTRACT, TORT, OR UNDER ANY OTHER THEORY OF LIABILITY, SHALL BE "
            "COMPLETELY UNCAPPED AND UNLIMITED. FURTHERMORE, CUSTOMER AGREES TO INDEMNIFY, "
            "DEFEND, AND HOLD HARMLESS VENDOR, ITS AFFILIATES, AND THEIR RESPECTIVE OFFICERS, "
            "DIRECTORS, AND EMPLOYEES FROM AND AGAINST ANY AND ALL LOSSES, DAMAGES, PENALTIES, "
            "AND EXPENSES (INCLUDING UNLIMITED LEGAL FEES) ARISING DIRECTLY OR INDIRECTLY FROM "
            "ANY USE OF THE DELIVERABLES, WAIVING ALL STATUTORY EXCLUSIONS OF CONSEQUENTIAL, "
            "PUNITIVE, OR SPECIAL DAMAGES.'"
        ),
    },
    {
        "id": "CLAUSE-02",
        "title": "Standard Net 30 Commercial Payment Terms (Master Services Agreement)",
        "state": (
            "CONTRACT SECTION 4.2: INVOICING AND PAYMENT TERMS\n"
            "'Vendor shall invoice Customer monthly in arrears for Services rendered in accordance "
            "with the applicable Statement of Work. All undisputed invoices shall be due and payable "
            "within thirty (30) days from the date of Customer's receipt of invoice (\"Net 30\"). "
            "Undisputed overdue amounts not paid when due shall accrue interest at the rate of 1.0% "
            "per month or the maximum rate permitted by applicable law, whichever is less. Each "
            "party shall be responsible for its own taxes assessed in connection with this Agreement.'"
        ),
    },
    {
        "id": "CLAUSE-03",
        "title": "Global Restrictive Covenant (Executive Employment Agreement)",
        "state": (
            "EMPLOYMENT AGREEMENT SECTION 8.1: RESTRICTIVE COVENANTS\n"
            "'During the term of Employee's engagement and for a period of twenty-four (24) months "
            "following termination of employment for any reason, Employee shall not directly or "
            "indirectly engage in, perform services for, advise, consult with, or hold an equity "
            "interest in any business, corporation, or entity anywhere in the world that competes, "
            "or plans to compete, with any product, service, or business line developed, contemplated, "
            "or researched by Employer. Employee acknowledges this worldwide geographic scope and "
            "24-month duration are strictly necessary to protect Employer's goodwill.'"
        ),
    },
]

# Definition of Jev questions matching TypeSafe API schema
CONTRACT_QUESTIONS = {
    "risk_level": {
        "type": "score",
        "instructions": "Rate the legal and financial exposure risk introduced by this clause on a 4-level scale.",
        "criteria": [
            "Level 0 - Negligible Risk: Standard benign commercial terms, customary mutual protections, minimal legal or financial exposure.",
            "Level 1 - Low Risk: Minor operational commitments or standard market obligations with balanced mutual terms.",
            "Level 2 - Moderate Risk: Asymmetric responsibilities, elevated liabilities, or non-standard operational covenants requiring business review.",
            "Level 3 - High / Critical Risk: Uncapped liability, broad one-sided indemnification, waiver of consequential damage limits, or severe restrictive covenants.",
        ],
    },
    "clause_type": {
        "type": "choice",
        "instructions": "Identify the primary legal domain and category of this contractual provision.",
        "criteria": {
            "liability": "Limitations of liability, aggregate damage caps, waiver of consequential damages, or financial risk ceilings.",
            "payment": "Invoicing schedules, payment net terms, late payment interest, payment dispute procedures, and taxes.",
            "ip": "Intellectual property ownership, work-made-for-hire assignments, patent/trademark rights, and license grants.",
            "non_compete": "Post-termination restrictive covenants, non-solicitation of clients or employees, and territorial non-compete bounds.",
            "termination": "Termination for breach or convenience, cure notices, post-termination wind-down, and survival obligations.",
            "indemnification": "Obligations to defend, hold harmless, and reimburse third-party legal claims, regulatory fines, or infringement actions.",
        },
    },
    "needs_legal_review": {
        "type": "noul",
        "instructions": "Does this clause warrant mandatory escalation, negotiation, or redlining by corporate legal counsel before signing?",
    },
    "is_standard": {
        "type": "noul",
        "instructions": "Does this provision reflect standard, balanced market boilerplate without aggressive or punitive non-standard deviations?",
    },
}


def query_jev(state: str, questions: dict, api_key: str) -> dict:
    """Send contract clause state and questions to Jev API."""
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


def simulate_jev_response(clause_id: str) -> dict:
    """Calibrated mock responses for offline execution and testing."""
    if clause_id == "CLAUSE-01":  # Unlimited Liability
        return {
            "answers": {
                "risk_level": {
                    "type": "score",
                    "score": 2.95,
                    "confidence": 0.98,
                    "probabilities": {"0": 0.0, "1": 0.01, "2": 0.03, "3": 0.96},
                },
                "clause_type": {
                    "type": "choice",
                    "choice": "liability",
                    "confidence": 0.94,
                    "probabilities": {
                        "liability": 0.94,
                        "payment": 0.00,
                        "ip": 0.00,
                        "non_compete": 0.00,
                        "termination": 0.00,
                        "indemnification": 0.06,
                    },
                },
                "needs_legal_review": {"type": "noul", "noul": 0.99, "confidence": 0.98},
                "is_standard": {"type": "noul", "noul": 0.02, "confidence": 0.97},
            }
        }
    elif clause_id == "CLAUSE-02":  # Standard Payment
        return {
            "answers": {
                "risk_level": {
                    "type": "score",
                    "score": 0.12,
                    "confidence": 0.95,
                    "probabilities": {"0": 0.89, "1": 0.10, "2": 0.01, "3": 0.00},
                },
                "clause_type": {
                    "type": "choice",
                    "choice": "payment",
                    "confidence": 0.99,
                    "probabilities": {
                        "liability": 0.00,
                        "payment": 0.99,
                        "ip": 0.00,
                        "non_compete": 0.00,
                        "termination": 0.01,
                        "indemnification": 0.00,
                    },
                },
                "needs_legal_review": {"type": "noul", "noul": 0.05, "confidence": 0.94},
                "is_standard": {"type": "noul", "noul": 0.96, "confidence": 0.95},
            }
        }
    else:  # Broad Non-compete
        return {
            "answers": {
                "risk_level": {
                    "type": "score",
                    "score": 2.78,
                    "confidence": 0.92,
                    "probabilities": {"0": 0.01, "1": 0.03, "2": 0.14, "3": 0.82},
                },
                "clause_type": {
                    "type": "choice",
                    "choice": "non_compete",
                    "confidence": 0.98,
                    "probabilities": {
                        "liability": 0.00,
                        "payment": 0.00,
                        "ip": 0.01,
                        "non_compete": 0.98,
                        "termination": 0.01,
                        "indemnification": 0.00,
                    },
                },
                "needs_legal_review": {"type": "noul", "noul": 0.97, "confidence": 0.94},
                "is_standard": {"type": "noul", "noul": 0.08, "confidence": 0.93},
            }
        }


def process_clause_decision(clause_meta: dict, answers: dict) -> None:
    """Execute procurement and legal review routing based on calibrated distributions."""
    risk = answers["risk_level"]
    clause_category = answers["clause_type"]
    review = answers["needs_legal_review"]
    standard = answers["is_standard"]

    risk_score = risk["score"]
    category_name = clause_category["choice"]
    cat_conf = clause_category["confidence"]
    review_prob = review["noul"]
    standard_prob = standard["noul"]

    if risk_score >= 2.5:
        risk_tier = "CRITICAL RISK"
    elif risk_score >= 1.5:
        risk_tier = "MODERATE RISK"
    elif risk_score >= 0.7:
        risk_tier = "LOW RISK"
    else:
        risk_tier = "NEGLIGIBLE RISK"

    print("=" * 70)
    print(f"CLAUSE SCANNER: {clause_meta['id']} - {clause_meta['title']}")
    print("=" * 70)
    print(f"Clause Type:           {category_name.upper()} (Confidence: {cat_conf*100:.1f}%)")
    print(f"Assessed Risk Tier:    {risk_tier} (Score: {risk_score:.2f} / 3.00)")
    print(f"Market Standard Term:  {'YES' if standard_prob >= 0.50 else 'NO'} ({standard_prob*100:.1f}%)")
    print(f"Legal Review Needed:   {'YES' if review_prob >= 0.50 else 'NO'} ({review_prob*100:.1f}%)")

    print("\n--- Workflow Routing Decision ---")

    # Workflow 1: High/Critical Risk or Non-Standard terms requiring attorney redlining
    if review_prob >= 0.75 or risk_score >= 2.0:
        print("[ROUTING: ESCALATE TO SENIOR COUNSEL]")
        print(f"  -> High exposure detected in '{category_name.upper()}' provision.")
        print("  -> Blocking contract execution until redline approval.")
        if category_name == "liability":
            print("  -> Playbook Suggestion: Insert mutual 12-month trailing fee liability cap.")
        elif category_name == "non_compete":
            print("  -> Playbook Suggestion: Strike worldwide territory; limit to direct competitors within 25 miles.")

    # Workflow 2: Standard boilerplate (Green track approval)
    elif standard_prob >= 0.80 and risk_score < 1.0:
        print("[ROUTING: EXPEDITED AUTO-APPROVAL]")
        print("  -> Clause conforms to company standard procurement terms.")
        print("  -> Green-pathed for digital signature; bypassed legal triage backlog.")

    # Workflow 3: Moderate business terms
    else:
        print("[ROUTING: BUSINESS UNIT STAKEHOLDER REVIEW]")
        print("  -> Terms non-critical but deviate from baseline. Routed to Finance/Procurement lead.")

    print("\n")


def main():
    print("Initializing Jev Legal Contract Clause Risk Scanner...")
    is_simulated = False

    if not API_KEY:
        print("Note: TYPESAFE_API_KEY environment variable not detected.")
        print("Running in DEMO / SIMULATION mode using calibrated sample distributions.\n")
        is_simulated = True
    else:
        print("Connected to TypeSafe AI API (model: jev-1.13.0).\n")

    for clause in CONTRACT_CLAUSES:
        if is_simulated:
            resp = simulate_jev_response(clause["id"])
        else:
            try:
                raw_resp = query_jev(clause["state"], CONTRACT_QUESTIONS, API_KEY)
                resp = raw_resp.get("answers", raw_resp)
                if "answers" in resp:
                    resp = resp["answers"]
                else:
                    resp = {"answers": resp}
            except Exception as exc:
                print(f"API call failed for {clause['id']}: {exc}")
                print("Falling back to simulated response for display...")
                resp = simulate_jev_response(clause["id"])

        answers = resp["answers"] if "answers" in resp else resp
        process_clause_decision(clause, answers)


if __name__ == "__main__":
    main()
