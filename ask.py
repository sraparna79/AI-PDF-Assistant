import asyncio
from pathlib import Path
import time
import streamlit as st
import inngest
from dotenv import load_dotenv
import os
import requests
import streamlit as st

# 🔥 ADD THESE 4 LINES 
if "rag_system_ready" not in st.session_state:
    st.session_state.rag_system_ready = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "documents" not in st.session_state:
    st.session_state.documents = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None


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
    <h1 style='font-size: 3rem; font-weight: 900; margin: 0; background: linear-gradient(45deg, #ffffff, #e0e7ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>AI-Powered PDF Assistant</h1>
    <p style='font-size: 1.3rem; opacity: 0.95; margin: 1rem 0 0 0;'>Production-Ready • Zero Cost • Inngest-Powered</p>
</div>
""", unsafe_allow_html=True)

@st.cache_resource
def get_inngest_client() -> inngest.Inngest:
    return inngest.Inngest(app_id="rag_app", is_production=False)

def save_uploaded_pdf(file) -> Path:
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    file_path = uploads_dir / file.name
    file_bytes = file.getbuffer()
    file_path.write_bytes(file_bytes)
    return file_path

async def send_rag_ingest_event(pdf_path: Path) -> None:
    client = get_inngest_client()
    await client.send(
        inngest.Event(
            name="rag/ingest_pdf",
            data={
                "pdf_path": str(pdf_path.resolve()),
                "source_id": pdf_path.name,
            },
        )
    )

async def send_rag_query_event(question: str, top_k: int):
    client = get_inngest_client()
    result = await client.send(
        inngest.Event(
            name="rag/query_pdf_ai",
            data={"question": question, "top_k": top_k},
        )
    )
    return result[0]

def _inngest_api_base() -> str:
    return os.getenv("INNGEST_API_BASE", "http://127.0.0.1:8288/v1")

def fetch_runs(event_id: str) -> list[dict]:
    url = f"{_inngest_api_base()}/events/{event_id}/runs"
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()
    return data.get("data", [])

def wait_for_run_output(event_id: str, timeout_s: float = 120.0, poll_interval_s: float = 0.5) -> dict:
    start = time.time()
    last_status = None
    while True:
        runs = fetch_runs(event_id)
        if runs:
            run = runs[0]
            status = run.get("status")
            last_status = status or last_status
            if status in ("Completed", "Succeeded", "Success", "Finished"):
                return run.get("output") or {}
            if status in ("Failed", "Cancelled"):
                raise RuntimeError(f"Function run {status}")
        if time.time() - start > timeout_s:
            raise TimeoutError(f"Timed out waiting for run output (last status: {last_status})")
        time.sleep(poll_interval_s)

# 📤 UPLOAD SECTION
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("<h2 style='color: #3b82f6;'>📤 Upload PDF</h2>", unsafe_allow_html=True)
    uploaded = st.file_uploader("Choose a PDF", type=["pdf"], accept_multiple_files=False, 
                               help="Supports all PDF formats up to 200MB")

if uploaded is not None:
    with st.spinner("🚀 Uploading & triggering Inngest pipeline..."):
        path = save_uploaded_pdf(uploaded)
        asyncio.run(send_rag_ingest_event(path))
        time.sleep(0.5)
    st.success(f"✅ **{path.name}** processed! Check <a href='http://localhost:8288' target='_blank'>Inngest Dashboard</a>", 
               unsafe_allow_html=True)

st.divider()

# ❓ QUERY SECTION  
st.markdown("<h2 style='color: #8b5cf6;'>❓ Ask Questions</h2>", unsafe_allow_html=True)

with st.form("rag_query_form", clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        question = st.text_input("💭 Your question", placeholder="e.g. What is Python used for?")
    with col2:
        top_k = st.number_input("📊 Top K", min_value=1, max_value=20, value=5, step=1)
    
    submitted = st.form_submit_button("🔍 **Generate Answer**", use_container_width=True)

if submitted and question.strip():
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 🎯 Animate search
    # event_id = asyncio.run(send_rag_query_event(question.strip(), int(top_k)))
    if st.session_state.rag_system_ready:
        response = query_rag_system(question.strip(), top_k=int(top_k))
        st.session_state.chat_history.append({"role": "user", "content": question})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
    else:
        st.error("❌ RAG system not ready. Upload PDFs first!")

    for i in range(101):
        progress_bar.progress(i)
        status_text.markdown(f"**🔍 Searching {len(question)} vectors...** {i}%")
        time.sleep(0.03)
    
    try:
        output = wait_for_run_output(event_id)
        answer = output.get("answer", "")
        sources = output.get("sources", [])
        
        # 🎨 ANSWER CARD
        st.markdown("""
        <div class='answer-card'>
            <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 16px;'>
                <span style='font-size: 2rem;'>🤖</span>
                <h3 style='margin: 0; color: #60a5fa;'>AI Answer</h3>
            </div>
            <div style='font-size: 1.1rem; line-height: 1.7; color: #e2e8f0;'>
                """ + answer.replace("\n", "<br>") + """
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 📊 METRIC CARD
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class='metric-container'>
                <div style='font-size: 2.5rem; margin-bottom: 8px;'>📄</div>
                <div style='font-size: 1.8rem; font-weight: 700; color: white;'>{len(set(sources)) if sources else 0}</div>
                <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem;'>Unique Sources</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 📚 SOURCES CARD (UNIQUE SOURCES)
        if sources:
            st.markdown("""
            <div class='sources-card'>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 16px;'>
                    <span style='font-size: 1.5rem;'>📚</span>
                    <h4 style='margin: 0; color: #10b981;'>Sources Used</h4>
                </div>
            """, unsafe_allow_html=True)
            
            unique_sources = list(set(sources))
            for i, source in enumerate(unique_sources, 1):
                st.markdown(f"**{i}.** `{source}`", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("🔗 Check http://localhost:8288 for detailed logs")

# 📈 DASHBOARD LINK
st.markdown("""
<div style='text-align: center; padding: 2rem; background: rgba(15, 23, 42, 0.5); border-radius: 16px; margin-top: 3rem;'>
    <h3 style='color: #94a3b8;'>📊 Live Dashboard</h3>
    <a href='http://localhost:8288' target='_blank' 
       style='display: inline-block; background: linear-gradient(45deg, #10b981, #059669); 
              color: white; padding: 12px 32px; border-radius: 25px; 
              text-decoration: none; font-weight: 700; font-size: 1.1rem;'>
        Open Inngest Dashboard →
    </a>
</div>
""", unsafe_allow_html=True)
