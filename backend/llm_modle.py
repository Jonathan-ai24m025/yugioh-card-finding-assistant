import json
import logging
from typing import List, Dict
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CardCandidate(BaseModel):
    name: str
    description: str
    tags: List[str] = []
    price: float = 0.0

class LLMResult(BaseModel):
    query: str
    results: List[Dict]
    note: str = ""

# choose small model for testing (can switch later)
MODEL_NAME = "gpt2"
logger.info(f"LLM module: using MODEL_NAME = {MODEL_NAME}")

# load model (keep try/except)
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)
    generator = pipeline("text-generation", model=model, tokenizer=tokenizer, device_map="auto")
    logger.info("Model loaded.")
except Exception:
    logger.exception("Model load failed - LLM will be unavailable.")
    generator = None

# Improved system prompt: force ONLY JSON and fallback
SYSTEM_PROMPT = """You are a Yu-Gi-Oh! assistant.
Given a user query and a list of candidate cards, recommend up to 3 relevant cards.

**VERY IMPORTANT**:
1) You MUST output **ONLY** one single valid JSON object and nothing else.
2) The JSON must use this exact schema (field names must match):
{"query":"...", "results":[{"name":"", "reason":"", "match_tags":[], "score":0.0}], "note":""}
3) Do not output any explanatory text, bullet points, or code fences.
4) If you cannot produce a valid JSON for any reason, output exactly:
{"error":"cannot produce JSON"}

Now produce the JSON for the following input.
"""

# Robust JSON extraction helper
def extract_first_valid_json(s: str) -> str | None:
    """
    Find balanced-brace JSON substrings and return the first that json.loads accepts.
    Tries all balanced {} substrings in order of appearance (short -> long).
    """
    starts = []
    results = []
    for i, ch in enumerate(s):
        if ch == '{':
            starts.append(i)
        elif ch == '}' and starts:
            # pair each start that is <= current start (we want substrings)
            start = starts.pop()  # last unmatched '{'
            candidate = s[start:i+1]
            results.append(candidate)
            # continue scanning (this simple stack finds nested segments)
    # Try the results from longest to shortest (greedy)
    results_sorted = sorted(results, key=len, reverse=True)
    for cand in results_sorted:
        try:
            parsed = json.loads(cand)
            return cand
        except Exception:
            continue
    # fallback: try to find any {...} using regex-like approach (last resort)
    # try expanding from first '{' to last '}' and attempt parsing
    first = s.find('{')
    last = s.rfind('}')
    if first != -1 and last != -1 and last > first:
        try:
            parsed = json.loads(s[first:last+1])
            return s[first:last+1]
        except Exception:
            return None
    return None

# call function
def call_llm(query: str, candidates: List[Dict]) -> Dict:
    if generator is None:
        return {"error": "LLM not available (model failed to load)"}

    # Basic guard
    if not isinstance(candidates, list) or len(candidates) == 0:
        return {"error": "candidates must be a non-empty list"}

    prompt = SYSTEM_PROMPT + f"\nUser query: {query}\nCandidates:\n" + json.dumps(candidates, indent=2) + "\nResult:\n"
    try:
        # deterministic; set temperature/sampling off
        out = generator(prompt, max_new_tokens=256, do_sample=False)
        output = out[0].get("generated_text", "") if isinstance(out, (list, tuple)) else str(out)
    except Exception as e:
        logger.exception("Generation error")
        return {"error": f"model generation error: {str(e)}"}

    # Try to extract valid JSON
    json_text = extract_first_valid_json(output)
    if json_text is None:
        return {"error": "Failed to parse JSON", "raw_text": output}

    try:
        parsed = json.loads(json_text)
    except json.JSONDecodeError:
        return {"error": "Failed to parse JSON after extraction", "raw_text": json_text}

    # Anti-hallucination: ensure names are in candidates
    candidate_names = {c["name"] for c in candidates if "name" in c}
    for r in parsed.get("results", []):
        if r.get("name") not in candidate_names:
            logger.warning("Model referenced a card not in candidates: %s", r.get("name"))
            return {"error": "Model referenced card not in candidates", "raw_text": output}

    # Validate using pydantic
    try:
        validated = LLMResult(**parsed)
        return validated.dict()
    except Exception:
        parsed.setdefault("note", "Warning: output did not fully validate against schema.")
        return parsed
