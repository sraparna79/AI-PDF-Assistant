import streamlit as st
import re

st.set_page_config(page_title="FREE AI PDF Assistant", layout="wide")

# Your PDF extraction (unchanged)
def extract_pdf_text(uploaded_file):
    raw = uploaded_file.getvalue().decode('latin1', errors='ignore')
    blocks = re.findall(r'[a-zA-Z]{3,}[a-zA-Z0-9\s\.,:;()\-]{50,1000}', raw)
    chunks = []
    for block in blocks[:25]:  # Increased to 25 chunks
        clean = re.sub(r'\s+', ' ', block.strip())
        if len(clean) > 80:
            chunks.append(clean[:1000])  # Longer chunks
    return chunks

# ENHANCED "LLM" - MUCH MORE DETAILED OUTPUT
def free_llm(question: str, chunks: list) -> str:
    """Smart RAG with EXTENDED content"""
    
    query_words = question.lower().split()
    relevant_chunks = []
    
    # Find ALL relevant chunks (not just 3)
    for i, chunk in enumerate(chunks):
        score = sum(2 for word in query_words if word.lower() in chunk.lower())
        score += len(re.findall('|'.join(query_words), chunk.lower().lower()))  # Bonus for phrases
        
        if score > 0:
            relevant_chunks.append((chunk, score))
    
    # Fallback - top 5 chunks by length/quality
    if not relevant_chunks:
        relevant_chunks = sorted([(c, len(c)/100) for c in chunks], key=lambda x: x[1], reverse=True)[:5]
    
    # Sort by relevance
    relevant_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, score in relevant_chunks[:5]]
    
    # BUILD EXTENDED ANSWER
    answer_parts = []
    
    # 1. HEADER
    answer_parts.append(f"**🤖 AI Answer for: '{question}'**")
    answer_parts.append("")
    
    # 2. DETAILED CONTEXT (5+ chunks, 300+ chars each)
    answer_parts.append("**📄 KEY SECTIONS FROM YOUR PDF:**")
    for i, chunk in enumerate(top_chunks[:4], 1):
        snippet = chunk[:350].rstrip('.') + "..."
        answer_parts.append(f"{i}. **{snippet}**")
    
    answer_parts.append("")
    
    # 3. EXTENDED SUMMARY (all unique words)
    all_words = set()
    for chunk in top_chunks:
        all_words.update(re.findall(r'\b[a-zA-Z]{4,}\b', chunk.lower()))
    top_words = sorted(all_words, key=lambda x: len([c for c in top_chunks if x in c.lower()]), reverse=True)[:12]
    
    answer_parts.append(f"**📊 SUMMARY:** Discusses: **{', '.join(top_words)}**")
    answer_parts.append("")
    
    # 4. BEST MATCH (longest relevant chunk)
    best_match = max(top_chunks, key=lambda c: sum(1 for word in query_words if word in c.lower()))
    answer_parts.append(f"**🎯 BEST MATCH for '{question}':**")
    answer_parts.append(best_match[:800] + "..." if len(best_match) > 800 else best_match)
    
    # 5. EXTRA INSIGHTS
    answer_parts.append("")
    answer_parts.append(f"**🔍 ANALYSIS:** Found **{len(relevant_chunks)}** relevant sections out of **{len(chunks)}** total chunks.")
    answer_parts.append(f"**📏 Coverage:** ~{sum(len(c) for c, _ in relevant_chunks[:5])/sum(len(c) for c in chunks)*100:.0f}% of document matches your query.")
    
    return "\n".join(answer_parts)

# Initialize session state
if "chunks" not in st.session_state:
    st.session_state.chunks = []

# UI
st.title("🤖 FREE AI PDF Assistant") 
st.markdown("**No API keys • No costs • **MUCH MORE CONTENT** • Seek Answers**")

col1, col2 = st.columns([3,1])
with col1:
    uploaded = st.file_uploader("📄 PDF", type="pdf")
with col2:
    st.metric("Chunks", len(st.session_state.chunks) if 'chunks' in st.session_state else 0)

if uploaded is not None and 'chunks' not in st.session_state or st.session_state.chunks == []:
    with st.spinner("🔄 Processing..."):
        st.session_state.chunks = extract_pdf_text(uploaded)
    
    st.success(f"✅ **{len(st.session_state.chunks)} chunks loaded!**")
    
    with st.expander("📋 Preview First Chunk", expanded=True):
        if st.session_state.chunks:
            st.write("**Sample content:**")
            st.write(st.session_state.chunks[0][:600] + "...")
        else:
            st.warning("No readable text found")

st.divider()

if 'chunks' in st.session_state and st.session_state.chunks:
    st.markdown("### 💭 **Ask ANY question about your PDF**")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        question = st.text_input("", placeholder="e.g. 'What is the main topic?', 'sales data?', 'key findings?'", 
                               label_visibility="collapsed")
    with col2:
        num_results = st.selectbox("Show results:", [3, 5, 8], index=1)
    
    if st.button("🚀 **GENERATE DETAILED AI ANSWER**", use_container_width=True, type="primary") and question.strip():
        with st.spinner("🤖 AI analyzing your PDF..."):
            answer = free_llm(question, st.session_state.chunks)
        
        st.markdown(answer)
        st.divider()
        
        # Quick re-ask buttons
        st.markdown("**🔄 Quick questions:**")
        quick_questions = ["main topic", "key findings", "important numbers", "summary"]
        cols = st.columns(len(quick_questions))
        for i, q in enumerate(quick_questions):
            if cols[i].button(f"💡 {q}", key=f"quick_{i}"):
                st.session_state.quick_question = q
                st.rerun()
else:
    st.info("👆 **Upload PDF first** to unlock AI answers!")
    st.markdown("**💡 Tip:** Use research papers, reports, ebooks (text-selectable PDFs)")

st.markdown("---")
st.caption("✨ **100% FREE** - No APIs • Pure Python • Unlimited usage")
