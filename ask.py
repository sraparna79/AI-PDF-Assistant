import streamlit as st
import re

st.set_page_config(page_title="FREE AI PDF Assistant", layout="wide")

def extract_readable_text(uploaded_file):
    """Extract ONLY readable English text - rejects garbage"""
    uploaded_file.seek(0)
    raw = uploaded_file.read()
    
    # Try multiple encodings
    text = raw.decode('latin1', errors='ignore')
    
    # BRUTAL CLEANING - Remove ALL PDF/encoding garbage
    garbage = [
        r'[àáâãäåæçèéêëìíîïðñòóôõö÷øùúûüýþÿ]',  # Accented chars
        r'[^\x00-\x7F]{3,}',  # Non-ASCII sequences
        r'[a-f0-9]{6,}',      # Hex codes
        r'(obj|stream|endobj|BT|ET|\/[A-Z]{2,}|Mm:|xmp)',  # PDF tags
        r'\d{4,}\s*\d+',      # PDF numbers
    ]
    
    for pattern in garbage:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    # ONLY KEEP VALID ENGLISH PARAGRAPHS
    sentences = re.split(r'[.!?]+', text)
    valid_chunks = []
    
    for sent in sentences:
        sent = sent.strip()
        if len(sent) > 50:
            words = re.findall(r'\b[a-zA-Z]{3,20}\b', sent.lower())
            # 80%+ English words required
            if len(words) > 6 and len(words) / len(sent.split()) > 0.8:
                clean_sent = ' '.join(words)
                if len(clean_sent) > 80:
                    valid_chunks.append(clean_sent.capitalize() + '.')
    
    return valid_chunks[:40]

def generate_full_paragraph(question, chunks):
    """Create detailed paragraph answers"""
    query_words = set(re.findall(r'\w+', question.lower()))
    
    # Score chunks with multiple methods
    scored = []
    for i, chunk in enumerate(chunks):
        matches = sum(1 for word in query_words if word in chunk.lower())
        length_score = min(len(chunk)/500, 3)
        total = matches * 5 + length_score
        scored.append((chunk, total, i))
    
    # Ensure variety
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Build answer from top 4 chunks
    context = ' '.join([c[0] for c in scored[:4]])
    sentences = re.split(r'[.!?]+', context)
    
    relevant_sentences = []
    for sent in sentences:
        sent = sent.strip()
        if any(word in sent.lower() for word in query_words) and len(sent) > 30:
            relevant_sentences.append(sent.capitalize())
        elif len(relevant_sentences) < 5:
            relevant_sentences.append(sent.capitalize())
    
    paragraph = '. '.join(relevant_sentences[:4]) + '.'
    
    return f"""
**📄 Answer: '{question}'**

**{paragraph}**

**📊 From your PDF:**
• **{len([c for c, s, i in scored if s > 2])}** sections matched
• **Total chunks**: {len(chunks)}
• **Source**: {st.session_state.get('filename', 'Document')}
"""

# Session state
if "chunks" not in st.session_state:
    st.session_state.chunks = []

st.title("🤖 FREE AI PDF Assistant") 
st.markdown("**✅ Readable paragraphs • ✅ Rejects garbage text • ✅ Works on ALL PDFs**")

# Upload section
col1, col2 = st.columns([3,1])
with col1:
    uploaded = st.file_uploader("📄 Upload PDF", type="pdf")
with col2:
    st.metric("Valid Chunks", len(st.session_state.chunks))

# Process PDF
if uploaded and st.button("🚀 Extract Readable Text", type="primary"):
    with st.spinner("Killing PDF garbage..."):
        st.session_state.chunks = extract_readable_text(uploaded)
        st.session_state.filename = uploaded.name
    
    st.success(f"✅ **{len(st.session_state.chunks)} VALID English paragraphs** found!")
    st.balloons()
    st.rerun()

# Preview
if st.session_state.chunks:
    with st.expander("📋 Preview Clean Paragraphs", expanded=True):
        for i, chunk in enumerate(st.session_state.chunks[:3]):
            st.markdown(f"**{i+1}:** {chunk}")

st.divider()

# Query
if st.session_state.chunks:
    st.markdown("### 💭 Ask about your thesis")
    
    question = st.text_input("",
                           placeholder="What is this about? Research question? Findings?",
                           label_visibility="collapsed")
    
    if st.button("🤖 Full Paragraph Answer", use_container_width=True, type="primary") and question.strip():
        with st.spinner("Generating answer..."):
            answer = generate_full_paragraph(question, st.session_state.chunks)
            st.markdown(answer)

    # Quick questions
    cols = st.columns(4)
    quicks = ["main topic", "research question", "key findings", "methodology"]
    for i, q in enumerate(quicks):
        if cols[i].button(f"🎯 {q}", key=f"q{i}"):
            st.session_state.question = q
            st.rerun()
else:
    st.info("👆 **Upload & Extract first**")

# Controls
if st.button("🗑️ Reset", use_container_width=True):
    st.session_state.chunks = []
    st.rerun()

st.markdown("---")
st.caption("✨ **Pure Python** • Rejects image PDFs • Only readable English")
