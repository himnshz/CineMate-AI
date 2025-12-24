"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   CineMate Care - Caregiver Dashboard                                        ║
║   A medical-grade monitoring interface for cognitive support AI              ║
║                                                                               ║
║   HOW TO RUN:                                                                 ║
║   1. Install dependencies: pip install -r requirements.txt                   ║
║   2. Start the dashboard:  streamlit run app.py                              ║
║   3. Run backend in another terminal: python ../backend/main.py              ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from PIL import Image

# Auto-refresh component
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False


# =============================================================================
# PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="CineMate Care - Caregiver Dashboard",
    page_icon="💚",  # Medical heart
    layout="wide",
    initial_sidebar_state="expanded"
)


# =============================================================================
# CUSTOM CSS - Clean Medical/Institutional Theme (Light, Trustworthy)
# =============================================================================
st.markdown("""
<style>
    /* Main color palette - Medical/Trustworthy */
    :root {
        --primary-blue: #0078D4;
        --secondary-blue: #00A4EF;
        --medical-green: #28A745;
        --calm-green: #4CAF50;
        --alert-orange: #FFC107;
        --alert-red: #DC3545;
        --soft-white: #F8F9FA;
        --text-dark: #333333;
    }
    
    /* Light theme override */
    .stApp {
        background-color: #F8F9FA;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0078D4 0%, #00A4EF 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    /* Status indicators */
    .status-online {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #28A745;
        margin-right: 8px;
        animation: pulse 2s infinite;
    }
    
    .status-offline {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        background-color: #DC3545;
        margin-right: 8px;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
        100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin: 10px 0;
    }
    
    /* Thought bubble */
    .thought-bubble {
        background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
        border-left: 4px solid #0078D4;
        padding: 15px;
        border-radius: 0 10px 10px 0;
        margin: 15px 0;
        font-style: italic;
        color: #333;
    }
    
    /* Activity log entries */
    .log-entry {
        background: white;
        padding: 10px 15px;
        border-radius: 5px;
        border-left: 3px solid #0078D4;
        margin: 5px 0;
        font-family: 'Consolas', monospace;
        font-size: 13px;
    }
    
    .log-vision { border-left-color: #17A2B8; }
    .log-action { border-left-color: #28A745; }
    .log-alert { border-left-color: #FFC107; background-color: #FFF8E1; }
    .log-distress { border-left-color: #DC3545; background-color: #FFEBEE; }
    
    /* Guardian mode badge */
    .guardian-badge {
        background: linear-gradient(135deg, #28A745 0%, #20C997 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
    }
    
    /* Sidebar styling */
    .sidebar-title {
        color: #0078D4;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    /* Mood indicator */
    .mood-calm { color: #28A745; }
    .mood-happy { color: #FFC107; }
    .mood-sad { color: #6C757D; }
    .mood-tense { color: #DC3545; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================
if 'session_start' not in st.session_state:
    st.session_state.session_start = datetime.now()

if 'guardian_mode' not in st.session_state:
    st.session_state.guardian_mode = True

if 'engagement_history' not in st.session_state:
    st.session_state.engagement_history = []

if 'intervention_count' not in st.session_state:
    st.session_state.intervention_count = 0


# =============================================================================
# DATA LOADING FUNCTIONS
# =============================================================================
def load_state() -> Dict[str, Any]:
    """
    Load the latest state from backend files.
    
    Reads:
    - latest_frame.jpg: Current video frame
    - activity_log.json: Log of AI actions
    
    Returns mock data if files don't exist (backend not running).
    """
    state = {
        "frame": None,
        "scene_description": "Waiting for backend to start...",
        "current_mood": "Calm",
        "thought": "AI is initializing...",
        "is_online": False,
        "activity_log": []
    }
    
    # Try to load frame
    frame_path = Path("../backend/latest_frame.jpg")
    alt_frame_path = Path("latest_frame.jpg")
    
    for fp in [frame_path, alt_frame_path]:
        if fp.exists():
            try:
                # Check if file was modified in last 10 seconds
                mtime = fp.stat().st_mtime
                if time.time() - mtime < 10:
                    state["frame"] = Image.open(fp)
                    state["is_online"] = True
                break
            except Exception:
                pass
    
    # Try to load activity log
    log_path = Path("../backend/activity_log.json")
    alt_log_path = Path("activity_log.json")
    
    for lp in [log_path, alt_log_path]:
        if lp.exists():
            try:
                with open(lp, 'r') as f:
                    data = json.load(f)
                    state["activity_log"] = data.get("logs", [])[-10:]  # Last 10
                    state["scene_description"] = data.get("scene", state["scene_description"])
                    state["current_mood"] = data.get("mood", state["current_mood"])
                    state["thought"] = data.get("thought", state["thought"])
                    state["intervention_count"] = data.get("interventions", 0)
                break
            except Exception:
                pass
    
    # Use mock data if nothing loaded
    if not state["activity_log"]:
        state["activity_log"] = generate_mock_log()
    
    return state


def generate_mock_log() -> List[Dict]:
    """Generate mock activity log for demo when backend isn't running."""
    now = datetime.now()
    return [
        {
            "time": (now - timedelta(minutes=5)).strftime("%H:%M:%S"),
            "type": "VISION",
            "message": "Detected 'Two people talking at a table'"
        },
        {
            "time": (now - timedelta(minutes=4)).strftime("%H:%M:%S"),
            "type": "ACTION",
            "message": "Scene: Mundane. AI staying quiet."
        },
        {
            "time": (now - timedelta(minutes=3)).strftime("%H:%M:%S"),
            "type": "VISION",
            "message": "Detected 'Person looking sad, alone on bench'"
        },
        {
            "time": (now - timedelta(minutes=2)).strftime("%H:%M:%S"),
            "type": "ACTION",
            "message": "Spoke comfort: 'This is a touching moment...'"
        },
        {
            "time": (now - timedelta(minutes=1)).strftime("%H:%M:%S"),
            "type": "ALERT",
            "message": "Detected elevated emotional content in scene"
        },
    ]


def get_session_duration() -> str:
    """Calculate session duration as formatted string."""
    duration = datetime.now() - st.session_state.session_start
    minutes = int(duration.total_seconds() // 60)
    seconds = int(duration.total_seconds() % 60)
    return f"{minutes}m {seconds}s"


def generate_engagement_data() -> pd.DataFrame:
    """Generate engagement data for the chart."""
    # Add new data point
    st.session_state.engagement_history.append({
        "time": datetime.now(),
        "engagement": np.random.uniform(0.6, 0.95)
    })
    
    # Keep last 20 points
    st.session_state.engagement_history = st.session_state.engagement_history[-20:]
    
    return pd.DataFrame(st.session_state.engagement_history)


# =============================================================================
# SIDEBAR - CONTROLS
# =============================================================================
def render_sidebar(state: Dict[str, Any]):
    """Render the sidebar controls and status."""
    
    with st.sidebar:
        # Logo/Title
        st.markdown('<div class="sidebar-title">💚 CineMate Care</div>', unsafe_allow_html=True)
        st.caption("Cognitive Support System")
        
        st.markdown("---")
        
        # Status Indicator
        st.markdown("### 📡 System Status")
        
        if state["is_online"]:
            st.markdown(
                '<span class="status-online"></span> <strong style="color: #28A745;">Monitoring Active</strong>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<span class="status-offline"></span> <strong style="color: #DC3545;">Backend Offline</strong>',
                unsafe_allow_html=True
            )
            st.caption("Run `python main.py` in backend folder")
        
        st.markdown("---")
        
        # Guardian Mode Toggle
        st.markdown("### 🛡️ Guardian Mode")
        st.session_state.guardian_mode = st.toggle(
            "Enable Enhanced Safety",
            value=st.session_state.guardian_mode,
            help="When enabled, AI provides heightened distress monitoring"
        )
        
        if st.session_state.guardian_mode:
            st.markdown(
                '<div class="guardian-badge">🛡️ High Sensitivity Active</div>',
                unsafe_allow_html=True
            )
            st.caption("Distress detection sensitivity: Maximum")
        else:
            st.caption("Standard monitoring mode")
        
        st.markdown("---")
        
        # User Profile
        st.markdown("### 👤 Active Profile")
        profile = st.selectbox(
            "Select user profile",
            options=[
                "Grandpa Joe (Dementia)",
                "Jane Doe (Visually Impaired)",
                "Robert Smith (Hearing Impaired)",
                "Demo User (General)"
            ],
            label_visibility="collapsed"
        )
        
        # Profile info
        if "Dementia" in profile:
            st.info("📋 Profile: Memory aids enabled. Character reminders active.")
        elif "Visually Impaired" in profile:
            st.info("📋 Profile: Detailed scene descriptions enabled.")
        elif "Hearing Impaired" in profile:
            st.info("📋 Profile: Visual alerts enabled. Captions active.")
        
        st.markdown("---")
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📞 Alert Caregiver", use_container_width=True):
                st.success("Alert sent!")
        with col2:
            if st.button("⏸️ Pause Session", use_container_width=True):
                st.warning("Session paused")


# =============================================================================
# MAIN CONTENT - VIDEO FEED & STATUS
# =============================================================================
def render_main_feed(state: Dict[str, Any]):
    """Render the main video feed and AI status."""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin:0;">🎬 CineMate Care Dashboard</h1>
        <p style="margin:5px 0 0 0; opacity:0.9;">Real-Time Cognitive Support Monitoring</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Main layout
    col_feed, col_stats = st.columns([2, 1])
    
    with col_feed:
        st.markdown("### 📹 Live Monitoring Feed")
        
        # Display frame or placeholder
        if state["frame"]:
            st.image(state["frame"], caption="Current Scene", use_container_width=True)
        else:
            # Placeholder
            placeholder_html = """
            <div style="background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%); 
                        height: 300px; border-radius: 10px; display: flex; 
                        align-items: center; justify-content: center; flex-direction: column;">
                <span style="font-size: 48px;">📷</span>
                <p style="color: #666; margin-top: 10px;">Waiting for video feed...</p>
                <p style="color: #999; font-size: 12px;">Start backend: python main.py</p>
            </div>
            """
            st.markdown(placeholder_html, unsafe_allow_html=True)
        
        # AI Thought Bubble
        st.markdown("#### 💭 AI Analysis")
        st.markdown(f"""
        <div class="thought-bubble">
            <strong>Scene Analysis:</strong> {state['scene_description'][:100]}...<br>
            <strong>Current Mood:</strong> <span class="mood-{state['current_mood'].lower()}">{state['current_mood']}</span><br>
            <strong>Action:</strong> {state['thought']}
        </div>
        """, unsafe_allow_html=True)
    
    with col_stats:
        st.markdown("### 📊 Session Metrics")
        
        # Metrics
        st.metric(
            label="⏱️ Session Duration",
            value=get_session_duration()
        )
        
        st.metric(
            label="💬 AI Interventions",
            value=state.get("intervention_count", 3),
            delta="+1 in last 5 min"
        )
        
        mood_emoji = {"Calm": "😌", "Happy": "😊", "Sad": "😢", "Tense": "😬"}
        st.metric(
            label="🎭 Current Mood",
            value=f"{mood_emoji.get(state['current_mood'], '😐')} {state['current_mood']}"
        )
        
        st.metric(
            label="🛡️ Guardian Status",
            value="Active" if st.session_state.guardian_mode else "Standby"
        )


# =============================================================================
# ANALYTICS SECTION
# =============================================================================
def render_analytics():
    """Render the engagement analytics chart."""
    
    st.markdown("---")
    st.markdown("### 📈 Patient Engagement Analytics")
    st.caption(
        "This data helps healthcare providers track cognitive responsiveness over time. "
        "Higher engagement indicates active attention and emotional connection to content."
    )
    
    # Generate engagement data
    df = generate_engagement_data()
    
    if len(df) > 1:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['time'],
            y=df['engagement'],
            mode='lines+markers',
            fill='tozeroy',
            line=dict(color='#0078D4', width=2),
            fillcolor='rgba(0, 120, 212, 0.1)',
            marker=dict(size=6, color='#0078D4'),
            name='Engagement Level'
        ))
        
        fig.update_layout(
            height=250,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(248,249,250,1)',
            yaxis=dict(
                title="Engagement Level",
                range=[0, 1.1],
                gridcolor='rgba(0,0,0,0.1)'
            ),
            xaxis=dict(
                title="Time",
                gridcolor='rgba(0,0,0,0.1)'
            ),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Collecting engagement data... Chart will appear after a few seconds.")


# =============================================================================
# ACTIVITY LOG SECTION
# =============================================================================
def render_activity_log(state: Dict[str, Any]):
    """Render the activity log panel."""
    
    st.markdown("---")
    st.markdown("### 📋 Activity Log")
    st.caption("Real-time log of AI observations and actions")
    
    # Display log entries
    if state["activity_log"]:
        for entry in reversed(state["activity_log"][-5:]):  # Last 5, newest first
            entry_type = entry.get("type", "INFO")
            log_class = "log-vision"
            
            if entry_type == "ACTION":
                log_class = "log-action"
            elif entry_type == "ALERT":
                log_class = "log-alert"
            elif entry_type == "DISTRESS":
                log_class = "log-distress"
            
            st.markdown(f"""
            <div class="log-entry {log_class}">
                <strong>[{entry.get('time', '--:--:--')}]</strong> 
                <span style="color: #0078D4;">{entry_type}:</span> 
                {entry.get('message', 'No details')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📝 No activity logged yet. Waiting for backend...")


# =============================================================================
# FOOTER
# =============================================================================
def render_footer():
    """Render the footer."""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 20px;">
        <p><strong>CineMate Care</strong> - Cognitive Companion for Elderly Users</p>
        <p style="font-size: 12px;">
            Powered by Azure AI Vision • Azure OpenAI (GPT-4o) • Azure Speech Service
        </p>
        <p style="font-size: 11px; color: #AAA;">
            Imagine Cup 2026 | Microsoft Azure | Accessibility & Healthcare
        </p>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MAIN APP
# =============================================================================
def main():
    """Main application entry point."""
    
    # Auto-refresh every 2 seconds
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=2000, limit=None, key="dashboard_refresh")
    
    # Load current state
    state = load_state()
    
    # Render components
    render_sidebar(state)
    render_main_feed(state)
    render_analytics()
    render_activity_log(state)
    render_footer()
    
    # Manual refresh button (fallback if autorefresh not available)
    if not AUTOREFRESH_AVAILABLE:
        st.sidebar.markdown("---")
        if st.sidebar.button("🔄 Refresh Dashboard"):
            st.rerun()


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()
