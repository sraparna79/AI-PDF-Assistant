import streamlit as st
import PyPDF2
import re
import time
from typing import List, Dict

st.set_page_config(page_title="PDF AI Assistant", page_icon="📄", layout="wide")

@st.cache_data
def extract_pdf_text_properly(uploaded_file):
    content = ""
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        for page in pdf_reader.pages[:20]:
            page_text = page.extract_text()
            if page_text and len(page_text.strip()) > 50:
                content += page_text + "\n"
    except:
        raw_content = uploaded_file.getvalue().decode('latin1', errors='ignore')
        text_blocks = re.findall(r'[a-zA-Z\s]{100,1000}', raw_content)
        content = " ".join(text_blocks[:50])
    
    content = re.sub(r'\s+', ' ', content.strip())
    sentences = re.split(r'[.!?]+', content)
    
    chunks = []
    sources = []
    for i, sent in enumerate(sentences):
        sent = sent.strip()
        if len(sent) > 80:
            chunks.append(sent[:900])
            sources.append({"filename": uploaded_file.name, "chunk_id": i+1})
    
    return chunks[:25], sources

def search_chunks(question: str, top_k: int = 5) -> Dict:
    if not st.session_state.chunks:
        return {"answer": "", "sources": [], "matches": 0}
    
    best_chunks = []
    query_lower = question.lower()
    
    for i, chunk in enumerate(st.session_state.chunks):
        score = 0
        query_words = question.lower().split()
        
        # Multiple matching strategies
        for word in query_words:
            if word in chunk.lower():
                score += 2
        score += min(len(chunk) / 1000, 1)  # Length bonus
        
        best_chunks.append((chunk, score, i))
    
    best_chunks.sort(key=lambda x: x[1], reverse=True)
    top_results = best_chunks[:top_k]
    
    answer_parts = [chunk[:400] + "..." for chunk, _, _ in top_results]
    sources = list({st.session_state.sources[i]["filename"] for _, _, i in top_results})
    
    return {
        "answer": " ".join(answer_parts),
        "sources": sources,
        "matches": len(top_results)
    }

if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "sources" not in st.session_state:
    st.session_state.sources = []

st.title("📄 PDF RAG Assistant")
col1, col2 = st.columns([2, 1])
with col1:
    uploaded = st.file_uploader("Choose PDF", type="pdf")
with col2:
    st.metric("Chunks", len(st.session_state.chunks))

if uploaded is not None:
    with st.spinner("🔄 Extracting text..."):
        st.session_state.chunks, st.session_state.sources = extract_pdf_text_properly(uploaded)
        time.sleep(0.5)
    
    st.success(f"✅ Loaded {len(st.session_state.chunks)} chunks")
    
    # DEBUG: Show first chunk
    with st.expander("📋 Preview content"):
        st.write(st.session_state.chunks[0][:500] + "..." if st.session_state.chunks else "No text found")

st.divider()
if st.session_state.chunks:
    with st.form("query"):
        question = st.text_input("Ask about the PDF:")
        submitted = st.form_submit_button("🔍 Search")
    
    if submitted and question:
        output = search_chunks(question, 5)
        st.markdown("### 📝 Answer")
        st.write(output["answer"])
        st.caption(f"**Sources**: {', '.join(output['sources'])}")
else:
    st.info("👆 Upload PDF first")

st.markdown("---")
