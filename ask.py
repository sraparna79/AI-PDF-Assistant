import streamlit as st
from pathlib import Path
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity
import re
st.set_page_config(page_title="PDF RAG Assistant", page_icon="📄", layout="wide")

# 🔥 SESSION STATE
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "sources" not in st.session_state:
    st.session_state.sources = []
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("📄 PDF RAG Assistant")
st.markdown("**Upload PDF → Process → Ask Questions**")

# 🔥 UPLOAD & PROCESS (Replaces Inngest)
uploaded_file = st.file_uploader("Choose PDF", type="pdf")

if uploaded_file is not None:
    with st.spinner("🔄 Processing PDF (Ingest Pipeline)..."):
        # Save file
        uploads_dir = Path("uploads")
        uploads_dir.mkdir(exist_ok=True)
        path = uploads_dir / uploaded_file.name
        path.write_bytes(uploaded_file.getvalue())
        
        # Read PDF bytes and extract text
        content = uploaded_file.getvalue()
        text = content.decode('latin1', errors='ignore')
        
        # Extract meaningful text blocks
        blocks = re.findall(r'[a-zA-Z]{5,}[a-zA-Z0-9\s\.,:;()]{50,400}', text)
        
        # Process chunks
        st.session_state.chunks = []
        st.session_state.sources = []
        
        for i, block in enumerate(blocks[:25]):
            clean_block = re.sub(r'\s+', ' ', block.strip())
            if len(clean_block) > 40:
                st.session_state.chunks.append(clean_block)
                st.session_state.sources.append({
                    "filename": uploaded_file.name,
                    "chunk_id": i+1
                })
        
        st.success(f"✅ **Ingested {uploaded_file.name}** - {len(st.session_state.chunks)} chunks ready!")
        
        # Simulate Inngest completion
        st.balloons()

# 🔥 STATUS
if st.session_state.chunks:
    col1, col2 = st.columns(2)
    col1.metric("📄 PDF", st.session_state.sources[0]["filename"])
    col2.metric("🔍 Chunks", len(st.session_state.chunks))

# 🔥 QUERY (Replaces your query event)
st.markdown("---")
st.markdown("### ❓ Query Your PDF")

if not st.session_state.chunks:
    st.warning("👆 **Upload PDF first**")
else:
    # Chat-like query
    question = st.text_input("Ask about your document:")
    
    if st.button("🔍 Search PDF") and question:
        with st.spinner("Searching..."):
            if not st.session_state.chunks:
                st.error("No chunks available. Upload PDF first.")
                st.stop()
            
        # Simple keyword relevance scoring
        best_chunks = []
        
        for i, chunk in enumerate(st.session_state.chunks):
            query_words = set(question.lower().split())
            chunk_words = set(chunk.lower().split())
            score = len(query_words.intersection(chunk_words))
            
            if score > 0:
                best_chunks.append((chunk, score, i))
        
        # Handle no matches
        if not best_chunks:
            st.warning(f"❌ No relevant content found for '{question}'. Try using keywords from the PDF.")
            st.stop()
        
        # Sort by relevance
        best_chunks.sort(key=lambda x: x[1], reverse=True)
        
        # Build answer
        answer = f"**{question}**\n\n"
        seen_sources = set()
        
        for chunk, score, idx in best_chunks[:4]:
            source = st.session_state.sources[idx]["filename"]
            
            # Only add source once
            if source not in seen_sources:
                seen_sources.add(source)
            
            # Extract key sentence
            sentences = re.split(r'[.!?]+', chunk)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 20:
                    answer += f"• **{sent.capitalize()}**\n"
                    break
        
        # SAFE source display - no more IndexError
        sources_list = list(seen_sources)
        if sources_list:
            answer += f"\n**Sources**: {', '.join(sources_list[:2])}"
            if len(sources_list) > 2:
                answer += f" +{len(sources_list)-2} more"
        else:
            answer += "\n**Sources**: Document content"
        
        # Display in chat style
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #1e293b, #334155); padding: 24px; border-radius: 16px; border-left: 5px solid #3b82f6; margin: 20px 0;'>
            <div style='font-size: 1.1rem; line-height: 1.7; color: #e2e8f0;'>
                {answer.replace('\n', '<br>')}
            </div>
        </div>
        """, unsafe_allow_html=True)

