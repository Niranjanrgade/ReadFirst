# main.py for FastAPI

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Literal
import requests
import fitz # PyMuPDF for PDF extraction
from bs4 import BeautifulSoup

# LangChain Imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings, OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOpenAI
from langchain_community.llms import Ollama
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.documents import Document

app = FastAPI()

# Global ChromaDB instance (for simplicity; in production, manage persistence)
vectorstore = None
global_embeddings_model = None # To store the chosen embedding model

# Pydantic models for request/response
class ProcessAgreementRequest(BaseModel):
    text: str
    is_url: bool = False
    sensitive_mode: bool = False
    verbose_mode: bool = False

class ClauseAnalysis(BaseModel):
    original_text: str
    summary_plain_english: str
    is_risky: bool
    risk_level: Literal["Low", "Medium", "High", "Not Applicable"] = "Not Applicable"
    implications: Optional[str] = None
    verbose_explanation: Optional[str] = None

class AgreementProcessingResponse(BaseModel):
    safe_clauses: List[ClauseAnalysis]
    risky_clauses: List[ClauseAnalysis]
    full_agreement_summary: str

class ChatAgreementRequest(BaseModel):
    question: str
    document_text: str
    full_agreement_summary: str
    sensitive_mode: bool

class ChatAgreementResponse(BaseModel):
    answer: str

# --- Helper Functions ---

def extract_text_from_url(url: str) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # A more robust way to extract main content, avoiding navs, footers etc.
        # This might need refinement based on typical agreement page structures
        main_content = soup.find('body')
        if main_content:
            text = main_content.get_text(separator='\n', strip=True)
            return text
        return soup.get_text(separator='\n', strip=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text from URL: {e}")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extract text from PDF: {e}")

def get_llm(sensitive_mode: bool):
    if sensitive_mode:
        # Ensure Ollama is running and model is pulled (e.g., ollama pull llama3)
        return Ollama(model="llama3", temperature=0.1)
    else:
        # Ensure OPENAI_API_KEY is set in your environment
        return ChatOpenAI(model="gpt-4o-mini", temperature=0.1)

def get_embeddings(sensitive_mode: bool):
    global global_embeddings_model
    if global_embeddings_model and (
        (sensitive_mode and isinstance(global_embeddings_model, OllamaEmbeddings)) or
        (not sensitive_mode and isinstance(global_embeddings_model, OpenAIEmbeddings))
    ):
        return global_embeddings_model # Reuse existing model if type matches

    if sensitive_mode:
        global_embeddings_model = OllamaEmbeddings(model="nomic-embed-text")
    else:
        global_embeddings_model = OpenAIEmbeddings()
    return global_embeddings_model

def segment_text_into_clauses(text: str) -> List[str]:
    # Use a recursive character splitter with custom separators
    # This tries to split by common agreement separators first, then by paragraphs, then by sentences
    text_splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n\n\n", # Large breaks
            "\n\n",  # Paragraphs
            "\n",    # New lines
            ". ",    # Sentence-ending periods
            "; ",    # Semicolons
        ],
        chunk_size=1000, # Max size for a chunk
        chunk_overlap=100, # Overlap to maintain context
        length_function=len,
        is_separator_regex=False
    )
    # A more sophisticated approach might involve checking for clause numbering patterns
    # For now, let's use a simple split by paragraphs/lines
    clauses = [clause.strip() for clause in text.split('\n\n') if clause.strip()]
    
    # You might want to filter out very short or uninformative clauses
    clauses = [c for c in clauses if len(c) > 50] # Example filter
    return clauses

# --- FastAPI Endpoints ---

