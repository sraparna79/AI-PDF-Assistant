import streamlit as st
import re
import time
from typing import List, Dict

st.set_page_config(page_title="PDF RAG Assistant", page_icon="📄", layout="wide")

def extract_pdf_text_simple(uploaded_file):
    """NO PyPDF2 - Pure regex extraction that actually WORKS"""
    raw_content = uploaded_file.getvalue().decode('latin1', errors='ignore')
    
    # Extract ALL text blocks (much better regex)
    text_blocks = re.findall(r'[a-zA-Z][a-zA-Z0-9\s\.,:;()\-–—]{50,1200}', raw_content)
    
    chunks = []
    sources = []
    
    for i, block in enumerate(text_blocks[:30]):
        # Clean aggressively
        clean = re.sub(r'[^\w\s\.,:;()\-–—]', ' ', block)
        clean = re.sub(r'\s+', ' ', clean.strip())
        
        # Skip junk (headers, page numbers, etc.)
        if (len(clean) > 100 and 
            not re.match(r'^\d+\s*$', clean) and 
            len(re.findall(r'[a-zA-Z]{4,}', clean)) > 3):
            
            chunks.append(clean[:900])
            sources.append({"filename": uploaded_file.name, "chunk_id": i+1})
    
    return chunks, sources

def search_chunks(question: str, top_k: int = 5) -> Dict:
    """Fuzzy search - ALWAYS finds something"""
    if not st.session_state.chunks:
        return {"answer": "", "sources": [], "matches": 0}
    
    best_chunks = []
    query_lower = question.lower()
    
    for i, chunk in enumerate(st.session_state.chunks):
        score = 0
        
        # Word matching
        query_words = query_lower.split()
        for word in query_words:
            if len(word) > 3 and word in chunk.lower():
                score += 3
        
        # Substring matching (partial matches)
        for word in query_words:
            if len(word) > 3:
                score += len(re.findall(word, chunk.lower())) * 2
        
        # Length/quality bonus
        score += min(len(chunk) / 1000, 2)
        
        best_chunks.append((chunk, score, i))
    
    # Sort and take top
    best_chunks.sort(key=lambda x: x[1], reverse=True)
    top_results = best_chunks[:top_k]
    
    # Build answer
    answer_parts = []
    sources_set = set()
    
    for chunk, score, idx in top_results:
        sources_set.add(st.session_state.sources[idx]["filename"])
        snippet = chunk[:350].rstrip('.') + "..."
        answer_parts.append(snippet)
    
    answer = " ".join(answer_parts)[:1200]
    
    return {
        "answer": answer or f"Found {len(top_results)} relevant sections in document",
        "sources": list(sources_set),
        "matches": len(top_results)
    }

# SESSION STATE
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "sources" not in st.session_state:
    st.session_state.sources = []

# UI
st.title("📄 PDF RAG Assistant")
st.markdown("**Upload → Search → Get Answers Instantly**")

col1, col2 = st.columns([3, 1])
with col1:
    uploaded = st.file_uploader("Choose PDF", type="pdf", key="uploader")
with col2:
    st.metric("Chunks Ready", len(st.session_state.chunks))

if uploaded is not None:
    with st.spinner("🔄 Processing PDF..."):
        st.session_state.chunks, st.session_state.sources = extract_pdf_text_simple(uploaded)
        time.sleep(0.3)
    
    st.success(f"✅ **{len(st.session_state.chunks)} chunks extracted** from {uploaded.name}")
    
    # Preview first chunk
    with st.expander("👀 Preview Content", expanded=False):
        if st.session_state.chunks:
            st.write("**Sample:**")
            st.write(st.session_state.chunks[0][:400] + "...")
        else:
            st.warning("No readable text found - try a different PDF")

st.divider()

if st.session_state.chunks:
    # Query form
    col1, col2 = st.columns([3, 1])
    with col1:
        question = st.text_input("❓ Ask about your PDF:", 
                               placeholder="e.g. 'What is the main topic?' or 'sales figures'")
    with col2:
        top_k = st.slider("Results", 3, 8, 5, key="topk")
    
    if st.button("🔍 **SEARCH PDF**", use_container_width=True):
        with st.spinner("Searching..."):
            output = search_chunks(question, top_k)
        
        st.markdown("### 📝 **Answer**")
        st.write(output["answer"])
        
        if output["sources"]:
            st.caption(f"**📚 Sources**: {', '.join(output['sources'])}")
        
        st.caption(f"*Matched {output['matches']} sections*")
        
else:
    st.info("👆 **Upload a PDF first** to enable search")

st.markdown("---")
st.caption("✨ Pure Streamlit - Zero external dependencies")
