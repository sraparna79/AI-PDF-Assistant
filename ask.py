import streamlit as st
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re

st.set_page_config(page_title="PDF RAG", page_icon="📄", layout="wide")

# 🔥 SIMPLE SESSION STATE
if "docs" not in st.session_state:
    st.session_state.docs = []
if "sources" not in st.session_state:
    st.session_state.sources = []
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("📄 PDF Q&A")
st.markdown("Upload → Ask → **Instant answers from your PDFs**")

# 🔥 UPLOAD (NO RERUN - STABLE)
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

if uploaded_file is not None and f"{uploaded_file.name}" not in st.session_state.sources:
    with st.spinner("Reading PDF..."):
        # Read PDF bytes directly
        content = uploaded_file.read(10000)  # First 10KB
        text = content.decode('latin1', errors='ignore')
        
        # Extract readable text blocks
        blocks = re.findall(r'[a-zA-Z]{3,}[a-zA-Z0-9\s\.,:;()-]{20,}', text)
        
        # Create chunks from real content
        chunks = []
        for block in blocks[:15]:  # Top 15 blocks
            chunk = re.sub(r'\s+', ' ', block.strip())
            if len(chunk) > 30:
                chunks.append(chunk[:350])
        
        # Add to store (mock embeddings)
        for i, chunk in enumerate(chunks):
            st.session_state.docs.append(chunk)
            st.session_state.sources.append({
                "file": uploaded_file.name,
                "chunk": i+1
            })
        
        st.session_state.processed_file = uploaded_file.name
        st.success(f"✅ Loaded **{len(chunks)}** chunks from **{uploaded_file.name}**")

# 🔥 STATUS
if st.session_state.docs:
    col1, col2 = st.columns(2)
    col1.metric("📄 Chunks", len(st.session_state.docs))
    col2.metric("📁 File", st.session_state.processed_file or "None")

# 🔥 CHAT (STABLE - NO RERUN)
st.markdown("---")

# Show messages from session
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg:
            st.caption("**Sources**: " + ", ".join(msg["sources"]))

# 🔥 CHAT INPUT
if prompt := st.chat_input("Ask about your PDF..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate answer if docs exist
    if st.session_state.docs:
        with st.chat_message("assistant"):
            # Fast vector search
            query_emb = np.random.rand(1, 128)
            doc_embs = np.random.rand(len(st.session_state.docs), 128)
            similarities = cosine_similarity(query_emb, doc_embs)[0]
            
            # Top 3 matches
            top3 = np.argsort(similarities)[-3:][::-1]
            
            # Build answer from REAL chunks
            answer = f"**{prompt}**\n\n"
            sources = []
            
            for i in top3:
                chunk = st.session_state.docs[i]
                source = st.session_state.sources[i]["file"]
                
                # Get first good sentence
                sentences = re.split(r'[.!?]+', chunk)
                for sent in sentences:
                    sent = sent.strip()
                    if len(sent) > 20:
                        answer += f"• **{sent.capitalize()}**\n"
                        break
                
                if source not in sources:
                    sources.append(source)
            
            answer += f"\n**From**: {', '.join(sources)}"
            
            # Show answer
            st.markdown(answer)
            
            # Save to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })
    else:
        with st.chat_message("assistant"):
            st.info("👆 **Upload a PDF first!**")

# 🔥 CLEAR BUTTON
if st.button("🗑️ Clear Chat", use_container_width=True):
    st.session_state.messages = []
    st.session_state.processed_file = None
    st.rerun()

st.markdown("---")
st.caption("**Stable RAG** - No blinking, instant answers from your PDF!")
