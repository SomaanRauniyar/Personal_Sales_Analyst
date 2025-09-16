import os
from dotenv import load_dotenv

load_dotenv()

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "biz-analyst-1024")
PINECONE_NAMESPACE = os.getenv("PINECONE_NAMESPACE", "default")

# GCP (optional for later)
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

CHUNK_OVERLAP = 100

# Cohere
COHERE_API_KEY = os.getenv("COHERE_API_KEY")
COHERE_EMBED_MODEL = os.getenv("COHERE_EMBED_MODEL", "embed-english-v3.0")
COHERE_INPUT_TYPE_DOCUMENT = os.getenv("COHERE_INPUT_TYPE_DOCUMENT", "search_document")
COHERE_INPUT_TYPE_QUERY = os.getenv("COHERE_INPUT_TYPE_QUERY", "search_query")
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))