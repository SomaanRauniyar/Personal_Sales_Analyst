import streamlit as st
import requests
import plotly.io as pio

st.set_page_config(page_title="Business Data Insight App", layout="wide")
st.title("Business Data Insight App")

# --- Step 1: User Identification ---
user_id = st.text_input("Enter your user ID (required)", key="user_id")

# --- Step 2: File Upload ---
uploaded_file = st.file_uploader(
    "Upload your data file (CSV, PDF, DOCX)",
    type=["csv", "pdf", "docx"],
    key="file_uploader"
)

data_preview = None
file_id = None

if uploaded_file and user_id:
    st.info("Uploading and analyzing your file...")
    files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
    data = {"user_id": user_id}
    try:
        resp = requests.post("http://127.0.0.1:8000/upload", files=files, data=data)
        upload_result = resp.json()
        file_id = upload_result.get("filename", uploaded_file.name)
        data_preview = upload_result.get("preview", [])
        columns = upload_result.get("columns", [])
        st.success(f"File '{file_id}' uploaded.")
        st.subheader("Data Preview")
        st.write(data_preview)
        # keep handy for plot builder
        # refresh columns via backend schema to ensure correct typing
        try:
            sch = requests.get(
                "http://127.0.0.1:8000/schema",
                params={"user_id": user_id, "file_id": file_id},
                timeout=10,
            ).json()
            columns = sch.get("columns", columns)
        except Exception:
            pass
        st.session_state["uploaded_columns"] = columns
        st.session_state["uploaded_file_id"] = file_id
        st.session_state["uploaded_user_id"] = user_id
    except Exception as e:
        st.error(f"Upload failed: {e}")

    # --- Step 3: Automatic Data Overview ---
    st.subheader("Automatic Data Overview (AI Summary)")
    if file_id:
        try:
            summary_resp = requests.post(
                "http://127.0.0.1:8000/query",
                params={
                    "user_query": "Give me an overview of the data",
                    "user_id": user_id,
                    "file_id": file_id
                }
            )
            st.write(summary_resp.json().get("answer", "No summary returned."))
        except Exception as e:
            st.warning(f"Overview unavailable: {e}")
    else:
        st.warning("Upload a file first before querying.")

    # --- Step 4: Automatic Key Plots (LLM + recommended plots) ---
    st.subheader("Automatic Key Plots")
    if file_id:
        try:
            plot_resp = requests.post(
                "http://127.0.0.1:8000/visualize_by_query",
                data={
                    "user_id": user_id,
                    "file_id": file_id,
                    "visualization_query": "Show the most important trends and distributions in my data"
                },
            )
            plot_jsons = plot_resp.json().get("plots", [])
            if plot_jsons:
                for i, plot_json in enumerate(plot_jsons):
                    fig = pio.from_json(plot_json)
                    st.plotly_chart(fig, use_container_width=True, key=f"auto_plot_{i}")
            else:
                st.write("No automatic plots returned.")
        except Exception as e:
            st.warning(f"Auto-plot error: {e}")
    else:
        st.warning("Upload a file first before visualizing.")

    # --- Step 5: Manual Q&A ---
    st.subheader("Ask a question about your data")
    user_query = st.text_input("Enter your query", key="user_query_in")
    if user_query:
        if file_id:
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/query",
                    params={
                        "user_query": user_query,
                        "user_id": user_id,
                        "file_id": file_id
                    }
                )
                st.write(response.json().get("answer", "No response."))
            except Exception as e:
                st.error(f"Query failed: {e}")
        else:
            st.warning("Upload a file first before querying.")

    # --- Step 6: Custom Plots ---
    st.subheader("Request a custom plot")
    plot_query = st.text_input("Describe the plot you want", key="plot_query")
    if plot_query:
        if file_id:
            try:
                custom_plot_resp = requests.post(
                    "http://127.0.0.1:8000/visualize_by_query",
                    data={
                        "user_id": user_id,
                        "file_id": file_id,
                        "visualization_query": plot_query
                    },
                )
                custom_plot_jsons = custom_plot_resp.json().get("plots", [])
                if custom_plot_jsons:
                    for i, plot_json in enumerate(custom_plot_jsons):
                        fig = pio.from_json(plot_json)
                        st.plotly_chart(fig, use_container_width=True, key=f"custom_plot_{i}")
                else:
                    st.write("No custom plots returned.")
            except Exception as e:
                st.error(f"Custom plot error: {e}")
        else:
            st.warning("Upload a file first before requesting a plot.")

    # --- Optional: Modal/Builder for custom plots ---
    st.subheader("Custom Plot Builder (guided)")
    def _normalize_columns(value):
        import re, ast, json
        cols = value
        # strings that may encode a list
        if isinstance(cols, str):
            s = cols.strip()
            # try JSON list or Python list literal
            if (s.startswith("[") and s.endswith("]")) or (s.startswith("(") and s.endswith(")")):
                try:
                    return [str(x) for x in json.loads(s.replace("(", "[").replace(")", "]"))]
                except Exception:
                    try:
                        parsed = ast.literal_eval(s)
                        if isinstance(parsed, (list, tuple)):
                            return [str(x) for x in list(parsed)]
                    except Exception:
                        pass
            # split by commas or any whitespace (tabs/newlines too)
            tokens = [t for t in re.split(r"[\s,]+", s) if t]
            return tokens
        # list with single combined string
        if isinstance(cols, list) and len(cols) == 1 and isinstance(cols[0], str):
            s = cols[0]
            return _normalize_columns(s)
        return cols or []

    cols_available = _normalize_columns(st.session_state.get("uploaded_columns", []))
    fid = st.session_state.get("uploaded_file_id")
    uid = st.session_state.get("uploaded_user_id")

    if fid and uid:
        # if not present, fetch schema from backend cache
        if not cols_available:
            try:
                sch = requests.get(
                    "http://127.0.0.1:8000/schema",
                    params={"user_id": uid, "file_id": fid},
                    timeout=10,
                ).json()
                cols_available = sch.get("columns", [])
            except Exception:
                cols_available = cols_available or []
        with st.expander("Open Plot Builder"):
            chart_type = st.selectbox("Chart type", ["bar", "line", "scatter", "pie", "histogram"], index=0, key="chart_type_sel")
            # allow selecting multiple features for X axis
            x_cols = st.multiselect("X axis (one or more)", cols_available, default=cols_available[:1] if cols_available else [])
            y_col = st.selectbox("Y axis", cols_available if cols_available else [""], key="y_col_sel")
            agg = st.selectbox("Aggregation (for bar/pie)", ["sum", "mean", "count", "none"], index=0, key="agg_sel")
            build_btn = st.button("Build & Plot", key="build_plot_btn")
            if build_btn:
                parts = [f"{chart_type}"]
                if x_cols:
                    parts.append(f"x: {', '.join(x_cols)}")
                if y_col:
                    parts.append(f"y: {y_col}")
                if agg and agg != "none":
                    parts.append(f"aggregate: {agg}")
                built_query = " ".join(parts)
                try:
                    resp = requests.post(
                        "http://127.0.0.1:8000/visualize_by_query",
                        data={
                            "user_id": uid,
                            "file_id": fid,
                            "visualization_query": built_query,
                            "x": ",".join(x_cols) if x_cols else None,
                            "y": y_col or None,
                            "aggregate": None if agg == "none" else agg,
                        },
                    )
                    # Handle non-JSON or error payloads gracefully
                    try:
                        bjson = resp.json()
                    except Exception:
                        st.error(f"Server error: {resp.text[:200]}")
                        bjson = {"plots": [], "error": "Invalid server response"}
                    plot_jsons = bjson.get("plots", [])
                    err = bjson.get("error")
                    if plot_jsons:
                        for i, plot_json in enumerate(plot_jsons):
                            fig = pio.from_json(plot_json)
                            st.plotly_chart(fig, use_container_width=True, key=f"builder_plot_{i}")
                    else:
                        st.info("No plots returned. Try adjusting X/Y or chart type.")
                        if err:
                            st.caption(f"Backend note: {err}")
                except Exception as e:
                    st.error(f"Builder plot error: {e}")
    else:
        st.caption("Upload a file to enable the Plot Builder.")
else:
    st.write("To begin, enter your user ID and upload a CSV, PDF, or DOCX file.")
