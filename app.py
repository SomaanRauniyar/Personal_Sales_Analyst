from fastapi import FastAPI, File, UploadFile, Form, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import BytesIO
import os
from dotenv import load_dotenv

from src.vector_manager import VectorDBManager
from src.embeddings import embed_chunks
from src.file_parser import parse_file
from src.query_llm import query_llm
from src.visualization import recommend_visualizations, detect_column_types
import plotly.express as px
from src.config import PINECONE_API_KEY as CFG_PINECONE_API_KEY, PINECONE_INDEX as CFG_PINECONE_INDEX

load_dotenv()

# Prefer src.config values; fall back to env for backward compatibility
PINECONE_API_KEY = CFG_PINECONE_API_KEY or os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = CFG_PINECONE_INDEX or os.getenv("PINECONE_INDEX") or os.getenv("PINECONE_INDEX_NAME")
if not PINECONE_API_KEY or not PINECONE_INDEX:
    raise ValueError("Missing Pinecone API key or index name")

app = FastAPI()
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

vector_db = VectorDBManager(api_key=PINECONE_API_KEY, index_name=PINECONE_INDEX)

# In-memory cache for uploaded DataFrames keyed by (user_id, filename)
DATA_CACHE = {}


@app.get("/")
def root():
    return {"status": "ok", "message": "Biz Analyst API running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/upload")
async def upload(file: UploadFile = File(...), user_id: str = Form(...)):
    contents = await file.read()
    filename = file.filename
    try:
        parsed = parse_file(BytesIO(contents), filename=filename)

        chunks = []
        for i, row in enumerate(parsed):
            chunks.append(
                {
                    "chunk_id": f"{filename}_chunk_{i}",
                    "file_id": filename,
                    "user_id": user_id,
                    "content": str(row),
                }
            )

        embedded_chunks = embed_chunks(chunks)

        vectors = [
            {
                "id": chunk["chunk_id"],
                "values": chunk["embedding"],
                "metadata": {
                    "content": chunk["content"],
                    "file_id": filename,
                    "user_id": user_id,
                },
            }
            for chunk in embedded_chunks
        ]

        namespace = f"user_{user_id}_{filename}"
        vector_db.upsert_vectors(vectors, namespace=namespace)

        if filename.lower().endswith(".csv"):
            df = pd.DataFrame(parsed)
            # ensure numeric columns are correctly typed (in case of stray quotes)
            for c in df.columns:
                if df[c].dtype == object:
                    coerced = pd.to_numeric(df[c], errors="ignore")
                    df[c] = coerced
            preview = df.head(5).to_dict(orient="records")
            columns = df.columns.tolist()
            # cache for later visualization queries
            DATA_CACHE[(user_id, filename)] = df
        else:
            # if parser returned list of dicts (tables from PDF/DOCX), cache as DataFrame
            if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
                df = pd.DataFrame(parsed)
                # numeric coercion
                for c in df.columns:
                    if df[c].dtype == object:
                        df[c] = pd.to_numeric(df[c], errors="ignore")
                preview = df.head(5).to_dict(orient="records")
                columns = df.columns.tolist()
                DATA_CACHE[(user_id, filename)] = df
            else:
                preview = parsed[:5]
                columns = []

        return {
            "filename": filename,
            "columns": columns,
            "preview": preview,
            "message": "File uploaded and vectors stored successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/query")
def query_text(
    user_query: str = Query(...),
    user_id: str = Query(...),
    file_id: str = Query(...)
):
    namespace = f"user_{user_id}_{file_id}"
    result = query_llm(user_query, namespace=namespace)
    return result

@app.get("/schema")
def get_schema(user_id: str = Query(...), file_id: str = Query(...)):
    df = DATA_CACHE.get((user_id, file_id))
    if df is None or df.empty:
        return {"columns": [], "types": {}}
    # prepare simple type hints
    types = {}
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            t = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[c]):
            t = "datetime"
        else:
            t = "categorical"
        types[c] = t
    return {"columns": list(df.columns), "types": types}

