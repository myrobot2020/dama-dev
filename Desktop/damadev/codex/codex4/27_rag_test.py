import lancedb
import pandas as pd
from sentence_transformers import SentenceTransformer
from pathlib import Path
import json
import requests

# Config
REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "data" / "damalance"
MODEL_NAME = 'all-MiniLM-L6-v2'
OLLAMA_URL = "http://localhost:11434/api/generate"

def rag_query(question: str, k: int = 3):
    print(f"\n[QUERY] {question}")

    # 1. Embed question
    model = SentenceTransformer(MODEL_NAME)
    q_vec = model.encode(question).tolist()

    # 2. Search LanceDB
    db = lancedb.connect(str(DB_PATH))
    table = db.open_table("sutta_knowledge")

    results = table.search(q_vec).limit(k).to_pandas()

    context_parts = []
    print("\n[RETRIEVED CHUNKS]")
    for i, row in results.iterrows():
        print(f" {i+1}. [{row['sutta_id']} {row['type']}] (dist: {row['_distance']:.3f})")
        context_parts.append(f"Source {row['sutta_id']} ({row['type']}):\n{row['text']}")

    context = "\n\n".join(context_parts)

    # 3. Prompt Ollama
    system_prompt = """You are a Buddhist scholar assistant.
    Use the provided sutta and commentary segments to answer the question.
    If the answer is not in the segments, say you don't know based on these sources.
    Keep it concise."""

    prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"

    payload = {
        "model": "mistral:instruct",
        "prompt": f"{system_prompt}\n\n{prompt}",
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        answer = response.json().get("response", "No response from Ollama")
        print("\n[DAMA CHAT ANSWER]")
        print(answer)
    except Exception as e:
        print(f"❌ Ollama Error: {e}")

if __name__ == "__main__":
    # Test queries based on the 5 AN suttas (4.20, 7.7.65-67, 20.1.95)
    rag_query("What does the Buddha say about the breaking up of the body?")
    rag_query("How many types of wealth are mentioned in AN 7.7.65?")
