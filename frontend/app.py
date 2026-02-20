import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

st.set_page_config(
    page_title="OpenSec | AI Runtime Security Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Sleek Dark & White Theme
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #000000;
        color: #f0f0f0;
        font-family: 'Inter', sans-serif;
    /* Hide Streamlit Header Navbar */
    [data-testid="stHeader"] {
        display: none;
    }
    .block-container {
        padding-top: 2rem !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #000000;
        border-right: 1px solid #1a1a1a;
    }
    /* Remove Sidebar Top Padding */
    [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding-top: 2rem !important;
    }
    
    /* Sidebar Text Input overrides */
    [data-testid="stSidebar"] .stTextArea textarea {
        background-color: #0a0a0a;
        color: #ffffff;
        border: 1px solid #333333;
    }
    [data-testid="stSidebar"] p {
        color: #888888 !important;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 500;
        letter-spacing: -0.5px;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        color: #ffffff !important;
        font-weight: 600;
        text-shadow: none;
    }
    .stMetric {
        background-color: transparent;
        padding: 20px;
        border-radius: 6px;
        border: 1px solid #333333;
        transition: border 0.2s ease;
        box-shadow: none;
    }
    .stMetric:hover {
        border: 1px solid #ffffff;
        transform: none;
    }
    
    /* Buttons */
    .stButton button {
        background: #ffffff;
        color: #050505;
        font-weight: 600;
        border: 1px solid #ffffff;
        border-radius: 4px;
        padding: 8px 24px;
        transition: all 0.2s ease;
    }
    .stButton button:hover {
        background: #050505;
        color: #ffffff;
        border: 1px solid #ffffff;
        box-shadow: none;
    }
    
    /* Dataframe and Tables */
    [data-testid="stDataFrame"] {
        background-color: #0a0a0a;
        border-radius: 6px;
        border: 1px solid #222222;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        color: #666666;
        height: 50px;
        font-weight: 500;
        font-size: 16px;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom-color: #ffffff !important;
        text-shadow: none;
    }
    
    /* Toggles */
    .st-bc {
        background-color: #ffffff !important;
    }

    hr {
        border-color: #222222;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to fetch data from backend
API_BASE = "http://localhost:8000/api"

@st.cache_data(ttl=1)
def fetch_api(endpoint):
    try:
        response = requests.get(f"{API_BASE}/{endpoint}", timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        return None
    return None

def post_api(endpoint, payload):
    try:
        response = requests.post(f"{API_BASE}/{endpoint}", json=payload, timeout=2)
        return response.status_code == 200
    except:
        return False

def post_gateway(prompt):
    try:
        response = requests.post("http://localhost:8000/gateway", json={"prompt": prompt}, timeout=20)
        if response.status_code == 200:
            return True, response.json()
        elif response.status_code == 403:
            return False, response.json()
        else:
            return False, {"detail": f"HTTP {response.status_code}"}
    except Exception as e:
        return False, {"detail": str(e)}

# Sidebar Navigation
with st.sidebar:
    st.markdown("## 🛡️ **OpenSec**")
    st.markdown("<p style='color:#8888aa; font-size: 14px; margin-top: -10px; font-weight: 500;'>Your Local Agentic Firewall</p>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigation", ["Dashboard", "Agents", "Policies", "Alerts & Logs"], label_visibility="collapsed")
    st.markdown("---")
    
    # Minimalist connection status
    stats = fetch_api("stats")
    if stats:
        st.caption("🟢 System Online")
    else:
        st.caption("🔴 System Offline")
        
    st.markdown("#### Terminal Emulator")
    with st.form("agent_prompt_form", clear_on_submit=True):
        agent_prompt = st.text_area("", placeholder="Enter action payload... (e.g. read file src/)", height=100, label_visibility="collapsed")
        submit_prompt = st.form_submit_button("Execute")
        
    if submit_prompt and agent_prompt:
        with st.spinner("Analyzing intent..."):
            success, data = post_gateway(agent_prompt)
            if success:
                st.success("✅ **ALLOWED**")
                with st.expander("Execution Output"):
                    st.code(data.get("output", ""))
            else:
                st.error("🛑 **BLOCKED**")
                # Handle different error formats safely
                detail = data.get("detail", "Forbidden")
                if isinstance(detail, list) and len(detail) > 0 and isinstance(detail[0], dict):
                    detail = detail[0].get("msg", str(detail))
                st.caption(f"Reason: {detail}")

# Dashboard View
if page == "Dashboard":
    st.title("Network Overview")
    
    stats = fetch_api("stats")
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Requests", f"{stats['totalRequests']:,}", "↑ 12% vs last 24h")
        col2.metric("Blocked Payload", f"{stats['blockedRequests']}", "⚠ Security Actions")
        col3.metric("Active Agents", f"{stats['activeAgents']}", "Online")
        col4.metric("High Risk Alerts", f"{stats['highRiskAlerts']}", "Critical")
    else:
        st.warning("Unable to reach backend API. Stats overview unavailable.")
        
    st.markdown("---")
    
    # Recent Activity (Full width since pie chart is removed)
    st.subheader("Recent Activity / Blocks")
    logs = fetch_api("logs")
    if logs:
        blocked_logs = [log for log in logs if log.get('decision') == 'BLOCK']
        # Only show latest 5
        for log in list(reversed(blocked_logs))[:5]:
            with st.container():
                st.markdown(f'''
                <div style="background: rgba(255, 255, 255, 0.05); border-left: 3px solid #ffffff; padding: 15px; margin-bottom: 15px; border-radius: 4px;">
                    <span style="color: #ffffff; font-weight: bold; font-size: 12px;">{log["timestamp"]}</span><br>
                    <span style="color: #aaaaaa; font-size: 14px;">{log["prompt"][:100]}...</span>
                </div>
                ''', unsafe_allow_html=True)
        if not blocked_logs:
            st.success("No recent block events recorded.")
    else:
        st.info("Log feed offline.")

# Agents View
elif page == "Agents":
    st.title("AI Agents Directory")
    agents = fetch_api("agents")
    if agents:
        df = pd.DataFrame(agents)
        # Apply rudimentary styling
        def highlight_status(val):
            if val == 'Active':
                return 'color: #ffffff; font-weight: bold'
            return 'color: #666666; font-weight: bold'
            
        st.dataframe(df.style.applymap(highlight_status, subset=['status']), 
                     use_container_width=True, hide_index=True)
    else:
        st.info("Failed to load agent directory.")

# Policies View
elif page == "Policies":
    st.title("Security Policies")
    st.write("Configure connection rules and runtime constraints for your AI agents.")
    
    policies = fetch_api("policies")
    if policies:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Core Guardrails")
            p_inj = st.toggle("Anti-Prompt Injection", value=policies.get("promptInjection", True))
            if p_inj != policies.get("promptInjection"):
                post_api("policies", {"policy": "promptInjection", "value": p_inj})
                st.experimental_rerun()
                
            d_leak = st.toggle("Data Leakage Prevention", value=policies.get("dataLeakage", True))
            if d_leak != policies.get("dataLeakage"):
                post_api("policies", {"policy": "dataLeakage", "value": d_leak})
                st.experimental_rerun()
                
        with col2:
            st.markdown("### Operational Sandbox")
            t_acc = st.toggle("External Tool Access (Browser, CLI)", value=policies.get("toolAccess", False))
            if t_acc != policies.get("toolAccess"):
                post_api("policies", {"policy": "toolAccess", "value": t_acc})
                st.experimental_rerun()
                
            h_app = st.toggle("Human-in-the-loop Approval", value=policies.get("humanApproval", True))
            if h_app != policies.get("humanApproval"):
                post_api("policies", {"policy": "humanApproval", "value": h_app})
                st.experimental_rerun()
    else:
        st.error("Failed to load policy engine.")

# Alerts & Logs View
elif page == "Alerts & Logs":
    st.title("Security Audit Logs")
    
    logs = fetch_api("logs")
    if logs:
        df = pd.DataFrame(logs)
        df = df[::-1].reset_index(drop=True)
        
        search = st.text_input("🔍 Search logs", placeholder="Filter by keyword or prompt...")
        if search:
            df = df[df['prompt'].str.contains(search, case=False, na=False)]
            
        # Display logic format
        def style_decision(val):
            if val == "BLOCK":
                return "background-color: rgba(255, 77, 77, 0.15); color: #ff6666; font-weight: bold;"
            return "color: #00cc99;"
            
        st.dataframe(df.style.applymap(style_decision, subset=["decision"]),
                     use_container_width=True, height=600)
    else:
        st.info("No logs found.")
