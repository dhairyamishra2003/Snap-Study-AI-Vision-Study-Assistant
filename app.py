"""
Snap & Study — AI Vision Study Assistant
Main Streamlit Application
"""

import os
import io
import re
import json
from datetime import datetime
from PIL import Image
import streamlit as st

# Third-party integrations
from dotenv import load_dotenv

# Try importing Google GenAI SDK
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# Try importing Twilio
try:
    from twilio.rest import Client as TwilioClient
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

# Try importing FPDF2
try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except ImportError:
    FPDF_AVAILABLE = False

# Local prompt templates
from prompts import (
    SYSTEM_PROMPT,
    ANALYSIS_PROMPT_TEMPLATE,
    SIMPLIFY_PROMPT_TEMPLATE,
    STUDY_NOTES_PROMPT_TEMPLATE,
    WHATSAPP_SUMMARY_PROMPT_TEMPLATE,
    DETECT_PARAJUMBLE_PROMPT,
    PARAJUMBLE_SYSTEM_PROMPT,
    PARAJUMBLE_PROMPT_TEMPLATE,
)

# Load local environment if present
load_dotenv()

# Active Gemini Vision & Multimodal Model
GEMINI_MODEL = "gemini-3.8-flash"

# ==============================================================================
# 1. STREAMLIT CONFIGURATION & CUSTOM STYLES
# ==============================================================================

