from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_openai import ChatOpenAI
from .config import logger, OPENROUTER_API_KEY, OPENROUTER_MODEL_NAME, KNOWLEDGE_BASE_DOCUMENTS
import os

llm = None
vectorstore = None
retrieval_chain = None
embeddings_model = None

def load_document(doc_config: Dict[str, str]) -> List[Any]:
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
            )
            loaded_docs = loader.load_and_split(text_splitter)
            logger.info(f"Loaded {len(loaded_docs)} chunks from {doc_path}")
            return loaded_docs
    except Exception as e:
        logger.error(f"Error loading document {doc_path}: {e}")
        return []

def load_all_documents(doc_configs: List[Dict[str, str]]) -> List[Any]:
    with ThreadPoolExecutor() as executor:
        loaded_docs_lists = list(executor.map(load_document, doc_configs))
    all_docs = [doc for docs in loaded_docs_lists for doc in docs]
    logger.info(f"Total loaded document chunks: {len(all_docs)}")
    return all_docs

def load_or_create_vectorstore(docs, embeddings_model):
    persist_directory = "chroma_db"
    try:
        if os.path.exists(persist_directory):
            logger.info("Loading existing vectorstore...")
            vectorstore = Chroma(persist_directory=persist_directory, embedding_function=embeddings_model)
            logger.info(f"Vectorstore loaded with {vectorstore._collection.count()} documents.")
            return vectorstore
        logger.info("Creating new vectorstore...")
        vectorstore = Chroma.from_documents(
            docs,
            embeddings_model,
            persist_directory=persist_directory
        )
        logger.info(f"Vectorstore created with {len(docs)} documents.")
        return vectorstore
    except Exception as e:
        logger.error(f"Error with vectorstore: {e}")
        raise

def initialize_langchain():
    global llm, vectorstore, retrieval_chain, embeddings_model
    if not OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY is not set")
    try:
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        logger.info("HuggingFace Embeddings model loaded")
        llm = ChatOpenAI(
            model=OPENROUTER_MODEL_NAME,
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=OPENROUTER_API_KEY,
            temperature=0.7
        )
        logger.info(f"LLM initialized using OpenRouter model: {OPENROUTER_MODEL_NAME}")
        all_docs = load_all_documents(KNOWLEDGE_BASE_DOCUMENTS)
        if not all_docs:
            raise ValueError("No documents loaded from any configured source")
        vectorstore = load_or_create_vectorstore(all_docs, embeddings_model)
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 8,  # Increase number of docs returned
                "fetch_k": 40,  # Increase number of docs fetched
                "lambda_mult": 0.5
            }
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an helpful AI assistant trained to provide information about Nepali tax. Based on the provided context, answer the user's question.\nIf the answer to the question is not in the context, politely state that the information is insufficient.\nAlways answer in English.\nContext: {context}"),
            ("human", "{input}")
        ])
        document_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        logger.info("LangChain components initialized successfully with OpenRouter and HuggingFace Embeddings, using multiple document types.")
        return llm, vectorstore, retrieval_chain, embeddings_model
    except Exception as e:
        logger.error(f"Error initializing LangChain components: {e}")
        llm, vectorstore, retrieval_chain, embeddings_model = None, None, None, None
        raise
