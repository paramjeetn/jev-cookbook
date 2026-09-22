"""Real-Time E-Commerce Fraud Detection using Jev (TypeSafe AI).

This example demonstrates sub-100ms semantic fraud evaluation during checkout.
Because Jev executes within ~100ms, fraud scoring happens synchronously before
the payment gateway authorization timeout (e.g., Stripe/Adyen 2-second deadline),
avoiding cart abandonment and chargeback liabilities.
"""

import os
import sys
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY")
API_URL = "https://api.typesafe.ai/v1/systemone"

# Three representative checkout scenarios
TRANSACTION_SCENARIOS = [
    {
        "id": "TX-7011",
        "name": "Normal Repeat Customer Purchase (Low Risk)",
        "state": (
            "TRANSACTION CHECKOUT TELEMETRY\n"
            "Order ID: ORD-20260922-7011\n"
            "Account: 'susan.k@example.com' (Account age: 4 years, 42 completed orders, 0 chargebacks)\n"
            "Cart Items: 1x Brooks Ghost Running Shoes ($140.00), 2x Athletic Socks ($24.00)\n"
            "Total Amount: $164.00 USD\n"
            "Payment Method: Saved Visa card ending in 8832 (CVV matched, AVS match full)\n"
            "Billing Address: 1404 Oak Ridge Dr, Austin, TX 78704\n"
            "Shipping Address: 1404 Oak Ridge Dr, Austin, TX 78704 (Matches billing)\n"
            "Network Telemetry: IP 72.181.99.12 (Residential AT&T Internet, Austin, TX)\n"
            "Browser Telemetry: Safari 17.1 on iPhone 14 Pro, Trusted device fingerprint matched\n"
            "Order Timestamp: 14:15:02 UTC (2:15 PM local). Velocity: 1st order in 30 days."
        ),
    },
    {
        "id": "TX-7012",
        "name": "Suspicious Bulk Digital Gift Cards at 3am (High Risk / Syndicate)",
        "state": (
            "TRANSACTION CHECKOUT TELEMETRY\n"
            "Order ID: ORD-20260922-7012\n"
            "Account: 'crypto_wizard99@tempmail.ninja' (Account age: 14 minutes, 0 previous orders)\n"
            "Cart Items: 5x $500 Apple E-Gift Cards (Digital Instant Delivery)\n"
            "Total Amount: $2,500.00 USD\n"
            "Payment Method: Visa ending in 4118 (First card entry attempt failed: invalid CVV. "
            "Second attempt succeeded. AVS: Postal code mismatch).\n"
            "Billing Address: 742 Evergreen Terrace, Miami, FL 33101\n"
            "Delivery Email: burner-delivery-08@tempmail.ninja\n"
            "Network Telemetry: IP 102.89.33.15 (AS37148 - Datacenter hosting proxy, Lagos, Nigeria).\n"
            "Browser Telemetry: Headless Chrome / Linux x86_64, WebGL fingerprint mismatch, Canvas noise injection detected.\n"
            "Order Timestamp: 03:28:14 UTC (3:28 AM local recipient time). Velocity: 3rd checkout attempt in 4 minutes."
        ),
    },
    {
        "id": "TX-7013",
        "name": "High-Value Purchase While Traveling (Borderline Case)",
        "state": (
            "TRANSACTION CHECKOUT TELEMETRY\n"
            "Order ID: ORD-20260922-7013\n"
            "Account: 'david.ross@corporate.org' (Account age: 2.5 years, 18 previous orders, typical order $110)\n"
            "Cart Items: 1x Razer Blade Gaming Laptop 16-inch ($2,450.00)\n"
            "Total Amount: $2,450.00 USD\n"
            "Payment Method: Mastercard ending in 1904 (CVV match, AVS Zip match)\n"
            "Billing Address: 450 N Michigan Ave, Chicago, IL 60611\n"
            "Shipping Address: 1820 16th St #402, Denver, CO 80202 (Airbnb short-term rental destination)\n"
            "Network Telemetry: IP 67.135.24.8 (Commercial Hotel Wi-Fi, Denver, CO)\n"
            "Browser Telemetry: Chrome on MacOS, Known laptop device fingerprint, valid authenticated session cookie\n"
            "Order Timestamp: 13:45:10 UTC (1:45 PM local). Velocity: Normal. Cart value is 20x historical average."
        ),
    },
]