@app.post("/visualize_by_query")
def visualize_by_query(
    user_id: str = Form(...),
    file_id: str = Form(...),
    visualization_query: str = Form(...),
    x: str | None = Form(None),
    y: str | None = Form(None),
    aggregate: str | None = Form(None)
):
    # Prefer cached DataFrame from upload
    df = DATA_CACHE.get((user_id, file_id))

    def _parse_plot_query(q: str, df_cols):
        ql = (q or "").lower()
        chart = "bar"
        if any(k in ql for k in ["line", "time series", "timeseries"]):
            chart = "line"
        elif "scatter" in ql:
            chart = "scatter"
        elif "pie" in ql:
            chart = "pie"
        elif "hist" in ql:
            chart = "histogram"

        import re
        x = None
        y = None
        m = re.search(r"x\s*[:=]\s*([a-zA-Z0-9_\- ]+)", ql)
        if m:
            x = m.group(1).strip()
        m = re.search(r"y\s*[:=]\s*([a-zA-Z0-9_\- ]+)", ql)
        if m:
            y = m.group(1).strip()
        if x is None and y is None:
            m = re.search(r"([a-zA-Z0-9_\- ]+)\s*(vs|by)\s*([a-zA-Z0-9_\- ]+)", ql)
            if m:
                left, _, right = m.groups()
                x, y = left.strip(), right.strip()

        def _resolve(name):
            if not name:
                return None
            for c in df_cols:
                if c.lower() == name.lower():
                    return c
            return None

        x = _resolve(x)
        y = _resolve(y)
        return chart, x, y

    if df is not None and not df.empty:
        # final coercion pass to detect numeric types robustly
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = pd.to_numeric(df[c], errors="ignore")
        types = detect_column_types(df)
        # explicit overrides from form take precedence
        if not x and not y:
            chart, x, y = _parse_plot_query(visualization_query, df.columns)
        else:
            chart, _, _ = _parse_plot_query(visualization_query, df.columns)
        if x is None:
            x = (types["categorical"][0] if types["categorical"] else
                 types["datetime"][0] if types["datetime"] else df.columns[0])
        if y is None:
            y = (types["numerical"][0] if types["numerical"] else None)

        # Support multi-x (comma-separated). Validate columns
        x_list = [c.strip() for c in (x.split(",") if isinstance(x, str) else [x]) if c]
        for xv in x_list:
            if xv not in df.columns:
                return {"plots": [], "error": f"Column not found for x: {xv}"}
        if y and y not in df.columns:
            return {"plots": [], "error": f"Column not found for y: {y}"}

        agg_fn = (aggregate or "sum").lower()
        if agg_fn not in ("sum", "mean", "count"):
            agg_fn = "sum"

        figs = []
        # For multiple X columns, create one plot per X
        if chart == "line" and y and x_list:
            for xv in x_list:
                figs.append(px.line(df, x=xv, y=y, title=f"{y} over {xv}"))
        elif chart == "scatter" and y and x_list:
            for xv in x_list:
                figs.append(px.scatter(df, x=xv, y=y, title=f"{y} vs {xv}"))
        elif chart == "pie" and y and x_list:
            xv = x_list[0]
            grouped = df.groupby(xv)[y]
            if agg_fn == "mean":
                agg_df = grouped.mean().reset_index()
            elif agg_fn == "count":
                agg_df = grouped.count().reset_index()
            else:
                agg_df = grouped.sum().reset_index()
            figs.append(px.pie(agg_df, names=xv, values=y, title=f"{y} by {xv}"))
        elif chart == "histogram" and (y or x):
            col = y or x_list[0]
            figs.append(px.histogram(df, x=col, title=f"Distribution of {col}"))
        elif y and x_list:
            xv = x_list[0]
            grouped = df.groupby(xv)[y]
            if agg_fn == "mean":
                agg_df = grouped.mean().reset_index()
            elif agg_fn == "count":
                agg_df = grouped.count().reset_index()
            else:
                agg_df = grouped.sum().reset_index()
            figs.append(px.bar(agg_df, x=xv, y=y, title=f"{y} by {xv}"))
        else:
            figs = recommend_visualizations(df)

        try:
            return {"plots": [fig.to_json() for fig in figs]}
        except Exception as e:
            return {"plots": [], "error": f"Plot rendering failed: {str(e)}"}

    # Fallback to RAG-derived small dataset
    namespace = f"user_{user_id}_{file_id}"
    full_query = f"{visualization_query}\nData source: {file_id}"
    llm_result = query_llm(full_query, namespace=namespace)

    import ast
    items = []
    for src in llm_result.get("resolved_sources", []):
        raw = src.get("raw") or src.get("snippet") or ""
        try:
            parsed = ast.literal_eval(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, dict):
                items.append(parsed)
        except Exception:
            continue
    df_fb = pd.DataFrame(items) if items else pd.DataFrame()
    figs = recommend_visualizations(df_fb)
    return {"plots": [fig.to_json() for fig in figs]}
