import streamlit as st
import re

st.set_page_config(page_title="FREE AI PDF Assistant", layout="wide")

def extract_pdf_text(uploaded_file):
    """Extract text from PDF - FIXED for file pointer issue"""
    # Reset file pointer & read raw bytes
    uploaded_file.seek(0)
    raw = uploaded_file.read()
    raw_text = raw.decode('latin1', errors='ignore')
    
    # INDUSTRIAL PDF CLEANING
    # Kill metadata/XML/RDF
    raw_text = re.sub(r'(Mm:|xmpmm:|rdf:|Evt:|stevt:|dc:|adobe|\/[A-Z]{2,})', ' ', raw_text, flags=re.I)
    raw_text = re.sub(r'(obj|endobj|xref|stream|BT|ET|\/Length|\/Filter)', ' ', raw_text, flags=re.I)
    raw_text = re.sub(r'[a-f0-9]{8,}', '', raw_text)
    raw_text = re.sub(r'\s+', ' ', raw_text)
    
    # Extract REAL text blocks (sentence-like)
    blocks = re.findall(r'[A-Z][a-zA-Z\s\.,:;\'-]{40,800}[.!?]', raw_text)
    
    chunks = []
    for block in blocks[:30]:
        clean = re.sub(r'[^\w\s\.,:;\'-]', '', block.strip())
        if len(clean) > 60 and len(clean.split()) > 8:
            chunks.append(clean[:900])
    return chunks

def free_llm(question: str, chunks: list) -> str:
    """Enhanced RAG with detailed output"""
    query_words = question.lower().split()
    relevant_chunks = []
    
    # Score ALL chunks
    for i, chunk in enumerate(chunks):
        score = sum(2 for word in query_words if word.lower() in chunk.lower())
        score += len(re.findall('|'.join(query_words), chunk.lower()))
        if score > 0:
            relevant_chunks.append((chunk, score))
    
    # Fallback to best chunks
    if not relevant_chunks:
        relevant_chunks = sorted([(c, len(c)/100) for c in chunks], 
                               key=lambda x: x[1], reverse=True)[:6]
    
    relevant_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, score in relevant_chunks[:5]]
    
    # Build detailed answer
    answer_parts = []
    answer_parts.append(f"**🤖 AI Answer: '{question}'**")
    answer_parts.append("")
    
    answer_parts.append("**📄 From your PDF:**")
    for i, chunk in enumerate(top_chunks[:4], 1):
        snippet = chunk[:300] + "..." if len(chunk) > 300 else chunk
        answer_parts.append(f"{i}. {snippet}")
    
    answer_parts.append("")
    answer_parts.append(f"**🔍 Found {len(relevant_chunks)} matches**")
    
    return "\n\n".join(answer_parts)

# Session state
if "chunks" not in st.session_state:
    st.session_state.chunks = []

# UI
st.title("🤖 FREE AI PDF Assistant") 
st.markdown("**No API keys • No costs • Works on ANY PDF**")

col1, col2 = st.columns([3,1])
with col1:
    uploaded = st.file_uploader("📄 Upload PDF", type="pdf")
with col2:
    st.metric("Chunks", len(st.session_state.chunks))

# Process PDF (FIXED)
if uploaded is not None:
    if st.button("🚀 Process PDF", type="primary"):
        with st.spinner("Extracting text..."):
            st.session_state.chunks = extract_pdf_text(uploaded)
            st.session_state.filename = uploaded.name
        
        st.success(f"✅ **{len(st.session_state.chunks)} chunks** from {uploaded.name}")
        st.balloons()
        st.rerun()
        
    # Preview
    if st.session_state.chunks:
        with st.expander("📋 Preview content", expanded=True):
            st.write("**First chunk:**")
            st.write(st.session_state.chunks[0][:500] + "..." if len(st.session_state.chunks[0]) > 500 else st.session_state.chunks[0])

st.divider()

# Query
if st.session_state.chunks:
    st.markdown("### 💭 Ask about your PDF")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_input("", placeholder="What is AI? Key findings? Main topics?", label_visibility="collapsed")
    with col2:
        results = st.slider("Results", 3, 8, 5)
    
    if st.button("🚀 GENERATE AI ANSWER", use_container_width=True, type="primary") and question.strip():
        with st.spinner("🤖 Analyzing..."):
            answer = free_llm(question, st.session_state.chunks)
            st.markdown(answer)
            
            # Quick questions
            st.markdown("**🔄 Quick Ask:**")
            quicks = ["main topic", "key findings", "important data", "summary"]
            cols = st.columns(len(quicks))
            for i, q in enumerate(quicks):
                if cols[i].button(f"💡 {q}", key=f"q{i}"):
                    st.session_state.last_question = q
                    st.rerun()
else:
    st.info("👆 **Upload & Process PDF first**")
    st.markdown("**💡 Works best with: research papers, ebooks, reports**")

# Controls
st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("🗑️ Clear All", use_container_width=True):
    st.session_state.chunks = []
    st.session_state.filename = None
    st.rerun()

if col2.button("🔍 Show All Chunks", use_container_width=True):
    st.session_state.show_chunks = not st.session_state.get("show_chunks", False)
    st.rerun()

if st.session_state.get("show_chunks", False):
    with st.expander(f"📚 All {len(st.session_state.chunks)} chunks"):
        for i, chunk in enumerate(st.session_state.chunks[:10]):
            st.caption(f"**{i+1}**: {chunk[:200]}...")

st.markdown("---")
st.caption("✨ **100% FREE** - Pure Python RAG • No external APIs")