# Definition of Jev questions matching TypeSafe API schema
FRAUD_QUESTIONS = {
    "is_fraudulent": {
        "type": "noul",
        "instructions": "Does this transaction exhibit high-confidence markers of unauthorized, fraudulent, or syndicate activity?",
    },
    "risk_tier": {
        "type": "choice",
        "instructions": "Assign the transaction to an operational fraud mitigation risk tier.",
        "criteria": {
            "low": "Transaction exhibits legitimate consumer patterns; approve automatically without checkout friction.",
            "medium": "Borderline risk signals or unusual transaction context; require step-up authentication (e.g. 3D Secure / SMS OTP).",
            "high": "High fraud probability or elevated risk indicators; hold order fulfillment and dispatch to human fraud review queue.",
            "block": "Severe fraud markers, proxy evasion, stolen identity patterns, or mass gift card liquidation; decline payment immediately.",
        },
    },
    "anomaly_score": {
        "type": "score",
        "instructions": "Score the severity of behavioral and contextual anomalies relative to baseline consumer activity on a 3-level scale.",
        "criteria": [
            "Nominal: Transaction attributes, velocity, and device footprint align with normal consumer patterns and account history.",
            "Elevated: Moderate behavioral or contextual deviation (e.g. unfamiliar IP geolocation, elevated cart value, new device fingerprint).",
            "Severe: Extreme behavioral outlier exhibiting high-risk velocity, high-liquidity digital gift cards, proxy evasion, or mismatched authentication.",
        ],
    },
    "needs_manual_review": {
        "type": "noul",
        "instructions": "Does this transaction warrant placing an order hold for manual inspection by a risk analyst?",
    },
}


