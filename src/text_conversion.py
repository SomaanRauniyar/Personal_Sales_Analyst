# src/text_conversion.py
"""
Convert parsed rows / chunks into deterministic, human-friendly text ready for embeddings.
Includes:
- row_to_text() for pandas rows
- sanitize_text() to fix escape sequences and collapse whitespace
- chunk_text_normalize() to prepend metadata and enforce length limits
- convert_chunks_for_embedding() to accept a list of chunk dicts or pandas.Series and return
  standardized dicts: {'chunk_id','file_id','text','metadata'}
"""

from typing import List, Dict, Any, Optional, Union
import pandas as pd
import re
import codecs

# Tunables
MAX_CELL_CHARS = 200        # max chars per CSV cell before truncation
MAX_CHUNK_CHARS = 2000      # max characters per chunk text stored for embedding/context
MAX_SNIPPET = 400           # snippet size to show in UI

def sanitize_text(s: Optional[str]) -> str:
    """
    Robust cleaning for:
    - literal escape sequences like '\\x84'
    - mojibake (e.g. 'Â' artifacts from wrong decoding)
    - non-printable control chars
    Returns normalized, whitespace-collapsed unicode string.
    """
    if s is None:
        return ""
    orig = str(s)

    # 1) If the string contains explicit backslash-x escapes, decode them first
    #    e.g. "Berguvsv\\x84gen" -> try to interpret the escape.
    if r"\x" in orig:
        try:
            t = codecs.decode(orig, "unicode_escape")
        except Exception:
            t = orig
    else:
        t = orig

    # 2) Replace leftover \xNN patterns by mapping the byte to cp1252 char
    #    This handles cases where sequences remained like "\x84"
    def _repl_hex(m):
        try:
            b = bytes([int(m.group(1), 16)])
            return b.decode("cp1252", errors="replace")
        except Exception:
            return ""
    t = re.sub(r"\\x([0-9A-Fa-f]{2})", _repl_hex, t)

    # 3) Fix common mojibake: if we see sequences like 'Ã' or 'Â' mixed with other text,
    #    try a latin1->utf-8 re-decode which often repairs utf8 decoded as latin1.
    #    Only attempt if it looks like mojibake, to avoid corrupting already-correct text.
    if re.search(r"[ÃÂ]", t):
        try:
            candidate = t.encode("latin1", errors="replace").decode("utf-8", errors="replace")
            # keep the candidate only if it improves (fewer replacement markers or fewer odd chars)
            if sum(1 for ch in candidate if ch == "�") <= sum(1 for ch in t if ch == "�"):
                t = candidate
        except Exception:
            pass

    # 4) Remove non-printable control characters and collapse whitespace
    t = re.sub(r"[^\x09\x0A\x0D\x20-\x7E\x80-\xFF]", " ", t)
    t = " ".join(t.split())
    return t.strip()

def row_to_text(row: pd.Series, max_cell_chars: int = MAX_CELL_CHARS) -> str:
    """
    Convert a pandas Series (row) into a single-line deterministic string:
      "COL1: val1 | COL2: val2 | ..."
    Truncates cells longer than max_cell_chars and drops NaNs.
    """
    parts = []
    for col in row.index:
        val = row[col]
        if pd.isna(val):
            continue
        s = str(val).strip()
        if len(s) > max_cell_chars:
            s = s[: max_cell_chars - 3] + "..."
        parts.append(f"{col}: {s}")
    text = " | ".join(parts)
    return sanitize_text(text)[:MAX_CHUNK_CHARS]

def chunk_text_normalize(text: str, prefix_meta: Optional[Dict[str, Any]] = None) -> str:
    """
    Normalize whitespace and optionally prepend metadata as 'key:value | ...'.
    Enforce MAX_CHUNK_CHARS limit.
    """
    t = sanitize_text(text)
    if prefix_meta:
        meta = " | ".join([f"{k}:{v}" for k, v in prefix_meta.items() if v is not None])
        t = f"{meta} | {t}"
    if len(t) > MAX_CHUNK_CHARS:
        t = t[: MAX_CHUNK_CHARS - 3] + "..."
    return t

