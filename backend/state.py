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

# Authorized Agents Data
AGENTS = [
    {"id": "ag-hw1", "name": "OpenClaw", "role": "Local System Access", "tools": ["read_local_file"], "lastActive": "Just now", "status": "Active"},
    {"id": "ag-hw2", "name": "WebSpider", "role": "Web Scraping & Analysis", "tools": ["fetch_website_content"], "lastActive": "Just now", "status": "Active"}
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
        "totalRequests": total_requests,
        "blockedRequests": blocked_requests,
        "activeAgents": active_agents,
        "highRiskAlerts": high_risk_alerts
    }

def get_risk_analysis(logs: List[Dict[str, Any]]):
    # Calculate risk distribution
    low = sum(1 for log in logs if log.get("score", 0) < 0.3)
    medium = sum(1 for log in logs if 0.3 <= log.get("score", 0) < 0.7)
    high = sum(1 for log in logs if log.get("score", 0) >= 0.7)
    
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
