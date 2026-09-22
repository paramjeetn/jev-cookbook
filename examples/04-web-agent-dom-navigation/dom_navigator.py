"""
Web Agent DOM Navigation using Jev Speculative Fan-Out.

This example demonstrates how a web browsing agent (inspired by jev-ultrafast)
evaluates an interactive page's DOM element table in a single ~100ms round trip.

Instead of issuing sequential LLM calls (e.g. "What operation?" followed by "Which element?"),
we ask Jev multiple questions speculatively in parallel:
  1. `operation`: High-level action (CLICK, TYPE_TEXT, SCROLL_DOWN, WAIT, DONE)
  2. `click_target`: Which element to click if the operation is CLICK
  3. `type_target`: Which input field to focus if the operation is TYPE_TEXT

The matching speculative branch is executed, and unused branches are discarded at zero latency cost.
"""

import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

API_URL = "https://api.typesafe.ai/v1/systemone"
API_KEY = os.getenv("TYPESAFE_API_KEY")


def build_google_flights_state() -> str:
    """Returns a realistic snapshot of a Google Flights booking page."""
    return """Goal: Book a one-way flight from San Francisco to London on November 15.

Current page elements:
[1] button    Change ticket type · Round trip
[2] combobox  Where from?        · San Francisco
[3] combobox  Where to?          · empty
[4] textbox   Departure          · empty
[5] button    Search             · disabled
[6] link      Explore destinations
[7] button    Flight class · Economy"""


def get_navigation_questions() -> dict:
    """Constructs the speculative questions payload for Jev."""
    return {
        "operation": {
            "type": "choice",
            "instructions": "What is the best next operation to advance the flight booking goal?",
            "criteria": {
                "CLICK": "Click an interactive element such as a button, dropdown toggle, or link.",
                "TYPE_TEXT": "Type text into a designated input field, combobox, or search box.",
                "SCROLL_DOWN": "Scroll down the page to reveal additional content or elements.",
                "WAIT": "Wait for page content, search results, or network requests to finish loading.",
                "DONE": "The flight booking goal has been completely achieved."
            }
        },
        "click_target": {
            "type": "choice",
            "instructions": "If the operation is CLICK, which element should be clicked?",
            "criteria": {
                "[1]": "Button: Change ticket type · Round trip (to change to one-way)",
                "[2]": "Combobox: Where from? · San Francisco",
                "[3]": "Combobox: Where to? · empty",
                "[4]": "Textbox: Departure · empty",
                "[5]": "Button: Search · disabled",
                "[6]": "Link: Explore destinations",
                "[7]": "Button: Flight class · Economy"
            }
        },
        "type_target": {
            "type": "choice",
            "instructions": "If the operation is TYPE_TEXT, which input field should receive text?",
            "criteria": {
                "[2]": "Where from? combobox (currently San Francisco)",
                "[3]": "Where to? combobox (currently empty)",
                "[4]": "Departure textbox (currently empty)"
            }
        }
    }


def query_jev(state: str, questions: dict) -> dict:
    """
    Sends the state and speculative questions to the Jev System One endpoint.
    If no API key is provided, returns a realistic mock response for local evaluation.
    """
    if not API_KEY:
        print("⚠️  No TYPESAFE_API_KEY found in environment. Using simulated response for demonstration.")
        time.sleep(0.1)  # Simulate ~100ms API latency
        return {
            "answers": {
                "operation": {
                    "type": "choice",
                    "choice": "CLICK",
                    "confidence": 0.96,
                    "probabilities": {
                        "CLICK": 0.96,
                        "TYPE_TEXT": 0.03,
                        "SCROLL_DOWN": 0.00,
                        "WAIT": 0.01,
                        "DONE": 0.00
                    }
                },
                "click_target": {
                    "type": "choice",
                    "choice": "[1]",
                    "confidence": 0.94,
                    "probabilities": {
                        "[1]": 0.94,
                        "[2]": 0.01,
                        "[3]": 0.03,
                        "[4]": 0.01,
                        "[5]": 0.00,
                        "[6]": 0.00,
                        "[7]": 0.01
                    }
                },
                "type_target": {
                    "type": "choice",
                    "choice": "[3]",
                    "confidence": 0.89,
                    "probabilities": {
                        "[2]": 0.04,
                        "[3]": 0.89,
                        "[4]": 0.07
                    }
                }
            },
            "eval_time_ms": 98.4
        }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "jev-1.13.0",
        "state": state,
        "questions": questions
    }

    start = time.perf_counter()
    response = requests.post(API_URL, headers=headers, json=payload, timeout=10)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.raise_for_status()

    result = response.json()
    result["eval_time_ms"] = round(elapsed_ms, 2)
    return result


def execute_navigation_step(result: dict) -> None:
    """Dispatches action execution based on Jev's parallel speculative evaluation."""
    answers = result.get("answers", {})

    operation_data = answers.get("operation", {})
    operation = operation_data.get("choice")
    op_confidence = operation_data.get("confidence", 0.0)

    print("\n" + "=" * 60)
    print("⚡ Jev Decision Summary")
    print("=" * 60)
    print(f"Operation Chosen  : {operation} (confidence: {op_confidence:.2%})")
    print(f"Server Latency    : ~{result.get('eval_time_ms', 100):.1f}ms")

    # Speculative branch execution
    if operation == "CLICK":
        target_data = answers.get("click_target", {})
        target_id = target_data.get("choice")
        confidence = target_data.get("confidence", 0.0)
        print(f"Action Executed   : CLICK on element {target_id}")
        print(f"Target Confidence : {confidence:.2%}")
        print("Note              : [type_target] speculative branch discarded without latency penalty.")
        print(f"\nBrowser Driver Call: driver.element('{target_id}').click()")

    elif operation == "TYPE_TEXT":
        target_data = answers.get("type_target", {})
        target_id = target_data.get("choice")
        confidence = target_data.get("confidence", 0.0)
        print(f"Action Executed   : FOCUS & TYPE on element {target_id}")
        print(f"Target Confidence : {confidence:.2%}")
        print("Note              : [click_target] speculative branch discarded without latency penalty.")
        print(f"\nBrowser Driver Call: driver.element('{target_id}').type('London')")

    elif operation == "SCROLL_DOWN":
        print("Action Executed   : SCROLL down 500px")
        print("\nBrowser Driver Call: driver.scroll(0, 500)")

    elif operation == "WAIT":
        print("Action Executed   : WAIT for network idle")
        print("\nBrowser Driver Call: driver.wait_for_idle(2.0)")

    elif operation == "DONE":
        print("Goal Complete     : Booking requirements satisfied.")

    else:
        print(f"Unhandled operation: {operation}")

    print("=" * 60)


def main():
    print("🛫 Initializing Web Agent DOM Navigation Demo...")
    state = build_google_flights_state()
    questions = get_navigation_questions()

    print("\n--- DOM Viewport Snapshot & Goal ---")
    print(state)

    print("\nEvaluating page with Jev (speculative fan-out)...")
    result = query_jev(state, questions)

    execute_navigation_step(result)


if __name__ == "__main__":
    main()
