"""
Real-Time Content Moderation Pipeline with Jev.

This script evaluates user-generated text across four orthogonal trust & safety dimensions
in a single ~100ms round trip:
  1. `is_toxic`: noul (probability of toxic language or personal attacks)
  2. `policy_violation`: choice (safe, spam, harassment, hate_speech, nsfw)
  3. `severity`: score (3 levels rubric: Benign, Moderate, High)
  4. `contains_pii`: noul (probability of private identifiable data)

Actions are governed by a Confidence-Gated policy:
  - Auto-Approve / Publish (Safe + High Confidence)
  - Auto-Quarantine / Reject (Severe Violation + High Confidence)
  - Escalate to Human Moderator Queue (Borderline, Moderate Severity, or Low Confidence)
  - Flag for PII Redaction (Contains sensitive personal data)
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

MODERATION_QUESTIONS = {
    "is_toxic": {
        "type": "noul",
        "instructions": "Does this comment contain toxic remarks, personal attacks, demeaning statements, or workplace harassment?"
    },
    "policy_violation": {
        "type": "choice",
        "instructions": "Which platform policy violation does this content represent?",
        "criteria": {
            "safe": "Content complies with community standards and contains no violations.",
            "spam": "Unsolicited promotional content, commercial scams, phishing, or deceptive links.",
            "harassment": "Targeted hostility, personal insults, bullying, disparagement, or workplace intimidation.",
            "hate_speech": "Attacks, demonization, or incitement directed against protected groups or identity classes.",
            "nsfw": "Explicit sexual content, pornographic material, or graphic violence."
        }
    },
    "severity": {
        "type": "score",
        "instructions": "What is the severity of the policy violation?",
        "criteria": [
            "Level 0: Benign. Content is civil, constructive, or neutral with no violation.",
            "Level 1: Low to Moderate. Borderline hostility, rude phrasing, or policy friction that may warrant a warning.",
            "Level 2: High. Severe violation, malicious harassment, hate speech, or dangerous spam requiring immediate removal."
        ]
    },
    "contains_pii": {
        "type": "noul",
        "instructions": "Does this text expose private personally identifiable information such as phone numbers, home addresses, or social security numbers?"
    }
}


def get_mock_response(content: str) -> Dict[str, Any]:
    """Provides calibrated mock moderation responses for demonstration without API key."""
    c_lower = content.lower()
    if "tutorial" in c_lower:
        return {
            "answers": {
                "is_toxic": {"noul": 0.01, "confidence": 0.99},
                "policy_violation": {"choice": "safe", "confidence": 0.98},
                "severity": {"score": 0.02, "confidence": 0.97},
                "contains_pii": {"noul": 0.01, "confidence": 0.99},
            },
            "eval_time_ms": 94.0
        }
    elif "diversity quota" in c_lower or "incompetent" in c_lower:
        return {
            "answers": {
                "is_toxic": {"noul": 0.94, "confidence": 0.96},
                "policy_violation": {"choice": "harassment", "confidence": 0.93},
                "severity": {"score": 1.88, "confidence": 0.92},
                "contains_pii": {"noul": 0.02, "confidence": 0.98},
            },
            "eval_time_ms": 104.2
        }
    elif "make $5000/day" in c_lower or "crypto" in c_lower:
        return {
            "answers": {
                "is_toxic": {"noul": 0.08, "confidence": 0.91},
                "policy_violation": {"choice": "spam", "confidence": 0.99},
                "severity": {"score": 1.95, "confidence": 0.98},
                "contains_pii": {"noul": 0.01, "confidence": 0.99},
            },
            "eval_time_ms": 96.5
        }
    elif "want to kill myself" in c_lower:
        # Borderline edge case: hyperbolic frustration vs self-harm
        return {
            "answers": {
                "is_toxic": {"noul": 0.48, "confidence": 0.68},
                "policy_violation": {"choice": "safe", "confidence": 0.58},
                "severity": {"score": 0.85, "confidence": 0.62},
                "contains_pii": {"noul": 0.01, "confidence": 0.98},
            },
            "eval_time_ms": 101.8
        }
    return {
        "answers": {
            "is_toxic": {"noul": 0.10, "confidence": 0.90},
            "policy_violation": {"choice": "safe", "confidence": 0.90},
            "severity": {"score": 0.10, "confidence": 0.90},
            "contains_pii": {"noul": 0.01, "confidence": 0.95},
        },
        "eval_time_ms": 100.0
    }


def evaluate_content(content: str) -> Dict[str, Any]:
    """Submits text to the Jev System One moderation endpoint."""
    if not API_KEY:
        time.sleep(0.05)  # Simulate network latency
        return get_mock_response(content)

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "jev-1.13.0",
        "state": f"User content: '{content}'",
        "questions": MODERATION_QUESTIONS
    }

    start = time.perf_counter()
    resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
    elapsed_ms = (time.perf_counter() - start) * 1000
    resp.raise_for_status()

    data = resp.json()
    data["eval_time_ms"] = round(elapsed_ms, 2)
    return data


def apply_moderation_policy(content: str, result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Implements confidence-gated decision logic.
    High confidence extremes are automated; ambiguous gray-zones escalate to humans.
    """
    answers = result.get("answers", {})

    is_toxic = answers.get("is_toxic", {}).get("noul", 0.0)
    violation_data = answers.get("policy_violation", {})
    violation = violation_data.get("choice", "safe")
    violation_conf = violation_data.get("confidence", 0.0)

    severity_data = answers.get("severity", {})
    severity_score = severity_data.get("score", 0.0)
    severity_conf = severity_data.get("confidence", 0.0)

    contains_pii = answers.get("contains_pii", {}).get("noul", 0.0)

    # Decision Matrix
    action = ""
    reason = ""

    # Check for PII first
    if contains_pii >= 0.70:
        action = "REDACT_PII_AND_HOLD"
        reason = f"Detected likely personally identifiable information (pii_prob={contains_pii:.2f})."
    # Auto-Approve: Low toxicity, safe category, high confidence
    elif violation == "safe" and is_toxic < 0.20 and severity_score < 0.50 and violation_conf >= 0.85:
        action = "AUTO_APPROVE"
        reason = f"Content is benign (toxic={is_toxic:.2f}, conf={violation_conf:.2%}). Approved for instant publication."
    # Auto-Reject: High severity and high confidence violation
    elif violation != "safe" and severity_score >= 1.50 and violation_conf >= 0.80:
        action = "AUTO_QUARANTINE"
        reason = f"Confirmed violation: '{violation}' (severity={severity_score:.2f}, conf={violation_conf:.2%}). Quarantined."
    # Human Review: Borderline severity, moderate toxicity, or low confidence
    else:
        action = "HUMAN_REVIEW_QUEUE"
        reason = (f"Ambiguous or borderline content (violation='{violation}', severity={severity_score:.2f}, "
                  f"toxic={is_toxic:.2f}, conf={violation_conf:.2%}). Escrowed for human moderator.")

    return {
        "content": content,
        "action": action,
        "reason": reason,
        "metrics": {
            "is_toxic": round(is_toxic, 3),
            "violation": violation,
            "violation_confidence": round(violation_conf, 3),
            "severity_score": round(severity_score, 3),
            "contains_pii": round(contains_pii, 3),
        },
        "latency_ms": result.get("eval_time_ms", 100)
    }