@app.post("/process_agreement", response_model=AgreementProcessingResponse)
async def process_agreement(request: ProcessAgreementRequest):
    global vectorstore

    raw_document_text = request.text
    if request.is_url:
        raw_document_text = extract_text_from_url(raw_document_text)
    # If PDF was uploaded, it would be handled here (e.g., pass bytes, then extract)
    # For this example, assuming 'text' already contains content if not URL

    if not raw_document_text:
        raise HTTPException(status_code=400, detail="No document content provided for processing.")

    clauses = segment_text_into_clauses(raw_document_text)
    if not clauses:
        raise HTTPException(status_code=400, detail="Could not segment document into meaningful clauses.")

    llm = get_llm(request.sensitive_mode)
    embeddings = get_embeddings(request.sensitive_mode)

    # Initialize or update ChromaDB
    # Convert clauses to LangChain Documents for Chroma
    lc_documents = [Document(page_content=clause) for clause in clauses]
    vectorstore = Chroma.from_documents(lc_documents, embeddings)

    # Prepare chains for clause analysis
    summary_prompt_template = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant specialized in legal document simplification.
         Your goal is to explain legal clauses in simple, plain English, understandable by an average person without legal background.
         Also, identify if a clause is common/safe or potentially risky/noteworthy.
         If 'verbose_mode' is true, provide more detailed explanations, potential implications, and a risk level.
         Risk levels: 'Low' (standard, harmless), 'Medium' (some consideration needed), 'High' (significant risk).
         If a clause is standard and common, explicitly state that.
         
         Provide output in a structured JSON format with the following keys:
         'summary_plain_english': A concise, plain English summary.
         'is_risky': boolean (true if noteworthy/risky, false if common/safe).
         'risk_level': 'Low', 'Medium', 'High', or 'Not Applicable'.
         'implications': (Optional) What this clause means for the user.
         'verbose_explanation': (Optional, only if verbose_mode is true) A more detailed breakdown.
         """),
        ("human", "Analyze the following clause based on sensitive_mode: {sensitive_mode} and verbose_mode: {verbose_mode}. Clause: {clause_text}")
    ])

    parser = StrOutputParser() # To parse the string output from LLM, will need more robust JSON parsing

    clause_analysis_chain = summary_prompt_template | llm | parser

    safe_clauses_list = []
    risky_clauses_list = []
    full_agreement_summary_parts = []

    # Process each clause
    for clause_text in clauses:
        try:
            # For simplicity, sending a flag, but ideally, the prompt adapts
            analysis_output = await clause_analysis_chain.ainvoke({
                "clause_text": clause_text,
                "sensitive_mode": request.sensitive_mode,
                "verbose_mode": request.verbose_mode
            })
            
            # --- IMPORTANT: You need a robust JSON parser here. LLM output can be flaky. ---
            # Using ast.literal_eval or a Pydantic parser with retry would be better.
            # For this example, assuming perfect JSON output for demonstration.
            try:
                parsed_analysis = json.loads(analysis_output)
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return perfect JSON
                parsed_analysis = {
                    "summary_plain_english": f"Could not parse analysis for: {clause_text[:100]}...",
                    "is_risky": True, # Assume risky if parsing failed, to highlight
                    "risk_level": "High",
                    "implications": "Parsing error, check original clause.",
                    "verbose_explanation": analysis_output # Raw output
                }
                print(f"Warning: Failed to parse JSON from LLM: {analysis_output}")

            clause_analysis_obj = ClauseAnalysis(
                original_text=clause_text,
                summary_plain_english=parsed_analysis.get("summary_plain_english", ""),
                is_risky=parsed_analysis.get("is_risky", False),
                risk_level=parsed_analysis.get("risk_level", "Not Applicable"),
                implications=parsed_analysis.get("implications"),
                verbose_explanation=parsed_analysis.get("verbose_explanation") if request.verbose_mode else None
            )

            if clause_analysis_obj.is_risky:
                risky_clauses_list.append(clause_analysis_obj)
            else:
                safe_clauses_list.append(clause_analysis_obj)
            
            full_agreement_summary_parts.append(clause_analysis_obj.summary_plain_english)

        except Exception as e:
            print(f"Error processing clause: {clause_text[:100]}... Error: {e}")
            # Add a placeholder for failed clauses
            risky_clauses_list.append(ClauseAnalysis(
                original_text=clause_text,
                summary_plain_english=f"Error summarizing this clause due to: {e}",
                is_risky=True,
                risk_level="High",
                implications="Processing error, manual review needed."
            ))

    # Generate a concise overall summary of the agreement for chat context
    # This could be a separate LLM call or concatenation of plain English summaries
    overall_summary_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an AI assistant. Summarize the following key points from an agreement into a single, concise paragraph for general understanding."),
        ("human", "Key points from agreement:\n\n{key_points}")
    ])
    overall_summary_chain = overall_summary_prompt | llm | StrOutputParser()
    full_agreement_summary_text = await overall_summary_chain.ainvoke({"key_points": "\n".join(full_agreement_summary_parts)})


    return AgreementProcessingResponse(
        safe_clauses=safe_clauses_list,
        risky_clauses=risky_clauses_list,
        full_agreement_summary=full_agreement_summary_text
    )


@app.post("/chat_agreement", response_model=ChatAgreementResponse)
async def chat_agreement(request: ChatAgreementRequest):
    if vectorstore is None:
        raise HTTPException(status_code=400, detail="No agreement has been processed yet. Please process an agreement first.")

    llm = get_llm(request.sensitive_mode)

    # Retrieval chain for QA
    Youtubeing_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant specifically designed to answer questions about legal agreements.
         You will be given a user's question, relevant clauses from the agreement, and a summary of the full agreement.
         Answer the question concisely and accurately based *only* on the provided context.
         If the information is not explicitly available in the provided context, state that you don't know politely.
         Do not hallucinate or make up information.
         
         Agreement Summary: {full_agreement_summary}
         Relevant Clauses: {context}
         """),
        ("human", "{input}")
    ])

    document_chain = create_stuff_documents_chain(llm, Youtubeing_prompt)
    
    # Ensure retriever uses the current vectorstore
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) # Retrieve top 5 relevant clauses

    retrieval_chain = create_retrieval_chain(retriever, document_chain)

    try:
        response = await retrieval_chain.ainvoke({
            "input": request.question,
            "full_agreement_summary": request.full_agreement_summary # Pass full summary directly to prompt
        })
        answer = response["answer"]
        return ChatAgreementResponse(answer=answer)
    except Exception as e:
        print(f"Error during chat processing: {e}")
        # A more refined error message might tell the user to rephrase or provide more context
        return ChatAgreementResponse(answer="I apologize, but I encountered an error while processing your question. Please try rephrasing it or ensure the agreement was processed correctly.")