def _make_snippet(text: str, n: int = MAX_SNIPPET) -> str:
    """Return a short snippet for UI from text."""
    if not text:
        return ""
    return text[:n] + ("..." if len(text) > n else "")

def convert_chunks_for_embedding(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Input: list of chunk dicts. Each chunk may be:
      - {'file_id', 'chunk_id', 'content' or 'text'} OR
      - a pandas.Series as 'content' (row)
    Output: list of dicts:
      {
        'chunk_id': ...,
        'file_id': ...,
        'text': <string ready for embedding>,
        'metadata': { ... }   # includes snippet, original_meta fields
      }
    """
    out = []
    for c in chunks:
        orig_meta = {}
        file_id = None
        chunk_id = None
        # Case: user passed a pandas Series directly
        if isinstance(c, pd.Series):
            orig_meta = {}
            file_id = None
            chunk_id = f"row-{int(c.name)}" if c.name is not None else None
            content = row_to_text(c)
        else:
            # assume dict-like
            if isinstance(c, dict):
                # preserve original metadata dict if present
                orig_meta = dict(c.get("metadata", {})) if c.get("metadata") is not None else {}
                # prefer explicit keys in dict, else metadata fallback
                file_id = c.get("file_id") if c.get("file_id") is not None else orig_meta.get("file_id")
                chunk_id = c.get("chunk_id") if c.get("chunk_id") is not None else orig_meta.get("chunk_id") or c.get("id")
                # retrieve content safely without evaluating a Series truthiness
                content_obj = None
                if "content" in c:
                    content_obj = c["content"]
                elif "text" in c:
                    content_obj = c["text"]
                elif orig_meta.get("content") is not None:
                    content_obj = orig_meta.get("content")
                else:
                    content_obj = ""

                # if the content_obj is a pandas Series, convert appropriately
                if isinstance(content_obj, pd.Series):
                    content = row_to_text(content_obj)
                else:
                    content = sanitize_text(str(content_obj))
            else:
                # unexpected type — stringify safely
                orig_meta = {}
                content = sanitize_text(str(c))
                file_id = None
                chunk_id = None

        # Prepare prefix metadata for context (keep small)
        prefix_meta = {}
        if file_id:
            prefix_meta["file_id"] = file_id
        if chunk_id:
            prefix_meta["chunk_id"] = chunk_id
        # normalize text with metadata and length guard
        text_for_embedding = chunk_text_normalize(content, prefix_meta=prefix_meta)

        metadata = {"snippet": _make_snippet(text_for_embedding, n=MAX_SNIPPET)}
        # preserve and merge original metadata keys (without huge fields)
        for k, v in orig_meta.items():
            if k not in ("content", "text"):
                metadata[k] = v

        out.append({
            "chunk_id": chunk_id,
            "file_id": file_id,
            "text": text_for_embedding,
            "metadata": metadata
        })
    return out

# quick self-test when run directly
if __name__ == "__main__":
    import pandas as pd
    # sample row as pandas Series
    s = pd.Series({"ORDERNUMBER": 10112, "SALES": 7209.11, "CUSTOMERNAME": "Volvo Model Replicas, Co", "ADDRESS": "Berguvsv\\x84gen 8"})
    s.name = 27  # simulate row index
    out = convert_chunks_for_embedding([{"file_id": "file123", "chunk_id": "row-27", "content": s}])
    assert len(out) == 1
    item = out[0]
    print("TEXT:", item["text"])
    print("METADATA:", item["metadata"])
    # ensure snippet length
    assert "snippet" in item["metadata"]
    assert len(item["text"]) <= MAX_CHUNK_CHARS
    print("Self-test passed.")