import json
import re
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from enum import Enum
from backend.state import POLICIES, AGENTS, get_stats, get_risk_analysis, PolicyUpdate
from backend.security_engine import security_engine, ScanDecision
from backend.execution_env import execution_env
from backend.bifrost import bifrost_app

app = FastAPI()

# Register the Bifrost AI Gateway proxy
app.include_router(bifrost_app, prefix="/bifrost")

LOG_FILE = Path(__file__).parent / "audit_log.json"

class AgentRequest(BaseModel):
    prompt: str

def log_event(prompt, score, decision):
    event = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "prompt": prompt,
        "score": round(score, 4),
        "decision": decision
    }
    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        else:
            data = []
        data.append(event)
        with open(LOG_FILE, "w") as f:
            json.dump(data[-20:], f)
    except Exception:
        with open(LOG_FILE, "w") as f:
            json.dump([event], f)

@app.post("/gateway")
async def security_gateway(request: AgentRequest):
    # 1. Evaluate prompt with Security Engine
    result = security_engine.evaluate_prompt(request.prompt)
    
    log_event(request.prompt, result.score, result.decision.value)

    if result.decision == ScanDecision.BLOCK:
        raise HTTPException(status_code=403, detail=f"Security Block: {result.details}")
    
    # 2. Execute command in E2B Sandbox
    output = execution_env.execute_command(request.prompt)
    
    return {
        "status": "success", 
        "message": f"Prompt allowed and executed.",
        "output": output,
        "details": result.details
    }

class AgentMessage(BaseModel):
    source_agent: str
    target_agent: str
    payload: str
    
@app.post("/api/agent-message")
async def route_agent_message(message: AgentMessage):
    """
    Centralized router for agent-to-agent communication.
    Intercepts the message, cleans it natively, checks it against the AI Security Engine,
    and forwards it to the target agent if safe.
    """
    # 1. Native Interception & PII Scrubbing
    from backend.interceptor import intercept_and_clean
    interceptor_result = intercept_and_clean(message.payload)
    
    if not interceptor_result.allowed:
        log_event(f"[{message.source_agent}->{message.target_agent}] {message.payload[:50]}...", 1.0, "BLOCK")
        raise HTTPException(status_code=403, detail=f"Interceptor Block: {interceptor_result.blocked_reason}")
        
    cleaned_payload = interceptor_result.redacted_content
    
    # 2. Advanced Security Engine Scan (Prompt Injection, Logic Analysis)
    engine_prompt = f"Analyze this compliance data: {cleaned_payload[:500]}"
    security_result = security_engine.evaluate_prompt(engine_prompt)
    
    log_event(f"[{message.source_agent}->{message.target_agent}] {cleaned_payload[:50]}...", security_result.score, security_result.decision.value)

    if security_result.decision == ScanDecision.BLOCK:
        raise HTTPException(status_code=403, detail=f"Security Engine Block: {security_result.details}")
        
    # 3. Simulate routing to target agent (Validator) natively
    if message.target_agent == "validator":
        import subprocess
        print(f"[Gateway Router] ✅ Message safe. Spawning {message.target_agent} agent...")
        try:
            # We call the validator script as a subprocess and pass the cleaned payload
            result = subprocess.run(
                ["python3", "validator.py", cleaned_payload],
                capture_output=True,
                text=True,
                timeout=200
            )
            return {
                "status": "success",
                "message": "Message successfully routed and processed",
                "clean_payload": cleaned_payload,
                "target_response": result.stdout
            }
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="Target agent timed out")
            
    raise HTTPException(status_code=404, detail=f"Target agent '{message.target_agent}' not found")

@app.get("/")
def root():
    return {"status": "OpenSec Gateway running"}

@app.post("/api/validate")
async def validate_request(request: AgentRequest):
    """
    Endpoint for local agents like OpenClaw.
    Validates the prompt but DOES NOT execute it in E2B.
    Returns ALLOW or BLOCK.
    """
    result = security_engine.evaluate_prompt(request.prompt)
    log_event(request.prompt, result.score, result.decision.value)

    if result.decision == ScanDecision.BLOCK:
        raise HTTPException(status_code=403, detail=f"Security Block: {result.details}")
    
    return {
        "status": "success",
        "decision": "ALLOW",
        "details": result.details
    }

class SqlRequest(BaseModel):
    query: str
    agent_id: str = "Database Guardian"

@app.post("/api/validate-sql")
async def validate_sql(request: SqlRequest):
    """
    Endpoint for the Database Guardian Agent natively intercepts SQL queries.
    Runs rule-based checks to prevent access to restricted tables or destructive commands.
    """
    q = request.query.upper()
    
    # Basic Rule-Based SQL Firewall checks
    is_blocked = False
    block_reason = ""
    score = 0.0
    
    if "USERS" in q:
        is_blocked = True
        block_reason = "Restricted Table Access ('users' table is blocked)"
        score = 1.0
    elif any(cmd in q for cmd in ["DROP", "DELETE", "TRUNCATE", "INSERT", "UPDATE"]):
        is_blocked = True
        block_reason = "Destructive/State-modifying SQL Command blocked"
        score = 1.0
        
    # Log the event
    log_event(f"[{request.agent_id}] SQL Query: {request.query[:100]}", score, "BLOCK" if is_blocked else "ALLOW")
    
    if is_blocked:
        raise HTTPException(status_code=403, detail=f"Database Firewall Block: {block_reason}")
        
    return {
        "status": "success",
        "decision": "ALLOW",
        "details": "SQL query safely analyzed and permitted."
    }

def get_all_logs():

    try:
        if LOG_FILE.exists():
            with open(LOG_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

@app.get("/api/stats")
def get_stats_api():
    logs = get_all_logs()
    return get_stats(logs)

@app.get("/api/logs")
def get_logs_api():
    return get_all_logs()

@app.get("/api/risk-analysis")
def get_risk_api():
    logs = get_all_logs()
    return get_risk_analysis(logs)

@app.get("/api/agents")
def get_agents_api():
    return AGENTS

@app.get("/api/policies")
def get_policies_api():
    return POLICIES

@app.post("/api/policies")
def update_policy_api(update: PolicyUpdate):
    if update.policy in POLICIES:
        POLICIES[update.policy] = update.value
        return {"status": "success", "policy": update.policy, "value": update.value}
    raise HTTPException(status_code=404, detail="Policy not found")
