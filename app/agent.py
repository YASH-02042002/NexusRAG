import os
from typing import List, Dict, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    raise ValueError("CRITICAL ERROR: GROQ_API_KEY missing from .env file configuration.")

client = Groq(api_key=GROQ_KEY)

MODEL_NAME = "llama-3.1-8b-instant"

class Agent:
    def __init__(self,query: str):
        self.query: str = query
        self.route: str = ""
        self.retrieved_docs: List[str] = []
        self.critic_verdict: str = ""
        self.loop_count: int = 0
        self.max_loops: int = 3
        self.logs: List[str] = []

    def log(self, message: str):
        self.logs.append(message)

MOCK_KNOWLEDGE_BASE = {
    "q1 corporate tax rate 2026": "The official corporate tax rate for entities operating under Q1 2026 guidelines is fixed at 22% for domestic companies, with an applicable 10% surcharge.",
    "hellobooks software compliance": "Hellobooks AI platform achieved full SOC2 Type II compliance security certification in late 2025, ensuring end-to-end encryption for financial vector indices."
}

async def retrieve_knowledge(query: str) -> List[str]:
    """
    Simulates semantic vector search retrieval logic.
    In production, swap this directly with a real FAISS or pgvector index query execution.
    """
    query_lower = query.lower()
    matches = []
    for key, content in MOCK_KNOWLEDGE_BASE.items():
        if any(word in query_lower for word in key.split()):
            matches.append(content)
    return matches if matches else ["No explicit direct matching records found in internal secure storage."]

async def routing_node(state: Agent) -> Agent:
    """Evaluates user intent and dynamiaclly determines system routting paths."""
    state.log("Entering Routing Node...")
    prompt = f"""
    You are an enterprise query router. Analyze the user request.
    If it asks about internal systems, companies, specific 2026 tax codes, software compliance, or corporate financial documents, reply with exactly 'knowledge_base'.
    Otherwise, if it's a general programming, math, or common knowledge query, reply with exactly 'general_llm'.
    
    User Request: {state.query}
    Routing Decision:"""
    try: 
        response = client.chat.completions.create(
            model = MODEL_NAME,
            messages = [{"role": "system", "content": prompt}],
            temperature = 0.0
        )
        decision = response.choices[0].message.content.strip().lower()
        state.route = "knowledge_base" if "knowlegde_base" in decision else "general_llm"
    except Exception as e:
        state.log(f"Routing error: {str(e)}. Falling back to knowledge_base.")
        state.route = "knowledge_base"
    state.log("Routing Node complete. Selected Path: {state.route}")
    return state

async def exection_node(state: Agent) -> Agent:
    state.log(f"Entering Execution Node (Attempt {state.loop_count + 1})...")
    if state.route == "general_llm":
        response = client.chat.completions.create(
            model = MODEL_NAME,
            messages = [{"role": "system", "content": state.query}],
            temperature = 0.3
        )
        state.generated_response = response.choices[0].message.content
        state.critic_verdict = "PASS"
    else:
        if not state.retrieved_docs:
            state.retrieved_docs = await retrieve_knowledge(state.query)
        context = "\n".join(state.retrieved_docs)
        prompt = f""" 
        You are a highly secure Enterprise Knowledge Assistant.
        Answer the user's query STRICTLY using only the provided context snippets.
        If the information is not contained within the context, state 'INSUFFICIENT_DATA'.
        
        Context Records:
        {context}
        
        User Query: {state.query}
        Answer:"""

        response = client.chat.completions.create(
            model = MODEL_NAME,
            messages = [{"role": "system", "content": state.query}],
            temperature = 0.1
        )
        state.generated_response = response.choices[0].message.content
    state.log("Execution Node completed Compiling draft answer.")
    return state

async def critic_node(state: Agent) -> Agent:
    if state.route == "general_llm":
        return state
        
    state.log("Entering Critic Validation Node...")
    context = "\n".join(state.retrieved_docs)
    
    prompt = f"""
    You are an automated AI Auditing System. Your sole job is to detect hallucinations.
    Compare the Generated Answer against the Verified Context.
    Rules:
    1. If the Generated Answer contains assertions NOT found in the Verified Context, reply with 'FAIL'.
    2. If the Generated Answer states 'INSUFFICIENT_DATA', reply with 'FAIL'.
    3. If the answer is completely true to the facts in the context, reply with 'PASS'.
    Verified Context:
    {context}
    Generated Answer:
    {state.generated_response}
    Audit Verdict (PASS or FAIL):"""
    
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    verdict = response.choices[0].message.content.strip().upper()
    state.critic_verdict = "PASS" if "PASS" in verdict else "FAIL"
    state.log(f"Critic Audit complete. Verdict: {state.critic_verdict}")
    return state

async def run_agentic_rag_pipeline(user_query: str) -> Dict[str, Any]:
    state = Agent(query = user_query)
    state = await routing_node(state)

    while state.loop_count < state.max_loops:
        state = await exection_node(state)
        state = await critic_node(state)

        if state.critic_verdict == "PASS":
            state.log("Pipeline verification succeeded. Exiting cleaanly.")
            break
        state.loop_count += 1
        state.log("Critique dynamic loop activated. Modifying query semantics for retry.")
        state.query = f"{state.query} detailed compliance records"
        state.retrieved_docs = []
    
    return{
        "query": user_query,
        "route_taken": state.route,
        "final_response": state.generated_response,
        "audit_status": state.critic_verdict,
        "total_recovery_loops": state.loop_count,
        "execution_telemetry_logs": state.logs
    }