import cohere
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()



# Get key from .env
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

if not COHERE_API_KEY:
    raise ValueError("⚠️ COHERE_API_KEY not found in .env")

# Initialize client
co = cohere.Client(COHERE_API_KEY)

# Simple test
resp = co.embed(
    texts=["Hello world from Cohere!"],
    model="embed-english-v3.0",
    input_type="search_document"   # or "search_query", "classification", "clustering"
)


print("Embedding length:", len(resp.embeddings[0]))
