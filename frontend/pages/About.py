import streamlit as st

# =====================
# PAGE CONFIG
# =====================
st.set_page_config(
    page_title="About - Yu-Gi-Oh Card Assistant",
    page_icon="🃏",
    layout="centered"
)

# =====================
# PAGE HEADER
# =====================
st.title("🃏 About Yu-Gi-Oh Card Assistant")
st.markdown("""
Welcome to the **Yu-Gi-Oh Card Assistant**, a smart tool designed to help duelists find and explore Yu-Gi-Oh cards with ease.
""")

# =====================
# DESCRIPTION
# =====================
st.header("How it Works")
st.markdown("""
This application leverages a **RAG (Retrieval-Augmented Generation) system** combined with a **large language model (LLM)** to:

1. **Search a card database** for specific cards based on your queries.
2. **Provide detailed card information** including name, attack, defense, price, and description.
3. **Offer smart suggestions** and explanations for your card choices.

The RAG component ensures that the model retrieves relevant data from the database, while the LLM generates natural language responses for a conversational experience.
""")

# =====================
# TARGET USERS
# =====================
st.header("Who is this for?")
st.markdown("""
- Yu-Gi-Oh players looking to quickly find cards for their decks.
- Collectors who want detailed information on cards.
- Anyone interested in exploring the Yu-Gi-Oh card universe through an AI assistant.
""")

# =====================
# TECH STACK
# =====================
st.header("Technology Behind the App")
st.markdown("""
- **Backend**: FastAPI for serving API endpoints.
- **Database**: PostgreSQL for storing card information.
- **Vector Database**: Weaviate for semantic search capabilities.
- **LLM**: OpenAI model (GPT-4o-mini) for natural language responses.
- **Frontend**: Streamlit for an interactive user interface.
- **RAG**: Combines retrieval from the database with LLM generation for accurate and conversational responses.
""")

# =====================
# FOOTER
# =====================
st.markdown("---")
st.markdown("Created with ❤️ for Yu-Gi-Oh enthusiasts by Jonathan Ketelslegers, Jannik Schwerdtner, Adnan Delic.")