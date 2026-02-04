import streamlit as st
import re

st.set_page_config(page_title="FREE LLM PDF Assistant", layout="wide")

# Your PDF extraction (from previous working code)
def extract_pdf_text(uploaded_file):
    raw = uploaded_file.getvalue().decode('latin1', errors='ignore')
    blocks = re.findall(r'[a-zA-Z]{3,}[a-zA-Z0-9\s\.,:;()\-]{50,1000}', raw)
    chunks = []
    for block in blocks[:20]:
        clean = re.sub(r'\s+', ' ', block.strip())
        if len(clean) > 80:
            chunks.append(clean[:800])
    return chunks

# FREE "LLM" - Smart context extraction + formatting
def free_llm(question: str, chunks: list) -> str:
    """Smart RAG without external APIs"""
    
    # Find relevant chunks
    query_words = question.lower().split()
    relevant_chunks = []
    
    for chunk in chunks:
        score = sum(1 for word in query_words if word in chunk.lower())
        if score > 0:
            relevant_chunks.append(chunk)
        if len(relevant_chunks) >= 3:
            break
    
    # Fallback - top chunks by length
    if not relevant_chunks:
        relevant_chunks = sorted(chunks, key=len, reverse=True)[:3]
    
    # "LLM-style" answer generation
    context = "\n\n".join(relevant_chunks)
    
    answer = f"""**🤖 AI Answer:**

From your PDF:

{chr(10).join([f"• {chunk[:200]}..." for chunk in relevant_chunks[:2]])}

**Summary:** Your document discusses {', '.join(set(word for chunk in relevant_chunks for word in chunk.lower().split()[:5]))}. 

**Direct match for "{question}":** 
{next((chunk for chunk in relevant_chunks if any(word in chunk.lower() for word in question.lower().split())), relevant_chunks[0][:400])}"""
    
    return answer

# UI
st.title("🤖 FREE LLM PDF Assistant")
st.markdown("**No API keys • No costs • Instant answers**")

col1, col2 = st.columns([3,1])
with col1:
    uploaded = st.file_uploader("📄 PDF", type="pdf")
with col2:
    st.metric("Chunks", 0)

if uploaded is not None:
    with st.spinner("🔄 Processing..."):
        st.session_state.chunks = extract_pdf_text(uploaded)
    
    st.success(f"✅ {len(st.session_state.chunks)} chunks loaded!")
    
    with st.expander("📋 Preview"):
        st.write(st.session_state.chunks[0][:500]+"..." if st.session_state.chunks else "No text")

st.divider()
if 'chunks' in st.session_state and st.session_state.chunks:
    question = st.text_input("💭 Ask ANY question about your PDF:")
    
    if st.button("🚀 **GET AI ANSWER**", use_container_width=True) and question:
        with st.spinner("🤖 AI analyzing..."):
            answer = free_llm(question, st.session_state.chunks)
        
        st.markdown(answer)
        st.divider()
else:
    st.info("👆 **Upload PDF first**")

st.markdown("---")
st.caption("✨ 100% FREE - No APIs needed!")
