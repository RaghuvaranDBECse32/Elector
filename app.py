import streamlit as st
import os
from dotenv import load_dotenv

# Gemini
import google.generativeai as genai

# Vertex
import vertexai
from vertexai.generative_models import GenerativeModel

# ---------------- LOAD ENV ----------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="ELECTOR AI", layout="wide")

# ---------------- MODE TOGGLE ----------------
st.sidebar.title("⚙️ AI Mode")
mode = st.sidebar.radio("Select AI Backend", [
    "Gemini API (Free)",
    "Vertex AI (GCP)"
])

# ---------------- INIT MODELS ----------------
if mode == "Gemini API (Free)":
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

elif mode == "Vertex AI (GCP)":
    vertexai.init(project=PROJECT_ID, location="us-central1")
    model = GenerativeModel("gemini-1.5-flash")

# ---------------- CSS ----------------
st.markdown("""
<style>
.hero {
    padding: 30px;
    border-radius: 20px;
    background: linear-gradient(135deg,#0f2027,#203a43,#2c5364);
    color: white;
    text-align: center;
}
.card {
    padding:20px;
    border-radius:20px;
    background: rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    color:white;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HERO ----------------
st.markdown("""
<div class="hero">
<h1>🗳️ ELECTOR AI</h1>
<p>Dual AI Mode: Gemini + Vertex</p>
</div>
""", unsafe_allow_html=True)

# ---------------- NAV ----------------
page = st.sidebar.radio("Navigate", [
    "🏠 Home",
    "💬 Chat",
    "🧠 Quiz"
])

# ---------------- AI FUNCTION ----------------
def generate(prompt):
    if mode == "Gemini API (Free)":
        return model.generate_content(prompt).text
    else:
        return model.generate_content(prompt).text

# ---------------- HOME ----------------
if page == "🏠 Home":
    st.success(f"Current Mode: {mode}")

    col1, col2, col3 = st.columns(3)
    col1.markdown('<div class="card">💬 AI Chat</div>', unsafe_allow_html=True)
    col2.markdown('<div class="card">⚙️ Dual Backend</div>', unsafe_allow_html=True)
    col3.markdown('<div class="card">🧠 Quiz</div>', unsafe_allow_html=True)

# ---------------- CHAT ----------------
elif page == "💬 Chat":
    st.title("💬 ELECTOR AI")

    if "chat" not in st.session_state:
        st.session_state.chat = []

    for msg in st.session_state.chat:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask about elections...")

    if prompt:
        st.session_state.chat.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            response = generate(
                f"You are Election Commission assistant. {prompt}"
            )
            st.markdown(response)

        st.session_state.chat.append({
            "role": "assistant",
            "content": response
        })

# ---------------- QUIZ ----------------
elif page == "🧠 Quiz":
    score = 0

    q1 = st.radio("First step?", ["Counting", "Registration", "Result"])
    if q1 == "Registration":
        score += 1

    q2 = st.radio("Who conducts elections?", ["ECI", "Police", "Court"])
    if q2 == "ECI":
        score += 1

    if st.button("Submit"):
        st.success(f"Score: {score}/2")
        if score == 2:
            st.balloons()
