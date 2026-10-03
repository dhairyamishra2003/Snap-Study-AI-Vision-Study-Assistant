import time
import toml
from google import genai
from google.genai import types

secrets = toml.load(".streamlit/secrets.toml")
client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

models_to_test = ["gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-flash-latest"]

with open("sample_questions/parajumble_crime_deterrence.png", "rb") as f:
    img_data = f.read()

for m in models_to_test:
    t0 = time.time()
    try:
        resp = client.models.generate_content(
            model=m,
            contents=[
                types.Part.from_bytes(data=img_data, mime_type="image/png"),
                "Is this a parajumble or sentence ordering question? Answer YES or NO."
            ],
            config=types.GenerateContentConfig(temperature=0.0)
        )
        elapsed = time.time() - t0
        print(f"Model {m}: {elapsed:.2f}s | Response: {resp.text.strip()[:40]}")
    except Exception as e:
        print(f"Model {m}: FAILED ({e})")
