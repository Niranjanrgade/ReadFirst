import streamlit as st
import requests

API_BASE = "http://localhost:8000"  # Your FastAPI endpoint
# # --- Custom Styling (Inline CSS) ---
# st.markdown("""
# <style>
#     /* General body styling */
#     body {
#         font-family: 'Inter', sans-serif;
#         background: linear-gradient(to bottom right, #e0f2fe, #bbdefb); /* Light blue gradient */
#     }
#     /* Main container styling */
#     .stApp {
#         padding: 2rem;
#     }
#     /* Centered card for input page */
#     .stApp > div:first-child > div:nth-child(2) > div:first-child {
#         display: flex;
#         flex-direction: column;
#         align-items: center;
#         justify-content: center;
#         min-height: calc(100vh - 4rem); /* Adjust for padding */
#     }
#     .stApp > div:first-child > div:nth-child(2) > div:first-child > div:first-child > div:first-child {
#         background-color: white;
#         border-radius: 1.5rem; /* 24px */
#         box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
#         padding: 3rem; /* 48px */
#         max-width: 50rem; /* 800px */
#         width: 100%;
#         text-align: center;
#         transition: all 0.3s ease-in-out;
#     }
#     .stApp > div:first-child > div:nth-child(2) > div:first-child > div:first-child > div:first-child:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
#     }

#     /* Titles and text */
#     h1, h2, h3 {
#         color: #1a202c; /* text-gray-900 */
#         font-weight: 800; /* extabold */
#     }
#     .stMarkdown p {
#         color: #4a5568; /* text-gray-600 */
#     }

#     /* Input elements styling */
#     .stTextInput>div>div>input, .stTextArea>div>div>textarea {
#         border-radius: 0.75rem; /* 12px */
#         border: 1px solid #cbd5e0; /* border-gray-300 */
#         padding: 1rem; /* 16px */
#         width: 100%;
#         transition: all 0.2s ease-in-out;
#     }
#     .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
#         border-color: #4f46e5; /* indigo-600 */
#         box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.5); /* ring-indigo-500 */
#         outline: none;
#     }

#     /* File Uploader Customization */
#     .stFileUploader > div > div {
#         border: 2px dashed #a78bfa; /* border-purple-300 */
#         border-radius: 0.75rem;
#         padding: 2rem;
#         text-align: center;
#         background-color: #f5f3ff; /* bg-purple-50 */
#         transition: all 0.2s ease-in-out;
#     }
#     .stFileUploader > div > div:hover {
#         border-color: #7c3aed; /* purple-600 */
#         background-color: #ede9fe; /* bg-purple-100 */
#     }
#     .stFileUploader label span {
#         color: #6d28d9 !important; /* purple-700 */
#         font-weight: 600;
#     }

#     /* Checkbox styling */
#     .stCheckbox > label {
#         display: flex;
#         align-items: center;
#         cursor: pointer;
#         color: #2d3748; /* text-gray-800 */
#     }
#     .stCheckbox > label > div:first-child {
#         border-radius: 0.25rem; /* rounded */
#         border: 1px solid #4f46e5; /* border-indigo-600 */
#         width: 1.25rem; /* w-5 */
#         height: 1.25rem; /* h-5 */
#         transition: all 0.2s ease-in-out;
#     }
#     .stCheckbox > label > div:first-child > div:first-child {
#         color: #4f46e5; /* text-indigo-600 */
#     }

#     /* Button Styling */
#     .stButton > button {
#         background-color: #4f46e5; /* indigo-600 */
#         color: white;
#         padding: 0.75rem 1.5rem; /* py-3 px-6 */
#         border-radius: 9999px; /* rounded-full */
#         font-weight: 600;
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
#         transition: all 0.3s ease-in-out;
#         border: none;
#         display: flex;
#         align-items: center;
#         justify-content: center;
#     }
#     .stButton > button:hover {
#         background-color: #4338ca; /* indigo-700 */
#         transform: translateY(-2px);
#         box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
#     }
#     .stButton > button:active {
#         transform: scale(0.98);
#     }
#     .stButton > button:disabled {
#         opacity: 0.6;
#         cursor: not-allowed;
#         transform: none;
#         box-shadow: none;
#     }

