from fastapi import FastAPI
import psycopg2
import os
import pandas as pd
import weaviate
from weaviate_init import initialize_weaviate

app = FastAPI(root_path="/api/v1")


# --- Database connection setup ---
DB_HOST = os.getenv("DATABASE_HOST", "postgres")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASS = os.getenv("DATABASE_PASSWORD", "postgres")

WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate")
WEAVIATE_PORT = os.getenv("WEAVIATE_PORT", "8080")

# --- Postgres connection ---
def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

@app.on_event("startup")
async def startup_event():
    pass
    # TODO: Weaviate doesn't work yet.
    #print("Checking Weaviate state...")
    #await initialize_weaviate("./cards.csv")

@app.get("/")
def root():
    return {"message": "FastAPI backend is running"}

@app.get("/cards")
def get_cards():
    """Return first 3 rows from the Postgres 'cards' table."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM cards LIMIT 3;")
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return [dict(zip(colnames, row)) for row in rows]
    except Exception as e:
        return {"error": str(e)}

@app.get("/rag/{text}")
def rag_search(text: str):
    """
    Query Weaviate for the 3 most similar cards to the input text.
    Returns their 'name', 'description', 'set_name', 'type', 'attribute'.
    """
    # TODO: Weaviate doesn't work yet.
    '''
    
    try:
        client = weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT)
        # Semantic search with limit=3
        result = (
            client.query
            .get("Card", ["name", "description", "set_name", "type", "attribute"])
            .with_near_text({"concepts": [text]})
            .with_limit(3)
            .do()
        )

        cards = result.get("data", {}).get("Get", {}).get("Card", [])
        return cards
    except Exception as e:
        return {"error": str(e)}

    '''
    return {"text": "some sample text."}