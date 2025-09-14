from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional, List, Dict
import json
import os

load_dotenv()

app = FastAPI(title="Personal RAG with Bedrock S3 Vector Index")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "client_type": client_type if client_type else "not initialized"
    }

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the appropriate client based on configuration
use_agent = os.getenv("USE_AGENT", "false").lower() == "true"
client = None
client_type = None

if use_agent:
    try:
        from bedrock_agent_client import BedrockAgentClient
        client = BedrockAgentClient()
        client_type = "agent"
        print("Using Bedrock Agent")
    except (ValueError, ImportError) as e:
        print(f"Warning: Could not initialize Bedrock Agent: {e}")
else:
    try:
        from bedrock_client import BedrockRAGClient
        client = BedrockRAGClient()
        client_type = "knowledge_base"
        print("Using Bedrock Knowledge Base")
    except ValueError as e:
        print(f"Warning: Could not initialize Bedrock Knowledge Base: {e}")

class QueryRequest(BaseModel):
    question: str
    max_results: Optional[int] = 5
    stream: Optional[bool] = False
    session_id: Optional[str] = None  # For agent conversation continuity

class SourceDocument(BaseModel):
    source: str
    score: float = 0.0
    snippet: str
    url: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    content_preview: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument] = []
    tokens_used: Optional[Dict] = None

@app.get("/")
async def root():
    return {"message": "Personal RAG API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "client_type": client_type if client else "not initialized",
        "bedrock_client": "initialized" if client else "not initialized"
    }

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Bedrock client not initialized. Check your environment variables."
        )

    try:
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                stream_generator(request.question, request.max_results, request.session_id),
                media_type="text/event-stream"
            )
        else:
            # Call the appropriate method based on client type
            if client_type == "agent":
                result = client.query_agent(
                    question=request.question,
                    session_id=request.session_id
                )
            else:
                result = client.query_knowledge_base(
                    query=request.question,
                    max_results=request.max_results
                )

            return QueryResponse(
                answer=result['answer'],
                sources=[
                    SourceDocument(**doc) for doc in result['sources']
                ],
                tokens_used=result.get('tokens_used')
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def stream_generator(question: str, max_results: int, session_id: Optional[str] = None):
    """Generator for streaming responses"""
    try:
        if client_type == "agent":
            for chunk in client.stream_query(question, session_id):
                # Format as Server-Sent Events
                yield f"data: {json.dumps(chunk)}\n\n"
        else:
            for chunk in client.stream_query(question, max_results):
                # Format as Server-Sent Events
                yield f"data: {json.dumps(chunk)}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
