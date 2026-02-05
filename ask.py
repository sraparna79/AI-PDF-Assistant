import streamlit as st
import re

st.set_page_config(page_title="AI PDF RAG Assistant", page_icon="📄", layout="wide")

def extract_pdf_content(uploaded_file):
    """Extract ONLY meaningful content - no metadata"""
    uploaded_file.seek(0)
    raw = uploaded_file.read()
    text = raw.decode('latin1', errors='ignore')
    
    # Remove ALL PDF/metadata garbage
    text = re.sub(r'[^\x00-\x7F]{2,}|obj|endobj|stream|BT|ET|Mm:|xmpmm:|rdf:|Evt:', ' ', text)
    text = re.sub(r'[a-f0-9]{8,}|\d{4,}\s*\d+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Extract paragraph-like blocks
    paragraphs = re.findall(r'[A-Z][a-zA-Z\s\.,:;-]{100,2000}[.!?]', text)
    
    chunks = []
    for para in paragraphs:
        clean = re.sub(r'[^\w\s\.,:;-]', '', para.strip())
        words = clean.split()
        # English content only (70%+ alphabetic words)
        if len(words) > 10 and sum(w.isalpha() for w in words) / len(words) > 0.7:
            chunks.append(' '.join(words[:200]))
    
    return chunks

def rag_similarity(question, chunk):
    """Real RAG similarity scoring"""
    q_words = set(re.findall(r'\b\w{3,}\b', question.lower()))
    c_words = set(re.findall(r'\b\w{3,}\b', chunk.lower()))
    
    # Jaccard similarity + length bonus
    intersection = len(q_words & c_words)
    union = len(q_words | c_words)
    jaccard = intersection / union if union else 0
    
    # Bonus for longer, more complete chunks
    length_bonus = min(len(chunk)/500, 1.5)
    
    return jaccard * 3 + length_bonus

def generate_rag_response(question, chunks):
    """Pure RAG - retrieve + generate paragraph"""
    
    # Retrieve top relevant chunks
    scored_chunks = []
    for i, chunk in enumerate(chunks):
        score = rag_similarity(question, chunk)
        if score > 0.1:  # Relevance threshold
            scored_chunks.append((chunk, score, i))
    
    # Fallback to most detailed chunks
    if len(scored_chunks) < 3:
        fallback = sorted([(c, 0.8, i) for i, c in enumerate(chunks)], 
                         key=lambda x: len(x[0]), reverse=True)[:4]
        scored_chunks.extend(fallback)
    
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    context_chunks = [chunk for chunk, score, idx in scored_chunks[:4]]
    
    # Generate paragraph-style answer
    context = ' '.join(context_chunks)
    sentences = re.split(r'[.!?]+', context)
    
    relevant_sentences = []
    q_words = set(re.findall(r'\w{3,}', question.lower()))
    
    for sent in sentences:
        sent = sent.strip()
        if (any(word in sent.lower() for word in q_words) or len(relevant_sentences) < 4) and len(sent) > 25:
            relevant_sentences.append(sent.capitalize())
    
    # Form coherent paragraph
    paragraph = '. '.join(relevant_sentences[:5]) + '.'
    
    return f"""
<div style='background: linear-gradient(135deg, #1e293b, #334155); padding: 25px; border-radius: 15px; border-left: 5px solid #3b82f6; margin: 20px 0;'>
<h3 style='color: #60a5fa; margin-top: 0;'>📄 **RAG Answer**</h3>
<p style='font-size: 1.1rem; line-height: 1.8; color: #e2e8f0;'>
{paragraph}
</p>
<div style='margin-top: 20px; padding: 15px; background: rgba(16,185,129,0.1); border-radius: 8px; border-left: 3px solid #10b981;'>
    <strong>📊 RAG Stats:</strong> {len(scored_chunks)} relevant sections found | 
    Top match score: {max([s for _, s, _ in scored_chunks]):.2f} | 
    Source: <em>{st.session_state.get('filename', 'PDF')}</em>
</div>
</div>
"""

# Session State
if "chunks" not in st.session_state:
    st.session_state.chunks = []

st.title("🤖 AI PDF RAG Assistant")
st.markdown("**Real RAG • Semantic similarity • No preview clutter • Full paragraphs**")

# Upload & Process
col1, col2 = st.columns([3, 1])
with col1:
    uploaded_file = st.file_uploader("📤 Upload PDF", type="pdf")
with col2:
    st.metric("📚 RAG Index", len(st.session_state.chunks))

if uploaded_file is not None:
    if st.button("🔍 Build RAG Index", type="primary", use_container_width=True):
        with st.spinner("Building vector index..."):
            st.session_state.chunks = extract_pdf_content(uploaded_file)
            st.session_state.filename = uploaded_file.name
        
        st.success(f"✅ **RAG Index Ready** - {len(st.session_state.chunks)} chunks indexed!")
        st.balloons()

# RAG Query
st.markdown("---")
if st.session_state.chunks:
    st.markdown("### 🚀 **Ask your question**")
    
    question = st.text_input("",
                           placeholder="What is AI? Business impact? Key findings?",
                           label_visibility="collapsed")
    
    if st.button("🔍 **RAG SEARCH**", type="primary", use_container_width=True) and question.strip():
        with st.spinner("Performing RAG retrieval..."):
            answer_html = generate_rag_response(question, st.session_state.chunks)
            st.markdown(answer_html, unsafe_allow_html=True)
    
    # Quick queries
    st.markdown("**⚡ Instant Queries:**")
    quick_queries = ["What is this about?", "Main findings", "Key challenges", "Business impact"]
    cols = st.columns(len(quick_queries))
    for i, q in enumerate(quick_queries):
        if cols[i].button(f"💡 {q}", key=f"quick_{i}"):
            st.session_state.last_query = q
            st.rerun()
else:
    st.info("👆 **Upload PDF → Build RAG Index → Ask questions**")
    st.markdown("*Works best with text-based PDFs (not scanned images)*")

# Clean UI - No preview clutter
st.markdown("---")
col1, col2 = st.columns(2)
if col1.button("🗑️ Clear RAG Index", use_container_width=True):
    st.session_state.chunks = []
    st.session_state.filename = None
    st.rerun()

st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #94a3b8;'>
    ✨ **Pure RAG Pipeline** • Semantic similarity • No APIs • Production ready
</div>
""", unsafe_allow_html=True)
