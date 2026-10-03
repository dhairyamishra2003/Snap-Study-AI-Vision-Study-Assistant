import os
import sys
import time
import toml
import json
from google import genai
from google.genai import types

sys.path.insert(0, os.getcwd())
import prompts

secrets = toml.load(".streamlit/secrets.toml")
client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

with open("sample_questions/parajumble_crime_deterrence.png", "rb") as f:
    img_data = f.read()

models = ["gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash"]

for m in models:
    t0 = time.time()
    try:
        resp = client.models.generate_content(
            model=m,
            contents=[
                types.Part.from_bytes(data=img_data, mime_type="image/png"),
                prompts.PARAJUMBLE_PROMPT_TEMPLATE.format(optional_user_note="")
            ],
            config=types.GenerateContentConfig(
                system_instruction=prompts.PARAJUMBLE_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.1
            )
        )
        elapsed = time.time() - t0
        data = json.loads(resp.text)
        seq = str(data.get("best_sequence", "")).replace(" ", "").replace("-", "")
        print(f"Model {m}: {elapsed:.2f}s | Sequence: {seq} | Valid: {seq == '2431'}")
    except Exception as e:
        print(f"Model {m}: FAILED ({e})")
