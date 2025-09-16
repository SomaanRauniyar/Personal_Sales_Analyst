# src/csv_ingestion.py
import os
import hashlib
import pandas as pd
from dotenv import load_dotenv
from src.vector_manager import VectorDBManager
from src.config import EMBED_DIM
from src.embeddings import get_embedding

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX", "biz-analyst-1024")
NAMESPACE = os.getenv("PINECONE_NAMESPACE", "default")

# Cohere-based embedding via src.embeddings.get_embedding

# Config
MAX_ROWS = 200           # set None to ingest all
MAX_CELL_CHARS = 200     # truncate long cell values
MAX_CONTENT_CHARS = 1000 # truncate final content stored in metadata
BATCH_SIZE = 200         # upsert in batches


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def detect_encoding(path: str):
    """
    Try to detect using charset-normalizer if available, else fallback to utf-8 then latin1.
    """
    try:
        from charset_normalizer import from_path
        res = from_path(path)
        if res and len(res) > 0:
            best = res.best()
            if best:
                return best.encoding
    except Exception:
        pass

    # fallback heuristics
    for enc in ("utf-8", "ISO-8859-1", "cp1252"):
        try:
            with open(path, "r", encoding=enc) as f:
                f.read(2048)
            return enc
        except Exception:
            continue
    return "utf-8"


def row_to_text(row: pd.Series) -> str:
    """
    Deterministic single-line representation of a CSV row; truncate long values.
    """
    parts = []
    for col in row.index:
        val = row[col]
        if pd.isna(val):
            continue
        s = str(val).strip()
        if len(s) > MAX_CELL_CHARS:
            s = s[: MAX_CELL_CHARS - 3] + "..."
        parts.append(f"{col}: {s}")
    text = " | ".join(parts)
    if len(text) > MAX_CONTENT_CHARS:
        text = text[: MAX_CONTENT_CHARS - 3] + "..."
    return " ".join(text.split())  # collapse whitespace


def batch_iterable(iterable, batch_size):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def ingest_csv_to_pinecone(csv_path: str, max_rows: int = MAX_ROWS):
    print(f"📂 Ingesting CSV: {csv_path}")

    # compute deterministic file id from raw bytes
    with open(csv_path, "rb") as f:
        raw = f.read()
    file_id = sha256_bytes(raw)
    filename = os.path.basename(csv_path)

    # detect encoding
    encoding = detect_encoding(csv_path)
    print(f"⚙️ Detected encoding: {encoding}")

    # load csv
    try:
        df = pd.read_csv(csv_path, encoding=encoding)
    except Exception as e:
        print("❌ Failed to read CSV with detected encodings:", e)
        raise

    if max_rows:
        df = df.head(max_rows)
        print(f"⚡ Limiting ingestion to first {len(df)} rows for testing.")

    # init pinecone manager
    db = VectorDBManager(api_key=PINECONE_API_KEY, index_name=PINECONE_INDEX, dimension=EMBED_DIM)

    vectors = []
    for i, row in df.iterrows():
        chunk_id = f"row-{int(i)}"
        vector_id = f"{file_id}__{chunk_id}"

        row_text = row_to_text(row)
        embedding = get_embedding(row_text)

        metadata = {
            "content": row_text,
            "file_id": file_id,
            "chunk_id": chunk_id,
            "row_index": int(i),
            "filename": filename
        }

        vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})

    # upsert in batches
    total = 0
    for batch in batch_iterable(vectors, BATCH_SIZE):
        db.upsert_vectors(batch, namespace=NAMESPACE)
        total += len(batch)
        print(f"  ↳ Upserted batch of {len(batch)} vectors (total {total})")

    print(f"✅ Ingested {total} vectors from {csv_path} into Pinecone (file_id={file_id})")
    # return manifest info for programmatic use
    return {"file_id": file_id, "filename": filename, "rows": len(df), "vectors_upserted": total}


if __name__ == "__main__":
    sample_csv = r"D:\resume_project_1\csv_doc_analyst\data\sales_data_sample.csv"
    ingest_csv_to_pinecone(sample_csv)
