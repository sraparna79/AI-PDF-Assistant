import streamlit as st
import re
import tiktoken  # For token counting
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

st.set_page_config(page_title="AI PDF Assistant", layout="wide")

# === PDF PROCESSING ===
def extract_pdf_text(uploaded_file):
    raw_content = uploaded_file.getvalue().decode('latin1', errors='ignore')
    blocks = re.findall(r'[a-zA-Z]{3,}[a-zA-Z0-9\s\.,:;()\-]{50,1000}', raw_content)
    
    chunks = []
    for block in blocks[:20]:
        clean = re.sub(r'\s+', ' ', block.strip())
        if len(clean) > 80:
            chunks.append(clean[:800])
    return chunks

# === LLM OPTIONS (ALL FREE TIER) ===
def get_llm_response(question: str, context: str, model="gpt-3.5-turbo"):
    """Multiple FREE LLM backends"""
    
    # Option 1: Together AI (FREE 50 req/min)
    if st.secrets.get("TOGETHER_API_KEY"):
        import openai
        client = openai.OpenAI(
            api_key=st.secrets["TOGETHER_API_KEY"],
            base_url="https://api.together.xyz/v1"
        )
        model = "mistralai/Mixtral-8x7B-Instruct-v0.1"
    
    # Option 2: OpenRouter (FREE tier)
    elif st.secrets.get("OPENROUTER_API_KEY"):
        import openai
        client = openai.OpenAI(
            api_key=st.secrets["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1"
        )
        model = "google/gemma-2-9b-it:free"
    
    # Option 3: Fallback mock LLM (always works)
    else:
        return f"""Based on PDF content:

CONTEXT FOUND:
{context[:1000]}...

This is a FREE demo LLM. Add Together AI or OpenRouter API key to Streamlit Secrets for real LLM responses."""

    prompt = f"""Use ONLY the following PDF context to answer.

CONTEXT:
{context}

QUESTION: {question}

Answer concisely using ONLY the context above:"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.1
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"LLM Error: {str(e)[:200]}\n\nFallback context:\n{context[:500]}"

# === SESSION STATE ===
if "chunks" not in st.session_state:
    st.session_state.chunks = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# === UI ===
st.title("🤖 LLM-Powered PDF RAG Assistant")
st.markdown("**Upload PDF → Ask natural questions → Get AI answers**")

# PDF Upload
col1, col2 = st.columns([3, 1])
with col1:
    uploaded = st.file_uploader("📄 Choose PDF", type="pdf")
with col2:
    st.metric("Chunks", len(st.session_state.chunks))

if uploaded is not None and uploaded != getattr(st.session_state, 'last_pdf', None):
    with st.spinner("🔄 Processing PDF..."):
        st.session_state.chunks = extract_pdf_text(uploaded)
        st.session_state.last_pdf = uploaded
        st.session_state.chat_history = []
    
    st.success(f"✅ Loaded {len(st.session_state.chunks)} chunks")
    
    with st.expander("📋 Preview"):
        st.write(st.session_state.chunks[0][:500] + "..." if st.session_state.chunks else "No text")

# LLM Setup
st.divider()
if st.session_state.chunks:
    st.subheader("💭 Chat with your PDF")
    
    # API Key input (Streamlit Secrets recommended)
    api_key = st.text_input("🔑 Together AI / OpenRouter API Key:", type="password")
    
    # Chat interface
    question = st.chat_input("Ask about your PDF...")
    
    if question:
        with st.spinner("🤖 LLM thinking..."):
            # Find relevant context
            query_words = question.lower().split()
            context_chunks = []
            
            for chunk in st.session_state.chunks:
                if any(word in chunk.lower() for word in query_words):
                    context_chunks.append(chunk)
                    if len(context_chunks) >= 3:
                        break
            
            context = "\n\n".join(context_chunks)
            
            # Get LLM response
            answer = get_llm_response(question, context)
            
            # Store in history
            st.session_state.chat_history.append({"question": question, "answer": answer})
        
        # Display chat history
        for chat in st.session_state.chat_history[-5:]:
            with st.chat_message("user"):
                st.write(chat["question"])
            with st.chat_message("assistant"):
                st.write(chat["answer"])
else:
    st.info("👆 Upload PDF first")

# Secrets instructions
with st.sidebar.expander("🚀 Production Setup"):
    st.markdown("""
    **Add to Streamlit Cloud Secrets:**
    ```
    TOGETHER_API_KEY = your_key_here
    ```
    **Get FREE keys:**
    - Together AI: together.ai (50 req/min free)
    - OpenRouter: openrouter.ai (free tier models)
    """)
