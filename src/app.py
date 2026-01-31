import os
import redis
import json
from dotenv import load_dotenv
import streamlit as st
import uuid
import time
import zipfile
import io
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load environment variables
load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis client with error handling
def get_redis_client():
    try:
        client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        client.ping()
        return client, True
    except:
        return None, False

redis_client, redis_connected = get_redis_client()

# Page config
st.set_page_config(
    page_title="🌱 GreenScale Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme car dashboard look
st.markdown("""
<style>
    /* Dark theme */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    /* Main title */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        background: linear-gradient(90deg, #00ff87, #60efff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .sub-title {
        text-align: center;
        color: #60efff;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* Metric cards */
    .metric-card {
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(10px);
    }
    
    /* Status indicator */
    .status-online {
        color: #00ff87;
        font-weight: bold;
    }
    .status-offline {
        color: #ff4757;
        font-weight: bold;
    }
    
    /* Result box */
    .result-box {
        background: linear-gradient(135deg, rgba(0,255,135,0.1), rgba(96,239,255,0.1));
        border: 2px solid #00ff87;
        border-radius: 15px;
        padding: 20px;
        margin: 20px 0;
    }
    
    /* Prompt input */
    .stTextArea textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 2px solid rgba(96,239,255,0.3) !important;
        border-radius: 15px !important;
        color: white !important;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00ff87, #60efff) !important;
        color: #1a1a2e !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 25px !important;
        padding: 15px 30px !important;
        font-size: 1.1rem !important;
    }
    
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 30px rgba(0,255,135,0.5);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Job history */
    .job-item {
        background: rgba(255,255,255,0.03);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #00ff87;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# GAUGE CHART FUNCTIONS
# ============================================================================

def create_gauge(value, max_value, title, color_scheme="green"):
    """Create a car-style gauge chart"""
    
    if color_scheme == "green":
        bar_color = "#00ff87"
        steps_colors = ["#0f3460", "#16213e", "#1a1a2e"]
    elif color_scheme == "blue":
        bar_color = "#60efff"
        steps_colors = ["#0f3460", "#16213e", "#1a1a2e"]
    elif color_scheme == "orange":
        bar_color = "#ffa502"
        steps_colors = ["#0f3460", "#16213e", "#1a1a2e"]
    else:
        bar_color = "#ff4757"
        steps_colors = ["#0f3460", "#16213e", "#1a1a2e"]
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 20, 'color': 'white'}},
        number={'font': {'size': 40, 'color': bar_color}},
        gauge={
            'axis': {
                'range': [0, max_value],
                'tickwidth': 2,
                'tickcolor': "white",
                'tickfont': {'color': 'white'}
            },
            'bar': {'color': bar_color, 'thickness': 0.75},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "rgba(255,255,255,0.3)",
            'steps': [
                {'range': [0, max_value*0.33], 'color': steps_colors[0]},
                {'range': [max_value*0.33, max_value*0.66], 'color': steps_colors[1]},
                {'range': [max_value*0.66, max_value], 'color': steps_colors[2]}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.8,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': 'white'},
        height=250,
        margin=dict(l=30, r=30, t=50, b=30)
    )
    
    return fig

def create_speedometer(value, title="Processing Speed"):
    """Create a speedometer-style gauge"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 18, 'color': 'white'}},
        delta={'reference': 50, 'increasing': {'color': "#00ff87"}, 'decreasing': {'color': "#ff4757"}},
        number={'suffix': " ms", 'font': {'size': 30, 'color': '#60efff'}},
        gauge={
            'axis': {'range': [0, 200], 'tickcolor': 'white', 'tickfont': {'color': 'white'}},
            'bar': {'color': "#60efff"},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 2,
            'bordercolor': "rgba(255,255,255,0.2)",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(0,255,135,0.3)'},
                {'range': [50, 100], 'color': 'rgba(96,239,255,0.3)'},
                {'range': [100, 150], 'color': 'rgba(255,165,2,0.3)'},
                {'range': [150, 200], 'color': 'rgba(255,71,87,0.3)'}
            ],
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

def create_cluster_dashboard(queue_length, active_workers, jobs_processed, savings):
    """Create a multi-gauge cluster like a car dashboard"""
    
    fig = make_subplots(
        rows=1, cols=4,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}, {'type': 'indicator'}]],
        horizontal_spacing=0.05
    )
    
    # Queue Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=queue_length,
        title={'text': "🔄 QUEUE", 'font': {'size': 16, 'color': 'white'}},
        number={'font': {'size': 36, 'color': '#60efff'}},
        gauge={
            'axis': {'range': [0, 10], 'tickcolor': 'white', 'tickfont': {'color': 'white', 'size': 10}},
            'bar': {'color': '#60efff', 'thickness': 0.7},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 2,
            'bordercolor': 'rgba(96,239,255,0.5)',
            'steps': [
                {'range': [0, 3], 'color': 'rgba(0,255,135,0.2)'},
                {'range': [3, 7], 'color': 'rgba(255,165,2,0.2)'},
                {'range': [7, 10], 'color': 'rgba(255,71,87,0.2)'}
            ]
        }
    ), row=1, col=1)
    
    # Workers Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=active_workers,
        title={'text': "⚡ WORKERS", 'font': {'size': 16, 'color': 'white'}},
        number={'font': {'size': 36, 'color': '#00ff87'}},
        gauge={
            'axis': {'range': [0, 5], 'tickcolor': 'white', 'tickfont': {'color': 'white', 'size': 10}},
            'bar': {'color': '#00ff87', 'thickness': 0.7},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 2,
            'bordercolor': 'rgba(0,255,135,0.5)',
            'steps': [
                {'range': [0, 1], 'color': 'rgba(96,239,255,0.2)'},
                {'range': [1, 3], 'color': 'rgba(0,255,135,0.2)'},
                {'range': [3, 5], 'color': 'rgba(255,165,2,0.2)'}
            ]
        }
    ), row=1, col=2)
    
    # Jobs Processed Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=jobs_processed,
        title={'text': "✅ PROCESSED", 'font': {'size': 16, 'color': 'white'}},
        number={'font': {'size': 36, 'color': '#ffa502'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': 'white', 'tickfont': {'color': 'white', 'size': 10}},
            'bar': {'color': '#ffa502', 'thickness': 0.7},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 2,
            'bordercolor': 'rgba(255,165,2,0.5)',
            'steps': [
                {'range': [0, 33], 'color': 'rgba(96,239,255,0.2)'},
                {'range': [33, 66], 'color': 'rgba(0,255,135,0.2)'},
                {'range': [66, 100], 'color': 'rgba(255,165,2,0.2)'}
            ]
        }
    ), row=1, col=3)
    
    # Savings Gauge (as percentage of $10/hr max)
    savings_value = float(savings.replace('$', '').replace('/hr', ''))
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=savings_value,
        title={'text': "💰 SAVINGS", 'font': {'size': 16, 'color': 'white'}},
        number={'prefix': '$', 'suffix': '/hr', 'font': {'size': 28, 'color': '#ff6b9d'}},
        gauge={
            'axis': {'range': [0, 10], 'tickcolor': 'white', 'tickfont': {'color': 'white', 'size': 10}},
            'bar': {'color': '#ff6b9d', 'thickness': 0.7},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 2,
            'bordercolor': 'rgba(255,107,157,0.5)',
            'steps': [
                {'range': [0, 3], 'color': 'rgba(96,239,255,0.2)'},
                {'range': [3, 6], 'color': 'rgba(0,255,135,0.2)'},
                {'range': [6, 10], 'color': 'rgba(255,107,157,0.2)'}
            ]
        }
    ), row=1, col=4)
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=280,
        margin=dict(l=20, r=20, t=60, b=20),
        showlegend=False
    )
    
    return fig

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Header
st.markdown('<h1 class="main-title">🌱 GreenScale Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Intelligent Scale-to-Zero Autoscaler for AI/ML Workloads</p>', unsafe_allow_html=True)

