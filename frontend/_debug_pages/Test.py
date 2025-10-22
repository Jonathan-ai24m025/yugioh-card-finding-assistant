import streamlit as st
import requests

# =====================
# ✅ CONFIG
# =====================
API_BASE = "http://backend:8000/api/v1"
# If running locally instead of Docker, use:
# API_BASE = "http://localhost:8000/api/v1"

# =====================
# ✅ PAGE SETUP
# =====================
st.set_page_config(page_title="Chat with Yu-Gi-Oh Assistant", page_icon="🃏")
st.title("🃏 Yu-Gi-Oh Chat Assistant")
st.caption("Chat with the AI assistant using the RAG + Ollama backend.")


# =====================
# ✅ SESSION STATE
# =====================
if "messages" not in st.session_state:
    st.session_state.messages = []  # chat history


# =====================
# ✅ CHAT INPUT
# =====================
with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("Your message:", placeholder="Ask about a Yu-Gi-Oh card...")
    send_button = st.form_submit_button("Send")

# =====================
# ✅ SEND MESSAGE
# =====================
if send_button and user_input.strip():
    # Add user message to local history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Prepare the payload for FastAPI
    payload = {
        "message": {"role": "user", "content": user_input},
        "history": st.session_state.messages[:-1],  # exclude the current user msg
    }

    try:
        # Send request to backend
        response = requests.post(f"{API_BASE}/chat", json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            assistant_reply = data.get("content", "(no response)")
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"⚠️ Error: {response.status_code} - {response.text}"
            })

    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Request failed: {e}"
        })


# =====================
# ✅ DISPLAY CHAT
# =====================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"🧑‍💬 **You:** {msg['content']}")
    else:
        st.markdown(f"🤖 **Assistant:** {msg['content']}")
