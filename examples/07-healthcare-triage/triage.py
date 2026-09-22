"""Healthcare Patient Intake Triage using Jev (TypeSafe AI).

This example demonstrates how to perform high-speed, calibrated patient intake
triage without clinical text generation.

IMPORTANT MEDICAL DISCLAIMER:
    Jev is a System One AI classifier, NOT a diagnostic engine. It classifies
    urgency, routes patients to appropriate care venues (ESI-style triage),
    and flags high-risk signals. It does NOT generate clinical diagnoses or
    treatment plans. A qualified clinician must always oversee medical decisions.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("TYPESAFE_API_KEY") or os.getenv("JEV_API_KEY")
API_URL = "https://api.typesafe.ai/v1/systemone"

# Three clinical intake scenarios
PATIENT_SCENARIOS = [
    {
        "id": "PT-10492",
        "name": "Chest Pain & Dyspnea (Suspected Acute Coronary Syndrome)",
        "state": (
            "PATIENT INTAKE SUMMARY\n"
            "Patient: John Doe | Age: 58 | Sex: Male\n"
            "Arrival Mode: Walk-in accompanied by spouse\n"
            "Chief Complaint: Severe retrosternal chest tightness radiating to the left "
            "shoulder and jaw, duration 45 minutes, sudden onset at rest. Patient describes "
            "feeling like an 'iron weight' on chest. Associated with marked dyspnea, diaphoresis "
            "(profuse cold sweating), dizziness, and mild nausea.\n"
            "Vitals: BP 172/104 mmHg, HR 112 bpm (irregular), RR 26/min, SpO2 91% on room air, Temp 98.6 F.\n"
            "Medical History: Hyperlipidemia, Type 2 Diabetes Mellitus, 30 pack-year cigarette smoking history.\n"
            "Current Medications: Atorvastatin 40mg, Metformin 1000mg BID.\n"
            "Known Allergies: Penicillin (hives).\n"
            "Clinical Presentation: Patient appears in acute distress, pale, clutching anterior chest, "
            "speech limited to two-word phrases due to breathlessness."
        ),
    },
    {
        "id": "PT-10493",
        "name": "Mild Headache for 2 Days (Non-emergent Tension Headache)",
        "state": (
            "PATIENT INTAKE SUMMARY\n"
            "Patient: Emily Chen | Age: 34 | Sex: Female\n"
            "Arrival Mode: Outpatient telehealth check-in\n"
            "Chief Complaint: Dull, band-like headache across forehead and temples for the past 48 hours. "
            "Rated 3/10 on pain scale. Denies fever, stiff neck, visual changes, aura, or focal weakness. "
            "Symptoms improve mildly with hydration and OTC acetaminophen.\n"
            "Vitals: BP 118/76 mmHg, HR 72 bpm, RR 14/min, SpO2 99% on room air, Temp 98.2 F.\n"
            "Medical History: None significant.\n"
            "Current Medications: Multivitamin daily, occasional acetaminophen 500mg.\n"
            "Known Allergies: NKDA.\n"
            "Clinical Presentation: Patient is alert, oriented x4, in no acute distress. Speaks in full sentences."
        ),
    },
    {
        "id": "PT-10494",
        "name": "Twisted Ankle While Jogging (Acute Musculoskeletal Sprain)",
        "state": (
            "PATIENT INTAKE SUMMARY\n"
            "Patient: Marcus Miller | Age: 24 | Sex: Male\n"
            "Arrival Mode: Walk-in with crutch assistance\n"
            "Chief Complaint: Inversion injury to right lateral ankle while trail running 2 hours ago. "
            "Heard a mild pop, followed by localized lateral swelling and bruising. Pain rated 6/10 on "
            "weight bearing; able to take 4 steps with severe limp. Skin intact, distal pulses palpable, "
            "no deformity or neurovascular deficit.\n"
            "Vitals: BP 124/80 mmHg, HR 82 bpm, RR 16/min, SpO2 99% on room air, Temp 98.4 F.\n"
            "Medical History: Active athlete, no previous fractures.\n"
            "Current Medications: Ibuprofen 400mg taken 1 hour ago.\n"
            "Known Allergies: NKDA.\n"
            "Clinical Presentation: Alert, cooperative, discomfort localized strictly to right lateral malleolus."
        ),
    },
]

# Definition of Jev questions matching TypeSafe API schema
TRIAGE_QUESTIONS = {
    "urgency": {
        "type": "score",
        "instructions": "Classify the clinical urgency of this patient intake according to standard triage acuity rubrics.",
        "criteria": [
            "Routine: Patient is stable with non-urgent symptoms; safe to await scheduled outpatient visit.",
            "Semi-urgent: Mild to moderate symptoms requiring non-emergent medical consultation within 24 to 48 hours.",
            "Urgent: Acute illness or injury with moderate distress requiring same-day physician evaluation; currently hemodynamically stable.",
            "Emergency: Critical, potentially life-threatening emergency requiring immediate resuscitation, telemetry, and advanced medical stabilization.",
        ],
    },
    "care_level": {
        "type": "choice",
        "instructions": "Select the most appropriate medical care venue or triage disposition for this patient.",
        "criteria": {
            "primary_care": "Standard outpatient clinic or primary care physician appointment within 3-7 days.",
            "urgent_care": "Same-day walk-in urgent care facility for minor trauma, sprains, or uncomplicated infections.",
            "emergency_room": "Hospital Emergency Department equipped with resuscitation bays, cardiac catheterization, and emergency imaging.",
            "call_911": "Immediate emergency medical services (EMS/911) dispatch with paramedic monitoring and pre-hospital cardiac intervention.",
        },
    },
    "follow_up_needed": {
        "type": "noul",
        "instructions": "Will this clinical condition require mandatory structured follow-up care and monitoring after initial triage?",
    },
    "mental_health_flag": {
        "type": "noul",
        "instructions": "Does this patient intake indicate an acute psychological crisis, active self-harm ideation, or severe psychiatric distress?",
    },
}


def query_jev(state: str, questions: dict, api_key: str) -> dict:
    """Send intake state and questions to Jev API."""
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


def simulate_jev_response(patient_id: str) -> dict:
    """Provide calibrated mock response if running without live API key."""
    if patient_id == "PT-10492":  # Chest pain
        return {
            "answers": {
                "urgency": {
                    "type": "score",
                    "score": 2.94,
                    "confidence": 0.98,
                    "probabilities": {"0": 0.0, "1": 0.01, "2": 0.04, "3": 0.95},
                },
                "care_level": {
                    "type": "choice",
                    "choice": "emergency_room",
                    "confidence": 0.96,
                    "probabilities": {
                        "primary_care": 0.00,
                        "urgent_care": 0.01,
                        "emergency_room": 0.96,
                        "call_911": 0.03,
                    },
                },
                "follow_up_needed": {"type": "noul", "noul": 0.99, "confidence": 0.97},
                "mental_health_flag": {"type": "noul", "noul": 0.02, "confidence": 0.99},
            }
        }
    elif patient_id == "PT-10493":  # Mild headache
        return {
            "answers": {
                "urgency": {
                    "type": "score",
                    "score": 0.15,
                    "confidence": 0.94,
                    "probabilities": {"0": 0.86, "1": 0.13, "2": 0.01, "3": 0.0},
                },
                "care_level": {
                    "type": "choice",
                    "choice": "primary_care",
                    "confidence": 0.93,
                    "probabilities": {
                        "primary_care": 0.93,
                        "urgent_care": 0.06,
                        "emergency_room": 0.01,
                        "call_911": 0.00,
                    },
                },
                "follow_up_needed": {"type": "noul", "noul": 0.28, "confidence": 0.89},
                "mental_health_flag": {"type": "noul", "noul": 0.01, "confidence": 0.99},
            }
        }
    else:  # Twisted ankle
        return {
            "answers": {
                "urgency": {
                    "type": "score",
                    "score": 1.88,
                    "confidence": 0.91,
                    "probabilities": {"0": 0.02, "1": 0.12, "2": 0.84, "3": 0.02},
                },
                "care_level": {
                    "type": "choice",
                    "choice": "urgent_care",
                    "confidence": 0.92,
                    "probabilities": {
                        "primary_care": 0.03,
                        "urgent_care": 0.92,
                        "emergency_room": 0.05,
                        "call_911": 0.00,
                    },
                },
                "follow_up_needed": {"type": "noul", "noul": 0.82, "confidence": 0.91},
                "mental_health_flag": {"type": "noul", "noul": 0.01, "confidence": 0.99},
            }
        }


def execute_triage_decision(patient_meta: dict, answers: dict) -> None:
    """Execute operational clinical routing logic based on calibrated distributions."""
    urgency = answers["urgency"]
    care = answers["care_level"]
    follow_up = answers["follow_up_needed"]
    mental_health = answers["mental_health_flag"]

    urgency_score = urgency["score"]
    chosen_venue = care["choice"]
    venue_conf = care["confidence"]
    follow_up_prob = follow_up["noul"]
    mental_risk_prob = mental_health["noul"]

    print("=" * 70)
    print(f"PATIENT INTAKE EVALUATION: {patient_meta['id']} - {patient_meta['name']}")
    print("=" * 70)
    print(f"Urgency Score (0-3 scale): {urgency_score:.2f} (Confidence: {urgency['confidence']*100:.1f}%)")
    print(f"Care Disposition:          {chosen_venue.upper()} (Confidence: {venue_conf*100:.1f}%)")
    print(f"Follow-up Probability:     {follow_up_prob*100:.1f}%")
    print(f"Mental Health Alert Flag:  {mental_risk_prob*100:.1f}%")

    print("\n--- Operational Action Taken ---")

    # Guardrail 1: Mental Health Escalation
    if mental_risk_prob > 0.60:
        print("[ACTION: CRISIS ESCALATION] Acute psychiatric indicator detected.")
        print("  -> Initiating immediate warm handoff to on-call Crisis Specialist.")
        print("  -> Do not leave patient unmonitored.")

    # Guardrail 2: Confidence gating on automated routing
    if venue_conf < 0.70:
        print("[ACTION: HUMAN TRIAGE OVERRIDE] Jev confidence below threshold (70%).")
        print("  -> Escalated to Triage Registered Nurse for manual assessment.")
        return

    # Deterministic Care Pathway Routing
    if chosen_venue in ("emergency_room", "call_911") or urgency_score >= 2.5:
        print("[ACTION: RED PATHWAY - IMMEDIATE EMERGENCY]")
        print("  -> Dispatched Code Triage alert to Emergency Resuscitation Bay.")
        print("  -> Prep: 12-lead ECG, continuous telemetry, oxygen, intravenous access.")
        print("  -> Directing patient/EMS to Acute Trauma/Cardiac Suite.")

    elif chosen_venue == "urgent_care" or (1.5 <= urgency_score < 2.5):
        print("[ACTION: YELLOW PATHWAY - SAME-DAY URGENT CARE]")
        print("  -> Scheduled immediate walk-in slot at Partner Urgent Care Clinic.")
        print("  -> Auto-requisitioned right ankle weight-bearing X-ray (Ottawa Ankle Rules).")
        print("  -> Issued digital check-in token and wait-time estimate (15 mins).")

    else:
        print("[ACTION: GREEN PATHWAY - PRIMARY CARE]")
        print("  -> Telehealth / Primary Care consult scheduled within 48-72 hours.")
        print("  -> Digital self-care packet and red-flag escalation instructions sent via SMS.")

    if follow_up_prob >= 0.70:
        print(f"  -> Automated Continuity: Flagged for mandatory 48-hour follow-up callback.")
    print("\n")


def main():
    print("Initializing Jev Healthcare Triage Engine...")
    is_simulated = False

    if not API_KEY:
        print("Note: TYPESAFE_API_KEY environment variable not detected.")
        print("Running in DEMO / SIMULATION mode using calibrated sample distributions.\n")
        is_simulated = True
    else:
        print("Connected to TypeSafe AI API (model: jev-1.13.0).\n")

    for scenario in PATIENT_SCENARIOS:
        if is_simulated:
            resp = simulate_jev_response(scenario["id"])
        else:
            try:
                raw_resp = query_jev(scenario["state"], TRIAGE_QUESTIONS, API_KEY)
                resp = raw_resp.get("answers", raw_resp)
                # Handle nested or top-level structures gracefully
                if "answers" in resp:
                    resp = resp["answers"]
                else:
                    resp = {"answers": resp}
            except Exception as exc:
                print(f"API call failed for {scenario['id']}: {exc}")
                print("Falling back to simulated response for display...")
                resp = simulate_jev_response(scenario["id"])

        answers = resp["answers"] if "answers" in resp else resp
        execute_triage_decision(scenario, answers)


if __name__ == "__main__":
    main()
