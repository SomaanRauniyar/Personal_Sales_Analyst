import streamlit as st
import requests
import plotly.io as pio
from pathlib import Path
import os

# Get API URL from environment variable (for production) or default to localhost
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def load_custom_css():
    """Load custom CSS styling"""
    css_file = Path("app/static/style.css")
    if css_file.exists():
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Fallback inline CSS if file doesn't exist
        st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .data-card {
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border: 1px solid rgba(0,0,0,0.05);
        }
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        </style>
        """, unsafe_allow_html=True)

st.set_page_config(
    page_title="DataInsight Pro", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
load_custom_css()

# Main Header
st.markdown("""
<div class="main-header fade-in">
    <h1>📊 DataInsight Pro</h1>
    <p>Transform your data into actionable insights with AI-powered analytics</p>
</div>
""", unsafe_allow_html=True)

# Sidebar navigation and inputs
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 1rem 0;">
        <h2 style="color: var(--primary-color); margin-bottom: 0.5rem;">🚀 Quick Start</h2>
        <p style="color: var(--text-secondary); font-size: 0.9rem;">Upload your data and start analyzing</p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = st.text_input(
        "👤 User ID", 
        placeholder="Enter your unique ID",
        key="user_id",
        help="This helps us organize your data securely"
    )
    
    uploaded_file = st.file_uploader(
        "📁 Upload Data File",
        type=["csv", "pdf", "docx", "xlsx"],
        key="file_uploader",
        help="Supported formats: CSV, PDF, DOCX, Excel"
    )
    
    st.markdown("---")
    
    # Feature highlights
    st.markdown("""
    <div style="background: var(--bg-secondary); padding: 1rem; border-radius: var(--radius-lg); margin: 1rem 0;">
        <h4 style="color: var(--primary-color); margin-bottom: 0.75rem;">✨ Features</h4>
        <ul style="color: var(--text-secondary); font-size: 0.85rem; margin: 0; padding-left: 1.2rem;">
            <li>AI-powered data analysis</li>
            <li>Automatic visualization</li>
            <li>Natural language queries</li>
            <li>Custom plot builder</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; margin-top: 2rem;">
        <p style="color: var(--text-muted); font-size: 0.8rem;">Built with ❤️ for modern analytics</p>
    </div>
    """, unsafe_allow_html=True)

# Tabs for main app sections
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Overview", "📈 Analytics", "🤖 AI Assistant", "🎨 Visualizations"]
)

file_id = None
data_preview = None
columns = []
upload_error = None

if uploaded_file and user_id:
    with st.spinner("Uploading and analyzing your file..."):
        files = {"file": (uploaded_file.name, uploaded_file, uploaded_file.type)}
        data = {"user_id": user_id}
        try:
            resp = requests.post(f"{API_URL}/upload", files=files, data=data)
            upload_result = resp.json()
            file_id = upload_result.get("filename", uploaded_file.name)
            data_preview = upload_result.get("preview", [])
            columns = upload_result.get("columns", [])
            # Store to session state for later use
            st.session_state["uploaded_columns"] = columns
            st.session_state["uploaded_file_id"] = file_id
            st.session_state["uploaded_user_id"] = user_id
        except Exception as e:
            upload_error = str(e)

with tab1:
    st.markdown("""
    <div class="data-card fade-in">
        <h2 style="color: var(--primary-color); margin-bottom: 1rem;">📊 Data Overview</h2>
    </div>
    """, unsafe_allow_html=True)
    
    if upload_error:
        st.error(f"❌ Upload failed: {upload_error}")
    elif data_preview:
        # Success message with file info
        st.markdown(f"""
        <div class="status-indicator status-success" style="margin-bottom: 1rem;">
            ✅ File '{file_id}' uploaded successfully
        </div>
        """, unsafe_allow_html=True)
        
        # Data preview in a styled container
        st.markdown("""
        <div class="data-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">📋 Data Preview</h3>
        </div>
        """, unsafe_allow_html=True)
        st.dataframe(data_preview, width='stretch')
        
        try:
            sch = requests.get(
                f"{API_URL}/schema",
                params={"user_id": user_id, "file_id": file_id},
                timeout=10,
            ).json()
            columns = sch.get("columns", columns)
            st.session_state["uploaded_columns"] = columns
            
            # Show column info
            if columns:
                st.markdown("""
                <div class="data-card">
                    <h3 style="color: var(--text-primary); margin-bottom: 1rem;">📊 Dataset Schema</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Columns", len(columns))
                with col2:
                    st.metric("Data Types", len(set(sch.get("types", {}).values())))
                
                # Column types display
                types = sch.get("types", {})
                if types:
                    st.markdown("**Column Information:**")
                    for col, col_type in types.items():
                        st.markdown(f"• **{col}**: `{col_type}`")
                        
        except Exception:
            pass
    else:
        st.info("👆 Upload a file above to preview your data")

    # AI Summary Section
    st.markdown("""
    <div class="data-card">
        <h3 style="color: var(--text-primary); margin-bottom: 1rem;">🤖 AI-Powered Data Summary</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if file_id:
        with st.spinner("🧠 AI is analyzing your data..."):
            try:
                summary_resp = requests.post(
                    f"{API_URL}/query",
                    params={
                        "user_query": "Give me a comprehensive overview of this dataset, including key insights, patterns, and recommendations",
                        "user_id": user_id,
                        "file_id": file_id
                    }
                )
                summary = summary_resp.json().get("answer", "No summary returned.")
                
                st.markdown(f"""
                <div class="data-card" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);">
                    <div style="color: var(--text-primary); line-height: 1.6;">
                        {summary}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"⚠️ AI summary unavailable: {e}")
    else:
        st.caption("📁 Upload a file to generate an AI-powered data summary")

