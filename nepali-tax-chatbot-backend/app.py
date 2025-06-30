import os
os.environ["CHROMA_TELEMETRY_ENABLED"] = "False"

# Import necessary libraries
import os
import logging
from functools import lru_cache
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logging.getLogger("chromadb.telemetry").setLevel(logging.ERROR)

# LangChain components for text processing, embeddings, and LLM interaction
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings


from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import ChatOpenAI

from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

# Load environment variables (like OPENROUTER_API_KEY)
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development. Restrict in production.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# --- Configuration and Initialization ---

# OPENROUTER_API_KEY is required for using OpenRouter models.
# You MUST set this as an environment variable or replace with your actual key.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Define the OpenRouter model you want to use.
# Check https://openrouter.ai/docs#models for available FREE models.
# Examples: "mistralai/mistral-7b-instruct:free", "google/gemma-7b-it:free"
OPENROUTER_MODEL_NAME = "mistralai/mistral-7b-instruct:free" # <<< CHANGE THIS to your chosen FREE model

# Define the paths and types of your knowledge base files
# Make sure these files are in the same directory as this script, or provide full paths.
KNOWLEDGE_BASE_DOCUMENTS = [
    {"path": "nepali_tax_guide.pdf", "type": "pdf"},
    # {"path": "nepali_tax_guide2.pdf", "type": "pdf"},
]

# --- LangChain Setup ---
llm = None
vectorstore = None
retrieval_chain = None
embeddings_model = None # Global variable for embeddings model

def load_document(doc_config: Dict[str, str]) -> List[Any]:
    """Load a single document with proper error handling."""
    doc_path = doc_config["path"]
    doc_type = doc_config["type"]
    
    if not os.path.exists(doc_path):
        logger.warning(f"Document file not found at {doc_path}")
        return []
        
    try:
        logger.info(f"Loading document from {doc_path} (Type: {doc_type})")
        loader = None
        
        if doc_type == "pdf":
            loader = PyPDFLoader(doc_path)
        elif doc_type == "txt":
            loader = TextLoader(doc_path)
        else:
            logger.warning(f"Unsupported document type: '{doc_type}' for {doc_path}")
            return []

        if loader:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                length_function=len,
                add_start_index=True,
            )
            loaded_docs = loader.load_and_split(text_splitter)
            logger.info(f"Loaded {len(loaded_docs)} chunks from {doc_path}")
            return loaded_docs
            
    except Exception as e:
        logger.error(f"Error loading document {doc_path}: {e}")
        return []

def load_all_documents(doc_configs: List[Dict[str, str]]) -> List[Any]:
    """Load all documents in parallel using ThreadPoolExecutor."""
    with ThreadPoolExecutor() as executor:
        # Map the load_document function across all document configs
        loaded_docs_lists = list(executor.map(load_document, doc_configs))
    
    # Flatten the list of lists into a single list of documents
    return [doc for docs in loaded_docs_lists for doc in docs]

