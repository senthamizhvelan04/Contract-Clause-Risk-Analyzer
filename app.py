import streamlit as st
import json
import os
from contract_analyzer import ContractAnalyzer
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Contract Clause Risk Analyzer", layout="wide")

# Custom CSS for legal-tech aesthetics
st.markdown("""
<style>
    .main-header {
        color: #60a5fa;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        margin-bottom: 2rem;
        border-bottom: 2px solid #334155;
        padding-bottom: 1rem;
    }
    
    .clause-card {
        background-color: #1e293b;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
        border-left: 6px solid #ccc;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .clause-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
    }
    
    .risk-High { border-left-color: #ef4444; }
    .risk-Medium { border-left-color: #f59e0b; }
    .risk-Low { border-left-color: #10b981; }
    
    .badge-High { background-color: rgba(239, 68, 68, 0.15); color: #fca5a5; padding: 0.3rem 0.8rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;}
    .badge-Medium { background-color: rgba(245, 158, 11, 0.15); color: #fcd34d; padding: 0.3rem 0.8rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;}
    .badge-Low { background-color: rgba(16, 185, 129, 0.15); color: #6ee7b7; padding: 0.3rem 0.8rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem;}
    
    .clause-type {
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #93c5fd;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .clause-text {
        font-family: 'Georgia', serif;
        font-style: italic;
        color: #cbd5e1;
        border-left: 3px solid #475569;
        padding-left: 1rem;
        margin: 1.5rem 0;
        line-height: 1.6;
    }
    
    .label { font-weight: 600; color: #94a3b8; margin-right: 0.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='main-header'>Contract Clause Risk Analyzer</h1>", unsafe_allow_html=True)

@st.cache_resource
def get_analyzer_v2():
    if not os.environ.get("GROQ_API_KEY"):
        return None
    try:
        return ContractAnalyzer("system_prompt.txt")
    except Exception as e:
        st.error(f"Failed to initialize analyzer: {str(e)}")
        return None

if not os.environ.get("GROQ_API_KEY"):
    st.warning("GROQ_API_KEY is not set. Please set it in your environment variables to use the analyzer.")
    st.info("Example: `export GROQ_API_KEY='your-key-here'`")
    st.stop()

analyzer = get_analyzer_v2()

if not analyzer:
    st.stop()

def render_clause_card(res, text: str, title: str = None):
    if res.get("error"):
        st.error(f"Error analyzing clause: {res.get('error')}")
        st.markdown(f"**Original Text:** {text}")
        return
        
    risk = res.get("risk_level", "Unknown")
    ctype = res.get("clause_type", "Unknown")
    reason = res.get("flag_reason", "")
    action = res.get("recommended_action", "")
    conf = res.get("confidence", "")
    
    card_html = f"""<div class="clause-card risk-{risk}">
{('<h4>' + title + '</h4>') if title else ''}
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
<div class="clause-type">{ctype}</div>
<div class="badge-{risk}">Risk: {risk}</div>
</div>
<div class="clause-text">"{text}"</div>
<p><span class="label">Reasoning:</span> {reason}</p>
<p><span class="label">Recommended Action:</span> {action}</p>
<p style="font-size: 0.8rem; color: #718096; margin-top: 1rem;">Confidence: {conf}</p>
</div>"""
    st.markdown(card_html, unsafe_allow_html=True)

tab1, tab2 = st.tabs(["Single Clause", "Batch Analysis"])

with tab1:
    st.subheader("Analyze a Single Clause")
    clause_input = st.text_area("Paste contract clause text here:", height=150)
    if st.button("Analyze Clause", type="primary"):
        if not clause_input.strip():
            st.warning("Please enter some text to analyze.")
        else:
            with st.spinner("Analyzing..."):
                res = analyzer.analyze_clause(clause_input)
                render_clause_card(res.__dict__, clause_input)

with tab2:
    st.subheader("Batch Analysis")
    st.write("Upload a JSON file containing an array of clause objects (must have a 'text' field).")
    uploaded_file = st.file_uploader("Upload clauses JSON", type=['json'])
    
    if uploaded_file is not None:
        try:
            clauses = json.load(uploaded_file)
            if not isinstance(clauses, list):
                st.error("Uploaded JSON must be a list of objects.")
            else:
                if st.button("Run Batch Analysis", type="primary"):
                    with st.spinner(f"Analyzing {len(clauses)} clauses..."):
                        batch_res = analyzer.analyze_batch(clauses)
                        
                        summary = batch_res["summary"]
                        results = batch_res["results"]
                        
                        st.markdown("### Summary Metrics")
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Clauses", summary["total_clauses"])
                        col2.metric("Errors", summary["error_count"])
                        col3.metric("High Risk", summary["risk_distribution"].get("High", 0))
                        
                        # Charts
                        c1, c2 = st.columns(2)
                        with c1:
                            risk_df = pd.DataFrame(list(summary["risk_distribution"].items()), columns=["Risk Level", "Count"])
                            fig = px.pie(risk_df, values='Count', names='Risk Level', 
                                         color='Risk Level',
                                         color_discrete_map={'High':'#e53e3e', 'Medium':'#dd6b20', 'Low':'#38a169'},
                                         title="Risk Level Distribution")
                            st.plotly_chart(fig, use_container_width=True)
                            
                        with c2:
                            type_df = pd.DataFrame(list(summary["clause_type_distribution"].items()), columns=["Clause Type", "Count"])
                            if not type_df.empty:
                                fig2 = px.bar(type_df, x='Count', y='Clause Type', orientation='h', title="Clause Types")
                                st.plotly_chart(fig2, use_container_width=True)
                        
                        st.markdown("### Detailed Results")
                        for item in results:
                            desc = item.get("description", f"Clause ID: {item.get('id', 'Unknown')}")
                            render_clause_card(item["analysis"], item.get("text", ""), title=desc)
                        
        except json.JSONDecodeError:
            st.error("Invalid JSON file uploaded.")
