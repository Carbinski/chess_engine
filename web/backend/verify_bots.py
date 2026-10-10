import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

bots_to_test = [
    "python_random",
    "python_aggressive",
    "python_dumb_eval",
    "python_basic_search",
    "python_fast_v2",
    "python_midgame_v1",
    "java_basic_v3",
    "java_fast_v2",
    "java_bot_v2"
]

fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

print("Verifying Bots...")

for bot in bots_to_test:
    print(f"Testing {bot}...", end=" ")
    try:
        response = requests.post(f"{BASE_URL}/move", json={"fen": fen, "botId": bot}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if data['move']:
                print(f"SUCCESS: {data['move']} ({data['time']:.2f}s, depth {data['depth']})")
            else:
                print(f"FAILED: No move returned")
        else:
            print(f"FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"FAILED: {e}")

print("Verification complete.")
