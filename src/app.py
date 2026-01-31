# File: src/app.py
# Owner: A (Ali) - Application Engineer
# Project: GreenScale (AIBoomi Hackathon)
# Goal: Create a visually polished, "GreenScale Command Center" Streamlit dashboard.
#       It will display dynamic metrics, allow JSON job submission to Redis,
#       poll for results, and present them in a high-tech, IoT-like interface.

# Core Requirements:
# 1. Imports: os, redis, json, uuid, time, streamlit, load_dotenv.
# 2. Environment Setup: Load .env file. Load REDIS_HOST & REDIS_PORT with defaults.
# 3. Redis Client: Initialize Redis client (decode_responses=True).

# Streamlit Page Configuration:
# 4. Page Config: st.set_page_config(page_title="🟢 GreenScale Dashboard", layout="wide", initial_sidebar_state="collapsed").

# Custom CSS for "Command Center" Theme (Crucial for polished look):
# 5. Inject CSS: Use st.markdown(css_string, unsafe_allow_html=True) to apply the following styles:
#    - General Background: Dark, e.g., #0E1117.
#    - Text Color: Light grey/white.
#    - Headers (h1, h3): Green accents, centered.
#    - Metric Cards: Darker background (e.g., #1A1A2E), green left border, rounded corners, shadow, light text, green values.
#    - Buttons: Green background, white text, rounded, hover effect.
#    - Text Area: Dark background, light text, green border.
#    - Spinner: Green spinner animation.
#    - Hide Streamlit default elements (MainMenu, footer, header) for a cleaner look.

# Dashboard Structure & Content:
# 6. Global Status Banner:
#    - Initialize `current_status = "INITIALIZING..."`.
#    - Create `status_placeholder = st.empty()` for a large, dynamic `st.info` or custom-styled banner to display this.
#    - Initialize `GPU_COST_PER_HR = 4.0`.
# 7. Main Title & Intro:
#    - Main Streamlit title: "🟢 GreenScale Dashboard".
#    - Subheader: "Intelligent Autoscaler for AI/ML Workloads on Kubernetes".
#    - Markdown intro: Explaining Scale-to-Zero and KEDA's role.

# Real-time Metrics Display ("Gauge Cluster"):
# 8. Layout: Use `st.columns(3)` for three prominent metric cards.
# 9. Metric 1: "📊 Jobs in Queue" - display `redis_client.llen("jobs")`.
# 10. Metric 2: "⚡ Active Workers" - placeholder logic: `1 if st.session_state.get('active_job_id') else 0`.
# 11. Metric 3: "💰 Estimated Savings (Total)" -
#     - Initialize `st.session_state.total_time_saved_seconds = 0` if not present.
#     - Define `AVG_JOB_TIME_SECONDS = 30` (average time a worker is active per job, including cooldown).
#     - Calculate `current_savings_value_usd = (st.session_state.total_time_saved_seconds / 3600) * GPU_COST_PER_HR`.
#     - Display using `st.metric` with a positive delta.
# 12. Error Handling: Include `try-except redis.ConnectionError` for robustness in metrics fetching.

# Job Submission Form:
# 13. Section Header: `st.subheader("📝 Submit a New Job")`.
# 14. Form Container: Use `with st.form("job_submission_form", clear_on_submit=True):`.
# 15. Input: `st.text_area` for `user_prompt`.
# 16. Button: `st.form_submit_button("✅ Submit Job to Queue")`.
# 17. Submission Logic (on button click):
#     - Validate `user_prompt`.
#     - Generate `job_id` (UUID).
#     - Create JSON payload `{"job_id": str(job_id), "prompt": user_prompt.strip()}`.
#     - `LPUSH` payload to Redis `jobs` list.
#     - Update `current_status` to "QUEUED".
#     - Store `job_id` in `st.session_state['active_job_id']`.
#     - Display `st.success` message with Job ID.
#     - Call `st.experimental_rerun()`.

# Result Polling and Display:
# 18. Check `st.session_state.get('active_job_id')` for an active job.
# 19. If active:
#     - Update `current_status` to "PROCESSING".
#     - Use `with st.status("Processing Job...", expanded=True) as status_message_box:` for detailed updates.
#     - Poll Redis for `result:{job_id}` in a loop (max 60 seconds, 1-second sleep).
#     - If result found:
#         - Update `status_message_box` to "Job complete!" and set `state="complete"`.
#         - Display result in `st.code` block.
#         - Update `current_status` to "COMPLETE".
#         - Increment `st.session_state.total_time_saved_seconds` by `AVG_JOB_TIME_SECONDS`.
#         - Clear `active_job_id` from session state.
#         - Call `st.experimental_rerun()`.
#     - If timeout:
#         - Update `status_message_box` to "Job timed out." and set `state="error"`.
#         - Update `current_status` to "ERROR".
#         - Clear `active_job_id` from session state.

