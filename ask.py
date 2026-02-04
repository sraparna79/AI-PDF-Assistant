import streamlit as st
from pathlib import Path
import re
from typing import List, Dict
import time

st.set_page_config(page_title="PDF RAG Assistant", page_icon="📄", layout="wide")

@st.cache_data
def process_pdf_content(uploaded_file) -> tuple[List[str], List[Dict]]:
    content = uploaded_file.getvalue().decode('latin1', errors='ignore')
    blocks = re.findall(r'[a-zA-Z]{5,}[a-zA-Z0-9\s\.,:;()]{50,400}', content)
    
    chunks, sources = [], []
    for i, block in enumerate(blocks[:25]):
        clean_block = re.sub(r'\s+', ' ', block.strip())
        if len(clean_block) > 40:
            chunks.append(clean_block)
            sources.append({"filename": uploaded_file.name, "chunk_id": i+1})
    
    return chunks, sources

# SESSION STATE
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "sources" not in st.session_state:
    st.session_state.sources = []

# SECTION 1: PDF INGESTION
st.title("📄 PDF RAG Assistant")
st.markdown("**Upload PDF → Process → Ask Questions**")

col1, col2 = st.columns([2, 1])
with col1:
    uploaded = st.file_uploader("Choose a PDF", type=["pdf"])
with col2:
    st.metric("📄 Status", "Ready" if not uploaded else "Processing")

if uploaded is not None:
    with st.spinner("🔄 Processing PDF..."):
        st.session_state.chunks, st.session_state.sources = process_pdf_content(uploaded)
        time.sleep(0.3)
    
    st.success(f"✅ **Ingested**: {uploaded.name}")
    st.caption(f"*{len(st.session_state.chunks)} chunks ready*")
    st.balloons()

# SECTION 2: QUERY FORM
st.divider()
st.title("❓ Ask a question about your PDF")

def search_pdf(question: str, top_k: int = 5) -> Dict:
    if not st.session_state.chunks:
        return {"answer": "", "sources": [], "matches": 0}
    
    best_chunks = []
    query_lower = question.lower()
    
    for i, chunk in enumerate(st.session_state.chunks):
        chunk_lower = chunk.lower()
        
        # 🔧 MULTIPLE SCORING METHODS (much more lenient)
        keyword_score = 0
        query_words = set(question.lower().split())
        chunk_words = set(chunk.lower().split())
        keyword_score = len(query_words.intersection(chunk_words))
        
        # Fuzzy matching (catches similar words)
        fuzzy_score = sum(1 for word in query_words if word in chunk_lower) * 2
        
        # Substring matching (catches phrases)
        substring_score = sum(1 for word in question.lower().split() if word in chunk_lower) * 1.5
        
        # Total score
        total_score = keyword_score + fuzzy_score + substring_score
        
        # Much lower threshold!
        if total_score > 0.5:  
            best_chunks.append((chunk, total_score, i))
    
    # Always return top chunks even with low scores
    if not best_chunks:
        # Fallback: return top 3 chunks by length/position
        fallback_chunks = sorted(enumerate(st.session_state.chunks), 
                               key=lambda x: len(x[1]), reverse=True)[:3]
        best_chunks = [(chunk, 1.0, idx) for idx, chunk in fallback_chunks]
    
    best_chunks.sort(key=lambda x: x[1], reverse=True)
    top_results = best_chunks[:top_k]
    
    # Build answer from ALL top chunks
    answer_parts = []
    seen_sources = set()
    
    for chunk, score, idx in top_results:
        source = st.session_state.sources[idx]["filename"]
        seen_sources.add(source)
        
        # Take first good chunk snippet
        snippet = chunk[:300].strip()
        if snippet:
            answer_parts.append(snippet)
    
    answer = " ".join(answer_parts)[:1000]  # Combine + truncate
    if len(answer) < 50:
        answer = f"Found relevant sections: {len(top_results)} chunks matched."
    
    return {
        "answer": answer,
        "sources": list(seen_sources),
        "matches": len(top_results)
    }
if uploaded is not None and st.session_state.chunks:
    with st.expander("🔍 DEBUG - Check Chunks"):
        st.write(f"**{len(st.session_state.chunks)} chunks extracted**")
        for i, chunk in enumerate(st.session_state.chunks[:3]):
            st.write(f"**Chunk {i+1}:** {chunk[:200]}...")
        if st.button("Test with chunk words"):
            st.write("Sample words:", " ".join(st.session_state.chunks[0].split()[:10]))
