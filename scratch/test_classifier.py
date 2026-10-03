import os
import sys
import toml
from PIL import Image
from google import genai
from google.genai import types

# Load API Key
secrets_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".streamlit", "secrets.toml")
if not os.path.exists(secrets_path):
    secrets_path = os.path.join(os.getcwd(), ".streamlit", "secrets.toml")

secrets = toml.load(secrets_path)
api_key = secrets.get("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

DETECT_PARAJUMBLE_PROMPT = """Examine this question image or text.
Is this a sentence-ordering, parajumble, or coherent paragraph arrangement question (asking to arrange/sequence numbered sentences such as 1, 2, 3, 4 into a coherent paragraph)?
Answer strictly with YES or NO as the very first word, followed by a brief 1-sentence reason."""

CANDIDATE_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
]

def generate_gemini_content(client, contents, system_instruction="", temperature=0.0):
    for m in CANDIDATE_MODELS:
        try:
            return client.models.generate_content(
                model=m,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=temperature
                )
            )
        except Exception as e:
            continue
    return None

def test_image(img_path):
    with open(img_path, "rb") as f:
        data = f.read()
    contents = [
        types.Part.from_bytes(data=data, mime_type="image/png"),
        DETECT_PARAJUMBLE_PROMPT
    ]
    resp = generate_gemini_content(client, contents)
    first_word = resp.text.strip().split()[0].upper() if resp and resp.text else "NONE"
    return "YES" in first_word, resp.text.strip() if resp else "NO_RESPONSE"

pj_img = "sample_questions/parajumble_crime_deterrence.png"
phys_img = "sample_questions/physics_problem.png"

is_pj, reason_pj = test_image(pj_img)
print(f"Parajumble image: is_pj={is_pj}, response: {reason_pj}")

is_phys, reason_phys = test_image(phys_img)
print(f"Physics image: is_phys={is_phys}, response: {reason_phys}")