# Final Status Update:
# 20. Call `status_placeholder.info(f"Status: {current_status}")` at the end to update the global banner
import os
import redis
import json
import uuid
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
st.set_page_config(page_title="🟢 GreenScale Dashboard", layout="wide", initial_sidebar_state="collapsed")
# Custom CSS for "Command Center" Theme
custom_css = """
<style>
/* General Background */
body {
    background-color: #0E1117;
    color: #E0E0E0;
}
h1, h3 {
    color: #00FF00;
    text-align: center;
}
/* Metric Cards */
.metric-card {
    background-color: #1A1A2E;
    border-left: 5px solid #00FF00;
    border-radius: 10px;
    box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.5);
    padding: 20px;
    color: #E0E0E0;
}
.metric-card .value {
    color: #00FF00;
    font-size: 2em;
}
/* Buttons */
.stButton>button {
    background-color: #00FF00;
    color: #000000;
    border-radius: 10px;
}
.stButton>button:hover {
    background-color: #00CC00;
}
/* Text Area */
.stTextArea textarea {
    background-color: #1A1A2E;
    color: #E0E0E0;
    border: 2px solid #00FF00;
    border-radius: 10px;
}
/* Spinner */
.stSpinner>div {
    border-top-color: #00FF00;
}
/* Hide Streamlit default elements */
#MainMenu, footer, header {
    visibility: hidden;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
# Global Status Banner
current_status = "INITIALIZING..."
status_placeholder = st.empty()
GPU_COST_PER_HR = 4.0
status_placeholder.info(f"Status: {current_status}")
# Main Title & Intro
st.title("🟢 GreenScale Dashboard" )
st.subheader("Intelligent Autoscaler for AI/ML Workloads on Kubernetes")
st.markdown("""
Welcome to the GreenScale Command Center! This dashboard provides real-time insights into your AI/ML
workloads, leveraging Scale-to-Zero strategies powered by KEDA to optimize resource usage and costs.
""")
# Real-time Metrics Display ("Gauge Cluster")
try:
    col1, col2, col3 = st.columns(3)
    with col1:
        jobs_in_queue = redis_client.llen("jobs")
        st.markdown(f"""
        <div class="metric-card">
            <h3>📊 Jobs in Queue</h3>
            <div class="value">{jobs_in_queue}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        active_workers = 1 if st.session_state.get('active_job_id') else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>⚡ Active Workers</h3>
            <div class="value">{active_workers}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        if 'total_time_saved_seconds' not in st.session_state:
            st.session_state.total_time_saved_seconds = 0
        AVG_JOB_TIME_SECONDS = 30
        current_savings_value_usd = (st.session_state.total_time_saved_seconds / 3600) * GPU_COST_PER_HR
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Estimated Savings (Total)</h3>
            <div class="value">${current_savings_value_usd:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
except redis.ConnectionError:
    st.error("Error connecting to Redis to fetch metrics.")
# Job Submission Form
st.subheader("📝 Submit a New Job")
with st.form("job_submission_form", clear_on_submit=True):
    user_prompt = st.text_area("Enter your job prompt here:", height=150)
    submit_button = st.form_submit_button("✅ Submit Job to Queue")
    if submit_button:
        if not user_prompt.strip():
            st.error("Prompt cannot be empty. Please enter a valid prompt.")
        else:
            job_id = str(uuid.uuid4())
            job_payload = {
                "job_id": job_id,
                "prompt": user_prompt.strip()
            }
            redis_client.lpush("jobs", json.dumps(job_payload))
            current_status = "QUEUED"
            st.session_state['active_job_id'] = job_id
            st.success(f"Job submitted successfully! Your Job ID is: {job_id}")
            st.experimental_rerun()
# Result Polling and Display
active_job_id = st.session_state.get('active_job_id')
if active_job_id:
    current_status = "PROCESSING"
    with st.status("Processing Job...", expanded=True) as status_message_box:
        start_time = time.time()
        result = None
        while time.time() - start_time < 60:
            result = redis_client.get(f"result:{active_job_id}")
            if result:
                status_message_box.success("Job complete!")
                status_message_box.markdown(f"### Result:\n```{result}```")
                current_status = "COMPLETE"
                st.session_state.total_time_saved_seconds += AVG_JOB_TIME_SECONDS
                del st.session_state['active_job_id']
                st.experimental_rerun()
            time.sleep(1)
        if not result:
            status_message_box.error("Job timed out.")
            current_status = "ERROR"
            del st.session_state['active_job_id']
# Final Status Update
status_placeholder.info(f"Status: {current_status}")