import streamlit as st
from pathlib import Path
import re
from typing import List, Dict
import time

# SIMULATE YOUR PRODUCTION PDF PROCESSING (no external deps)
def process_pdf_production_style(uploaded_file):
    """Mimic data_loader.py + vector_db.py locally"""
    content = uploaded_file.getvalue().decode('latin1', errors='ignore')
    
    # Better text extraction (closer to PDFReader)
    blocks = re.findall(r'.{100,1000}', content)  # Simple sentence-like chunks
    chunks = []
    for block in blocks[:30]:
        clean = re.sub(r'\s+', ' ', block.strip())
        if len(clean) > 100 and not re.match(r'^\d+\s*$', clean):  # Skip page numbers
            chunks.append(clean[:800])
    
    sources = [{"filename": uploaded_file.name, "chunk_id": i+1} for i in range(len(chunks))]
    return chunks, sources

def search_with_similarity(question: str, top_k: int = 5) -> Dict:
    """SIMPLE COSINE SIMILARITY (no embeddings needed)"""
    if not st.session_state.chunks:
        return {"answer": "", "sources": [], "matches": 0}
    
    best_chunks = []
    query_words = set(question.lower().split())
    
    for i, chunk in enumerate(st.session_state.chunks):
        # Multi-score matching (like your production embed+search)
        chunk_words = set(chunk.lower().split())
        keyword_score = len(query_words.intersection(chunk_words))
        
        # Phrase matching
        phrase_score = sum(1 for word in question.lower().split() if word in chunk.lower())
        
        # Length bonus (prefer content-rich chunks)
        length_score = min(len(chunk) / 1000, 1.0)
        
        total_score = keyword_score * 3 + phrase_score * 2 + length_score
        best_chunks.append((chunk, total_score, i))
    
    # Sort + take top
    best_chunks.sort(key=lambda x: x[1], reverse=True)
    top_results = best_chunks[:top_k]
    
    # Build answer
    answer_parts = [chunk[:400] + "..." for chunk, _, _ in top_results]
    sources = list({st.session_state.sources[i]["filename"] for _, _, i in top_results})
    
    return {
        "answer": " ".join(answer_parts),
        "sources": sources,
        "matches": len(top_results)
    }

# UI (same as before but FIXED)
st.set_page_config(page_title="PDF RAG Assistant", page_icon="📄", layout="wide")

if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "sources" not in st.session_state:
    st.session_state.sources = []

st.title("📄 PDF RAG Assistant")
col1, col2 = st.columns([2, 1])
with col1:
    uploaded = st.file_uploader("Choose PDF", type="pdf")
with col2:
    st.metric("Status", f"{len(st.session_state.chunks)} chunks" if st.session_state.chunks else "Ready")

if uploaded is not None and uploaded != st.session_state.get("last_uploaded", None):
    with st.spinner("🔄 Processing..."):
        st.session_state.chunks, st.session_state.sources = process_pdf_production_style(uploaded)
        st.session_state.last_uploaded = uploaded
        time.sleep(0.5)
    
    st.success(f"✅ Loaded {len(st.session_state.chunks)} chunks from {uploaded.name}")

st.divider()
st.subheader("❓ Ask Question")

if st.session_state.chunks:
    with st.form("query_form"):
        question = st.text_input("Question:", placeholder="What does the PDF say about...")
        top_k = st.slider("Results", 1, 10, 3)
        submitted = st.form_submit_button("🔍 Search")
    
    if submitted and question.strip():
        with st.spinner("Searching..."):
            output = search_with_similarity(question.strip(), top_k)
        
        st.markdown("### 📝 Answer")
        st.write(output["answer"] or "No content found")
        
        if output["sources"]:
            st.caption("**Sources**: " + ", ".join(output["sources"]))
        st.caption(f"_Matched {output['matches']} sections_")
        
        # DEBUG: Show sample chunk
        with st.expander("📋 Sample Content"):
            st.write(st.session_state.chunks[0][:500] + "...")
else:
    st.info("👆 Upload PDF first")

st.markdown("---")
st.caption("Production-ready RAG")
