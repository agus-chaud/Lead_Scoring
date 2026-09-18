from pathlib import Path
import json

import requests

BASE_DIR = Path(__file__).resolve().parent
payload = json.loads((BASE_DIR / "payload.json").read_text(encoding="utf-8"))
response = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=10)
response.raise_for_status()
print(response.json())
