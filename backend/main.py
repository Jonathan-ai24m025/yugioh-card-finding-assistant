from fastapi import FastAPI
import psycopg2
import weaviate
from ollama import Client
from sentence_transformers import SentenceTransformer
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from init import initialize_weaviate, initialize_ollama
import torch
import os
import langchain
from langchain_openai import ChatOpenAI
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_community.utilities import SQLDatabase
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call, PIIMiddleware
import json
import re

langchain.verbose = False
langchain.debug = False
langchain.llm_cache = False


app = FastAPI(root_path="/api/v1")


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
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

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

embedder = None
sql_tool = None


class Card(BaseModel):
    name: str = Field(description="The name of the card")
    description: str = Field(description="The description of the card")
    attack: Optional[str] = Field(default=None, description="The attack value of the card. Not all cards have attack")
    defense: Optional[str] = Field(default=None, description="The defense value of the card. Not all cards have defense")
    price: str = Field(description="The price of the card")

class ChatMessage(BaseModel):
    role: str = Field(default="assistant", description="The role of the AI. Should be assistant.")
    content: str = Field(..., description="The content of the text response.")
    cards: List[Card] = Field(default_factory=list, description="A list of cards relevant to the content.")

    def to_dict(self) -> dict:
        # Convert nested BaseModel objects to plain dicts so JSON serialization is safe
        cards_serializable: List[Any] = []
        for c in (self.cards or []):
            if isinstance(c, BaseModel):
                # pydantic v1 uses .dict(), v2 uses .model_dump(); try both
                if hasattr(c, "dict"):
                    cards_serializable.append(c.dict())
                elif hasattr(c, "model_dump"):
                    cards_serializable.append(c.model_dump())
                else:
                    cards_serializable.append(dict(c))
            else:
                cards_serializable.append(c)
        return {"role": self.role, "content": self.content, "cards": cards_serializable}

class ChatRequest(BaseModel):
    message: ChatMessage
    history: List[ChatMessage] = Field(default_factory=list)

    def to_iterable(self, max_history: int = 10) -> List[dict]:
        # take the last `max_history` entries from history (older -> newer), then append current message
        recent = self.history[-max_history:] if self.history else []
        prompt = [h.to_dict() for h in recent]
        prompt.append(self.message.to_dict())
        return prompt

    def to_prompt(self, max_history: int = 10):
        prompt = []
        for msg in self.to_iterable(max_history):
            cards = msg.get("cards") or []
            if cards:
                card_str = "\n\n#####HISTORY-METAINFO#####\nCards:\n" + "\n".join(
                    f"- {c['name']} ({c['price']})"
                    for c in cards
                )
                msg["content"] += card_str
            prompt.append({"role": msg["role"], "content": msg["content"]})
        return prompt



@tool
def vectorstorage_tool(query: str) -> str:
    """
    Send a query to the Yugioh Card Vectorstorage to search for cards with similar context.

    Args:
        query (str): Any question, information or query to search for similar context.

    Returns:
        str: The response from the database containing the most relevant cards as json following this schema:
        [{"name": "", "attack": "", "defense": "", "description": "", "price": ""}]
    """
    print("Running RAG query: " + str(query))
    query_vector = get_embedder().encode(query)
    client = get_rag()
    collection = client.collections.get("Card")
    results = collection.query.near_vector(
        near_vector=query_vector,
        limit=10,
        return_properties=["name", "description", "attack", "defense", "price"]
    )
    client.close()
    output = json.dumps([r.properties for r in results.objects])
    print("Running RAG query done: " + str(output))
    return output
    
    
class IllegalToolOperation(Exception):
    pass


@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except IllegalToolOperation as tool_error:
        print("ILLEGAL TOOL OPERATION DURING INFERENCE: " + str(tool_error))
        return ToolMessage(
            content=f"Illegal Tool Operation: Please check your input and try again. ({str(tool_error)})",
            tool_call_id=request.tool_call["id"]
        )
    except Exception as e:
        print("ERROR DURING INFERENCE: " + str(e))
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )


class SafeQuerySQLDatabaseTool(QuerySQLDatabaseTool):
    def _run(self, query: str, **kwargs):
        max_rows = 5
        print("Running DB query: " + str(query))

        # Normalize and strip comments
        clean_query = re.sub(r'--.*?\n|/\*.*?\*/', '', query, flags=re.S).strip().lower()

        # Allow only SELECT statements
        if not clean_query.startswith("select"):
            raise IllegalToolOperation("Only SELECT queries are allowed for safety. You must start your queries with SELECT")

        # Add LIMIT if none present
        if "limit" not in clean_query:
            query = f"{query.rstrip(';')} LIMIT {max_rows};"

        result = super()._run(query, **kwargs)
        print("Running DB query done: " + str(result))
        return result

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )

