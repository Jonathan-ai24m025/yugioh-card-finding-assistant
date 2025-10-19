import streamlit as st
import requests
import json
import datetime

# Page configuration
st.set_page_config(
    page_title="Text to API",
    page_icon="📤",
    layout="centered"
)

st.title("📤 Send Text to API")

# Hardcoded API endpoint - replace with your actual endpoint
API_ENDPOINT = "https://your-api-endpoint.com/data"

# Text input
text_input = st.text_area(
    "Enter your text to send:",
    placeholder="Type your message here...",
    height=120
)

# Send button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    send_button = st.button("📨 Send Text", type="primary", use_container_width=True)

if send_button:
    if text_input.strip():
        try:
            # Prepare data
            payload = {
                "message": text_input,
                "timestamp": datetime.now().isoformat()  # You can add datetime.now() here
            }
            
            # Send to API
            with st.spinner("Sending..."):
                response = requests.post(
                    API_ENDPOINT,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
            
            if response.status_code == 200:
                st.success("Message sent successfully!")
                st.balloons()
            else:
                st.error(f"Failed to send. Status: {response.status_code}")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter some text first")