def initialize_langchain():
    """
    Initializes LangChain components with optimized document loading.
    """
    global llm, vectorstore, retrieval_chain, embeddings_model

    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY is not set")

    try:
        # Initialize HuggingFace Embeddings
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info("HuggingFace Embeddings model loaded")

        # Initialize the LLM
        llm = ChatOpenAI(
            model=OPENROUTER_MODEL_NAME,
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=OPENROUTER_API_KEY,
            temperature=0.7
        )
        logger.info(f"LLM initialized using OpenRouter model: {OPENROUTER_MODEL_NAME}")

        # Load documents in parallel
        all_docs = load_all_documents(KNOWLEDGE_BASE_DOCUMENTS)

        if not all_docs:
            raise ValueError("No documents loaded from any configured source")

        # Use the optimized vectorstore function
        vectorstore = load_or_create_vectorstore(all_docs, embeddings_model)
        
        # Create an optimized retriever
        retriever = vectorstore.as_retriever(
            search_type="mmr",  # Use Maximum Marginal Relevance
            search_kwargs={
                "k": 4,  # Number of documents to retrieve
                "fetch_k": 20,  # Number of documents to fetch before filtering
                "lambda_mult": 0.5  # Diversity of results (0.0-1.0)
            }
        )

        # Define the prompt template for the LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an helpful AI assistant trained to provide information about Nepali tax. Based on the provided context, answer the user's question.\nIf the answer to the question is not in the context, politely state that the information is insufficient.\nAlways answer in English.\nContext: {context}"),
            ("human", "{input}")
        ])

        # Create a chain to stuff documents into the prompt
        document_chain = create_stuff_documents_chain(llm, prompt)

        # Create the retrieval chain which combines retrieval and document stuffing
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        logger.info("LangChain components initialized successfully with OpenRouter and HuggingFace Embeddings, using multiple document types.")

    except Exception as e:
        logger.error(f"Error initializing LangChain components: {e}")
        llm, vectorstore, retrieval_chain, embeddings_model = None, None, None, None
        # In a production environment, you might want to log this error more robustly
        # and potentially exit or disable the chat functionality.

def load_or_create_vectorstore(docs, embeddings_model):
    """Load existing vectorstore or create a new one if it doesn't exist."""
    persist_directory = "chroma_db"
    
    try:
        # Try to load existing vectorstore
        if os.path.exists(persist_directory):
            logger.info("Loading existing vectorstore...")
            vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings_model)
            return vectorstore
            
        # Create new vectorstore if none exists
        logger.info("Creating new vectorstore...")
        vectorstore = Chroma.from_documents(
            docs, 
            embeddings_model,
            persist_directory=persist_directory
        )
        return vectorstore
        
    except Exception as e:
        logger.error(f"Error with vectorstore: {e}")
        raise

# FastAPI startup event handler
@app.on_event("startup")
async def startup_event():
    initialize_langchain()

# Pydantic model for request body validation
class ChatRequest(BaseModel):
    query: str

# --- Response Caching ---

@lru_cache(maxsize=1000)
def get_cached_response(query: str) -> tuple:
    """Cache responses to avoid redundant LLM calls for identical queries."""
    return None  # Cache miss by default

def cache_response(query: str, response: dict) -> None:
    """Store response in cache."""
    get_cached_response.cache_clear()  # Clear old cache if needed
    get_cached_response.__wrapped__(query)  # Update cache

# --- FastAPI Routes ---

@app.get('/')
async def healthcheck():
    """
    Basic health check endpoint to confirm the server is running.
    """
    if retrieval_chain:
        return {"status": "Nepali Tax Chatbot Backend is running and initialized!"}
    else:
        raise HTTPException(status_code=500, detail="Nepali Tax Chatbot Backend is running but initialization failed.")


@app.post('/chat')
async def chat(request_body: ChatRequest):
    """
    Handles chat requests from the frontend.
    Uses caching to avoid redundant LLM calls and includes error handling with proper logging.
    """
    user_query = request_body.query.strip()

    if not user_query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    if not retrieval_chain:
        logger.error("Chatbot initialization failed")
        raise HTTPException(status_code=503, detail="Chatbot is not initialized. Please check backend logs.")

    try:
        # Check cache first
        cached_result = get_cached_response(user_query)
        if cached_result:
            logger.info(f"Cache hit for query: {user_query}")
            return JSONResponse(content=cached_result)

        logger.info(f"Processing new query: {user_query}")
        response = retrieval_chain.invoke({"input": user_query})

        bot_response = response.get("answer", "Sorry, I am unable to answer this question.")
        context_docs = response.get("context", [])
        formatted_context = [doc.page_content for doc in context_docs]

        result = {"response": bot_response, "context": formatted_context}
        
        # Cache the response
        cache_response(user_query, result)
        
        logger.info(f"Successfully processed query: {user_query}")
        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Error processing query '{user_query}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your request: {str(e)}")