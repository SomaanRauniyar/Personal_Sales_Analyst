# src/utils.py

import os
import psutil
import logging
import uuid
import time


def get_available_memory_gb():
    """
    Returns available system memory in gigabytes.
    Useful to dynamically manage chunk sizes or monitor resource usage.
    """
    mem = psutil.virtual_memory()
    return mem.available / (1024 ** 3)


def generate_chunk_id(file_id, index):
    """
    Generates a unique chunk ID combining the file ID, row/index, and a random UUID suffix.
    Useful for traceability in vector DB and query referencing.
    """
    unique_suffix = uuid.uuid4().hex[:8]
    return f"{file_id}-chunk-{index}-{unique_suffix}"


def setup_logger(name="doc_analyst", level=logging.INFO):
    """
    Sets up a logger instance with timestamps and level info.
    Use this for consistent logging throughout your app backend.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def profile_time(func):
    """
    Decorator for timing function executions for profiling and debugging.
    Prints execution time on function completion.
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"[PROFILE] {func.__name__} executed in {elapsed:.3f} seconds")
        return result
    return wrapper


def validate_dataframe(df, min_rows=1):
    """
    Simple check if an object is a valid pandas DataFrame with data.
    Returns True if DataFrame has >= min_rows rows.
    """
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        return False
    if df.empty or df.shape[0] < min_rows:
        return False
    return True


def ensure_dir_exists(path):
    """
    Utility to create directories if they don't exist.
    Useful for caching or result storage paths.
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
        return True
    return False


def sanitize_text(text):
    """
    A safe wrapper around text cleaning utilities (can extend with your text_conversion.py).
    """
    return str(text).strip()


# Example usage:
if __name__ == "__main__":
    logger = setup_logger()
    logger.info("Utils module loaded")

    print(f"Available memory: {get_available_memory_gb():.2f} GB")
    print(generate_chunk_id("file123", 44))

