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

app = FastAPI()

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