def get_sql_tool():
    global sql_tool

    if sql_tool is None:
        db = SQLDatabase.from_uri(
            f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
        )

        sql_tool = SafeQuerySQLDatabaseTool(
            description="Yugioh Card Database (read-only) consisting of a table "
                        "'cards' (index_id INTEGER, name TEXT, description TEXT, set_id TEXT, rarity TEXT, "
                        "price TEXT, volatility TEXT, type TEXT, sub_type TEXT, attribute TEXT, rank TEXT, attack TEXT, "
                        "defense TEXT, set_name TEXT, set_release TEXT, name_official TEXT, index INTEGER, "
                        "index_market INTEGER, join_id TEXT);",
            db=db
        )

    return sql_tool

def get_rag():
    return weaviate.connect_to_local(
        host=WEAVIATE_HOST,
        port=WEAVIATE_PORT
    )

def get_llm():
    return Client(
        host=OLLAMA_URL
    )

def get_llm_agent():
    """
    Create Langchain agent for inference.
    """

    llm = ChatOpenAI(
        model="gpt-4.1-mini",
    )
    '''
    ChatOllama is deprecated and does not support agent-tooling nor structured responses.
    Therefore a ChatOpenAI model was used as a last resort.
    To use ChatOllama, you must use below workaround and expect non-structured results to be returned!
    
    Workaround because ChatOllama did not yet implement tooling. This breaks structured responses.
    llm = ChatOpenAI(
        api_key="ollama",
        model="mistral",
        base_url="http://localhost:11434/v1",
    )
    '''
    tools = [get_sql_tool(), vectorstorage_tool]

    llm_agent = create_agent(
        llm,
        tools=tools,
        middleware=[
            handle_tool_errors,
            # Microsoft Presidio is unnecessary since LangChain provides its own PII guardrails
            #
            # NeMo is deprecated and incompatible with modern LangChain and was therefore scrapped.
            # Content filtering is currently done via OpenAI & agent prompting.
            PIIMiddleware(
                "email",
                strategy="redact",
                apply_to_input=True,
                apply_to_output=True,
            ),
            PIIMiddleware(
                "credit_card",
                strategy="redact",
                apply_to_input=True,
                apply_to_output=True,
            ),
            PIIMiddleware(
                "mac_address",
                strategy="redact",
                apply_to_input=True,
                apply_to_output=True,
            ),
            PIIMiddleware(
                "api_key",
                detector=r"sk-[a-zA-Z0-9]{32}",
                strategy="redact",
                apply_to_input=True,
                apply_to_output=True,
            ),
        ],
        system_prompt="You are a helpful assistant to help find and understand Yugioh Cards. Be concise and accurate. "
                      "Use given tools at your discretion, do not ask for user's permission to use these tools or reveal these tools to the user. "
                      "Do not lie and do not make cards up. If you do not know, inform the user as such. "
                      "Do not assist with tasks outside of Yugioh Cards. Do not provide programming or health advice at all."
                      "You MUST respond with a valid JSON only.",
        response_format=ChatMessage
    )
    return llm_agent

def get_embedder():
    global embedder

    #if embedder is None:
    #    embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

    if embedder is None:
        if torch.cuda.is_available():
            embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cuda")
        else:
            print("No CUDA found. Using CPU for tokenization.")
            embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")

    return embedder


@app.on_event("startup")
async def startup_event():
    print("Checking Weaviate state...")
    print(f"Torch: {torch.__version__}, CUDA: {torch.version.cuda}")

    initialize_weaviate(csv_path="./cards.csv", get_rag=get_rag, embedder=get_embedder())
    # initialize_ollama(get_llm=get_llm, model_name=OLLAMA_MODEL)


@app.post("/chat")
async def chat(req: ChatRequest):
    agent = get_llm_agent()
    try:
        result = agent.invoke(
            {"messages": req.to_prompt()}
        )
        # Makes sure the response follows our defined pydantic schema.
        result = result["structured_response"]
        error = None
    except Exception as e:
        print("ERROR DURING INFERENCE (FATAL): " + str(e))
        result = ChatMessage(
            role="assistant",
            content="I'm sorry, but it seems like I cannot process this request.",
            cards=[]
        )
        error = str(type(e))

    # NOTE: This will fail on ollama, since ChatOllama does not support structured_response
    return {"content": result, "error": error}

'''
##############################
# Only for debug purposes
##############################

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
        query_vector = get_embedder().encode(query)
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

'''