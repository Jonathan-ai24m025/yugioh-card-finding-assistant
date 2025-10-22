import streamlit as st
import requests
from typing import List, Dict, Any

# -------------------------------
# Streamlit Page Setup
# -------------------------------
st.set_page_config(page_title="Yu-Gi-Oh Chat Assistant", page_icon="🃏", layout="wide")

st.title("🃏 Yu-Gi-Oh Chat Assistant")
st.caption("Chat with the AI assistant using the RAG + Ollama backend.")

# -------------------------------
# API Endpoint
# -------------------------------
API_BASE_URL = "http://backend:8000/api/v1"

# -------------------------------
# Persistent State
# -------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history: list[dict[str, any]] = []
if "error" not in st.session_state:
    st.session_state.error = None

# -------------------------------
# Helper: Convert to API format
# -------------------------------
def build_api_history(history: list[dict[str, any]]) -> list[dict[str, any]]:
    api_hist = []
    for item in history:
        api_hist.append({"role": "user", "content": item["user"], "cards": []})
        api_hist.append({"role": "assistant", "content": item["assistant"], "cards": item["cards"]})
    return api_hist

# -------------------------------
# Send message to backend
# -------------------------------
def send_message(user_text: str):
    payload = {
        "message": {"role": "user", "content": user_text, "cards": []},
        "history": build_api_history(st.session_state.chat_history),
    }

    try:
        resp = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        st.session_state.error = f"Request failed: {e}"
        return None, None, str(e)

    try:
        data = resp.json()
    except Exception as e:
        st.session_state.error = f"Failed to parse JSON: {e}"
        return None, None, str(e)

    msg = data.get("content", data)
    error = data.get("error", None)
    assistant_text = str(msg.get("content", ""))
    cards = msg.get("cards", []) or []

    normalized_cards = [
        {
            "name": c.get("name", "Unknown"),
            "description": c.get("description", "No description."),
            "attack": c.get("attack", "N/A"),
            "defense": c.get("defense", "N/A"),
            "price": c.get("price", "N/A"),
        }
        for c in cards if isinstance(c, dict)
    ]

    return assistant_text, normalized_cards, error

# -------------------------------
# Render Chat
# -------------------------------
for msg in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(msg["user"])

    with st.chat_message("assistant"):
        st.markdown(msg["assistant"])

        # Render any returned cards in a nice grid
        cards = msg.get("cards", [])
        if cards:
            cols = st.columns(min(len(cards), 3))
            for i, card in enumerate(cards):
                with cols[i % len(cols)]:
                    st.markdown(f"**{card['name']}**")
                    st.caption(card["description"])
                    st.text(f"ATK: {card['attack']} | DEF: {card['defense']}")
                    st.text(f"💰 Price: {card['price']}")

# -------------------------------
# Chat Input Handling
# -------------------------------
user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message
    st.chat_message("user").markdown(user_input)

    assistant_text, cards, error = send_message(user_input)

    if assistant_text is not None:
        # Show assistant message
        with st.chat_message("assistant"):
            if error:
                # Highlight error visually
                st.markdown(
                    f"<div style='background-color:#F8D7DA; color:#842029; padding:10px; border-radius:5px;'>"
                    f"⚠️ {assistant_text}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(assistant_text)

            # Show cards normally
            if cards:
                cols = st.columns(min(len(cards), 3))
                for i, card in enumerate(cards):
                    with cols[i % len(cols)]:
                        st.markdown(f"**{card['name']}**")
                        st.caption(card["description"])
                        st.text(f"ATK: {card['attack']} | DEF: {card['defense']}")
                        st.text(f"💰 Price: {card['price']}")

        # Save to history
        st.session_state.chat_history.append(
            {"user": user_input, "assistant": assistant_text, "cards": cards}
        )