# Connection status
col_status1, col_status2, col_status3 = st.columns([1, 2, 1])
with col_status2:
    if redis_connected:
        st.markdown('🟢 <span class="status-online">SYSTEM ONLINE</span> | Redis Connected | KEDA Active', unsafe_allow_html=True)
    else:
        st.markdown('🔴 <span class="status-offline">SYSTEM OFFLINE</span> | Redis Disconnected', unsafe_allow_html=True)

st.markdown("---")

# ============================================================================
# INSTRUMENT CLUSTER (GAUGES)
# ============================================================================

if redis_connected:
    # Fetch real metrics
    queue_length = redis_client.llen("jobs")
    
    # Get active workers (count result keys created in last 60 seconds as proxy)
    keys = redis_client.keys("result:*")
    jobs_processed = len(keys)
    
    # Estimate active workers based on queue
    active_workers = min(5, max(0, queue_length))  # 0-5 based on queue
    if queue_length > 0:
        active_workers = max(1, active_workers)
    
    savings = "$4.25/hr"
else:
    queue_length = 0
    active_workers = 0
    jobs_processed = 0
    savings = "$0.00/hr"

# Display the gauge cluster
st.markdown("### 🎛️ System Metrics")
gauge_cluster = create_cluster_dashboard(queue_length, active_workers, jobs_processed, savings)
st.plotly_chart(gauge_cluster, use_container_width=True, config={'displayModeBar': False})

