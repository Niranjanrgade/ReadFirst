import streamlit as st
import requests

API_BASE = "http://localhost:8000"  # Your FastAPI endpoint

st.set_page_config(page_title="ReadFirst - Understand Before You Agree", layout="centered", initial_sidebar_state="collapsed")

# Initialize session state variables if they don't exist
if 'page' not in st.session_state:
    st.session_state.page = 'input'
if 'raw_text' not in st.session_state:
    st.session_state.raw_text = ""
if 'safe_clauses' not in st.session_state:
    st.session_state.safe_clauses = []
if 'risky_clauses' not in st.session_state:
    st.session_state.risky_clauses = []
if 'selected_clause' not in st.session_state:
    st.session_state.selected_clause = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'agreement_summary_for_chat' not in st.session_state:
    st.session_state.agreement_summary_for_chat = ""
if 'sensitive_mode' not in st.session_state:
    st.session_state.sensitive_mode = False
if 'verbose_mode' not in st.session_state:
    st.session_state.verbose_mode = False


# --- Helper functions to navigate pages ---
def go_to_summary():
    st.session_state.page = 'summary'

def go_to_input():
    st.session_state.page = 'input'
    # Clear previous data when going back to input
    st.session_state.raw_text = ""
    st.session_state.safe_clauses = []
    st.session_state.risky_clauses = []
    st.session_state.selected_clause = ""
    st.session_state.chat_history = []
    st.session_state.agreement_summary_for_chat = ""
    st.session_state.sensitive_mode = False
    st.session_state.verbose_mode = False

def go_to_detail(clause_text):
    st.session_state.selected_clause = clause_text
    st.session_state.page = 'detail'

def go_to_chat_agreement():
    st.session_state.page = 'chat_agreement'


# --- Page: INPUT (Landing Page) ---
if st.session_state.page == 'input':
    st.markdown("<h1 style='text-align: center;'>🧾 ReadFirst</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Understand Before You Agree</h3>", unsafe_allow_html=True)

    st.write("---") # Horizontal line for separation

    # Centered input options
    # col1, col2, col3 = st.columns([1, 4, 1])
    # with col2: # Use the middle column for centering
    uploaded_file = st.file_uploader("Upload Agreement (PDF or Text)", type=['pdf', 'txt'], key="file_uploader")
    url_input = st.text_input("Or paste URL here", key="url_input", help="Enter a public URL to an agreement document.")
    text_input = st.text_area("Or paste raw text here", key="text_input", height=150, help="Directly paste the content of the agreement.")

    st.write("---") # Separator before options

    # Checkboxes for sensitive and verbose modes
    col_chk1, col_chk2 = st.columns(2)
    with col_chk1:
        st.session_state.sensitive_mode = st.checkbox("Sensitive Mode (Local Processing)", help="Process using local, open-source models for sensitive data.", value=st.session_state.sensitive_mode)
    with col_chk2:
        st.session_state.verbose_mode = st.checkbox("I have some time (Verbose Explanation)", help="Get more detailed explanations for clauses.", value=st.session_state.verbose_mode)

    st.write("") # Add some vertical space

    if st.button("Understand Agreement", use_container_width=True, type="primary"):
        raw_text = ""
        if uploaded_file:
            # Assuming PDF processing happens on the backend or using a library like PyPDF2
            # For now, just simulate reading if it's text
            if uploaded_file.type == "text/plain":
                raw_text = uploaded_file.read().decode("utf-8")
            elif uploaded_file.type == "application/pdf":
                # In a real app, you'd send the PDF to the backend for processing
                st.warning("PDF upload requires backend processing. Simulating for now.")
                # Placeholder: You might read a few lines as a demo or prompt user for text copy-paste for now
                raw_text = "This is a placeholder for PDF content. In a real scenario, the backend would extract text from the PDF."
        elif text_input:
            raw_text = text_input
        elif url_input:
            # Backend will handle fetching content from URL
            st.session_state.raw_text = url_input # Store URL for backend to fetch
            raw_text = "URL_PROVIDED" # Signal to backend that a URL was provided
        else:
            st.warning("Please upload a file, paste a URL, or enter text to proceed.")
            st.stop()

        if raw_text:
            st.session_state.raw_text = raw_text # Store the extracted/input text for later use

            # Call FastAPI backend to process the agreement
            try:
                with st.spinner("Analyzing agreement... This might take a moment."):
                    payload = {
                        "text": raw_text,
                        "is_url": True if url_input else False, # Inform backend if it's a URL
                        "sensitive_mode": st.session_state.sensitive_mode,
                        "verbose_mode": st.session_state.verbose_mode
                    }
                    res = requests.post(f"{API_BASE}/process_agreement", json=payload)
                    res.raise_for_status() # Raise an exception for HTTP errors
                    response_data = res.json()

                    st.session_state.safe_clauses = response_data.get("safe_clauses", [])
                    st.session_state.risky_clauses = response_data.get("risky_clauses", [])
                    st.session_state.agreement_summary_for_chat = response_data.get("full_agreement_summary", "")

                    go_to_summary() # Navigate to summary page
            except requests.exceptions.RequestException as e:
                st.error(f"Could not connect to the backend server. Please ensure the backend is running at {API_BASE}. Error: {e}")
            except Exception as e:
                st.error(f"An error occurred during processing: {e}")
        else:
            st.warning("No content provided to analyze. Please upload, paste URL, or enter text.")


