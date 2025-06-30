from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
from .config import logger
from .models import ChatRequest
from .langchain_utils import initialize_langchain

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LangChain global state ---
llm = None
vectorstore = None
retrieval_chain = None
embeddings_model = None

@app.on_event("startup")
async def startup_event():
    global llm, vectorstore, retrieval_chain, embeddings_model
    llm, vectorstore, retrieval_chain, embeddings_model = initialize_langchain()

# --- Response Caching ---
@lru_cache(maxsize=1000)
def get_cached_response(query: str) -> dict:
    return None

def cache_response(query: str, response: dict) -> None:
    get_cached_response.cache_clear()
    get_cached_response.__wrapped__(query)

@app.get("/")
async def healthcheck():
    if retrieval_chain:
        return {"status": "Nepali Tax Chatbot Backend is running and initialized!"}
    else:
        raise HTTPException(status_code=500, detail="Nepali Tax Chatbot Backend is running but initialization failed.")

@app.post("/chat")
async def chat(request_body: ChatRequest):
    user_query = request_body.query.strip()
    if not user_query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    if not retrieval_chain:
        logger.error("Chatbot initialization failed")
        raise HTTPException(status_code=503, detail="Chatbot is not initialized. Please check backend logs.")
    try:
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
        cache_response(user_query, result)
        logger.info(f"Successfully processed query: {user_query}")
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error processing query '{user_query}': {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your request: {str(e)}")
