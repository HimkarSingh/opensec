import random
import time
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any

# Mock Policies State
POLICIES = {
    "promptInjection": True,
    "toolAccess": False,
    "humanApproval": True,
    "dataLeakage": True
}

# Mock Agents Data
AGENTS = [
    {"id": "ag-01", "name": "CodeAssistant", "role": "Developer", "tools": ["Search", "File System", "Code Execution"], "lastActive": "Just now", "status": "Active"},
    {"id": "ag-02", "name": "DataAnalyst", "role": "Analyst", "tools": ["Database", "Web Scraping"], "lastActive": "2 mins ago", "status": "Active"},
    {"id": "ag-03", "name": "EmailBot", "role": "Communication", "tools": ["Email"], "lastActive": "15 mins ago", "status": "Suspended"},
    {"id": "ag-04", "name": "ResearchBot", "role": "Researcher", "tools": ["Search", "Browser"], "lastActive": "5 mins ago", "status": "Active"},
]

class PolicyUpdate(BaseModel):
    policy: str
    value: bool

def get_stats(logs: List[Dict[str, Any]]):
    total_requests = len(logs)
    blocked_requests = sum(1 for log in logs if log.get("decision") == "BLOCK")
    active_agents = sum(1 for agent in AGENTS if agent["status"] == "Active")
    # High risk alerts are those with score > 0.8
    high_risk_alerts = sum(1 for log in logs if log.get("score", 0) >= 0.8 and log.get("decision") == "BLOCK")
    
    return {
        "totalRequests": total_requests + 1420,  # Add some base numbers for demo
        "blockedRequests": blocked_requests + 85,
        "activeAgents": active_agents,
        "highRiskAlerts": high_risk_alerts + 12
    }

def get_risk_analysis(logs: List[Dict[str, Any]]):
    # Calculate risk distribution
    low = sum(1 for log in logs if log.get("score", 0) < 0.3) + 75
    medium = sum(1 for log in logs if 0.3 <= log.get("score", 0) < 0.7) + 20
    high = sum(1 for log in logs if log.get("score", 0) >= 0.7) + 5
    
    total = low + medium + high
    
    # Mock daily blocked actions for the last 7 days
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    blocked_counts = [12, 19, 15, 25, 22, 10, len([l for l in logs if l.get("decision") == "BLOCK"])]
    
    return {
        "pieChart": {
            "low": round((low / total) * 100),
            "medium": round((medium / total) * 100),
            "high": round((high / total) * 100)
        },
        "barChart": {
            "labels": days,
            "data": blocked_counts
        }
    }