#     /* Error and Success Messages */
#     .stAlert > div {
#         border-radius: 0.75rem;
#         padding: 1rem;
#         margin-top: 1rem;
#     }
#     .stAlert.st-emotion-cache-p5m8sr { /* Error alert specific class */
#         background-color: #fee2e2; /* red-100 */
#         border: 1px solid #ef4444; /* red-500 */
#         color: #b91c1c; /* red-700 */
#     }
#     .stAlert.st-emotion-cache-12qp09k { /* Success alert specific class */
#         background-color: #d1fae5; /* green-100 */
#         border: 1px solid #10b981; /* green-500 */
#         color: #065f46; /* green-700 */
#     }


#     /* Specific styling for summary and detail pages */
#     .summary-card, .detail-card, .chat-card {
#         background-color: white;
#         border-radius: 1.5rem; /* 24px */
#         box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
#         padding: 2.5rem; /* 40px */
#         transition: all 0.3s ease-in-out;
#         max-width: 70rem; /* Wide layout, adjust as needed */
#         margin: 0 auto;
#     }
#     .summary-card:hover, .detail-card:hover, .chat-card:hover {
#         transform: translateY(-5px);
#         box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
#     }
#     .risky-clause-button {
#         width: 100%;
#         text-align: left;
#         padding: 0.75rem;
#         background-color: white;
#         border: 1px solid #fdba74; /* orange-300 */
#         border-radius: 0.75rem;
#         box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
#         transition: all 0.2s ease-in-out;
#         display: flex;
#         align-items: center;
#         color: #1a202c; /* text-gray-900 */
#         font-weight: 500;
#     }
#     .risky-clause-button:hover {
#         background-color: #fff7ed; /* orange-50 */
#         border-color: #f97316; /* orange-500 */
#         transform: translateY(-2px);
#         box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
#     }
#     .risky-clause-button .icon-margin-right {
#         margin-right: 0.5rem;
#         color: #f97316; /* orange-500 */
#     }
#     .risky-clause-button .icon-rotate {
#         margin-left: auto;
#         transform: rotate(180deg);
#         color: #f97316; /* orange-500 */
#     }

#     /* Chat Styling */
#     .chat-message-user {
#         background-color: #4f46e5; /* indigo-600 */
#         color: white;
#         border-radius: 0.75rem;
#         padding: 0.75rem 1rem;
#         margin-left: auto; /* Push to right */
#         max-width: 70%;
#         border-bottom-right-radius: 0;
#     }
#     .chat-message-bot {
#         background-color: #e2e8f0; /* gray-200 */
#         color: #2d3748; /* gray-800 */
#         border-radius: 0.75rem;
#         padding: 0.75rem 1rem;
#         margin-right: auto; /* Push to left */
#         max-width: 70%;
#         border-bottom-left-radius: 0;
#     }
#     .chat-input-container {
#         display: flex;
#         align-items: center;
#         margin-top: 1.5rem;
#     }
#     .chat-input {
#         flex-grow: 1;
#         border-radius: 9999px; /* full rounded */
#         padding: 0.75rem 1.25rem;
#         border: 1px solid #cbd5e0;
#         transition: all 0.2s ease-in-out;
#     }
#     .chat-input:focus {
#         border-color: #4f46e5;
#         box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.5);
#         outline: none;
#     }
#     .chat-send-button {
#         margin-left: 0.75rem;
#         background-color: #4f46e5;
#         color: white;
#         border-radius: 9999px;
#         padding: 0.75rem;
#         box-shadow: 0 2px 4px -1px rgba(0, 0, 0, 0.1);
#         transition: all 0.3s ease-in-out;
#         border: none;
#     }
#     .chat-send-button:hover {
#         background-color: #4338ca;
#         transform: translateY(-1px);
#     }
#     .chat-send-button:disabled {
#         opacity: 0.6;
#         cursor: not-allowed;
#     }
# </style>
# """, unsafe_allow_html=True)

st.set_page_config(page_title="ReadFirst", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = 'input'

# ---------- PAGE: INPUT ----------
if st.session_state.page == 'input':
    st.markdown("## 🧾 ReadFirst")
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
            with st.spinner("Let me think..."):
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
