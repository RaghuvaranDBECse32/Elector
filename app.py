import streamlit as st
import vertexai
from vertexai.generative_models import GenerativeModel

# GCP Init
PROJECT_ID = "your-project-id" 
vertexai.init(project=PROJECT_ID, location="us-central1")
model = GenerativeModel("gemini-1.5-flash")

# UI Configuration for Mobile + Desktop
st.set_page_config(page_title="ECI Assistant", layout="wide")

# 3D Neumorphic CSS
st.markdown("""
    <style>
    .main {
        background-color: #f0f2f5;
    }
    /* 3D Card Effect */
    .stButton>button {
        border-radius: 20px;
        background: #f0f2f5;
        box-shadow: 8px 8px 16px #d1d9e6, -8px -8px 16px #ffffff;
        border: none;
        transition: 0.3s;
        color: #003366;
        font-weight: bold;
    }
    .stButton>button:hover {
        box-shadow: inset 6px 6px 12px #d1d9e6, inset -6px -6px 12px #ffffff;
        color: #ff9933;
    }
    /* ECI Header Style */
    .eci-header {
        background: linear-gradient(90deg, #ff9933 0%, #ffffff 50%, #128807 100%);
        padding: 10px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    /* Mobile Responsiveness */
    @media (max-width: 640px) {
        .stChatMessage { width: 100% !important; }
    }
    </style>
    <div class="eci-header">
        <h1 style="color: #000080; margin:0;">भारत निर्वाचन आयोग</h1>
        <p style="color: #000080; margin:0;">Election Commission of India - AI Assistant</p>
    </div>
    """, unsafe_allow_html=True)

# App Content
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🛠️ Quick Actions")
    if st.button("Check Registration Status"):
        st.info("Directing to National Voters' Service Portal...")
    if st.button("Find My Polling Station"):
        st.info("Locating nearest booth...")

with col2:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask me about the voting process..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Dynamic reasoning context
            full_prompt = f"System: You are an official ECI assistant. Be formal, neutral, and accurate. User: {prompt}"
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
          
