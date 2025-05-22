import os
import random
import textwrap

from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

USE_MOCK = os.environ.get("USE_MOCK", "true").lower() == "true"
SECURITY_THRESHOLD = 11.0


def generate_random_bases(n):
    """Generates a list of random bases ('+' or 'x')."""
    return [random.choice(["+", "x"]) for _ in range(n)]


def generate_random_bits(n):
    """Generates a list of random bits (0 or 1)."""
    return [random.choice([0, 1]) for _ in range(n)]


def generate_eve_bases(alice_bases, strategy):
    """Generates Eve's measurement bases based on her strategy."""
    if strategy == "beginner":
        return ["+" for _ in alice_bases]
    elif strategy == "intermediate":
        return [random.choice(["+", "x"]) for _ in alice_bases]
    elif strategy == "expert":
        return [ab if random.random() < 0.7 else random.choice(["+", "x"]) for ab in alice_bases]
    else:
        return generate_random_bases(len(alice_bases))


def simulate_bb84(n, eve_strategy="intermediate"):
    """Simulates the BB84 protocol including Eve's interference and calculates error metrics."""
    alice_bits = generate_random_bits(n)
    alice_bases = generate_random_bases(n)
    eve_bases = generate_eve_bases(alice_bases, eve_strategy)
    bob_bases = generate_random_bases(n)

    qubits = [bit if ab == eb else random.choice([0, 1]) for bit, ab, eb in zip(alice_bits, alice_bases, eve_bases)]
    bob_bits = [q if bb == ab else random.choice([0, 1]) for q, bb, ab in zip(qubits, bob_bases, alice_bases)]

    matching_indices = [i for i in range(n) if alice_bases[i] == bob_bases[i]]
    error_positions = [i for i in matching_indices if alice_bits[i] != bob_bits[i]]
    error_rate = round((len(error_positions) / len(matching_indices)) * 100, 2) if matching_indices else 0
    is_secure = error_rate < SECURITY_THRESHOLD

    return {
        "alice_bits": alice_bits,
        "alice_bases": alice_bases,
        "eve_bases": eve_bases,
        "bob_bases": bob_bases,
        "bob_bits": bob_bits,
        "error_positions": error_positions,
        "error_rate": error_rate,
        "is_secure": is_secure,
        "matching_indices": matching_indices
    }


def compute_match_rate(alice_bases, eve_bases):
    """Computes the match rate between Alice's and Eve's bases."""
    match_count = sum(1 for a, e in zip(alice_bases, eve_bases) if a == e)
    match_rate = round((match_count / len(alice_bases)) * 100, 2)
    return match_count, match_rate


def query_cerebras(prompt):
    """Queries the Cerebras API with a structured prompt and returns the parsed analysis."""
    api_key = os.environ.get("CEREBRAS_API_KEY")
    url = "https://api.cerebras.ai/v1/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "qwen-3-32b",
        "prompt": prompt.strip() + "\n[END]",
        "temperature": 0.1,
        "max_tokens": 200
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    text = response.json()["choices"][0]["text"].strip()

    strategy_guess = "Unknown"
    justification = ""

    if "Answer=" in text and "|" in text:
        try:
            parts = text.split("Answer=")[1].split("|")
            strategy_guess = parts[0].strip()
            justification = parts[1].strip()
        except Exception as e:
            justification = f"Parsing error: {str(e)}"
    else:
        justification = text

    return {
        "strategy_guess": strategy_guess,
        "justification": justification
    }


@app.route("/api/bb84", methods=["POST"])
def generate():
    """API endpoint to simulate BB84 protocol and optionally call Cerebras AI to analyze Eve's strategy."""
    data = request.get_json()
    num_bits = data.get("num_bits", 16)
    eve_strategy = data.get("eve_strategy", "intermediate")
    use_mock_override = data.get("use_mock", None)
    use_mock_mode = USE_MOCK if use_mock_override is None else use_mock_override

    sim_result = simulate_bb84(num_bits, eve_strategy)
    _, match_rate = compute_match_rate(sim_result["alice_bases"], sim_result["eve_bases"])

    if use_mock_mode:
        eve_analysis = {
            "strategy_guess": "Intermediate",
            "justification": "Eve’s basis choices appear random, matching Alice's about 50% of the time."
        }
    else:
        try:
            strategy_prompt = textwrap.dedent(f"""
                You are analyzing a quantum key exchange using BB84, a Quantum Key Distribution protocol.

                Eve, an eavesdropper, uses one of the following strategies:
                - Beginner: always uses '+' basis
                - Intermediate: randomly picks '+' or 'x'
                - Expert: mimics Alice’s basis most of the time

                In this protocol:
                - Alice randomly chooses a basis (+ or x) to encode each bit. These are listed under 'Alice bases'.
                - Eve chooses a basis to measure each qubit. These are listed under 'Eve bases'.

                The match rate indicates how often Eve's basis matched Alice's basis — a high rate may suggest mimicry, while a low rate may suggest randomness or fixed strategy.

                Data from one simulation:
                - Alice bases: {sim_result['alice_bases']}
                - Eve bases: {sim_result['eve_bases']}
                - Match rate: {match_rate}%

                Based on this information, which strategy did Eve most likely use?

                Respond in this format:
                Answer=<Beginner | Intermediate | Expert> | <Justification, max 30 words>
            """)
            eve_analysis = query_cerebras(strategy_prompt)
        except Exception as e:
            eve_analysis = {
                "strategy_guess": "Unknown",
                "justification": f"Model error: {str(e)}"
            }

    return jsonify({
        **sim_result,
        "narration": "This is a simulated quantum key distribution scenario.",
        "eve_analysis": eve_analysis
    })


if __name__ == "__main__":
    app.run(debug=True)