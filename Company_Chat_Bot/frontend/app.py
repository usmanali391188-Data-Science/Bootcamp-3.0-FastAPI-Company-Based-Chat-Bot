import streamlit as st
import requests

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Company Chatbot", layout="wide")
st.title("💬 Company Chatbot")


if "company" not in st.session_state:
    st.session_state.company = None
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar.form("setup_form"):
    st.markdown("<h2 style='text-align:center'>Setup Company Bot</h2>", unsafe_allow_html=True)
    company_name = st.text_input("Company Name", placeholder="Enter Company Name", key="company_name")
    company_website = st.text_input("Website", placeholder="Enter Company Website", key="company_website")
    submit_setup = st.form_submit_button("Transform Bot")

    if submit_setup:
        if company_name.strip() and company_website.strip():
            with st.spinner("Transforming bot..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/scrape",
                                        json={"name": company_name, "website": company_website}, timeout=15)
                    if res.status_code == 200:
                        st.session_state.company = res.json()
                        st.session_state.messages = []
                        st.success(f"✅ Bot ready for **{company_name}**!")
                    else:
                        st.error("⚠️ Backend error!")
                except Exception as e:
                    st.error(f"⚠️ Failed to reach backend: {e}")
        else:
            st.warning("Enter both name and website.")

if st.session_state.company:
    company = st.session_state.company


    col1, col2 = st.columns([1, 5])
    with col1:
        if company.get("logo"):
            st.image(company["logo"], width=100)
    with col2:
        st.markdown(f"<h2 style='margin-bottom:5px'>{company['name']}</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:gray; margin-top:0'>{company.get('description','')}</p>", unsafe_allow_html=True)

    st.markdown("---")


    user_input = st.text_input("Type your question here...", key="chat_input")
    send_pressed = st.button("Send")

    if send_pressed and user_input.strip():
        question = user_input.strip()
        st.session_state.messages.append({"role": "user", "content": question})

        with st.spinner("Assistant is thinking..."):
            try:
                resp = requests.post(f"{BACKEND_URL}/chat",
                                     json={"question": question, "company": company}, timeout=20)
                if resp.status_code == 200:
                    answer = resp.json().get("reply", "")
                else:
                    answer = "⚠️ Backend returned an error."
            except Exception as e:
                answer = f"⚠️ Failed to reach backend: {e}"

        st.session_state.messages.append({"role": "assistant", "content": answer})

    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(
                f"<div style='text-align:right; background:#FFD966; padding:10px; border-radius:10px; margin:5px 0; color:black'>{msg['content']}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='text-align:left; background:#D9EAD3; padding:10px; border-radius:10px; margin:5px 0; color:black'>{msg['content']}</div>",
                unsafe_allow_html=True,
            )
























































































