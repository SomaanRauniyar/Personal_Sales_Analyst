from sentence_transformers import SentenceTransformer

# Load HuggingFace model once
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def get_embedding(text: str):
    """
    HuggingFace model se ek text ka embedding nikalta hai
    """
    return embedder.encode(text).tolist()

def embed_chunks(chunks):
    """
    Har chunk ke liye embedding add karta hai (batch mode for speed)
    """
    # Extract all texts for batch embedding
    texts = [chunk["content"] for chunk in chunks]
    
    # Batch encode all texts at once (adjust batch_size as needed)
    vectors = embedder.encode(texts, batch_size=32)
    
    # Assign embeddings back to chunks
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = vectors[i].tolist()
    
    return chunks