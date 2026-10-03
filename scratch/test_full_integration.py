import os
import sys
import toml
import json

sys.path.insert(0, os.getcwd())
from google import genai
from google.genai import types
import app
import prompts

# Ensure secrets are loaded
secrets_path = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml")
secrets = toml.load(secrets_path)
api_key = secrets.get("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)

print("=" * 60)
print("TEST 1: Crime Deterrence Parajumble Image Analysis")
print("=" * 60)

pj_img_path = "sample_questions/parajumble_crime_deterrence.png"
with open(pj_img_path, "rb") as f:
    pj_bytes = f.read()

# 1. Test detection
is_pj = app.is_sentence_ordering_question(client, pj_bytes, "image/png", "")
print(f"Parajumble Detection Result: {is_pj}")
assert is_pj is True, "Failed to detect parajumble image!"

# 2. Test analysis with candidate validation
pj_prompt = prompts.PARAJUMBLE_PROMPT_TEMPLATE.format(optional_user_note="")
contents = [
    types.Part.from_bytes(data=pj_bytes, mime_type="image/png"),
    pj_prompt
]

response = app.generate_gemini_content(
    client=client,
    contents=contents,
    system_instruction=prompts.PARAJUMBLE_SYSTEM_PROMPT,
    temperature=0.1,
    response_mime_type="application/json",
)

pj_data = json.loads(response.text)
print(f"Detected best sequence: {pj_data.get('best_sequence')}")
print(f"Dependencies: {len(pj_data.get('dependencies', []))}")
for d in pj_data.get('dependencies', []):
    print(f"  - Sent {d.get('dependent_sentence')} -> Sent {d.get('antecedent_sentence')} ({d.get('marker')}): {d.get('explanation')}")

markdown_out = app.format_parajumble_solution_markdown(pj_data)
subj, top, ans = app.extract_metadata_from_analysis(markdown_out)
print(f"Extracted metadata: Subject='{subj}', Topic='{top}', Final Answer='{ans}'")

# Check sections parsed
sections = app.parse_solution_sections(markdown_out)
print(f"Parsed sections: {list(sections.keys())}")
assert "RELATIONSHIPS" in sections, "Missing RELATIONSHIPS section!"
assert "QUESTION" in sections, "Missing QUESTION section!"
assert "FINAL_ANSWER" in sections, "Missing FINAL_ANSWER section!"

# Assert final answer is 2431
best_seq_clean = pj_data.get('best_sequence', '').strip().replace(" ", "").replace("->", "").replace("-", "")
print(f"ASSERTION CHECK: Expected '2431', Got '{best_seq_clean}'")
assert best_seq_clean == "2431", f"Expected 2431, but got {best_seq_clean}"
print(">>> TEST 1 PASSED: 2431 selected based on discourse linguistics! <<<")

print("\n" + "=" * 60)
print("TEST 2: Physics Problem Image Analysis (Ensuring standard flow preserved)")
print("=" * 60)

phys_img_path = "sample_questions/physics_problem.png"
with open(phys_img_path, "rb") as f:
    phys_bytes = f.read()

is_pj_phys = app.is_sentence_ordering_question(client, phys_bytes, "image/png", "")
print(f"Physics Detection Result (should be False): {is_pj_phys}")
assert is_pj_phys is False, "Incorrectly flagged physics problem as parajumble!"

analysis_prompt = prompts.ANALYSIS_PROMPT_TEMPLATE.format(
    level="Standard",
    optional_user_question=""
)
phys_contents = [
    types.Part.from_bytes(data=phys_bytes, mime_type="image/png"),
    analysis_prompt
]
phys_resp = app.generate_gemini_content(
    client=client,
    contents=phys_contents,
    system_instruction=prompts.SYSTEM_PROMPT,
    temperature=0.3
)
phys_sections = app.parse_solution_sections(phys_resp.text)
phys_subj, phys_top, phys_ans = app.extract_metadata_from_analysis(phys_resp.text)
print(f"Physics metadata: Subject='{phys_subj}', Topic='{phys_top}', Answer='{phys_ans}'")
print(f"Physics sections: {list(phys_sections.keys())}")
assert "QUESTION" in phys_sections
assert "SOLUTION" in phys_sections
print(">>> TEST 2 PASSED: Normal question pipeline works flawlessly! <<<")

print("\n" + "=" * 60)
print("ALL INTEGRATION TESTS PASSED (100%)!")
print("=" * 60)
