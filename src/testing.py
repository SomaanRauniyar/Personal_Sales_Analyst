from src.vector_manager import VectorDBManager
from src.embeddings import get_embedding
import os
from dotenv import load_dotenv

# Load env variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "biz-analyst")

def main():
    db = VectorDBManager(api_key=PINECONE_API_KEY, index_name=PINECONE_INDEX)

    # Sample text
    text = "This is a test document about customer sales and revenue."
    
    # Generate embedding
    embedding = get_embedding(text)

    # Prepare vector for Pinecone
    sample_vector = [{
        "id": "test-doc-1",
        "values": embedding,
        "metadata": {"content": text}
    }]

    # Insert into Pinecone
    db.upsert_vectors(sample_vector)

    # Query back using same embedding
    results = db.query(embedding, top_k=2)
    print("🔍 Query Results:")
    for match in results['matches']:
        print(f" - ID: {match['id']}, Score: {match['score']}, Content: {match['metadata']['content']}")

if __name__ == "__main__":
    main()
