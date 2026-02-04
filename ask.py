import streamlit as st
import asyncio
import time
from pathlib import Path
import re
from typing import List, Dict, Optional

st.set_page_config(page_title="PDF RAG Assistant", page_icon="📄", layout="wide")

# 🔥 SIMULATED INGESTION PIPELINE (No Inngest needed)
@st.cache_data
def process_pdf_content(uploaded_file) -> tuple[List[str], List[Dict]]:
    """Simulate Inngest ingestion - extract & chunk PDF locally"""
    content = uploaded_file.getvalue().decode('latin1', errors='ignore')
    blocks = re.findall(r'[a-zA-Z]{5,}[a-zA-Z0-9\s\.,:;()]{50,400}', content)
    
    chunks, sources = [], []
    for i, block in enumerate(blocks[:25]):
        clean_block = re.sub(r'\s+', ' ', block.strip())
        if len(clean_block) > 40:
            chunks.append(clean_block)
            sources.append({"filename": uploaded_file.name, "chunk_id": i+1})
    
    return chunks, sources

# 🔥 SESSION STATE
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "sources" not in st.session_state:
    st.session_state.sources = []

# ═══════════════════════════════════════════════════════
# SECTION 1: PDF INGESTION (Matches Inngest upload style)
# ═══════════════════════════════════════════════════════
st.title("📄 PDF RAG Assistant")
st.markdown("**Upload PDF → Process → Ask Questions**")

col1, col2 = st.columns([2, 1])
with col1:
    uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False)

with col2:
    st.metric("📄 Status", "Ready" if not uploaded else "Processing")

if uploaded is not None:
    with st.spinner("🔄 Processing PDF (Ingest Pipeline)..."):
        # Simulate async Inngest event
        st.session_state.chunks, st.session_state.sources = process_pdf_content(uploaded)
        time.sleep(0.3)  # Visual feedback pause
    
    st.success(f"✅ **Ingested**: {uploaded.name}")
    st.caption(f"*{len(st.session_state.chunks)} chunks ready*")
    st.balloons()

# ═══════════════════════════════════════════════════════
# SECTION 2: QUERY FORM (Exact Inngest-style form)
# ═══════════════════════════════════════════════════════
st.divider()
st.title("❓ Ask a question about your PDF")


    # 🔥 ASYNC-STYLE QUERY PROCESSING (No Inngest, pure local)
    # Remove ALL asyncio code - replace with:
def search_pdf(question: str, top_k: int = 5) -> Dict:  # Make it sync
    """Local PDF search (no async needed)"""
    best_chunks = []

    for i, chunk in enumerate(st.session_state.chunks):
        query_words = set(question.lower().split())
        chunk_words = set(chunk.lower().split())
        score = len(query_words.intersection(chunk_words))
        if score > 0:  # This is too strict!
            best_chunks.append((chunk, score, i))
    
    if not best_chunks:
        return {"answer": "", "sources": [], "matches": 0}
    
    best_chunks.sort(key=lambda x: x[1], reverse=True)
    top_results = best_chunks[:top_k]
    
    answer_parts = []
    seen_sources = set()
    for chunk, score, idx in top_results:
        source = st.session_state.sources[idx]["filename"]
        seen_sources.add(source)
        
        sentences = re.split(r'[.!?]+', chunk)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 20:
                answer_parts.append(sent.capitalize())
                break
    
    return {
        "answer": " ".join(answer_parts[:3]) or "Found relevant content (no full sentences extracted)",
        "sources": list(seen_sources),
        "matches": len(top_results)
    }

# In the form section, replace asyncio with:
if submitted and question.strip():
    with st.spinner("🔄 Searching PDF..."):
        output = search_pdf(question.strip(), top_k)  # Direct call
