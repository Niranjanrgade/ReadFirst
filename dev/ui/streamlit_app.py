import streamlit as st
import requests

API_BASE = "http://localhost:8000"  # Your FastAPI endpoint

st.set_page_config(page_title="ClauseSense", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 'input'

# ---------- PAGE: INPUT ----------
if st.session_state.page == 'input':
    st.markdown("## 🧾 ClauseSense")
    st.markdown("### Understand Before You Agree")

    uploaded_file = st.file_uploader("Upload Agreement (PDF or Text)", type=['pdf', 'txt'])
    url_input = st.text_input("Or paste URL")
    text_input = st.text_area("Or paste raw text here")

    col1, col2 = st.columns(2)
    with col1:
        sensitive = st.checkbox("Sensitive Mode")
    with col2:
        verbose = st.checkbox("I have some time")

    if st.button("Submit"):
        # Extract input
        if uploaded_file:
            raw_text = uploaded_file.read().decode("utf-8")
        elif text_input:
            raw_text = text_input
        elif url_input:
            raw_text = f"Agreement content from URL: {url_input}"  # Placeholder
        else:
            st.warning("Please upload a file or enter text.")
            st.stop()

        # Call FastAPI backend to summarize
        try:
            with st.spinner("Processing with LLM..."):
                res = requests.post(f"{API_BASE}/summarize", json={"text": raw_text})
                res.raise_for_status()
                summary = res.json()["summary"]

                # For now, simulate safe/risky separation
                st.session_state.safe_clauses = ["Clause is general and safe."]
                st.session_state.risky_clauses = [summary]  # Treat full summary as one risky clause
                st.session_state.page = 'summary'
        except Exception as e:
            st.error(f"Failed to summarize: {e}")

# ---------- PAGE: SUMMARY ----------
elif st.session_state.page == 'summary':
    st.markdown("## 📑 Summary of Agreement")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ✅ Safe Clauses")
        for clause in st.session_state.safe_clauses:
            st.markdown(f"- {clause}")

    with col2:
        st.markdown("### ⚠️ Risky Clauses")
        for i, clause in enumerate(st.session_state.risky_clauses):
            if st.button(clause[:60] + "...", key=f"clause_{i}"):
                st.session_state.selected_clause = clause
                st.session_state.page = 'detail'

    st.text_input("💬 Ask a question about this document", key="chatbox_input")

# ---------- PAGE: DETAIL ----------
elif st.session_state.page == 'detail':
    st.markdown("## 🧾 Clause Detail")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📄 Original Clause")
        st.code(st.session_state.selected_clause)

    with col2:
        st.markdown("### 💡 Explanation")
        # Just echo summary for now, replace with real explanation logic if needed
        st.markdown(f"_Plain English: {st.session_state.selected_clause}_")

    st.text_input("💬 Ask a question about this clause", key="detail_chat_input")
    st.button("Back to Summary", on_click=lambda: st.session_state.update({"page": "summary"}))
