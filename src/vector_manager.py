from pinecone import Pinecone, ServerlessSpec
from concurrent.futures import ThreadPoolExecutor

class VectorDBManager:
    def __init__(self, api_key, index_name, dimension=384, metric="cosine"):
        """
        Pinecone ke saath vector database manager banata hai.
        Index ko create karega agar exist nahi karta ho.
        """
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name

        # Sab indexes ka list nikaalo
        existing_indexes = [i.name for i in self.pc.list_indexes()]

        # Agar index nahi hai toh create karo
        if self.index_name not in existing_indexes:
            print(f"📌 Creating Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric=metric,
                spec=ServerlessSpec(  # 👈 New SDK ke liye mandatory
                    cloud="aws",
                    region="us-east-1"
                )
            )
        else:
            print(f"✅ Index '{self.index_name}' already exists!")

        # Index attach karo
        self.index = self.pc.Index(self.index_name)

    def upsert_vectors(self, vectors, namespace="default", batch_size=20, max_workers=4):
        """
        Upload embeddings to Pinecone in parallel batches to improve speed.
        Args:
            vectors: list of dicts [{id, values, metadata}]
            namespace: Pinecone namespace string
            batch_size: number of vectors per batch
            max_workers: number of parallel upsert threads
        """
        n = len(vectors)
        batches = [vectors[i:i + batch_size] for i in range(0, n, batch_size)]

        def upsert_batch(batch):
            self.index.upsert(vectors=batch, namespace=namespace)
            print(f"✅ Batch upserted {len(batch)} vectors into '{self.index_name}' [namespace={namespace}]")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(upsert_batch, batches)

    def query(self, vector, top_k=5, namespace="default"):
        """
        Similarity search given vector against Pinecone index.
        """
        result = self.index.query(
            vector=vector,
            top_k=top_k,
            include_metadata=True,
            namespace=namespace
        )
        return result


# 🧪 For local testing
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()

    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX", "biz-analyst")

    db = VectorDBManager(api_key=PINECONE_API_KEY, index_name=PINECONE_INDEX)

    sample_vectors = [
        {"id": "vec1", "values": [0.1] * 384, "metadata": {"content": "Hello world!"}}
    ]

    db.upsert_vectors(sample_vectors)

    q = db.query([0.1] * 384, top_k=2)
    print(q)