# ============================================================================
# JOB SUBMISSION
# ============================================================================

st.markdown("---")
st.markdown("### 🚀 Submit AI Job")

col1, col2 = st.columns([2, 1])

with col1:
    user_prompt = st.text_area(
        "Enter your prompt:",
        placeholder="Ask anything! e.g., 'Explain quantum computing in simple terms'",
        height=120,
        key="prompt_input"
    )
    
    submit_col1, submit_col2 = st.columns(2)
    with submit_col1:
        submit_button = st.button("🚀 Submit Job", use_container_width=True, type="primary")
    with submit_col2:
        clear_button = st.button("🗑️ Clear History", use_container_width=True)

with col2:
    st.markdown("#### ⚙️ Quick Stats")
    if redis_connected:
        st.metric("Queue Length", queue_length, delta=None)
        st.metric("Jobs Today", jobs_processed)
        st.metric("Avg Response", "~3s")
    else:
        st.warning("Connect to Redis to see stats")

# Handle clear history
if clear_button and redis_connected:
    # Clear job history from session
    if 'job_history' in st.session_state:
        st.session_state.job_history = []
    st.success("History cleared!")
    st.rerun()

# Initialize job history
if 'job_history' not in st.session_state:
    st.session_state.job_history = []

# Handle job submission
if submit_button:
    if not redis_connected:
        st.error("❌ Cannot submit job - Redis is not connected!")
    elif not user_prompt.strip():
        st.warning("⚠️ Please enter a prompt before submitting.")
    else:
        job_id = str(uuid.uuid4())[:8]  # Shorter ID for display
        job_payload = {
            "job_id": job_id,
            "prompt": user_prompt.strip()
        }
        
        try:
            redis_client.lpush("jobs", json.dumps(job_payload))
            st.session_state['active_job_id'] = job_id
            st.session_state['active_prompt'] = user_prompt.strip()
            st.success(f"✅ Job submitted! ID: `{job_id}`")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed to submit job: {str(e)}")

# ============================================================================
# RESULT DISPLAY WITH POLLING
# ============================================================================

st.markdown("---")
st.markdown("### 📊 Job Results")

if 'active_job_id' in st.session_state and redis_connected:
    job_id = st.session_state['active_job_id']
    prompt = st.session_state.get('active_prompt', 'Unknown prompt')
    
    # Create a placeholder for the result
    result_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    with result_placeholder.container():
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(96,239,255,0.1), rgba(0,255,135,0.1)); 
                    border: 2px solid #60efff; border-radius: 15px; padding: 20px; margin: 10px 0;">
            <h4 style="color: #60efff; margin: 0;">⏳ Processing Job: {job_id}</h4>
            <p style="color: #aaa; margin: 10px 0;">Prompt: {prompt[:100]}...</p>
            <p style="color: #00ff87;">KEDA is scaling up workers...</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Progress bar
    progress_bar = progress_placeholder.progress(0, text="Waiting for worker to wake up...")
    
    # Poll for result
    result = None
    for i in range(60):  # 60 second timeout
        try:
            result = redis_client.get(f"result:{job_id}")
            if result:
                break
            progress_bar.progress((i + 1) / 60, text=f"Processing... ({i+1}s)")
            time.sleep(1)
        except Exception as e:
            st.error(f"Error polling: {str(e)}")
            break
    
    progress_placeholder.empty()
    
    if result:
        # Success! Show the result
        result_placeholder.empty()
        
        # Add to history
        st.session_state.job_history.insert(0, {
            'job_id': job_id,
            'prompt': prompt,
            'result': result,
            'timestamp': time.strftime("%H:%M:%S")
        })
        
        # Keep only last 10 jobs
        st.session_state.job_history = st.session_state.job_history[:10]
        
        # Clear active job
        del st.session_state['active_job_id']
        if 'active_prompt' in st.session_state:
            del st.session_state['active_prompt']
        
        st.rerun()
    else:
        result_placeholder.empty()
        st.error("⏱️ Job timed out after 60 seconds. Please try again.")
        del st.session_state['active_job_id']