st.set_page_config(
    page_title="Snap & Study — AI Vision Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS for rich aesthetics and clean typography
st.markdown(
    """
    <style>
    /* Main body background & fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top banner card */
    .snap-hero-card {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4338ca 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 20px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(67, 56, 202, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .snap-hero-title {
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 0.35rem;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 0.6rem;
    }
    .snap-hero-subtitle {
        font-size: 1.15rem;
        color: #c7d2fe;
        margin-bottom: 0;
        font-weight: 400;
    }

    /* Onboarding Card */
    .onboarding-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 24px;
        padding: 3rem 2.5rem;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.05);
        max-width: 580px;
        margin: 2rem auto;
        text-align: center;
    }

    /* Badges */
    .subject-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background-color: #ede9fe;
        color: #5b21b6;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        text-transform: uppercase;
        border: 1px solid #ddd6fe;
    }
    .topic-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #bae6fd;
    }

    /* Content Cards */
    .stCard {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
        margin-bottom: 1.25rem;
    }

    /* Answer Highlight box */
    .final-answer-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        border: 1.5px solid #86efac;
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        color: #14532d;
        margin: 1.2rem 0;
    }
    .final-answer-title {
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #166534;
        margin-bottom: 0.25rem;
    }
    .final-answer-content {
        font-size: 1.25rem;
        font-weight: 700;
    }

    /* Sidebar helper styling */
    .sidebar-student-tag {
        background-color: #f1f5f9;
        padding: 0.75rem 1rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }

    /* Structured Solution Cards (High-contrast, professional design) */
    .solution-block-card {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 16px;
        padding: 1.25rem 1.4rem;
        margin-bottom: 1.1rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.06);
    }
    .solution-block-card:hover {
        border-color: rgba(99, 102, 241, 0.45);
    }
    .card-tag {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.8rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 0.25rem 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.75rem;
    }
    .tag-question { background: rgba(59, 130, 246, 0.18); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.35); }
    .tag-concept  { background: rgba(168, 85, 247, 0.18); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.35); }
    .tag-formula  { background: rgba(14, 165, 233, 0.18); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.35); }
    .tag-relationships { background: rgba(16, 185, 129, 0.18); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); }
    .tag-solution { background: rgba(99, 102, 241, 0.18); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.35); }
    .tag-simple   { background: rgba(234, 179, 8, 0.18); color: #fde047; border: 1px solid rgba(234, 179, 8, 0.35); }
    .tag-warning  { background: rgba(239, 68, 68, 0.18); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.35); }
    .tag-takeaway { background: rgba(139, 92, 246, 0.18); color: #d8b4fe; border: 1px solid rgba(139, 92, 246, 0.35); }

    /* Final Answer Hero Container */
    .final-answer-hero-box {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.25) 100%);
        border: 2px solid #10b981;
        border-radius: 18px;
        padding: 1.5rem 1.6rem;
        margin: 1.35rem 0;
        box-shadow: 0 10px 25px -5px rgba(16, 185, 129, 0.25);
    }
    .final-answer-hero-tag {
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #34d399;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .final-answer-hero-text {
        font-size: 1.35rem;
        font-weight: 700;
        color: #ffffff;
        line-height: 1.4;
    }

    /* Individual step card */
    .individual-step-container {
        background: rgba(255, 255, 255, 0.035);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# 2. SESSION STATE INITIALIZATION
# ==============================================================================

SESSION_DEFAULTS = {
    "student_name": "",
    "onboarded": False,
    "uploaded_image_bytes": None,
    "uploaded_image_mime": None,
    "uploaded_image_name": None,
    "current_question": "",
    "detected_subject": "General",
    "detected_topic": "General Study",
    "analysis_result": None,
    "final_answer": None,
    "simplified_explanation": None,
    "generated_notes": None,
    "chat_history": [],
    "whatsapp_status": None,
}

for key, val in SESSION_DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ==============================================================================
# 3. SECRETS & CLIENT MANAGEMENT
# ==============================================================================

def get_secret(key: str, default: str = "") -> str:
    """Safely retrieves a configuration key from Streamlit secrets or env vars."""
    if key in st.secrets:
        val = str(st.secrets[key]).strip()
        if val and not val.startswith("your_"):
            return val
    env_val = os.environ.get(key, "").strip()
    if env_val and not env_val.startswith("your_"):
        return env_val
    return default

@st.cache_resource
def get_gemini_client(api_key: str):
    """
    Creates and caches the Google GenAI client instance.
    Cached across reruns to avoid redundant allocations.
    """
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        st.error(f"Failed to initialize Gemini client: {exc}")
        return None

CANDIDATE_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-flash-latest",
    "gemini-3.8-flash",
    "gemini-3.5-flash",
]

def generate_gemini_content(
    client,
    contents,
    system_instruction=SYSTEM_PROMPT,
    temperature=0.3,
    response_mime_type=None,
):
    """
    Invokes Gemini Vision with automatic failover across candidate flash models
    to protect against transient API load or deprecation issues.
    """
    last_exc = None
    config_kwargs = {
        "system_instruction": system_instruction,
        "temperature": temperature,
    }
    if response_mime_type:
        config_kwargs["response_mime_type"] = response_mime_type

    for model_name in CANDIDATE_MODELS:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
        except Exception as exc:
            last_exc = exc
            continue
    # pyrefly: ignore [bad-raise]
    raise last_exc

# Parajumble & sentence ordering detection keywords
PARAJUMBLE_KEYWORDS = [
    "properly sequenced",
    "coherent paragraph",
    "order of the sentences",
    "sequence of the four numbers",
    "arrange the sentences",
    "sentence arrangement",
    "rearrange the sentences",
    "sentence-ordering",
    "parajumble",
    "parajumbles",
    "order the sentences",
    "correct sequence",
    "sequence of sentences",
]

def is_sentence_ordering_question(client, image_bytes: bytes, image_mime: str, user_text: str = "") -> bool:
    """
    Detects whether the question is a sentence-ordering / parajumble problem.
    Uses instantaneous keyword matching first, then falls back to ultra-fast flash AI classification.
    """
    if user_text:
        text_lower = user_text.lower()
        if any(kw in text_lower for kw in PARAJUMBLE_KEYWORDS):
            return True

    if client and image_bytes:
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=image_mime or "image/jpeg"),
            DETECT_PARAJUMBLE_PROMPT,
        ]
        for m in ["gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.7-flash", "gemini-flash-latest"]:
            try:
                resp = client.models.generate_content(
                    model=m,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction="You are an expert question classifier. Answer strictly YES or NO as the very first word.",
                        temperature=0.0,
                    ),
                )
                if resp and resp.text:
                    clean = resp.text.strip().upper()
                    if "YES" in clean:
                        return True
                    elif "NO" in clean:
                        return False
            except Exception:
                continue

    return False

def format_parajumble_solution_markdown(data: dict) -> str:
    """
    Transforms the structured two-pass parajumble JSON analysis into clean,
    user-facing markdown sections without exposing raw internal chain-of-thought.
    """
    sentences = data.get("extracted_sentences", [])
    dependencies = data.get("dependencies", [])
    best_seq = str(data.get("best_sequence", "")).strip().replace(" ", "").replace("-", "").replace("->", "")
    explanation_steps = data.get("explanation_steps", [])
    pitfall = data.get("common_pitfall", "")
    takeaway = data.get("key_takeaway", "")

    # 1. Extracted problem sentences rendered in clean executive quote cards
    q_lines = ["**Arrange the following sentences into a coherent, logical paragraph:**\n"]
    for s in sentences:
        num = s.get("number", "")
        text = s.get("text", "")
        q_lines.append(f"> **[{num}]** {text}")
    question_md = "\n\n".join(q_lines) if sentences else "Sentences extracted from question image."

    # 2. Sentence Relationships & References
    rel_lines = []
    for dep in dependencies:
        dep_s = dep.get("dependent_sentence", "")
        ant_s = dep.get("antecedent_sentence", "")
        marker = dep.get("marker", "")
        exp = dep.get("explanation", "")
        rel_lines.append(f"- 🔗 **Sentence {dep_s} -> Sentence {ant_s}** (Reference: *\"{marker}\"*):\n  {exp}")
    relationships_md = "\n\n".join(rel_lines) if rel_lines else "Order established through logical general-to-specific discourse progression."

    # 3. Step-by-Step explanation of discourse progression
    step_lines = []
    for idx, step in enumerate(explanation_steps, 1):
        step_lines.append(f"{idx}. **Step {idx}:** {step}")
    solution_md = "\n\n".join(step_lines)

    # 4. Intuitive explanation of why this sequence is correct
    arrow_seq = " -> ".join(list(best_seq)) if best_seq.isdigit() else best_seq
    simple_exp = (
        f"**Why {arrow_seq}?**\n\n"
        f"The paragraph opens by establishing the empirical research finding, then anchors the core concept forward using grammatical reference markers ('the principle', 'the effect'). "
        f"It then transitions seamlessly from the broad population to a specific sub-case, before culminating in a decisive concluding synthesis."
    )

    return f"""### 📋 QUESTION
{question_md}

### 📚 SUBJECT & TOPIC
- **Subject:** English / Verbal Ability
- **Topic:** Sentence Ordering & Parajumbles

### 💡 CONCEPT
Discourse linguistics requires arranging sentences based on **grammatical antecedents**, **lexical reference markers** (e.g., 'the principle', 'the effect'), and **general-to-specific logical progression**, rather than superficial topical similarity.

### 🔗 SENTENCE RELATIONSHIPS & REFERENCES
{relationships_md}

### 📝 STEP-BY-STEP SOLUTION
{solution_md}

### 🎯 FINAL ANSWER
{best_seq} (Sequence: {arrow_seq})

### 🌟 SIMPLE EXPLANATION
{simple_exp}

### ⚠️ COMMON MISTAKE
{pitfall}

### 📌 KEY TAKEAWAY
{takeaway}
"""

# ==============================================================================
# 4. UTILITY & SERVICE FUNCTIONS
# ==============================================================================

def extract_metadata_from_analysis(analysis_text: str):
    """Parses subject, topic, and final answer from markdown headings."""
    subject = "General"
    topic = "General Academic"
    final_answer = ""

    # Subject regex
    subj_match = re.search(r"-\s*\*\*Subject:\*\*\s*(.+)", analysis_text, re.IGNORECASE)
    if subj_match:
        subject = subj_match.group(1).strip()
    else:
        subj_alt = re.search(r"SUBJECT\s*\n\s*(.+)", analysis_text, re.IGNORECASE)
        if subj_alt:
            subject = subj_alt.group(1).strip()

    # Topic regex
    topic_match = re.search(r"-\s*\*\*Topic:\*\*\s*(.+)", analysis_text, re.IGNORECASE)
    if topic_match:
        topic = topic_match.group(1).strip()
    else:
        topic_alt = re.search(r"TOPIC\s*\n\s*(.+)", analysis_text, re.IGNORECASE)
        if topic_alt:
            topic = topic_alt.group(1).strip()

    # Final answer regex
    ans_match = re.search(r"###\s*🎯\s*FINAL ANSWER\s*\n+([\s\S]*?)(?=\n###|\Z)", analysis_text, re.IGNORECASE)
    if ans_match:
        final_answer = ans_match.group(1).strip()
    else:
        ans_alt = re.search(r"FINAL ANSWER\s*\n+([\s\S]*?)(?=\n[A-Z\s]{4,}|\Z)", analysis_text, re.IGNORECASE)
        if ans_alt:
            final_answer = ans_alt.group(1).strip()

    final_answer = final_answer.replace("**", "").replace("*", "").strip()

    return subject, topic, final_answer

def sanitize_solution_markdown(text: str) -> str:
    """
    Sanitizes markdown and fixes common malformed LaTeX patterns so that
    KaTeX and Streamlit markdown render cleanly without red error blobs.
    """
    if not text:
        return ""
    # 1. Un-glue headings concatenated with dashes (e.g. '--- ###')
    text = re.sub(r'---\s*###', '\n\n###', text)
    # 2. Ensure clear double line breaks before any ### heading
    text = re.sub(r'([^\n])\s*(###\s+[^\n]+)', r'\1\n\n\2\n\n', text)
    # 3. Fix broken LaTeX cases (e.g., \end{cases} with no \begin{cases})
    if r'\end{cases}' in text and r'\begin{cases}' not in text:
        text = text.replace(r'\end{cases}', '')
    # 4. Ensure display math $$ has blank lines around it so markdown doesn't collapse
    text = re.sub(r'([^\n])\s*\$\$', r'\1\n\n$$', text)
    text = re.sub(r'\$\$\s*([^\n])', r'$$\n\n\1', text)
    # 5. Ensure numbered steps (e.g. 1. **Title**) have line breaks
    text = re.sub(r'([^\n])\s*(\d+\.\s+\*\*)', r'\1\n\n\2', text)
    # 6. Ensure bullet points (- $ or - **) have separate lines
    text = re.sub(r'([^\n])\s*(-\s+[\*\$A-Za-z])', r'\1\n\n\2', text)
    return text.strip()

def parse_solution_sections(text: str) -> dict:
    """
    Parses the structured AI response into named sections for individual card rendering.
    """
    cleaned = sanitize_solution_markdown(text)
    sections = {}
    current_key = "INTRO"
    current_lines = []

    for line in cleaned.splitlines():
        header_match = re.match(r"^###\s*([^\n]+)", line.strip())
        if header_match:
            if current_lines:
                sections[current_key] = "\n".join(current_lines).strip()
                current_lines = []
            raw = header_match.group(1).upper()
            if "QUESTION" in raw:
                current_key = "QUESTION"
            elif "SUBJECT" in raw or "TOPIC" in raw:
                current_key = "SUBJECT_TOPIC"
            elif "CONCEPT" in raw:
                current_key = "CONCEPT"
            elif "RELATIONSHIP" in raw or "DEPENDENC" in raw:
                current_key = "RELATIONSHIPS"
            elif "FORMULA" in raw or "RULE" in raw:
                current_key = "FORMULA"
            elif "STEP" in raw or "SOLUTION" in raw:
                current_key = "SOLUTION"
            elif "FINAL ANSWER" in raw:
                current_key = "FINAL_ANSWER"
            elif "SIMPLE" in raw:
                current_key = "SIMPLE_EXPLANATION"
            elif "MISTAKE" in raw:
                current_key = "COMMON_MISTAKE"
            elif "TAKEAWAY" in raw:
                current_key = "KEY_TAKEAWAY"
            else:
                current_key = header_match.group(1).strip()
        else:
            current_lines.append(line)

    if current_lines:
        sections[current_key] = "\n".join(current_lines).strip()

    return sections

def render_structured_solution(raw_text: str):
    """
    Renders AI educational analysis in distinct, high-contrast, professional cards
    rather than a single collapsed raw markdown dump.
    """
    sections = parse_solution_sections(raw_text)

    # 1. Final Answer Hero Banner (Large, celebratory emerald green card placed at the very top for instant clarity)
    if "FINAL_ANSWER" in sections and sections["FINAL_ANSWER"]:
        ans_clean = sections["FINAL_ANSWER"].strip()
        display_ans = ans_clean.replace("**", "").replace("*", "").strip()
        st.markdown(
            f"""
            <div class="final-answer-hero-box">
                <div class="final-answer-hero-tag">🎯 FINAL VERIFIED ANSWER</div>
                <div class="final-answer-hero-text">{display_ans}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Extracted Question Card
    if "QUESTION" in sections and sections["QUESTION"]:
        with st.container(border=True):
            st.markdown('<div class="card-tag tag-question">📋 Extracted Problem</div>', unsafe_allow_html=True)
            st.markdown(sections["QUESTION"])

    # 3. Sentence Relationships & References (for parajumbles and structured verbal analysis)
    if "RELATIONSHIPS" in sections and sections["RELATIONSHIPS"]:
        with st.container(border=True):
            st.markdown('<div class="card-tag tag-relationships">🔗 Sentence Relationships & References</div>', unsafe_allow_html=True)
            st.markdown(sections["RELATIONSHIPS"])

    # 4. Core Concept Card
    if "CONCEPT" in sections and sections["CONCEPT"]:
        with st.container(border=True):
            st.markdown('<div class="card-tag tag-concept">💡 Core Concept</div>', unsafe_allow_html=True)
            st.markdown(sections["CONCEPT"])

    # 5. Formula / Rule Card (for STEM)
    if "FORMULA" in sections and sections["FORMULA"]:
        with st.container(border=True):
            st.markdown('<div class="card-tag tag-formula">📐 Formula & Governing Rules</div>', unsafe_allow_html=True)
            st.markdown(sections["FORMULA"])

    # 6. Step-by-Step Solution (Separated cleanly by numbered steps)
    if "SOLUTION" in sections and sections["SOLUTION"]:
        with st.container(border=True):
            st.markdown('<div class="card-tag tag-solution">📝 Step-by-Step Solution</div>', unsafe_allow_html=True)
            sol_text = sections["SOLUTION"]
            steps = re.split(r'\n+(?=\d+\.\s+\*\*)', sol_text.strip())
            if len(steps) > 1:
                for step in steps:
                    if step.strip():
                        with st.container(border=True):
                            st.markdown(step.strip())
            else:
                st.markdown(sol_text)

    # 7. Plain-English Intuitive Explanation
    if "SIMPLE_EXPLANATION" in sections and sections["SIMPLE_EXPLANATION"]:
        with st.container(border=True):
            st.markdown('<div class="card-tag tag-simple">🌟 Plain-English Explanation</div>', unsafe_allow_html=True)
            st.markdown(sections["SIMPLE_EXPLANATION"])

    # 8. Common Mistake Warning
    if "COMMON_MISTAKE" in sections and sections["COMMON_MISTAKE"]:
        with st.container(border=True):
            st.markdown('<div class="card-tag tag-warning">⚠️ Common Mistake to Avoid</div>', unsafe_allow_html=True)
            st.markdown(sections["COMMON_MISTAKE"])

    # 9. Key Takeaway
    if "KEY_TAKEAWAY" in sections and sections["KEY_TAKEAWAY"]:
        with st.container(border=True):
            st.markdown('<div class="card-tag tag-takeaway">📌 Key Exam Takeaway</div>', unsafe_allow_html=True)
            st.markdown(sections["KEY_TAKEAWAY"])

    # Fallback if no sections were identified
    if not sections or (len(sections) == 1 and "INTRO" in sections):
        with st.container(border=True):
            st.markdown(sanitize_solution_markdown(raw_text))

def sanitize_text_for_pdf(text: str) -> str:
    """Replaces Unicode characters and emojis with PDF-safe equivalents."""
    replacements = {
        "—": "-", "–": "-", "“": '"', "”": '"', "‘": "'", "’": "'",
        "•": "*", "→": "->", "←": "<-", "≥": ">=", "≤": "<=", "≠": "!=",
        "±": "+/-", "°": " deg", "²": "^2", "³": "^3", "×": "x", "÷": "/"
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Strip emojis and unsupported symbols for core Latin-1 font compatibility
    cleaned = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return cleaned

def generate_pdf_notes(student_name: str, subject: str, topic: str, notes_markdown: str) -> bytes:
    """Generates a styled, readable PDF of the study notes using fpdf2."""
    if not FPDF_AVAILABLE:
        return b""

    class PDFDoc(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(30, 41, 59)
            self.cell(0, 10, "Snap & Study - Revision Notes", border=0, align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(203, 213, 225)
            self.line(10, 22, 200, 22)
            self.ln(6)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(148, 163, 184)
            page_text = f"Page {self.page_no()} | Generated by Snap & Study for {sanitize_text_for_pdf(student_name)}"
            self.cell(0, 10, page_text, border=0, align="C")

    pdf = PDFDoc()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Meta banner
    pdf.set_fill_color(241, 245, 249)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(71, 85, 105)
    date_str = datetime.now().strftime("%B %d, %Y")
    banner_text = f"STUDENT: {sanitize_text_for_pdf(student_name)}   |   SUBJECT: {sanitize_text_for_pdf(subject)}   |   TOPIC: {sanitize_text_for_pdf(topic)}   |   {date_str}"
    pdf.cell(0, 8, banner_text, border=0, align="L", fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # Clean lines and format
    lines = notes_markdown.splitlines()
    for raw_line in lines:
        clean_line = sanitize_text_for_pdf(raw_line.strip())
        if not clean_line:
            pdf.ln(2)
            continue

        if clean_line.startswith("---"):
            pdf.set_draw_color(226, 232, 240)
            y = pdf.get_y() + 1
            pdf.line(10, y, 200, y)
            pdf.ln(4)
            continue

        if clean_line.startswith("# ") or clean_line.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(30, 41, 59)
            clean_title = re.sub(r'[*#]', '', clean_line).strip()
            pdf.cell(0, 8, clean_title, border=0, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif clean_line.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(67, 56, 202)
            clean_section = re.sub(r'[*#]', '', clean_line).strip()
            pdf.cell(0, 7, clean_section, border=0, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif clean_line.startswith("- ") or clean_line.startswith("* "):
            bullet_body = clean_line[2:].strip()
            b_kv = re.match(r'^\*\*(.+?):\*\*\s*(.*)$', bullet_body)
            if b_kv:
                lbl = b_kv.group(1).replace('*', '').strip()
                val = b_kv.group(2).replace('*', '').strip()
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 41, 59)
                pdf.write(5, f"  * {lbl}: ")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(51, 65, 85)
                pdf.write(5, val)
                pdf.ln(6)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(51, 65, 85)
                clean_bullet = bullet_body.replace('*', '').strip()
                pdf.multi_cell(0, 5, f"  * {clean_bullet}", border=0, new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1)
        else:
            kv = re.match(r'^\*\*(.+?):\*\*\s*(.*)$', clean_line)
            if kv:
                lbl = kv.group(1).replace('*', '').strip()
                val = kv.group(2).replace('*', '').strip()
                if "final answer" in lbl.lower():
                    pdf.set_font("Helvetica", "B", 11)
                    pdf.set_text_color(5, 150, 105)
                    pdf.write(6, f"{lbl}: ")
                    pdf.set_font("Helvetica", "B", 11)
                    pdf.write(6, val)
                    pdf.ln(7)
                else:
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.set_text_color(30, 41, 59)
                    pdf.write(5, f"{lbl}: ")
                    pdf.set_font("Helvetica", "", 10)
                    pdf.set_text_color(51, 65, 85)
                    pdf.write(5, val)
                    pdf.ln(6)
            else:
                num_step = re.match(r'^(\d+\.)\s+\*\*(.+?):\*\*\s*(.*)$', clean_line)
                if num_step:
                    num_prefix = num_step.group(1)
                    lbl = num_step.group(2).replace('*', '').strip()
                    val = num_step.group(3).replace('*', '').strip()
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.set_text_color(30, 41, 59)
                    pdf.write(5, f"{num_prefix} {lbl}: ")
                    pdf.set_font("Helvetica", "", 10)
                    pdf.set_text_color(51, 65, 85)
                    pdf.write(5, val)
                    pdf.ln(6)
                else:
                    pdf.set_font("Helvetica", "", 10)
                    pdf.set_text_color(51, 65, 85)
                    clean_content = clean_line.replace('*', '').strip()
                    pdf.multi_cell(0, 5, clean_content, border=0, new_x="LMARGIN", new_y="NEXT")
                    pdf.ln(1)

    return bytes(pdf.output())

def send_whatsapp_notes(to_phone: str, notes_text: str) -> tuple[bool, str]:
    """Sends study notes to student's WhatsApp via Twilio API."""
    if not TWILIO_AVAILABLE:
        return False, "Twilio library is not installed in the environment."

    account_sid = get_secret("TWILIO_ACCOUNT_SID")
    auth_token = get_secret("TWILIO_AUTH_TOKEN")
    from_number = get_secret("TWILIO_PHONE_NUMBER", default="whatsapp:+14155238886")
    content_sid = get_secret("TWILIO_CONTENT_SID", default="")

    if not account_sid or not auth_token:
        return False, "Twilio credentials are missing in secrets.toml (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)."

    # Format recipient phone number
    clean_digits = re.sub(r"[^\d+]", "", to_phone)
    if not clean_digits:
        return False, "Please enter a valid phone number with country code (e.g. +14155552671)."

    if not clean_digits.startswith("+"):
        clean_digits = "+" + clean_digits

    formatted_to = f"whatsapp:{clean_digits}"
    formatted_from = from_number if from_number.startswith("whatsapp:") else f"whatsapp:{from_number}"

    try:
        client = TwilioClient(account_sid, auth_token)

        # Truncate or chunk if notes exceed standard WhatsApp body limit
        body_to_send = notes_text
        if len(body_to_send) > 1500:
            body_to_send = body_to_send[:1450] + "\n\n...[Notes truncated for WhatsApp preview. See full notes in web app]"

        if content_sid:
            msg = client.messages.create(
                from_=formatted_from,
                to=formatted_to,
                content_sid=content_sid
            )
        else:
            msg = client.messages.create(
                body=body_to_send,
                from_=formatted_from,
                to=formatted_to
            )
        return True, msg.sid
    except TwilioRestException as exc:
        return False, f"Twilio API Error: {exc.msg} (Code {exc.code})"
    except Exception as exc:
        return False, f"Unexpected error: {str(exc)}"

# ==============================================================================
# 5. ONBOARDING SCREEN
# ==============================================================================

if not st.session_state.onboarded or not st.session_state.student_name:
    st.markdown(
        """
        <div class="onboarding-card">
            <div style="font-size: 3.5rem; margin-bottom: 0.5rem;">📸 🎓</div>
            <h1 style="color: #1e1b4b; font-size: 2.2rem; font-weight: 800; margin-bottom: 0.5rem;">
                Welcome to Snap & Study
            </h1>
            <p style="color: #64748b; font-size: 1.15rem; margin-bottom: 2rem;">
                Snap a question. Understand the solution.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container():
        col_space1, col_form, col_space2 = st.columns([1, 1.6, 1])
        with col_form:
            name_input = st.text_input(
                "Student Name",
                placeholder="Enter your name (e.g. Alex)",
                help="We use your name to personalize your study notes and explanations.",
            )
            start_btn = st.button("🚀 Start Learning", use_container_width=True, type="primary")

            if start_btn:
                if name_input.strip():
                    st.session_state.student_name = name_input.strip()
                    st.session_state.onboarded = True
                    st.rerun()
                else:
                    st.error("Please enter your name to get started!")
    st.stop()

# ==============================================================================
# 6. MAIN STUDY SCREEN
# ==============================================================================

# API Configuration Check
gemini_key = get_secret("GEMINI_API_KEY")

# Top Navigation / Hero Banner
st.markdown(
    f"""
    <div class="snap-hero-card">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <div class="snap-hero-title">
                    <span>🎓</span> Snap & Study
                </div>
                <div class="snap-hero-subtitle">
                    Upload a question or problem and let AI explain it step-by-step.
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.12); padding: 0.6rem 1.2rem; border-radius: 12px; margin-top: 0.5rem;">
                <span style="color: #c7d2fe; font-size: 0.85rem;">Student</span><br/>
                <strong style="color: #ffffff; font-size: 1.05rem;">{st.session_state.student_name}</strong>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Sidebar with Status & Actions
with st.sidebar:
    st.markdown("### ⚙️ Study Workspace")
    st.markdown(
        f"""
        <div class="sidebar-student-tag">
            <span style="color: #64748b; font-size: 0.8rem; text-transform: uppercase; font-weight: 700;">Active Student</span><br/>
            <strong style="color: #0f172a; font-size: 1.1rem;">{st.session_state.student_name}</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🔄 Switch Student / Reset", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.markdown("---")
    st.markdown("#### 🔑 API Key Setup")
    
    # Check if key is already loaded from secrets or session
    session_key = st.session_state.get("user_provided_gemini_key", "")
    active_key = gemini_key or session_key

    if active_key:
        st.success("✅ Gemini Vision API Ready")
        if not gemini_key and session_key:
            st.caption("Using session API key.")
    else:
        st.error("⚠️ Gemini API Key Missing")
        user_key_input = st.text_input(
            "Paste Gemini API Key",
            type="password",
            placeholder="AIzaSy...",
            help="Get your free Gemini API key from https://aistudio.google.com/",
        )
        if user_key_input.strip():
            st.session_state["user_provided_gemini_key"] = user_key_input.strip()
            st.success("API Key saved for this session!")
            st.rerun()
        st.caption("Or save it permanently in `.streamlit/secrets.toml`.")

    gemini_key = active_key

    twilio_ready = bool(get_secret("TWILIO_ACCOUNT_SID") and get_secret("TWILIO_AUTH_TOKEN"))
    if twilio_ready:
        st.success("✅ Twilio WhatsApp Ready")
    else:
        st.caption("ℹ️ Twilio WhatsApp is optional (for WhatsApp delivery).")

# ==============================================================================
# 7. UPLOAD & ANALYSIS WORKSPACE
# ==============================================================================

tab_solve, tab_chat, tab_notes = st.tabs(["📸 Question & Solution", "💬 Interactive Chat", "📖 Study Notes"])

with tab_solve:
    col_input, col_display = st.columns([1, 1.25], gap="large")

    with col_input:
        st.markdown("### 📤 Upload Your Question")
        uploaded_file = st.file_uploader(
            "Upload Question Image",
            type=["jpg", "jpeg", "png", "webp"],
            help="Supported formats: JPG, JPEG, PNG, WEBP. Max 20MB.",
        )

        user_typed_question = st.text_area(
            "Optional: Specific question or instructions",
            placeholder="e.g. 'Can you explain step 3 specifically?' or 'Solve part (b) only'",
            height=80,
        )

        level_choice = st.selectbox(
            "Explanation Level",
            options=["Beginner", "Standard", "Detailed"],
            index=1,
            help=(
                "Beginner: Simple terms and intuitive steps.\n"
                "Standard: Standard academic formulas and logic.\n"
                "Detailed: Rigorous derivation, edge cases, and pitfalls."
            ),
        )

        # Image preview & validation
        if uploaded_file is not None:
            # Validate size (< 20MB)
            file_bytes = uploaded_file.getvalue()
            size_mb = len(file_bytes) / (1024 * 1024)

            if size_mb > 20:
                st.error("The uploaded image exceeds 20MB. Please upload a smaller image.")
            else:
                try:
                    pil_img = Image.open(io.BytesIO(file_bytes))
                    st.image(pil_img, caption=f"Preview: {uploaded_file.name} ({pil_img.format}, {size_mb:.1f} MB)", use_container_width=True)
                    st.session_state.uploaded_image_bytes = file_bytes
                    st.session_state.uploaded_image_mime = uploaded_file.type
                    st.session_state.uploaded_image_name = uploaded_file.name
                except Exception as exc:
                    st.error("Invalid/unclear image: I couldn't clearly read the question. Please upload a clearer image.")

        analyze_clicked = st.button("✨ Analyze Question", type="primary", use_container_width=True)

        if analyze_clicked:
            # 1. Validation checks
            if not st.session_state.uploaded_image_bytes and not user_typed_question.strip():
                st.error("Please provide a question or upload an image.")
            elif not st.session_state.uploaded_image_bytes:
                st.error("Please upload a question image.")
            elif not gemini_key:
                st.error("Missing Gemini API configuration. Please configure GEMINI_API_KEY in `.streamlit/secrets.toml`.")
            else:
                with st.spinner("🔍 AI Vision is analyzing your question..."):
                    client = get_gemini_client(gemini_key)
                    if not client:
                        st.error("AI analysis failed. Please try again.")
                    else:
                        opt_text = f"\nStudent additional note: {user_typed_question.strip()}" if user_typed_question.strip() else ""

                        try:
                            # Build multimodal contents
                            contents = []
                            if st.session_state.uploaded_image_bytes:
                                contents.append(
                                    types.Part.from_bytes(
                                        data=st.session_state.uploaded_image_bytes,
                                        mime_type=st.session_state.uploaded_image_mime or "image/jpeg"
                                    )
                                )

                            # Detect whether question is a parajumble / sentence ordering problem
                            is_pj = is_sentence_ordering_question(
                                client=client,
                                image_bytes=st.session_state.uploaded_image_bytes,
                                image_mime=st.session_state.uploaded_image_mime,
                                user_text=user_typed_question.strip(),
                            )

                            if is_pj:
                                # Dedicated sentence-ordering reasoning flow with two-pass discourse validation
                                pj_prompt = PARAJUMBLE_PROMPT_TEMPLATE.format(optional_user_note=opt_text)
                                contents.append(pj_prompt)

                                response = generate_gemini_content(
                                    client=client,
                                    contents=contents,
                                    system_instruction=PARAJUMBLE_SYSTEM_PROMPT,
                                    temperature=0.1,
                                    response_mime_type="application/json",
                                )

                                if response and response.text:
                                    pj_data = json.loads(response.text)
                                    analysis_text = format_parajumble_solution_markdown(pj_data)
                                else:
                                    raise ValueError("Empty response received from AI model.")
                            else:
                                # Standard question analysis flow
                                analysis_prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                                    level=level_choice,
                                    optional_user_question=opt_text
                                )
                                contents.append(analysis_prompt)

                                response = generate_gemini_content(
                                    client=client,
                                    contents=contents,
                                    system_instruction=SYSTEM_PROMPT,
                                    temperature=0.3,
                                )

                                if response and response.text:
                                    analysis_text = response.text
                                else:
                                    raise ValueError("Empty response received from AI model.")

                            if analysis_text:
                                subj, top, ans = extract_metadata_from_analysis(analysis_text)
                                st.session_state.analysis_result = analysis_text
                                st.session_state.detected_subject = subj
                                st.session_state.detected_topic = top
                                st.session_state.final_answer = ans
                                st.session_state.current_question = user_typed_question.strip() or f"Question from {st.session_state.uploaded_image_name}"
                                st.session_state.simplified_explanation = None
                                st.session_state.generated_notes = None

                                # Seed conversation history
                                st.session_state.chat_history = [
                                    {
                                        "role": "user",
                                        "content": f"Please analyze this {subj} question on {top}."
                                    },
                                    {
                                        "role": "assistant",
                                        "content": analysis_text
                                    }
                                ]
                                st.success("Analysis complete!")
                                st.rerun()
                            else:
                                st.error("AI analysis failed. Please try again.")
                        except APIError as api_err:
                            st.error(f"AI analysis failed: {api_err.message}. Please try again.")
                        except Exception as exc:
                            err_str = str(exc)
                            if "quota" in err_str.lower() or "rate" in err_str.lower():
                                st.error("API quota limit reached. Please check your Gemini API plan.")
                            else:
                                st.error(f"AI analysis failed. Please try again.")

    # Display Column: Solution and Interactive Actions
    with col_display:
        st.markdown("### 💡 AI Solution & Breakdown")

        if not st.session_state.analysis_result:
            st.info("Upload an image and click **'Analyze Question'** to view the step-by-step solution here.")
        else:
            # Metadata chips
            st.markdown(
                f"""
                <div style="margin-bottom: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                    <span class="subject-badge">📚 {st.session_state.detected_subject}</span>
                    <span class="topic-badge">🏷️ {st.session_state.detected_topic}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Structured, professional card rendering
            render_structured_solution(st.session_state.analysis_result)

            st.markdown("---")

            # Action Buttons Row
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                simplify_btn = st.button("🌱 Explain More Simply", use_container_width=True)
            with btn_col2:
                make_notes_btn = st.button("📖 Generate Study Notes", use_container_width=True, type="secondary")

            # Handle Explain More Simply
            if simplify_btn:
                if not gemini_key:
                    st.error("Missing Gemini API key.")
                else:
                    with st.spinner("Simplifying explanation into intuitive terms..."):
                        client = get_gemini_client(gemini_key)
                        prompt = SIMPLIFY_PROMPT_TEMPLATE.format(
                            question=st.session_state.current_question,
                            final_answer=st.session_state.final_answer or "Refer to original solution",
                            previous_explanation=st.session_state.analysis_result
                        )
                        try:
                            resp = generate_gemini_content(
                                client=client,
                                contents=[prompt],
                                system_instruction=SYSTEM_PROMPT,
                                temperature=0.4,
                            )
                            if resp and resp.text:
                                st.session_state.simplified_explanation = resp.text
                                st.session_state.chat_history.append({"role": "user", "content": "Explain this solution more simply."})
                                st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
                                st.rerun()
                        except Exception as exc:
                            st.error("AI analysis failed. Please try again.")

            # Show Simplified Explanation if present
            if st.session_state.simplified_explanation:
                st.markdown("#### 🌟 Simplified Explanation")
                st.info(st.session_state.simplified_explanation)

            # Handle Generate Study Notes
            if make_notes_btn:
                if not gemini_key:
                    st.error("Missing Gemini API key.")
                else:
                    with st.spinner("Condensing problem into high-yield revision notes..."):
                        client = get_gemini_client(gemini_key)
                        prompt = STUDY_NOTES_PROMPT_TEMPLATE.format(
                            subject=st.session_state.detected_subject,
                            topic=st.session_state.detected_topic,
                            question=st.session_state.current_question,
                            solution_context=st.session_state.analysis_result
                        )
                        try:
                            resp = generate_gemini_content(
                                client=client,
                                contents=[prompt],
                                system_instruction=SYSTEM_PROMPT,
                                temperature=0.2,
                            )
                            if resp and resp.text:
                                st.session_state.generated_notes = resp.text
                                st.toast("✅ Study Notes generated! Check the 'Study Notes' tab.", icon="📖")
                        except Exception as exc:
                            st.error("Failed to generate study notes. Please try again.")

# ==============================================================================
# 8. INTERACTIVE CHAT TAB
# ==============================================================================

with tab_chat:
    st.markdown("### 💬 Interactive Study Chat")
    st.caption("Ask questions, explore edge cases, or request similar practice problems.")

    if not st.session_state.analysis_result:
        st.info("Analyze a problem first to start an interactive chat about it.")
    else:
        # Quick prompts
        st.markdown("**Quick Prompts:**")
        quick_cols = st.columns(4)
        quick_prompts = [
            "Why did you use this formula?",
            "Give me another example.",
            "Quiz me on this topic.",
            "What if this value changes?",
        ]
        
        selected_quick_prompt = None
        for i, qp in enumerate(quick_prompts):
            with quick_cols[i]:
                if st.button(qp, key=f"quick_{i}", use_container_width=True):
                    selected_quick_prompt = qp

        st.markdown("---")

        # Render chat history
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Chat Input
        user_msg = st.chat_input("Ask a follow-up question...") or selected_quick_prompt

        if user_msg:
            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(user_msg)
            st.session_state.chat_history.append({"role": "user", "content": user_msg})

            if not gemini_key:
                st.error("Gemini API key is missing. Please add it to secrets.toml.")
            else:
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        client = get_gemini_client(gemini_key)
                        
                        # Build context with initial image and dialogue
                        context_parts = []
                        if st.session_state.uploaded_image_bytes:
                            context_parts.append(
                                types.Part.from_bytes(
                                    data=st.session_state.uploaded_image_bytes,
                                    mime_type=st.session_state.uploaded_image_mime or "image/jpeg"
                                )
                            )

                        # Context summary
                        dialogue_context = f"""
ACADEMIC CONTEXT:
Subject: {st.session_state.detected_subject}
Topic: {st.session_state.detected_topic}
Current Problem: {st.session_state.current_question}
Initial Solution Summary:
{st.session_state.analysis_result}

STUDENT FOLLOW-UP QUESTION:
{user_msg}

Answer clearly, keeping all previous steps and context in mind.
"""
                        context_parts.append(dialogue_context)

                        try:
                            resp = generate_gemini_content(
                                client=client,
                                contents=context_parts,
                                system_instruction=SYSTEM_PROMPT,
                                temperature=0.4,
                            )
                            if resp and resp.text:
                                st.markdown(resp.text)
                                st.session_state.chat_history.append({"role": "assistant", "content": resp.text})
                                st.rerun()
                        except Exception as exc:
                            st.error("AI analysis failed. Please try again.")

# ==============================================================================
# 9. STUDY NOTES TAB
# ==============================================================================

with tab_notes:
    st.markdown("### 📖 High-Yield Revision Notes")

    if not st.session_state.analysis_result:
        st.info("Analyze a problem first to generate high-yield study notes.")
    elif not st.session_state.generated_notes:
        st.info("Click **'Generate Study Notes'** in the Solution tab or below to create concise revision notes.")
        if st.button("✨ Generate Study Notes Now", type="primary"):
            if not gemini_key:
                st.error("Missing Gemini API key.")
            else:
                with st.spinner("Summarizing notes..."):
                    client = get_gemini_client(gemini_key)
                    prompt = STUDY_NOTES_PROMPT_TEMPLATE.format(
                        subject=st.session_state.detected_subject,
                        topic=st.session_state.detected_topic,
                        question=st.session_state.current_question,
                        solution_context=st.session_state.analysis_result
                    )
                    try:
                        resp = generate_gemini_content(
                            client=client,
                            contents=[prompt],
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.2,
                        )
                        if resp and resp.text:
                            st.session_state.generated_notes = resp.text
                            st.rerun()
                    except Exception as exc:
                        st.error("Failed to generate study notes.")
    else:
        # Display the generated notes
        st.markdown(st.session_state.generated_notes)
        st.markdown("---")

        # Action Buttons
        st.markdown("#### 📥 Actions & Sharing")
        action_col1, action_col2, action_col3 = st.columns([1, 1, 1.2])

        # 1. Download TXT
        with action_col1:
            st.download_button(
                label="📄 Download TXT",
                data=st.session_state.generated_notes,
                file_name=f"Study_Notes_{st.session_state.detected_subject}_{st.session_state.detected_topic}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # 2. Download PDF
        with action_col2:
            pdf_bytes = generate_pdf_notes(
                student_name=st.session_state.student_name,
                subject=st.session_state.detected_subject,
                topic=st.session_state.detected_topic,
                notes_markdown=st.session_state.generated_notes
            )
            st.download_button(
                label="📑 Download PDF",
                data=bytes(pdf_bytes),
                file_name=f"Study_Notes_{st.session_state.detected_subject}_{st.session_state.detected_topic}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        # 3. Twilio WhatsApp Sender
        with action_col3:
            with st.popover("📱 Send to WhatsApp", use_container_width=True):
                st.markdown("**Send Notes to WhatsApp**")
                phone_num = st.text_input(
                    "Recipient Phone Number",
                    placeholder="+14155552671",
                    help="Include country code (e.g. +1 for US, +91 for India)."
                )
                send_wa_btn = st.button("Send Now", type="primary", use_container_width=True)

                if send_wa_btn:
                    if not phone_num.strip():
                        st.error("Please enter a valid phone number.")
                    else:
                        with st.spinner("Sending WhatsApp message via Twilio..."):
                            success, msg_result = send_whatsapp_notes(
                                to_phone=phone_num.strip(),
                                notes_text=st.session_state.generated_notes
                            )
                            if success:
                                st.success(f"✅ Notes sent to WhatsApp! (ID: {msg_result[:16]}...)")
                            else:
                                st.error("Unable to send the notes to WhatsApp. Please try again.")
                                st.caption(msg_result)

        # Copyable raw notes section
        with st.expander("📋 View Copyable Raw Text"):
            st.code(st.session_state.generated_notes, language="markdown")
