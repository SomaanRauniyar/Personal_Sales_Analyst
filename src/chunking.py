# src/chunking.py

import io
import csv
from transformers import AutoTokenizer
from src.config import CHUNK_OVERLAP


# HuggingFace lightweight tokenizer (local + deployable)
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

def num_tokens_from_string(text: str) -> int:
    """
    Count number of tokens in a string using HuggingFace tokenizer.
    """
    tokens = tokenizer.encode(text, add_special_tokens=False)
    return len(tokens)


def calculate_chunk_params(total_tokens: int):
    """
    Dynamically adjust chunk_size based on file size.
    """
    if total_tokens < 2000:  
        chunk_size = 200
    elif total_tokens < 10000:
        chunk_size = 500
    else:
        chunk_size = 1000

    overlap = CHUNK_OVERLAP if CHUNK_OVERLAP < chunk_size else int(chunk_size / 5)
    return chunk_size, overlap


def rolling_window_chunk(text: str):
    """
    Rolling window based smart chunking for text (PDF, Word, TXT).
    Maintains semantic continuity with overlap.
    """
    tokens = tokenizer.encode(text, add_special_tokens=False)
    total_tokens = len(tokens)

    chunk_size, overlap = calculate_chunk_params(total_tokens)

    chunks = []
    start = 0
    chunk_id = 0

    while start < total_tokens:
        end = min(start + chunk_size, total_tokens)
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens)

        chunks.append({
            "chunk_id": chunk_id,
            "content": chunk_text,
            "start_token": start,
            "end_token": end
        })
        chunk_id += 1
        start += (chunk_size - overlap)

    return chunks


def csv_chunker(file_obj):
    """
    Chunk CSV rows directly from in-memory BytesIO/StringIO.
    Groups rows until token limit (dynamic) is reached.
    """
    file_obj.seek(0)
    reader = csv.reader(io.TextIOWrapper(file_obj, encoding="utf-8"))

    header = next(reader)  # keep header for context
    chunks = []
    current_chunk = []
    current_tokens = 0
    chunk_id = 0

    for row in reader:
        row_text = ", ".join(row)
        row_tokens = num_tokens_from_string(row_text)

        if current_tokens + row_tokens > 500:  # default ~500 tokens per chunk
            chunks.append({
                "chunk_id": chunk_id,
                "content": "\n".join(current_chunk),
            })
            chunk_id += 1
            current_chunk = []
            current_tokens = 0

        current_chunk.append(row_text)
        current_tokens += row_tokens

    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "content": "\n".join(current_chunk),
        })

    return chunks


def smart_chunk(parsed_text, file_type, file_obj=None):
    """
    Decide chunking strategy based on file type.
    """
    if file_type == "csv" and file_obj:
        return csv_chunker(file_obj)
    else:
        return rolling_window_chunk(parsed_text)


if __name__ == "__main__":
    # Example for text input
    sample_text = """Artificial Intelligence is transforming industries.
    It has applications in healthcare, finance, education, and beyond.
    Contextual embeddings improve information retrieval systems significantly."""

    chunks = rolling_window_chunk(sample_text)
    for c in chunks:
        print(c)
