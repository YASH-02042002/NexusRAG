from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.agent import run_agentic_rag_pipeline

app = FastAPI(
    title = "NexusRAG: Autonomous Enterprise Knowledge Pipeline",
    version = "1.0.0",
    description = "Asynchronous self-correcting multi-agent execution sysytem backend."
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    route_taken: str
    final_response: str
    audit_status: str
    total_recovery_loops: int
    execution_telemetry_logs: list[str]

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agentic-rag-core"}

@app.post("/api/v1/chat", response_model=QueryResponse)
async def process_agent_query(request: QueryRequest):
    """
    Primary ingestion point for parsing text through the self-correcting agent loop.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Inbound user query parameters cannot be empty.")
    try:
        pipeline_result = await run_agentic_rag_pipeline(user_query=request.query)
        return pipeline_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Pipeline Execution Error: {str(e)}")
    
@app.get("/")
async def root():
    return {"message": "Welcome to the NexusRAG Enterprise Pipeline. Visit /docs to test the API."}