with tab2:
    st.markdown("""
    <div class="data-card fade-in">
        <h2 style="color: var(--primary-color); margin-bottom: 1rem;">📈 Smart Analytics</h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">AI-powered insights and automatic visualizations</p>
    </div>
    """, unsafe_allow_html=True)
    
    if file_id:
        with st.spinner("🔍 Analyzing patterns and generating insights..."):
            try:
                plot_resp = requests.post(
                    f"{API_URL}/visualize_by_query",
                    data={
                        "user_id": user_id,
                        "file_id": file_id,
                        "visualization_query": "Show the most important trends, distributions, and key insights in my data with professional visualizations"
                    },
                )
                plot_jsons = plot_resp.json().get("plots", [])
                if plot_jsons:
                    st.markdown("""
                    <div class="data-card">
                        <h3 style="color: var(--text-primary); margin-bottom: 1rem;">📊 Key Insights & Trends</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for i, plot_json in enumerate(plot_jsons):
                        fig = pio.from_json(plot_json)
                        # Update plot styling for professional look
                        fig.update_layout(
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(family="Inter, sans-serif", size=12),
                            title_font=dict(size=16, color='#1f2937'),
                            margin=dict(l=20, r=20, t=40, b=20)
                        )
                        st.plotly_chart(fig, width='stretch', key=f"auto_plot_{i}")
                else:
                    st.info("📊 No automatic insights available for this dataset.")
            except Exception as e:
                st.warning(f"⚠️ Analytics error: {e}")
    else:
        st.info("📁 Upload a file to unlock AI-powered analytics and insights")

with tab3:
    st.markdown("""
    <div class="data-card fade-in">
        <h2 style="color: var(--primary-color); margin-bottom: 1rem;">🤖 AI Assistant</h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">Ask questions about your data in natural language</p>
    </div>
    """, unsafe_allow_html=True)
    
    if file_id:
        # Example questions
        st.markdown("""
        <div class="data-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">💡 Try asking:</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 0.5rem;">
                <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: var(--radius-md); font-size: 0.9rem; color: var(--text-secondary);">
                    "What are the main trends in this data?"
                </div>
                <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: var(--radius-md); font-size: 0.9rem; color: var(--text-secondary);">
                    "Which category has the highest values?"
                </div>
                <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: var(--radius-md); font-size: 0.9rem; color: var(--text-secondary);">
                    "Show me correlations between variables"
                </div>
                <div style="background: var(--bg-secondary); padding: 0.75rem; border-radius: var(--radius-md); font-size: 0.9rem; color: var(--text-secondary);">
                    "What insights can you find?"
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        user_query = st.text_area(
            "💬 Ask your question", 
            placeholder="e.g., What are the key patterns in my data?",
            key="user_query",
            height=100,
            help="Ask any question about your uploaded data"
        )
        
        if user_query:
            with st.spinner("🧠 AI is thinking..."):
                try:
                    response = requests.post(
                        f"{API_URL}/query",
                        params={"user_query": user_query, "user_id": user_id, "file_id": file_id}
                    )
                    answer = response.json().get("answer", "No response available.")
                    
                    st.markdown(f"""
                    <div class="data-card" style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(34, 197, 94, 0.05) 100%);">
                        <h4 style="color: var(--success-color); margin-bottom: 1rem;">🤖 AI Response</h4>
                        <div style="color: var(--text-primary); line-height: 1.6;">
                            {answer}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"❌ Query failed: {e}")
    else:
        st.info("📁 Upload a file to start asking questions about your data")

with tab4:
    st.markdown("""
    <div class="data-card fade-in">
        <h2 style="color: var(--primary-color); margin-bottom: 1rem;">🎨 Custom Visualizations</h2>
        <p style="color: var(--text-secondary); margin-bottom: 0;">Build professional charts tailored to your needs</p>
    </div>
    """, unsafe_allow_html=True)
    
    cols_available = st.session_state.get("uploaded_columns", [])
    fid = st.session_state.get("uploaded_file_id")
    uid = st.session_state.get("uploaded_user_id")
    
    if fid and uid and cols_available:
        st.markdown("""
        <div class="data-card">
            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">🛠️ Plot Builder</h3>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            chart_type = st.selectbox(
                "📊 Chart Type", 
                ["bar", "line", "scatter", "pie", "histogram"], 
                index=0,
                help="Choose the type of visualization"
            )
            
            x_cols = st.multiselect(
                "📈 X-axis Columns", 
                cols_available, 
                default=cols_available[:1] if cols_available else [],
                help="Select one or more columns for the X-axis"
            )
        
        with col2:
            y_col = st.selectbox(
                "📉 Y-axis Column", 
                cols_available,
                help="Select the column for the Y-axis"
            )
            
            agg = st.selectbox(
                "🔢 Aggregation", 
                ["sum", "mean", "count", "none"], 
                index=0,
                help="Choose how to aggregate data (for bar/pie charts)"
            )
        
        build_btn = st.button("🚀 Create Visualization", type="primary")
        
        if build_btn:
            parts = [f"{chart_type}"]
            if x_cols:
                parts.append(f"x: {', '.join(x_cols)}")
            if y_col:
                parts.append(f"y: {y_col}")
            if agg and agg != "none":
                parts.append(f"aggregate: {agg}")
            built_query = " ".join(parts)
            
            with st.spinner("🎨 Creating your visualization..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/visualize_by_query",
                        data={
                            "user_id": uid,
                            "file_id": fid,
                            "visualization_query": built_query,
                            "x": ",".join(x_cols),
                            "y": y_col,
                            "aggregate": None if agg == "none" else agg,
                        }
                    )
                    bjson = resp.json()
                    plot_jsons = bjson.get("plots", [])
                    if plot_jsons:
                        st.markdown("""
                        <div class="data-card">
                            <h3 style="color: var(--text-primary); margin-bottom: 1rem;">📊 Your Custom Visualization</h3>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        for i, plot_json in enumerate(plot_jsons):
                            fig = pio.from_json(plot_json)
                            # Apply professional styling
                            fig.update_layout(
                                plot_bgcolor='rgba(0,0,0,0)',
                                paper_bgcolor='rgba(0,0,0,0)',
                                font=dict(family="Inter, sans-serif", size=12),
                                title_font=dict(size=16, color='#1f2937'),
                                margin=dict(l=20, r=20, t=40, b=20),
                                showlegend=True,
                                legend=dict(
                                    orientation="h",
                                    yanchor="bottom",
                                    y=1.02,
                                    xanchor="right",
                                    x=1
                                )
                            )
                            st.plotly_chart(fig, width='stretch', key=f"custom_plot_{i}")
                    else:
                        st.info("📊 No visualization could be created with the selected parameters.")
                except Exception as e:
                    st.error(f"❌ Visualization failed: {e}")
    else:
        st.info("📁 Upload a file and enter your user ID to access the custom plot builder")

# Welcome message for new users
if not uploaded_file or not user_id:
    st.markdown("""
    <div class="data-card" style="text-align: center; padding: 3rem 2rem; background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);">
        <h2 style="color: var(--primary-color); margin-bottom: 1rem;">🚀 Welcome to DataInsight Pro</h2>
        <p style="color: var(--text-secondary); font-size: 1.1rem; margin-bottom: 2rem;">
            Get started by entering your user ID and uploading your data file
        </p>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-top: 2rem;">
            <div style="background: var(--bg-primary); padding: 1.5rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
                <h4 style="color: var(--primary-color); margin-bottom: 0.5rem;">📊 Upload Data</h4>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">CSV, PDF, DOCX, Excel files</p>
            </div>
            <div style="background: var(--bg-primary); padding: 1.5rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
                <h4 style="color: var(--primary-color); margin-bottom: 0.5rem;">🤖 AI Analysis</h4>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">Automatic insights and patterns</p>
            </div>
            <div style="background: var(--bg-primary); padding: 1.5rem; border-radius: var(--radius-lg); box-shadow: var(--shadow-sm);">
                <h4 style="color: var(--primary-color); margin-bottom: 0.5rem;">📈 Visualizations</h4>
                <p style="color: var(--text-secondary); font-size: 0.9rem; margin: 0;">Professional charts and graphs</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)