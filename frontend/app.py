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

# Custom CSS for Dark Theme & Neon Accents
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #0a0a16 0%, #151528 100%);
        color: #e0e0e0;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 15, 30, 0.95);
        border-right: 1px solid #2a2a4a;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Metric Cards */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        color: #00eaff !important;
        text-shadow: 0 0 10px rgba(0, 234, 255, 0.3);
    }
    .stMetric {
        background: linear-gradient(145deg, rgba(30,30,50,0.8), rgba(20,20,40,0.9));
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #3d3d6b;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 40px rgba(0, 234, 255, 0.15);
        border: 1px solid #00eaff;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(90deg, #00eaff, #0088ff);
        color: #fff;
        font-weight: bold;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background: linear-gradient(90deg, #00ffff, #00aaff);
        box-shadow: 0 0 15px rgba(0, 234, 255, 0.4);
    }
    /* Danger Buttons */
    .btn-danger button {
        background: linear-gradient(90deg, #ff4d4d, #cc0000);
    }
    .btn-danger button:hover {
        background: linear-gradient(90deg, #ff6666, #ff0000);
        box-shadow: 0 0 15px rgba(255, 77, 77, 0.4);
    }
    
    /* Dataframe and Tables */
    [data-testid="stDataFrame"] {
        background: rgba(20, 20, 40, 0.7);
        border-radius: 10px;
        border: 1px solid #2a2a4a;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        color: #8888aa;
        height: 50px;
        font-weight: 600;
        font-size: 16px;
    }
    .stTabs [aria-selected="true"] {
        color: #00eaff !important;
        border-bottom-color: #00eaff !important;
        text-shadow: 0 0 10px rgba(0, 234, 255, 0.3);
    }
    
    /* Toggles */
    .st-bc {
        background-color: #00eaff !important;
    }

    hr {
        border-color: #2a2a4a;
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

# Sidebar Navigation
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2092/2092663.png", width=60) # placeholder logo
    st.markdown("## 🛡️ **OpenSec**")
    st.markdown("<p style='color:#8888aa; font-size: 14px; margin-top: -10px;'>AI Runtime Security</p>", unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("Navigation", ["Dashboard", "Agents", "Policies", "Alerts & Logs"])
    st.markdown("---")
    
    # Simulate connection status
    stats = fetch_api("stats")
    if stats:
        st.success("🟢 API Connected")
    else:
        st.error("🔴 API Offline")

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
    
    # Two column layout for charts and recent activity
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Risk Distribution")
        risk_data = fetch_api("risk-analysis")
        if risk_data:
            # Prepare donut chart
            metrics = risk_data['pieChart']
            df = pd.DataFrame({"Risk Level": list(metrics.keys()), "Value": list(metrics.values())})
            fig = px.pie(df, values='Value', names='Risk Level', hole=0.7,
                         color='Risk Level', 
                         color_discrete_map={'low':'#00cc99', 'medium':'#ffaa00', 'high':'#ff4da6'})
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), 
                              paper_bgcolor='rgba(0,0,0,0)', 
                              plot_bgcolor='rgba(0,0,0,0)',
                              font=dict(color='#e0e0e0'))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No risk data available.")
            
    with c2:
        st.subheader("Recent Blocks")
        logs = fetch_api("logs")
        if logs:
            blocked_logs = [log for log in logs if log.get('decision') == 'BLOCK']
            # Only show latest 5
            for log in list(reversed(blocked_logs))[:5]:
                with st.container():
                    st.markdown(f'''
                    <div style="background: rgba(255, 77, 166, 0.1); border-left: 3px solid #ff4da6; padding: 10px; margin-bottom: 10px; border-radius: 4px;">
                        <span style="color: #ff4da6; font-weight: bold; font-size: 12px;">{log["timestamp"]}</span><br>
                        <span style="color: #ccc; font-size: 14px;">{log["prompt"][:50]}...</span>
                    </div>
                    ''', unsafe_allow_html=True)
            if not blocked_logs:
                st.success("No recent block events.")
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
                return 'color: #00cc99; font-weight: bold'
            return 'color: #ffaa00; font-weight: bold'
            
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
                return "background-color: rgba(255, 77, 166, 0.2); color: #ff4da6; font-weight: bold;"
            return "color: #00cc99;"
            
        st.dataframe(df.style.applymap(style_decision, subset=["decision"]),
                     use_container_width=True, height=600)
    else:
        st.info("No logs found.")
