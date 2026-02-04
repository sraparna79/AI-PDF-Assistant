import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

st.set_page_config(page_title="AI PDF Assistant", page_icon="📄", layout="wide")

# Session state
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "sources" not in st.session_state:
    st.session_state.sources = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed" not in st.session_state:
    st.session_state.processed = False

st.markdown("""
<style>
.main {background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); color: #e2e8f0;}
.stButton > button {background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; border-radius: 12px;}
.answer-box {background: linear-gradient(135deg, #1e293b, #334155); padding: 20px; border-radius: 16px; border-left: 4px solid #3b82f6;}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #1e293b, #334155); border-radius: 20px;'>
    <h1 style='color: #3b82f6; font-size: 3rem;'>📄 AI PDF Assistant</h1>
    <p style='color: #94a3b8;'>Upload PDF → Ask Questions → Get Answers from YOUR Document</p>
</div>
""", unsafe_allow_html=True)

# Upload
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("Choose PDF file", type="pdf")

with col2:
    if st.session_state.chunks:
        st.metric("Chunks", len(st.session_state.chunks))
    else:
        st.info("No PDF loaded")

# Process PDF (ONCE)
if uploaded_file is not None and not st.session_state.processed:
    with st.spinner("Analyzing PDF..."):
        # Read PDF bytes and extract text blocks
        content = uploaded_file.read()
        text = content.decode('latin1', errors='ignore')
        
        # Extract meaningful text blocks (real content)
        text_blocks = re.findall(r'[a-zA-Z]{4,}[a-zA-Z0-9\s\.,:;()]{30,500}', text)
        
        # Clean and chunk
        st.session_state.chunks = []
        st.session_state.sources = []
        
        for i, block in enumerate(text_blocks[:20]):  # Top 20 blocks
            clean_block = re.sub(r'\s+', ' ', block.strip())
            if len(clean_block) > 40:
                st.session_state.chunks.append(clean_block[:400])
                st.session_state.sources.append({
                    "filename": uploaded_file.name,
                    "chunk_id": i+1
                })
        
        st.session_state.processed = True
        st.session_state.filename = uploaded_file.name
        
        st.success(f"✅ **{uploaded_file.name}** analyzed! Found {len(st.session_state.chunks)} text blocks")
        st.balloons()

# Metrics
if st.session_state.chunks:
    col1, col2 = st.columns(2)
    col1.metric("📄 Document", st.session_state.filename)
    col2.metric("🔍 Chunks", len(st.session_state.chunks))

# Chat interface
st.markdown("---")
st.markdown("### 💬 Ask about your PDF")

# Show chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message:
            st.caption(f"**Source**: {message['sources'][0]}")

# Chat input
if prompt := st.chat_input("Ask a question about your PDF..."):
    # User message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if st.session_state.chunks:
        with st.chat_message("assistant"):
            with st.spinner("Searching document..."):
                # Simple keyword + position search (stable)
                best_chunks = []
                scores = []
                
                for i, chunk in enumerate(st.session_state.chunks):
                    # Keyword matching
                    score = sum(1 for word in prompt.lower().split() if word in chunk.lower())
                    if score > 0:
                        best_chunks.append((chunk, i))
                        scores.append(score)
                
                # Sort by relevance
                if best_chunks:
                    best_chunks.sort(key=lambda x: scores[st.session_state.chunks.index(x[0])], reverse=True)
                    top_chunks = best_chunks[:3]
                else:
                    top_chunks = [(st.session_state.chunks[0], 0)]  # Fallback
                
                # Build answer
                answer = f"**{prompt}**"
                
                seen_sources = set()
                for chunk, chunk_id in top_chunks:
                    source = st.session_state.sources[chunk_id]["filename"]
                    
                    # Extract sentences
                    sentences = re.split(r'[.!?]+', chunk)
                    for sentence in sentences:
                        sentence = sentence.strip()
                        if len(sentence) > 25:
                            answer += f"\n• **{sentence.capitalize()}**"
                            break
                    
                    if source not in seen_sources:
                        seen_sources.add(source)
                
                answer += f"\n\n**From your PDF**: {list(seen_sources)[0]}"
                
                # Display
                st.markdown(f"""
                <div class='answer-box'>
                    <div style='font-size: 1.1rem; line-height: 1.6;'>
                        {answer.replace('\\n', '<br>')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Save message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": [list(seen_sources)[0]]
                })
    else:
        with st.chat_message("assistant"):
            st.warning("👆 Upload and process PDF first!")

# Controls
col1, col2 = st.columns(2)
if col1.button("🔄 New PDF", use_container_width=True):
    st.session_state.chunks = []
    st.session_state.sources = []
    st.session_state.messages = []
    st.session_state.processed = False
    st.rerun()

if col2.button("🗑️ Clear Chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

st.markdown("---")
st.markdown("*Production-ready PDF RAG Assistant - Stable & Fast*")
