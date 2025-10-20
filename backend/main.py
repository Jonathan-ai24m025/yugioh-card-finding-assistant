from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
import weaviate
from ollama import Client
from sentence_transformers import SentenceTransformer
from init import initialize_weaviate, initialize_ollama
import torch
import os


app = FastAPI(root_path="/api/v1")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama-test:11434")
#OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:latest")
DB_HOST = os.getenv("DATABASE_HOST", "postgres")
#DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_NAME = os.getenv("DATABASE_NAME", "postgres")
DB_USER = os.getenv("DATABASE_USER", "postgres")
DB_PASS = os.getenv("DATABASE_PASSWORD", "postgres")
WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate")
#WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "localhost")
WEAVIATE_PORT = os.getenv("WEAVIATE_PORT", 8080)


def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def get_rag():
    return weaviate.connect_to_local(
        host=WEAVIATE_HOST,
        port=WEAVIATE_PORT
    )

def get_llm():
    return Client(
        host=OLLAMA_URL
    )


@app.on_event("startup")
async def startup_event():
    print("Checking Weaviate state...")
    print(f"Torch: {torch.__version__}, CUDA: {torch.version.cuda}")

    if torch.cuda.is_available():
        tokenizer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cuda")
    else:
        print("No CUDA found. Using CPU for tokenization.")
        tokenizer = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

    initialize_weaviate(csv_path="./cards.csv", get_rag=get_rag, tokenizer=tokenizer)
    initialize_ollama(get_llm=get_llm, model_name=OLLAMA_MODEL)
    #TODO: figure out CUDA problems (wrong pyTorch version, Docker GPU passthrough)
    app.state.tokenizer = tokenizer
    app.state.weaviate = weaviate.connect_to_local(host=WEAVIATE_HOST, port=WEAVIATE_PORT)


class ChatMessage(BaseModel):
    role: str
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}

class ChatRequest(BaseModel):
    message: ChatMessage
    history: list[ChatMessage] = []

    def to_prompt(self) -> list:
        hist = []
        for h in self.history:
            hist.append(h.to_dict())
        hist.append(self.message.to_dict())
        return hist


@app.post("/chat")
async def chat(req: ChatRequest):
    client = Client(host=OLLAMA_URL)
    print(req.to_prompt())
    response = client.chat(model="mistral:latest", messages=req.to_prompt())
    return {"content": response.message.content, "role": response.message.role}


@app.get("/cards")
def get_cards():
    """Return first 3 rows from the Postgres 'cards' table."""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM cards LIMIT 3;")
        rows = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        conn.close()
        return [dict(zip(colnames, row)) for row in rows]
    except Exception as e:
        return {"error": str(e)}


@app.get("/rag/{query}")
def rag_search(query: str):
    try:
        query_vector = app.state.tokenizer.encode(query)
        client = get_rag()
        collection = client.collections.get("Card")

        results = collection.query.near_vector(
            near_vector=query_vector,
            limit=10,
            return_properties=["name", "description", "attack", "defense", "price"]
        )

        client.close()
        return {"results": results}
    except Exception as e:
        return {"error": str(e)}