# --- Page: SUMMARY ---
elif st.session_state.page == 'summary':
    st.markdown("## 📑 Summary of Agreement")
    st.button("↩️ Back to Input", on_click=go_to_input) # Back button at the top

    st.write("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### ✅ Common & Non-Harmful Clauses")
        if st.session_state.safe_clauses:
            for i, clause in enumerate(st.session_state.safe_clauses):
                st.expander(f"Clause {i+1}: {clause['summary_plain_english'][:70]}...").markdown(f"- **Original:** {clause['original_text']}\n- **Plain English:** {clause['summary_plain_english']}")
        else:
            st.info("No common or non-harmful clauses identified or summarized yet.")

    with col2:
        st.markdown("### ⚠️ Potentially Risky/Noteworthy Clauses")
        if st.session_state.risky_clauses:
            for i, clause in enumerate(st.session_state.risky_clauses):
                # Button to go to detail page for risky clauses
                if st.button(f"**{clause['summary_plain_english'][:90]}...**", key=f"risky_clause_btn_{i}", use_container_width=True):
                    go_to_detail(clause) # Pass the full clause object
        else:
            st.info("No potentially risky or noteworthy clauses identified.")

    st.write("---")
    st.markdown("### 💬 Have a question about this agreement?")
    st.button("Ask a Question", on_click=go_to_chat_agreement, use_container_width=True)


# --- Page: DETAIL ---
elif st.session_state.page == 'detail':
    st.markdown("## 🧾 Clause Detail")
    st.button("↩️ Back to Summary", on_click=go_to_summary)
    st.write("---")

    if st.session_state.selected_clause:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 📄 Original Clause")
            st.code(st.session_state.selected_clause["original_text"])

        with col2:
            st.markdown("### 💡 Explanation")
            st.markdown(f"**Plain English:** {st.session_state.selected_clause['summary_plain_english']}")
            if st.session_state.verbose_mode:
                st.markdown(f"**Detailed Explanation:** {st.session_state.selected_clause.get('verbose_explanation', 'No detailed explanation available.')}")
            st.markdown(f"**Potential Implications:** {st.session_state.selected_clause.get('implications', 'No specific implications highlighted.')}")
            st.markdown(f"**Risk Level:** {st.session_state.selected_clause.get('risk_level', 'Not specified.')}")

    st.write("---")
    st.markdown("### 💬 Ask a question about this clause")
    # This chat could be a mini-chat specific to the clause, or you could redirect to the main chat
    st.text_input("Your question:", key="detail_chat_input_box", on_change=go_to_chat_agreement) # You could also have a dedicated button and pass the clause context


# --- Page: CHAT ABOUT AGREEMENT ---
elif st.session_state.page == 'chat_agreement':
    st.markdown("## 💬 Chat with the Agreement")
    st.button("↩️ Back to Summary", on_click=go_to_summary)
    st.write("---")

    # Display chat history
    for chat in st.session_state.chat_history:
        if chat["role"] == "user":
            st.markdown(f"**You:** {chat['content']}")
        else:
            st.markdown(f"**ReadFirst:** {chat['content']}")

    user_query = st.text_input("Ask your question about the agreement:", key="chat_input")

    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        # Call backend for chat response
        try:
            with st.spinner("Getting an answer..."):
                payload = {
                    "question": user_query,
                    "document_text": st.session_state.raw_text, # Send full document text for context
                    "full_agreement_summary": st.session_state.agreement_summary_for_chat, # Send full summary for broader context
                    "sensitive_mode": st.session_state.sensitive_mode
                }
                chat_res = requests.post(f"{API_BASE}/chat_agreement", json=payload)
                chat_res.raise_for_status()
                chat_response = chat_res.json()["answer"]
                st.session_state.chat_history.append({"role": "ReadFirst", "content": chat_response})
        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to the backend server. Error: {e}")
            st.session_state.chat_history.append({"role": "ReadFirst", "content": "I apologize, but I'm having trouble connecting to my processing unit right now. Please try again later."})
        except Exception as e:
            st.error(f"An error occurred while getting the chat response: {e}")
            st.session_state.chat_history.append({"role": "ReadFirst", "content": "I encountered an unexpected error while processing your question."})

        # Rerun to update chat history display
        st.rerun()