def main():
    print("=" * 80)
    print("🛡️ Real-Time Content Moderation Pipeline (Jev System One)")
    print("=" * 80)
    if not API_KEY:
        print("💡 [INFO] Running in demonstration mode (set TYPESAFE_API_KEY in .env for live API).\n")

    test_samples = [
        # 1. Normal comment
        "Thanks for sharing this tutorial! It helped me fix the bug in my React build.",
        # 2. Subtle harassment
        "Everyone knows you only got this job because of diversity quotas, you completely lack talent.",
        # 3. Blatant spam
        "🔥 MAKE $5000/DAY WORKING FROM HOME!! Click here bit.ly/easy-crypto-wealth-now GUARANTEED 🔥",
        # 4. Borderline edge case (hyperbolic frustration vs self-harm / policy violation)
        "I honestly hate this software update so much, the new UI makes me want to kill myself."
    ]

    for idx, sample in enumerate(test_samples, 1):
        raw_result = evaluate_content(sample)
        decision = apply_moderation_policy(sample, raw_result)
        m = decision["metrics"]

        print(f"[{idx}] Text: \"{sample}\"")
        print(f"    📊 Jev Metrics : toxic={m['is_toxic']} | violation={m['violation']} (conf: {m['violation_confidence']:.0%}) | "
              f"severity={m['severity_score']}/2.0 | pii={m['contains_pii']} (~{decision['latency_ms']}ms)")
        print(f"    🎯 Gate Action : {decision['action']}")
        print(f"    📝 Decision Log: {decision['reason']}")
        print("-" * 80)


if __name__ == "__main__":
    main()
