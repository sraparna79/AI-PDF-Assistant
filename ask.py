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

def search_pdf(question: str, top_k: int = 5) -> Dict:  # ← FIXED: Proper indentation
    if not st.session_state.chunks:
        return {"answer": "", "sources": [], "matches": 0}
    
    best_chunks = []
    for i, chunk in enumerate(st.session_state.chunks):
        query_words = set(question.lower().split())
        chunk_words = set(chunk.lower().split())
        score = len(query_words.intersection(chunk_words))
        if score > 0:
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
    
    answer = " ".join(answer_parts[:3])
    if not answer:
        answer = f"Found {len(top_results)} relevant chunks (no complete sentences extracted)"
    
    return {
        "answer": answer,
        "sources": list(seen_sources),
        "matches": len(top_results)
    }

# FORM - NOW PROPERLY STRUCTURED
if st.session_state.chunks:
    with st.form("rag_query_form", clear_on_submit=True):
        question = st.text_input("Your question", placeholder="e.g. What is the main topic?")
        top_k = st.number_input("Top chunks", min_value=1, max_value=10, value=4)
        col1, col2 = st.columns(2)
        submitted = col1.form_submit_button("🔍 Ask")
        col2.form_submit_button("🗑️ Clear All")

    if submitted and question.strip():
        with st.spinner("🔄 Searching PDF..."):
            output = search_pdf(question.strip(), top_k)

        st.subheader("📝 Answer")
        if output["answer"]:
            st.markdown(f"**Q: {question}**")
            st.write(output["answer"])
        else:
            st.warning("❌ No relevant content found. Try using keywords from the PDF.")
        
        if output["sources"]:
            st.subheader("📚 Sources")
            for source in output["sources"]:
                st.caption(f"• {source}")
        
        st.caption(f"*Found {output['matches']} matching chunks*")
else:
    st.info("👆 Upload a PDF first")

st.markdown("---")
st.caption("Production RAG Pipeline - Powered by Streamlit")
