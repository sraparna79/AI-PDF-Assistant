import streamlit as st
import ollama
import re

st.set_page_config(page_title="LLM-Powered PDF RAG", layout="wide")

# Your existing PDF extraction...
def extract_pdf_text(uploaded_file):
    # [Your working extraction code]
    pass

@st.cache_resource
def init_llm():
    return "llama3.2"  # 1B model - fast & free

def rag_llm_query(question: str, chunks: list):
    # Simple keyword search for context
    context_chunks = []
    query_words = question.lower().split()
    
    for chunk in chunks:
        if any(word in chunk.lower() for word in query_words):
            context_chunks.append(chunk[:500])
            if len(context_chunks) >= 3:
                break
    
    context = "\n\n".join(context_chunks)
    
    prompt = f"""Using ONLY the following PDF context, answer the question concisely.

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
    
    try:
        stream = ollama.chat(
            model=init_llm(),
            messages=[{'role': 'user', 'content': prompt}],
            stream=True
        )
        
        response = st.empty()
        full_answer = ""
        for chunk in stream:
            full_answer += chunk['message']['content']
            response.markdown(full_answer + "▌")
        
        return full_answer
    except:
        return f"Found context but LLM unavailable:\n\n{context[:800]}..."

# UI
st.title("🤖 LLM-Powered PDF Assistant")

# PDF Upload + Processing (your code)
uploaded = st.file_uploader("📄 PDF")
if uploaded:
    chunks = extract_pdf_text(uploaded)
    st.session_state.chunks = chunks

# LLM Chat
if st.session_state.chunks:
    question = st.text_input("💭 Ask the LLM about your PDF:")
    
    if st.button("🚀 Get LLM Answer") and question:
        with st.spinner("LLM generating..."):
            answer = rag_llm_query(question, st.session_state.chunks)
        
        st.markdown("### 🤖 **LLM Answer**")
        st.write(answer)
