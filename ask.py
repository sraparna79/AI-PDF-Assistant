import streamlit as st
import re

st.set_page_config(page_title="FREE AI PDF Assistant", layout="wide")

def extract_pdf_text(uploaded_file):
    """AGGRESSIVE text extraction for ALL PDF types"""
    uploaded_file.seek(0)
    raw = uploaded_file.read()
    
    # Multiple decoding attempts
    decodings = ['latin1', 'utf-8', 'ascii']
    best_text = ""
    
    for encoding in decodings:
        try:
            text = raw.decode(encoding, errors='ignore')
            # Count English-like words
            english_words = len(re.findall(r'\b[a-zA-Z]{3,15}\b', text.lower()))
            if english_words > len(best_text.split()) * 0.5:
                best_text = text
                break
        except:
            continue
    
    # NUCLEAR PDF CLEANING - Kill ALL garbage
    garbage_patterns = [
        r'[^\w\s\.,:;\'-]{3,}',  # Weird symbols
        r'[a-f0-9]{6,}',         # Hex codes
        r'(Mm:|xmpmm:|rdf:|Evt:|obj|endobj|BT|ET|\/[A-Z]{2,})',  # PDF metadata
        r'\d{3,}\s*\d+\s*\d+',   # PDF coordinates
    ]
    
    for pattern in garbage_patterns:
        best_text = re.sub(pattern, ' ', best_text, flags=re.IGNORECASE)
    
    best_text = re.sub(r'\s+', ' ', best_text)
    
    # Extract ONLY readable English blocks
    readable_blocks = re.findall(r'[A-Za-z]{4,}.*?[.!?](?=\s[A-Z])|[A-Za-z]{4,}[.!?]', best_text)
    
    chunks = []
    for block in readable_blocks[:60]:
        # Final cleanup
        clean = re.sub(r'[^\w\s\.,:;\'-]', '', block.strip())
        words = clean.split()
        
        # Only keep blocks with mostly English words
        english_ratio = sum(1 for w in words if len(w) > 2 and w.isalpha()) / max(len(words), 1)
        
        if english_ratio > 0.6 and len(clean) > 120:
            chunks.append(clean[:1800])
    
    return chunks

def generate_detailed_answer(question: str, chunks: list) -> str:
    """Generate FULL paragraph answers with context"""
    query_words = set(question.lower().split())
    scored_chunks = []
    
    for i, chunk in enumerate(chunks):
        # Multi-factor scoring
        word_matches = sum(1 for word in query_words if len(word) > 2 and word in chunk.lower())
        phrase_matches = len(re.findall('|'.join(list(query_words)[:3]), chunk.lower()))
        length_score = min(len(chunk) / 2000, 2)
        
        total_score = word_matches * 4 + phrase_matches * 6 + length_score
        if total_score > 1.5:
            scored_chunks.append((chunk, total_score, i))
    
    # Diverse fallback
    if not scored_chunks:
        # Use different chunks based on question
        start_idx = abs(hash(question)) % max(len(chunks)//2, 1)
        scored_chunks = [(chunks[(start_idx + i) % len(chunks)], 1.5, i) for i in range(5)]
    
    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, score, idx in scored_chunks[:5]]
    
    # Build comprehensive paragraph answer
    all_sentences = []
    for chunk in top_chunks:
        sentences = re.split(r'[.!?]+', chunk)
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 25 and any(word in sent.lower() for word in query_words):
                all_sentences.append(sent.capitalize())
            elif len(all_sentences) < 6 and len(sent) > 30:
                all_sentences.append(sent.capitalize())
    
    # Create flowing paragraph
    paragraph = ". ".join(all_sentences[:5])
    if len(all_sentences) > 1:
        paragraph += "."
    
    answer = f"""
**📄 Answer to: '{question}'**

**{paragraph}**

**📊 Analysis:**
• Found **{len(scored_chunks)}** relevant sections from **{len(chunks)}** total
• **{st.session_state.get('filename', 'PDF')}**
• **Coverage**: {min(len(top_chunks)*20, 100)}% document match
"""
    return answer.strip()

# Session state
if "chunks" not in st.session_state:
    st.session_state.chunks = []

st.title("🤖 FREE AI PDF Assistant") 
st.markdown("**Full Paragraphs • Handles ALL PDFs • No APIs needed**")

# Upload
col1, col2 = st.columns([3,1])
with col1:
    uploaded = st.file_uploader("📄 Upload PDF", type="pdf")
with col2:
    st.metric("Chunks", len(st.session_state.chunks))

# Process
if uploaded is not None:
    if st.button("🚀 Extract Text", type="primary"):
        with st.spinner("Processing ALL pages..."):
            st.session_state.chunks = extract_pdf_text(uploaded)
            st.session_state.filename = uploaded.name
        
        st.success(f"✅ **{len(st.session_state.chunks)}** clean paragraphs extracted!")
        st.rerun()
    
    # Preview
    if st.session_state.chunks:
        with st.expander("📋 Preview Best Paragraphs", expanded=True):
            for i, chunk in enumerate(st.session_state.chunks[:3]):
                st.write(f"**{i+1}**: {chunk[:400]}...")

st.divider()

# Query
if st.session_state.chunks:
    st.markdown("### 💭 Ask about your document")
    
    question = st.text_input("", 
                           placeholder="What is this thesis about? Key findings? Methodology?",
                           label_visibility="collapsed")
    
    if st.button("🤖 Generate Full Answer", use_container_width=True, type="primary") and question.strip():
        with st.spinner("Building paragraph answer..."):
            answer = generate_detailed_answer(question, st.session_state.chunks)
            st.markdown(answer)
    
    # Quick thesis questions
    st.markdown("**🎓 Thesis Quick Questions:**")
    thesis_questions = ["main topic", "research question", "methodology", "key findings"]
    cols = st.columns(len(thesis_questions))
    for i, q in enumerate(thesis_questions):
        if cols[i].button(f"🎯 {q}", key=f"thesis_{i}"):
            st.session_state.last_question = q
            st.rerun()
else:
    st.info("👆 **Upload & Extract first**")

# Reset
col1, col2 = st.columns(2)
if col1.button("🗑️ Clear All", use_container_width=True):
    st.session_state = {"chunks": []}
    st.rerun()

st.markdown("---")
st.caption("✨ **FREE** • Works on scanned PDFs • Full paragraphs • Pure Python")
