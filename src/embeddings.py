import os
from dotenv import load_dotenv
import cohere

# Load env once
load_dotenv()

# Cohere configuration
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_EMBED_MODEL = os.getenv("COHERE_EMBED_MODEL", "embed-english-v3.0")
# Use "search_document" for corpus/doc vectors; use "search_query" when embedding queries
COHERE_INPUT_TYPE_DOCUMENT = os.getenv("COHERE_INPUT_TYPE_DOCUMENT", "search_document")
COHERE_INPUT_TYPE_QUERY = os.getenv("COHERE_INPUT_TYPE_QUERY", "search_query")

if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY not set in environment")

# Initialize Cohere client once
_co = cohere.Client(COHERE_API_KEY)

def get_embedding(text: str, *, is_query: bool = False):
    """
    Return embedding vector for a given text using Cohere embeddings API.
    Set is_query=True when embedding user queries to improve retrieval quality.
    """
    input_type = COHERE_INPUT_TYPE_QUERY if is_query else COHERE_INPUT_TYPE_DOCUMENT
    resp = _co.embed(
        texts=[text],
        model=COHERE_EMBED_MODEL,
        input_type=input_type,
    )
    return resp.embeddings[0]

def embed_chunks(chunks):
    """
    Add embedding for each chunk in batch using Cohere embeddings API.
    Expects each chunk to contain key "content".
    """
    if not chunks:
        return chunks

    texts = [chunk.get("content", "") for chunk in chunks]
    resp = _co.embed(
        texts=texts,
        model=COHERE_EMBED_MODEL,
        input_type=COHERE_INPUT_TYPE_DOCUMENT,
    )
    vectors = resp.embeddings

    for i, chunk in enumerate(chunks):
        chunk["embedding"] = vectors[i]

    return chunks