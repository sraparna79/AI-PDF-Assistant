import streamlit as st
import re

st.set_page_config(page_title="FREE AI PDF Assistant", layout="wide")

def extract_pdf_text(uploaded_file):
    """Extract MORE text chunks for better coverage"""
    uploaded_file.seek(0)
    raw = uploaded_file.read()
    raw_text = raw.decode('latin1', errors='ignore')
    
    # Clean aggressively
    raw_text = re.sub(r'[a-f0-9]{8,}|Mm:|xmpmm:|rdf:|Evt:|obj|endobj', ' ', raw_text, flags=re.I)
    raw_text = re.sub(r'\s+', ' ', raw_text)
    
    # Extract LONGER blocks (full paragraphs)
    blocks = re.findall(r'[A-Za-z]{4,}.*?[.!?](?=\s[A-Z]{1,})|[A-Za-z]{4,}[.!?]', raw_text)
    
    chunks = []
    for block in blocks[:50]:  # MORE chunks
        clean = re.sub(r'[^\w\s\.,:;\'-]', '', block.strip())
        if len(clean) > 100:  # LONGER chunks
            chunks.append(clean[:1500])  # Much longer
    return chunks

def generate_paragraph_answer(question: str, chunks: list) -> str:
    """Generate FULL PARAGRAPH answers with VARIATION"""
    
    query_words = set(question.lower().split())
    scored_chunks = []
    
    # Advanced scoring - different chunks for different questions
    for i, chunk in enumerate(chunks):
        # Multiple scoring methods for diversity
        word_score = sum(1 for word in query_words if word in chunk.lower())
        phrase_score = len(re.findall('|'.join(query_words), chunk.lower()))
        length_bonus = len(chunk) / 1000  # Favor longer chunks
        
        total_score = word_score * 3 + phrase_score * 5 + length_bonus
        if total_score > 1:
            scored_chunks.append((chunk, total_score, i))
    
    # Fallback: diverse chunks
    if not scored_chunks:
        # Rotate chunks based on question hash for variety
        seed = hash(question) % len(chunks)
        fallback = [(chunks[(seed + i) % len(chunks)], 1.0, i) for i in range(4)]
        scored_chunks = fallback
    
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, score, idx in scored_chunks[:4]]
    
    # Build FULL PARAGRAPH response
    answer = f"**📄 Answer to: '{question}'**\n\n"
    
    # Combine multiple chunks into coherent paragraph
    full_context = " ".join(top_chunks)
    
    # Extract 2-3 full sentences
    sentences = re.split(r'[.!?]+', full_context)
    relevant_sentences = []
    
    for sent in sentences:
        sent = sent.strip()
        if len(sent) > 30 and any(word in sent.lower() for word in query_words):
            relevant_sentences.append(sent.capitalize())
        elif len(relevant_sentences) < 3 and len(sent) > 40:
            relevant_sentences.append(sent.capitalize())
    
    # Create paragraph
    paragraph = ". ".join(relevant_sentences[:4]) + "."
    
    answer += f"**{paragraph}**\n\n"
    answer += f"**📊 Found in {len(scored_chunks)} sections** of your PDF\n"
    answer += f"**📁 Document**: {st.session_state.get('filename', 'PDF')}"
    
    return answer

# Session state
if "chunks" not in st.session_state:
    st.session_state.chunks = []

# UI
st.title("🤖 FREE AI PDF Assistant") 
st.markdown("**Seeking Answers • Question and Answers • No APIs needed**")

col1, col2 = st.columns([3,1])
with col1:
    uploaded = st.file_uploader("📄 Upload PDF", type="pdf")
with col2:
    st.metric("Chunks", len(st.session_state.chunks))

# Process PDF
if uploaded is not None:
    if st.button("🚀 Process PDF", type="primary"):
        with st.spinner("Extracting paragraphs..."):
            st.session_state.chunks = extract_pdf_text(uploaded)
            st.session_state.filename = uploaded.name
        
        st.success(f"✅ **{len(st.session_state.chunks)} paragraphs** extracted!")
        st.balloons()
        st.rerun()

st.divider()

# Query interface
if st.session_state.chunks:
    st.markdown("### 💭 Ask about your PDF")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_input("", 
                               placeholder="What is AI? Business impact? Key findings?", 
                               label_visibility="collapsed")
    with col2:
        st.info(f"**{len(st.session_state.chunks)}** chunks ready")
    
    if st.button("🤖 Generate Paragraph Answer", use_container_width=True, type="primary") and question.strip():
        with st.spinner("Generating full answer..."):
            answer = generate_paragraph_answer(question, st.session_state.chunks)
            st.markdown(answer)
    
    # Quick questions with variety
    st.markdown("**🔄 Quick Questions:**")
    quicks = ["Methodology", "Interesting", "Key challenges", "Main findings"]
    cols = st.columns(len(quicks))
    for i, q in enumerate(quicks):
        if cols[i].button(f"💡 {q}", key=f"quick{i}"):
            st.session_state.last_q = q
            st.rerun()
else:
    st.info("👆 **Upload & Process first**")

# Reset
if st.button("🗑️ Clear All", use_container_width=True):
    st.session_state.chunks = []
    st.session_state.filename = None
    st.rerun()

st.markdown("---")
st.caption("✨ **FREE** - Full paragraphs • question & answers • Try it")
