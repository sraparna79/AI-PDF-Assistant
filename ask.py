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

if st.session_state.chunks:
    # 🔥 ASYNC-STYLE QUERY PROCESSING (No Inngest, pure local)
    async def search_pdf(question: str, top_k: int = 5) -> Dict:
        """Simulate Inngest query event processing"""
        best_chunks = []
        
        for i, chunk in enumerate(st.session_state.chunks):
            query_words = set(question.lower().split())
            chunk_words = set(chunk.lower().split())
            score = len(query_words.intersection(chunk_words))
            if score > 0:
                best_chunks.append((chunk, score, i))
        
        best_chunks.sort(key=lambda x: x[1], reverse=True)
        top_results = best_chunks[:top_k]
        
        answer_parts = []
        seen_sources = set()
        for chunk, score, idx in top_results:
            source = st.session_state.sources[idx]["filename"]
            if source not in seen_sources:
                seen_sources.add(source)
            
            sentences = re.split(r'[.!?]+', chunk)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 20:
                    answer_parts.append(sent.capitalize())
                    break
        
        return {
            "answer": " ".join(answer_parts[:3]),
            "sources": list(seen_sources),
            "matches": len(top_results)
        }

    # 🔥 FORM (Exact Inngest replica)
    with st.form("rag_query_form", clear_on_submit=True):
        question = st.text_input("Your question", placeholder="e.g. What is the main topic?")
        top_k = st.number_input("Top chunks", min_value=1, max_value=10, value=4, step=1)
        col1, col2 = st.columns(2)
        submitted = col1.form_submit_button("🔍 Ask", use_container_width=True)
        
        if col2.form_submit_button("🗑️ Clear", use_container_width=True):
            st.session_state.chunks = []
            st.session_state.sources = []
            st.rerun()

    if submitted and question.strip():
        with st.spinner("🔄 Generating answer..."):
            # Simulate Inngest event flow with asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            output = loop.run_until_complete(search_pdf(question.strip(), top_k))
            loop.close()

        # 🔥 ANSWER DISPLAY (Inngest-style)
        st.subheader("📝 Answer")
        if output["answer"]:
            st.markdown(f"**{question}**")
            st.write(output["answer"])
        else:
            st.warning("No relevant content found. Try different keywords.")
        
        if output["sources"]:
            st.subheader("📚 Sources")
            for source in output["sources"]:
                st.caption(f"• {source}")
        
        st.caption(f"*Found {output['matches']} matching chunks*")
        
else:
    st.info("👆 **Upload a PDF first** to start querying")

# Footer
st.markdown("---")
st.caption("**Production RAG Pipeline** - Powered by Streamlit")