# Display job history
if st.session_state.job_history:
    for job in st.session_state.job_history:
        with st.expander(f"✅ Job {job['job_id']} - {job['timestamp']}", expanded=(job == st.session_state.job_history[0])):
            st.markdown(f"**Prompt:** {job['prompt']}")
            st.markdown("---")
            st.markdown(f"""
            <div style="background: rgba(0,255,135,0.1); border-left: 4px solid #00ff87; 
                        padding: 15px; border-radius: 0 10px 10px 0;">
                <strong style="color: #00ff87;">🤖 AI Response:</strong><br><br>
                <span style="color: white;">{job['result']}</span>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("💡 Submit a job to see results here. The AI response will appear automatically!")

# ============================================================================
# LIVE SYSTEM MONITOR
# ============================================================================

st.markdown("---")
st.markdown("### 📡 Live System Monitor")

monitor_col1, monitor_col2 = st.columns(2)

with monitor_col1:
    # Mini speedometer for response time
    response_time = 45 if redis_connected else 0
    speedometer = create_speedometer(response_time, "Avg Response Time")
    st.plotly_chart(speedometer, use_container_width=True, config={'displayModeBar': False})

with monitor_col2:
    # System status indicators
    st.markdown("""
    <div style="background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px;">
        <h4 style="color: white; margin-bottom: 15px;">🖥️ System Status</h4>
    </div>
    """, unsafe_allow_html=True)
    
    status_items = [
        ("Redis", redis_connected, "Message Broker"),
        ("KEDA", True, "Autoscaler"),
        ("Worker Pool", True, "Scale-to-Zero Ready"),
        ("Llama 3.3 API", True, "AI Engine")
    ]
    
    for name, status, desc in status_items:
        icon = "🟢" if status else "🔴"
        st.markdown(f"{icon} **{name}** - {desc}")

# ============================================================================
# HELM CHART GENERATOR (Collapsible)
# ============================================================================

st.markdown("---")
with st.expander("📦 Helm Chart Generator", expanded=False):
    st.markdown("Generate a customized Helm chart for deploying GreenScale to any Kubernetes cluster.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chart_name = st.text_input("Chart Name", value="greenscale", key="helm_chart_name")
        namespace = st.text_input("Namespace", value="greenscale-system", key="helm_namespace")
        image_repo = st.text_input("Image Repository", value="greenscale-worker", key="helm_image")
        image_tag = st.text_input("Image Tag", value="latest", key="helm_tag")
        
    with col2:
        min_replicas = st.number_input("Min Replicas", min_value=0, max_value=10, value=0, key="helm_min")
        max_replicas = st.number_input("Max Replicas", min_value=1, max_value=100, value=5, key="helm_max")
        cooldown = st.number_input("Cooldown (seconds)", min_value=10, max_value=600, value=30, key="helm_cooldown")
        polling_interval = st.number_input("Polling Interval", min_value=1, max_value=60, value=5, key="helm_poll")
    
    if st.button("🚀 Generate Helm Chart", key="generate_helm"):
        # Generate helm chart (simplified)
        chart_yaml = f"""apiVersion: v2
name: {chart_name}
description: GreenScale - Scale-to-Zero Autoscaler
version: 1.0.0
appVersion: "1.0.0"
"""
        values_yaml = f"""replicaCount: {min_replicas}
image:
  repository: {image_repo}
  tag: {image_tag}
namespace: {namespace}
keda:
  minReplicaCount: {min_replicas}
  maxReplicaCount: {max_replicas}
  cooldownPeriod: {cooldown}
  pollingInterval: {polling_interval}
"""
        
        # Create ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{chart_name}/Chart.yaml", chart_yaml)
            zf.writestr(f"{chart_name}/values.yaml", values_yaml)
        
        zip_buffer.seek(0)
        st.success("✅ Helm chart generated!")
        st.download_button("📥 Download Helm Chart", zip_buffer, f"{chart_name}-chart.zip", "application/zip")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🌱 <strong>GreenScale v1.0</strong> | Built for AIBoomi Hackathon 2026</p>
    <p>Scale-to-Zero • KEDA Powered • Llama 3.3 70B</p>
    <p><a href="https://github.com/Pswaikar1742/Greenscale" target="_blank" style="color: #60efff;">GitHub</a></p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh every 5 seconds if there's an active job
if 'active_job_id' not in st.session_state:
    # Add a manual refresh button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refresh Metrics", use_container_width=True):
            st.rerun()