def query_jev(state: str, questions: dict, api_key: str) -> dict:
    """Send transaction telemetry to Jev API and record latency."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "jev-1.13.0",
        "state": state,
        "questions": questions,
    }

    t0 = time.perf_counter()
    response = requests.post(API_URL, headers=headers, json=payload, timeout=5)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    response.raise_for_status()
    data = response.json()
    data["_elapsed_ms"] = elapsed_ms
    return data


def simulate_jev_response(tx_id: str) -> dict:
    """Calibrated mock responses for offline execution and testing."""
    if tx_id == "TX-7011":  # Normal repeat customer
        return {
            "answers": {
                "is_fraudulent": {"type": "noul", "noul": 0.01, "confidence": 0.99},
                "risk_tier": {
                    "type": "choice",
                    "choice": "low",
                    "confidence": 0.98,
                    "probabilities": {"low": 0.98, "medium": 0.02, "high": 0.00, "block": 0.00},
                },
                "anomaly_score": {
                    "type": "score",
                    "score": 0.04,
                    "confidence": 0.98,
                    "probabilities": {"0": 0.96, "1": 0.04, "2": 0.00},
                },
                "needs_manual_review": {"type": "noul", "noul": 0.02, "confidence": 0.99},
            },
            "_elapsed_ms": 94.2,
        }
    elif tx_id == "TX-7012":  # Bulk gift cards at 3am
        return {
            "answers": {
                "is_fraudulent": {"type": "noul", "noul": 0.98, "confidence": 0.97},
                "risk_tier": {
                    "type": "choice",
                    "choice": "block",
                    "confidence": 0.96,
                    "probabilities": {"low": 0.00, "medium": 0.01, "high": 0.03, "block": 0.96},
                },
                "anomaly_score": {
                    "type": "score",
                    "score": 1.96,
                    "confidence": 0.96,
                    "probabilities": {"0": 0.00, "1": 0.04, "2": 0.96},
                },
                "needs_manual_review": {"type": "noul", "noul": 0.05, "confidence": 0.95},
            },
            "_elapsed_ms": 98.6,
        }
    else:  # Borderline traveling customer
        return {
            "answers": {
                "is_fraudulent": {"type": "noul", "noul": 0.36, "confidence": 0.78},
                "risk_tier": {
                    "type": "choice",
                    "choice": "medium",
                    "confidence": 0.81,
                    "probabilities": {"low": 0.12, "medium": 0.81, "high": 0.07, "block": 0.00},
                },
                "anomaly_score": {
                    "type": "score",
                    "score": 1.18,
                    "confidence": 0.84,
                    "probabilities": {"0": 0.10, "1": 0.62, "2": 0.28},
                },
                "needs_manual_review": {"type": "noul", "noul": 0.72, "confidence": 0.86},
            },
            "_elapsed_ms": 102.1,
        }


def execute_fraud_decision(scenario: dict, resp: dict) -> None:
    """Execute real-time inline payment authorization logic."""
    answers = resp["answers"]
    elapsed_ms = resp.get("_elapsed_ms", 100.0)

    fraud_prob = answers["is_fraudulent"]["noul"]
    tier = answers["risk_tier"]["choice"]
    tier_conf = answers["risk_tier"]["confidence"]
    anomaly = answers["anomaly_score"]["score"]
    manual_review_prob = answers["needs_manual_review"]["noul"]

    print("=" * 72)
    print(f"CHECKOUT FRAUD EVALUATION: {scenario['id']} - {scenario['name']}")
    print(f"Gateway Decision Latency:  {elapsed_ms:.1f} ms (Deadline: 2,000 ms)")
    print("=" * 72)
    print(f"Fraud Probability:         {fraud_prob*100:.1f}%")
    print(f"Assigned Risk Tier:        {tier.upper()} (Confidence: {tier_conf*100:.1f}%)")
    print(f"Anomaly Score (0-2 scale): {anomaly:.2f}")
    print(f"Manual Review Probability: {manual_review_prob*100:.1f}%")

    print("\n--- Inline Gateway Action ---")

    # Tier 1: Auto-block syndicate / stolen card fraud
    if tier == "block" or fraud_prob >= 0.85:
        print("[GATEWAY RESPONSE: DECLINED / BLOCKED]")
        print("  -> Immediate transaction rejection (HTTP 402 Payment Declined).")
        print("  -> Blacklisted originating IP subnet and browser canvas fingerprint.")
        print("  -> Card issuer alerted: Stolen Card / Account Takeover pattern.")

    # Tier 2: Adaptive step-up authentication (Friction inserted only when uncertain)
    elif tier == "medium" or (0.30 <= fraud_prob < 0.85):
        print("[GATEWAY RESPONSE: STEP-UP AUTHENTICATION (3D SECURE 2.0)]")
        print("  -> Borderline risk / travel anomaly detected.")
        print("  -> Dispatched frictionless biometric / SMS-OTP challenge to cardholder's mobile.")
        if manual_review_prob >= 0.60:
            print("  -> Fulfillment status set to HOLD pending 3DS confirmation.")

    # Tier 3: High risk manual review
    elif tier == "high" or manual_review_prob >= 0.75:
        print("[GATEWAY RESPONSE: AUTHORIZED WITH ORDER HOLD]")
        print("  -> Payment pre-authorized; warehouse pick list hold engaged.")
        print("  -> Routed to Tier-2 Fraud Analyst dashboard with highlighted signals.")

    # Tier 4: Frictionless approval for trusted legitimate transactions
    else:
        print("[GATEWAY RESPONSE: INSTANT AUTHORIZATION APPROVED]")
        print("  -> Zero checkout friction. Payment captured successfully.")
        print("  -> Order immediately dispatched to fulfillment pipeline.")

    print("\n")


def main():
    print("Initializing Jev Real-Time E-Commerce Fraud Decision Engine...")
    is_simulated = False

    if not API_KEY:
        print("Note: TYPESAFE_API_KEY environment variable not detected.")
        print("Running in DEMO / SIMULATION mode using calibrated sample distributions.\n")
        is_simulated = True
    else:
        print("Connected to TypeSafe AI API (model: jev-1.13.0).\n")

    for scenario in TRANSACTION_SCENARIOS:
        if is_simulated:
            resp = simulate_jev_response(scenario["id"])
        else:
            try:
                resp = query_jev(scenario["state"], FRAUD_QUESTIONS, API_KEY)
                if "answers" not in resp:
                    resp = {"answers": resp, "_elapsed_ms": resp.get("_elapsed_ms", 100.0)}
            except Exception as exc:
                print(f"API call failed for {scenario['id']}: {exc}")
                print("Falling back to simulated response for display...")
                resp = simulate_jev_response(scenario["id"])

        execute_fraud_decision(scenario, resp)


if __name__ == "__main__":
    main()
