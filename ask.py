import streamlit as st
from pathlib import Path
import time
from dotenv import load_dotenv
import os

# 🔥 SESSION STATE INITIALIZATION (CRITICAL FOR STREAMLIT CLOUD)
if "rag_system_ready" not in st.session_state:
    st.session_state.rag_system_ready = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "documents" not in st.session_state:
    st.session_state.documents = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "sources" not in st.session_state:
    st.session_state.sources = []

load_dotenv()

# 🔥 MODERN DARK THEME + CUSTOM CSS
st.set_page_config(
    page_title="📄 AI PDF Assistant", 
    page_icon="✨", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
        color: #e2e8f0;
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        background: linear-gradient(145deg, #1e293b, #334155);
        color: #f8fafc;
        border: 2px solid #3b82f6;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 16px;
    }
    .stButton > button {
        background: linear-gradient(45deg, #3b82f6, #8b5cf6, #ec4899);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 14px 32px;
        font-weight: 700;
        font-size: 16px;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(59, 130, 246, 0.5);
        background: linear-gradient(45deg, #2563eb, #7c3aed, #db2777);
    }
    .answer-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 20px;
        padding: 24px;
        border: 1px solid #475569;
        box-shadow: 0 20px 40px rgba(0,0,0,0.3);
        margin: 20px 0;
    }
    .sources-card {
        background: linear-gradient(145deg, #0f172a, #1e293b);
        border-radius: 16px;
        padding: 20px;
        border-left: 4px solid #10b981;
    }
    .metric-container {
        background: linear-gradient(135deg, #3b82f6, #8b5cf6);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# 🚀 HERO HEADER
st.markdown("""
<div style='text-align: center; padding: 3rem 2rem; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #8b5cf6 100%); border-radius: 24px; margin-bottom: 3rem; box-shadow: 0 25px 50px rgba(59, 130, 246, 0.3);'>
    <div style='font-size: 4rem; margin-bottom: 1rem;'>📄🧠✨</div>
    <h1 style='font-size: 3rem; font-weight: 900; margin: 0; background: linear-gradient(45deg, #ffffff, #e0e7ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>AI-PDF Assistant</h1>
    <p style='font-size: 1.3rem; opacity: 0.95; margin: 1rem 0 0 0;'>Production-Ready RAG • Streamlit Cloud • Zero Cost</p>
</div>
""", unsafe_allow_html=True)

# 🔥 MOCK RAG FUNCTIONS (Replace with your actual implementations)
def mock_load_documents(file_path):
    """Mock PDF loader - replace with real loader"""
    return [f"Document from {file_path.name} - Page 1 content...", 
            f"Document from {file_path.name} - Page 2 content..."]

def mock_create_vectorstore(docs):
    """Mock vectorstore - replace with Qdrant"""
    return {"docs": docs, "ready": True}

def mock_query_rag_system(question, top_k):
    """Mock RAG query - replace with real Qdrant query"""
    return f"""🤖 Based on your uploaded PDFs, here's what I found about "{question}":

**Key Findings:**
• Your documents contain relevant information about the query topic
• Top {top_k} sources were analyzed from your PDFs
• Answer generated using local vector search (Qdrant)

**Sources Used:**
1. Your uploaded PDF document
2. Page content matched your question

*Note: This is a demo. Full RAG implementation requires Qdrant + embeddings.*

**Production Stack (Local):**


"""

def save_uploaded_pdf(file):
    """Save uploaded PDF locally"""
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_bytes = file.getbuffer()
    file_path.write_bytes(file_bytes)
    return file_path

# 📤 UPLOAD SECTION (DIRECT PROCESSING - NO INNGEST)
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("<h2 style='color: #3b82f6;'>📤 Upload PDF</h2>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False, 
                               help="Supports all PDF formats up to 200MB")

if uploaded is not None:
    with st.spinner("📥 Processing your PDF..."):
        path = save_uploaded_pdf(uploaded)
        
        # 🔥 DIRECT PROCESSING (NO INNGEST)
        documents = mock_load_documents(path)
        st.session_state.documents.extend(documents)
        
        # Create vectorstore directly
        if st.session_state.vectorstore is None:
            st.session_state.vectorstore = mock_create_vectorstore(documents)
        else:
            st.session_state.vectorstore["docs"].extend(documents)
        
        st.session_state.rag_system_ready = True
        st.session_state.sources = [path.name]  # Track sources
        
    st.success(f"✅ **{path.name}** processed! ({len(st.session_state.documents)} pages indexed)")
    st.balloons()

st.divider()

# ❓ QUERY SECTION (DIRECT RAG - NO INNGEST)
st.markdown("<h2 style='color: #8b5cf6;'>❓ Ask Questions</h2>", unsafe_allow_html=True)

# Show chat history
if st.session_state.chat_history:
    st.markdown("### 💬 Chat History")
    for msg in st.session_state.chat_history[-4:]:  # Last 4 messages
        if msg["role"] == "user":
            st.markdown(f"**👤 You:** {msg['content']}")
        else:
            st.markdown(f"**🤖 AI:** {msg['content'][:200]}...")

with st.form("rag_query_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        question = st.text_input("💭 Your question", placeholder="e.g. What is Python used for?")
    with col2:
        top_k = st.number_input("📊 Top K", min_value=1, max_value=20, value=5, step=1)
    
    submitted = st.form_submit_button("🔍 **Generate Answer**", use_container_width=True)

if submitted and question.strip():
    if st.session_state.rag_system_ready:
        with st.spinner("🔍 Searching your PDFs..."):
            # 🔥 DIRECT RAG QUERY (NO INNGEST)
            response = mock_query_rag_system(question.strip(), int(top_k))
            st.session_state.chat_history.append({"role": "user", "content": question})
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # 🎨 ANSWER CARD
            st.markdown("""
            <div class='answer-card'>
                <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 16px;'>
                    <span style='font-size: 2rem;'>🤖</span>
                    <h3 style='margin: 0; color: #60a5fa;'>AI Answer from Your PDFs</h3>
                </div>
                <div style='font-size: 1.1rem; line-height: 1.7; color: #e2e8f0;'>
                    """ + response.replace("\n", "<br>") + """
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 📊 METRIC CARD
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div class='metric-container'>
                    <div style='font-size: 2.5rem; margin-bottom: 8px;'>📄</div>
                    <div style='font-size: 1.8rem; font-weight: 700; color: white;'>{len(set(st.session_state.sources))}</div>
                    <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem;'>PDF Sources</div>
                </div>
                """, unsafe_allow_html=True)
            
            # 📚 SOURCES CARD
            if st.session_state.sources:
                st.markdown("""
                <div class='sources-card'>
                    <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 16px;'>
                        <span style='font-size: 1.5rem;'>📚</span>
                        <h4 style='margin: 0; color: #10b981;'>Sources Used</h4>
                    </div>
                """, unsafe_allow_html=True)
                
                unique_sources = list(set(st.session_state.sources))
                for i, source in enumerate(unique_sources, 1):
                    st.markdown(f"**{i}.** `{source}`", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
                
            st.balloons()
            st.success("✅ Ready for next question!")
            st.rerun()
    else:
        st.error("❌ Please upload PDFs first and process documents!")
        st.info("📚 **Steps:** 1️⃣ Upload PDF → 2️⃣ Wait for processing → 3️⃣ Ask questions")

# 📈 STATUS DASHBOARD
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📄 PDFs Processed", len(st.session_state.documents) if st.session_state.documents else 0)
with col2:
    st.metric("💬 Chat Messages", len(st.session_state.chat_history))
with col3:
    st.metric("✅ RAG Ready", "Yes" if st.session_state.rag_system_ready else "No")

# 🎉 FOOTER
st.markdown("""
<div style='text-align: center; padding: 2rem; background: rgba(15, 23, 42, 0.5); border-radius: 16px; margin-top: 3rem;'>
    <h3 style='color: #94a3b8;'>🚀 Production RAG Stack</h3>
    <p style='color: #64748b; margin-bottom: 1rem;'>Streamlit Cloud • Qdrant Ready • Zero Cost</p>
    <div style='font-size: 0.9rem; color: #475569;'>
        <strong>Full Stack (Local):</strong><br>
        T1: <code>docker run -p 6333:6333 qdrant/qdrant</code><br>
        T2: <code>streamlit run ask.py</code>
    </div>
</div>
""", unsafe_allow_html=True)
