import streamlit as st
import requests

# -------------------------------
# Streamlit Page Setup
# -------------------------------
st.set_page_config(
    page_title="Text to API",
    page_icon="📤",
    layout="wide"
)

# -------------------------------
# Page Title
# -------------------------------
st.title("📤 Send Text to API")

# -------------------------------
# API Endpoint
# -------------------------------
API_BASE_URL = "http://backend:8000/api/v1"  # ✅ Adjust based on your setup

# -------------------------------
# Input Section
# -------------------------------
text_input = st.text_area(
    "Enter your text to send:",
    placeholder="Type your message here...",
    height=120
)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    send_button = st.button("📨 Send Text", type="primary", use_container_width=True)

# -------------------------------
# CSS Styling for Card Look
# -------------------------------
st.markdown("""
<style>
    .stApp {
        background-color: #F8F9FA;
    }
    div[data-testid="stMarkdownContainer"] h3 {
        color: #2E86C1;
        margin-bottom: 0.3rem;
    }
    div[data-testid="stMarkdownContainer"] p {
        margin: 0.2rem 0;
    }
    small {
        color: #555;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# API Call and Display
# -------------------------------
if send_button:
    if text_input.strip():
        try:
            with st.spinner("⏳ Sending request..."):
                response = requests.get(
                    f"{API_BASE_URL}/rag/{text_input}",
                    timeout=10
                )

            if response.status_code == 200:
                st.success("✅ Data fetched successfully!")

                data = response.json()
                objects = data.get("results", {}).get("objects", [])

                if not objects:
                    st.info("No cards found.")
                else:
                    st.subheader("🃏 Results:")

                    # Create a grid layout: 3 cards per row
                    num_cols = 3
                    for i in range(0, len(objects), num_cols):
                        cols = st.columns(num_cols)
                        for j, col in enumerate(cols):
                            if i + j < len(objects):
                                card = objects[i + j]
                                props = card.get("properties", {})

                                with col.container(border=True):
                                    st.markdown(f"### {props.get('name', 'Unknown')}")
                                    st.markdown(f"**Price:** {props.get('price', 'N/A')}")
                                    st.markdown(f"**Attack:** {props.get('attack', 'N/A')}")
                                    st.markdown(f"**Defense:** {props.get('defense', 'N/A')}")
                                    st.markdown(
                                        f"<small>{props.get('description', 'No description')}</small>",
                                        unsafe_allow_html=True
                                    )

            else:
                st.error(f"❌ Failed to send. Status: {response.status_code}")
        except Exception as e:
            st.error(f"⚠️ Error: {str(e)}")
    else:
        st.warning("⚠️ Please enter some text first.")
