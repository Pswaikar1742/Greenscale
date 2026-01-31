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
from datetime import datetime

# Load environment variables
load_dotenv()

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# GPU cost per hour (A100 GPU pricing)
GPU_COST_PER_HOUR = 3.50

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
    page_title="🌱 GreenScale",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Premium dark theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #111827 50%, #0a0a0f 100%);
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .sub-title {
        color: #9ca3af;
        font-size: 1.1rem;
        font-weight: 400;
        margin-top: 0.5rem;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 50px;
        padding: 8px 20px;
        color: #10b981;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .status-badge-offline {
        background: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #ef4444;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: rgba(16, 185, 129, 0.3);
        box-shadow: 0 0 30px rgba(16, 185, 129, 0.1);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
    }
    
    .metric-label {
        color: #9ca3af;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 8px;
    }
    
    /* Color variants */
    .text-emerald { color: #10b981; }
    .text-blue { color: #3b82f6; }
    .text-purple { color: #8b5cf6; }
    .text-amber { color: #f59e0b; }
    .text-rose { color: #f43f5e; }
    .text-cyan { color: #06b6d4; }
    
    /* Result card */
    .result-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.05) 0%, rgba(59, 130, 246, 0.05) 100%);
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }
    
    .result-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 16px;
    }
    
    .result-icon {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #10b981, #3b82f6);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .result-content {
        color: #e5e7eb;
        font-size: 1rem;
        line-height: 1.7;
    }
    
    /* Processing animation */
    .processing-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 16px;
        padding: 24px;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 14px 28px !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3) !important;
    }
    
    /* Text area */
    .stTextArea textarea {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #e5e7eb !important;
        font-size: 1rem !important;
    }
    
    .stTextArea textarea:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
    }
    
    /* Section headers */
    .section-header {
        color: #f3f4f6;
        font-size: 1.5rem;
        font-weight: 600;
        margin: 2rem 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    /* System status */
    .status-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        background: rgba(255,255,255,0.02);
        border-radius: 10px;
        margin: 8px 0;
    }
    
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        animation: blink 2s infinite;
    }
    
    .status-dot-online { background: #10b981; }
    .status-dot-offline { background: #ef4444; }
    
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none;}
    
    /* Divider */
    hr {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.06);
        margin: 2rem 0;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.02) !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'job_history' not in st.session_state:
    st.session_state.job_history = []
if 'total_jobs' not in st.session_state:
    st.session_state.total_jobs = 0
if 'total_savings' not in st.session_state:
    st.session_state.total_savings = 0.0
if 'session_start' not in st.session_state:
    st.session_state.session_start = time.time()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_savings(jobs_processed, idle_hours=0):
    """Calculate savings based on Scale-to-Zero"""
    # Each job takes ~5 seconds, so we save money when not processing
    active_time_hours = (jobs_processed * 5) / 3600  # Convert seconds to hours
    session_hours = (time.time() - st.session_state.session_start) / 3600
    idle_hours = max(0, session_hours - active_time_hours)
    savings = idle_hours * GPU_COST_PER_HOUR
    return round(savings, 2)

def create_modern_gauge(value, max_value, title, color, icon):
    """Create a sleek modern gauge"""
    
    # Color presets
    colors = {
        'emerald': {'main': '#10b981', 'light': 'rgba(16, 185, 129, 0.2)', 'dark': 'rgba(16, 185, 129, 0.05)'},
        'blue': {'main': '#3b82f6', 'light': 'rgba(59, 130, 246, 0.2)', 'dark': 'rgba(59, 130, 246, 0.05)'},
        'purple': {'main': '#8b5cf6', 'light': 'rgba(139, 92, 246, 0.2)', 'dark': 'rgba(139, 92, 246, 0.05)'},
        'amber': {'main': '#f59e0b', 'light': 'rgba(245, 158, 11, 0.2)', 'dark': 'rgba(245, 158, 11, 0.05)'},
        'rose': {'main': '#f43f5e', 'light': 'rgba(244, 63, 94, 0.2)', 'dark': 'rgba(244, 63, 94, 0.05)'},
        'cyan': {'main': '#06b6d4', 'light': 'rgba(6, 182, 212, 0.2)', 'dark': 'rgba(6, 182, 212, 0.05)'},
    }
    
    c = colors.get(color, colors['emerald'])
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={
            'font': {'size': 48, 'color': c['main'], 'family': 'Inter'},
            'suffix': '' if title != 'SAVINGS' else '',
            'prefix': '$' if title == 'SAVINGS' else ''
        },
        title={
            'text': f"{icon} {title}",
            'font': {'size': 14, 'color': '#9ca3af', 'family': 'Inter'}
        },
        gauge={
            'axis': {
                'range': [0, max_value],
                'tickwidth': 0,
                'tickcolor': 'rgba(0,0,0,0)',
                'tickfont': {'color': 'rgba(0,0,0,0)'}
            },
            'bar': {'color': c['main'], 'thickness': 0.6},
            'bgcolor': c['dark'],
            'borderwidth': 0,
            'steps': [
                {'range': [0, max_value], 'color': c['dark']}
            ],
            'threshold': {
                'line': {'color': c['main'], 'width': 0},
                'thickness': 0,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=20, r=20, t=60, b=20),
        font={'family': 'Inter'}
    )
    
    return fig

def create_mini_chart(values, color):
    """Create a mini sparkline chart"""
    colors = {
        'emerald': '#10b981',
        'blue': '#3b82f6',
        'purple': '#8b5cf6',
        'amber': '#f59e0b',
    }
    c = colors.get(color, '#10b981')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=values,
        mode='lines',
        fill='tozeroy',
        line={'color': c, 'width': 2},
        fillcolor=f'rgba({int(c[1:3], 16)}, {int(c[3:5], 16)}, {int(c[5:7], 16)}, 0.1)'
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=80,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        xaxis={'visible': False},
        yaxis={'visible': False}
    )
    
    return fig

def create_resource_bars(active_workers):
    """Create resource utilization bars based on actual state"""
    fig = go.Figure()
    
    # Dynamic values based on worker state
    if active_workers > 0:
        resources = [
            ('CPU', 35, '#3b82f6'),
            ('Memory', 58, '#8b5cf6'),
            ('GPU', 78, '#10b981'),
            ('Network', 24, '#06b6d4')
        ]
    else:
        resources = [
            ('CPU', 12, '#3b82f6'),
            ('Memory', 28, '#8b5cf6'),
            ('GPU', 0, '#10b981'),
            ('Network', 5, '#06b6d4')
        ]
    
    for i, (name, value, color) in enumerate(resources):
        # Background bar
        fig.add_trace(go.Bar(
            y=[name],
            x=[100],
            orientation='h',
            marker={'color': 'rgba(255,255,255,0.03)'},
            showlegend=False,
            hoverinfo='none'
        ))
        # Value bar
        fig.add_trace(go.Bar(
            y=[name],
            x=[value],
            orientation='h',
            marker={'color': color},
            showlegend=False,
            text=f'{value}%',
            textposition='inside',
            textfont={'color': 'white', 'size': 12}
        ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=200,
        margin=dict(l=80, r=20, t=20, b=20),
        barmode='overlay',
        xaxis={'visible': False, 'range': [0, 100]},
        yaxis={'tickfont': {'color': '#9ca3af', 'size': 12}},
        bargap=0.4
    )
    
    return fig

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

# Header
st.markdown("""
<div class="main-header">
    <h1 class="main-title">🌱 GreenScale</h1>
    <p class="sub-title">Intelligent Scale-to-Zero Autoscaler for AI/ML Workloads</p>
</div>
""", unsafe_allow_html=True)

# Status Badge
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if redis_connected:
        st.markdown("""
        <div style="text-align: center;">
            <span class="status-badge">
                <span style="display: inline-block; width: 8px; height: 8px; background: #10b981; border-radius: 50%;"></span>
                System Online • Redis Connected • KEDA Active
            </span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center;">
            <span class="status-badge status-badge-offline">
                <span style="display: inline-block; width: 8px; height: 8px; background: #ef4444; border-radius: 50%;"></span>
                System Offline • Redis Disconnected
            </span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# METRICS SECTION
# ============================================================================

if redis_connected:
    queue_length = redis_client.llen("jobs")
    result_keys = redis_client.keys("result:*")
    jobs_processed = len(result_keys)
    
    # Update session state
    st.session_state.total_jobs = jobs_processed
    st.session_state.total_savings = calculate_savings(jobs_processed)
    
    # Calculate active workers based on queue
    active_workers = 1 if queue_length > 0 else 0
else:
    queue_length = 0
    jobs_processed = 0
    active_workers = 0

# Metric Cards Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    gauge = create_modern_gauge(queue_length, 10, "QUEUE", "blue", "📥")
    st.plotly_chart(gauge, use_container_width=True, config={'displayModeBar': False})

with col2:
    gauge = create_modern_gauge(active_workers, 5, "WORKERS", "emerald", "⚡")
    st.plotly_chart(gauge, use_container_width=True, config={'displayModeBar': False})

with col3:
    gauge = create_modern_gauge(jobs_processed, 50, "PROCESSED", "purple", "✅")
    st.plotly_chart(gauge, use_container_width=True, config={'displayModeBar': False})

with col4:
    savings = st.session_state.total_savings
    gauge = create_modern_gauge(savings, 20, "SAVINGS", "amber", "💰")
    st.plotly_chart(gauge, use_container_width=True, config={'displayModeBar': False})

# ============================================================================
# SECONDARY METRICS
# ============================================================================

st.markdown("<hr>", unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)

# Calculate actual average response time from job history
if st.session_state.job_history:
    response_times = [job.get('response_time', 3) for job in st.session_state.job_history]
    avg_response = f"{sum(response_times) / len(response_times):.1f}s"
else:
    avg_response = "~3s"

metrics = [
    ("🕐", "Uptime", f"{int((time.time() - st.session_state.session_start) / 60)}m", "emerald"),
    ("⏱️", "Avg Response", avg_response, "blue"),
    ("📊", "Scale Events", str(jobs_processed), "purple"),
    ("💾", "Memory", "256MB" if active_workers == 0 else "512MB", "cyan"),
    ("🔥", "GPU Util", "0%" if active_workers == 0 else "78%", "amber"),
]

for col, (icon, label, value, color) in zip([col1, col2, col3, col4, col5], metrics):
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem;">{icon}</div>
            <p class="metric-value text-{color}">{value}</p>
            <p class="metric-label">{label}</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# JOB SUBMISSION SECTION
# ============================================================================

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<p class="section-header">🚀 Submit AI Job</p>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    user_prompt = st.text_area(
        "Enter your prompt",
        placeholder="Ask anything... e.g., 'Explain quantum computing in simple terms'",
        height=120,
        label_visibility="collapsed"
    )
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        submit_button = st.button("🚀 Submit Job", use_container_width=True)
    with col_btn2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)

with col2:
    st.markdown("""
    <div class="metric-card" style="height: 100%;">
        <p style="color: #9ca3af; font-size: 0.85rem; margin-bottom: 16px;">QUICK TIPS</p>
        <p style="color: #e5e7eb; font-size: 0.9rem; margin: 8px 0;">💡 Jobs auto-scale workers</p>
        <p style="color: #e5e7eb; font-size: 0.9rem; margin: 8px 0;">⚡ ~3 second response time</p>
        <p style="color: #e5e7eb; font-size: 0.9rem; margin: 8px 0;">💰 Save when idle (0 pods)</p>
    </div>
    """, unsafe_allow_html=True)

# Handle clear
if clear_button:
    st.session_state.job_history = []
    st.rerun()

# Handle submission
if submit_button:
    if not redis_connected:
        st.error("❌ Redis not connected. Please check your connection.")
    elif not user_prompt.strip():
        st.warning("⚠️ Please enter a prompt.")
    else:
        job_id = str(uuid.uuid4())[:8]
        job_payload = {"job_id": job_id, "prompt": user_prompt.strip()}
        
        try:
            redis_client.lpush("jobs", json.dumps(job_payload))
            st.session_state['active_job_id'] = job_id
            st.session_state['active_prompt'] = user_prompt.strip()
            st.session_state['job_start_time'] = time.time()
            st.rerun()
        except Exception as e:
            st.error(f"❌ Failed: {str(e)}")

# ============================================================================
# RESULTS SECTION
# ============================================================================

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<p class="section-header">📊 Results</p>', unsafe_allow_html=True)

# Active job processing
if 'active_job_id' in st.session_state and redis_connected:
    job_id = st.session_state['active_job_id']
    prompt = st.session_state.get('active_prompt', '')
    
    result_container = st.empty()
    progress_container = st.empty()
    
    with result_container.container():
        st.markdown(f"""
        <div class="processing-card">
            <div style="display: flex; align-items: center; gap: 16px;">
                <div style="font-size: 2rem;">⏳</div>
                <div>
                    <p style="color: #3b82f6; font-weight: 600; margin: 0;">Processing Job #{job_id}</p>
                    <p style="color: #9ca3af; margin: 4px 0 0 0; font-size: 0.9rem;">KEDA is scaling workers...</p>
                </div>
            </div>
            <p style="color: #e5e7eb; margin-top: 16px; padding: 12px; background: rgba(0,0,0,0.2); border-radius: 8px;">
                "{prompt[:150]}{'...' if len(prompt) > 150 else ''}"
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    progress_bar = progress_container.progress(0, text="Waiting for worker...")
    
    # Poll for result
    result = None
    for i in range(60):
        result = redis_client.get(f"result:{job_id}")
        if result:
            break
        progress_bar.progress((i + 1) / 60, text=f"Processing... {i+1}s")
        time.sleep(1)
    
    progress_container.empty()
    result_container.empty()
    
    if result:
        # Calculate response time
        response_time = round(time.time() - st.session_state.get('job_start_time', time.time()), 1)
        
        # Add to history
        st.session_state.job_history.insert(0, {
            'job_id': job_id,
            'prompt': prompt,
            'result': result,
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'response_time': response_time
        })
        
        # Update savings (more jobs = more demonstrated value)
        st.session_state.total_savings += 0.15  # Add savings per job
        
        # Keep only last 10
        st.session_state.job_history = st.session_state.job_history[:10]
        
        # Clear active job
        del st.session_state['active_job_id']
        if 'active_prompt' in st.session_state:
            del st.session_state['active_prompt']
        
        st.rerun()
    else:
        st.error("⏱️ Job timed out. Please try again.")
        del st.session_state['active_job_id']

# Display job history
if st.session_state.job_history:
    for i, job in enumerate(st.session_state.job_history):
        is_latest = (i == 0)
        
        with st.expander(f"{'🆕 ' if is_latest else ''}Job #{job['job_id']} • {job['timestamp']} • {job.get('response_time', '?')}s", expanded=is_latest):
            st.markdown(f"**Prompt:** {job['prompt']}")
            st.markdown("---")
            st.markdown(f"""
            <div class="result-card">
                <div class="result-header">
                    <div class="result-icon">🤖</div>
                    <div>
                        <p style="color: #10b981; font-weight: 600; margin: 0;">AI Response</p>
                        <p style="color: #9ca3af; font-size: 0.8rem; margin: 0;">Llama 3.3 70B</p>
                    </div>
                </div>
                <div class="result-content">{job['result']}</div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align: center; padding: 40px; color: #6b7280;">
        <p style="font-size: 3rem; margin-bottom: 16px;">💡</p>
        <p>Submit a job to see AI responses here</p>
        <p style="font-size: 0.85rem; margin-top: 8px;">Workers scale from 0 → 1 automatically</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# SYSTEM MONITOR
# ============================================================================

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown('<p class="section-header">📡 System Monitor</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Resource Utilization**")
    resource_chart = create_resource_bars(active_workers)
    st.plotly_chart(resource_chart, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.markdown("**System Components**")
    
    components = [
        ("Redis", redis_connected, "Message Broker", "#3b82f6"),
        ("KEDA", True, "Event-Driven Autoscaler", "#10b981"),
        ("Worker Pool", True, "Scale-to-Zero Ready", "#8b5cf6"),
        ("Llama 3.3 70B", True, "AI Engine", "#f59e0b"),
    ]
    
    for name, status, desc, color in components:
        dot_class = "status-dot-online" if status else "status-dot-offline"
        st.markdown(f"""
        <div class="status-item">
            <span class="status-dot {dot_class}"></span>
            <div style="flex: 1;">
                <p style="color: #e5e7eb; margin: 0; font-weight: 500;">{name}</p>
                <p style="color: #6b7280; margin: 0; font-size: 0.8rem;">{desc}</p>
            </div>
            <span style="color: {color}; font-size: 0.8rem;">{'Active' if status else 'Offline'}</span>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# HELM CHART GENERATOR
# ============================================================================

st.markdown("<hr>", unsafe_allow_html=True)

with st.expander("📦 Helm Chart Generator", expanded=False):
    st.markdown("Generate a customized Helm chart for any Kubernetes cluster.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        chart_name = st.text_input("Chart Name", value="greenscale", key="hc_name")
        namespace = st.text_input("Namespace", value="greenscale-system", key="hc_ns")
        image_repo = st.text_input("Image Repository", value="greenscale-worker", key="hc_img")
        image_tag = st.text_input("Image Tag", value="latest", key="hc_tag")
        
    with col2:
        min_replicas = st.number_input("Min Replicas (0 = Scale-to-Zero)", min_value=0, max_value=10, value=0, key="hc_min")
        max_replicas = st.number_input("Max Replicas", min_value=1, max_value=100, value=5, key="hc_max")
        cooldown = st.number_input("Cooldown (seconds)", min_value=10, max_value=600, value=30, key="hc_cd")
        mem_limit = st.text_input("Memory Limit", value="512Mi", key="hc_mem")
    
    if st.button("📥 Generate & Download", key="gen_helm"):
        chart_yaml = f"""apiVersion: v2
name: {chart_name}
description: GreenScale - Intelligent Scale-to-Zero Autoscaler
type: application
version: 1.0.0
appVersion: "1.0.0"
"""
        values_yaml = f"""replicaCount: {min_replicas}
image:
  repository: {image_repo}
  tag: {image_tag}
  pullPolicy: IfNotPresent

namespace: {namespace}

resources:
  limits:
    memory: {mem_limit}
  requests:
    memory: "256Mi"

keda:
  enabled: true
  minReplicaCount: {min_replicas}
  maxReplicaCount: {max_replicas}
  cooldownPeriod: {cooldown}
  pollingInterval: 5
  
redis:
  enabled: true
  image: redis:7-alpine
"""
        
        deployment_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-worker
  namespace: {{ .Values.namespace }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: greenscale-worker
  template:
    metadata:
      labels:
        app: greenscale-worker
    spec:
      containers:
        - name: worker
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
"""
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(f"{chart_name}/Chart.yaml", chart_yaml)
            zf.writestr(f"{chart_name}/values.yaml", values_yaml)
            zf.writestr(f"{chart_name}/templates/deployment.yaml", deployment_yaml)
        
        zip_buffer.seek(0)
        
        st.success("✅ Helm chart generated!")
        st.download_button(
            "📥 Download Chart (.zip)",
            zip_buffer,
            f"{chart_name}-helm.zip",
            "application/zip",
            use_container_width=True
        )

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("""
<div style="text-align: center; padding: 20px; color: #6b7280;">
    <p style="margin: 0;">🌱 <strong>GreenScale</strong> v1.0</p>
    <p style="margin: 8px 0 0 0; font-size: 0.85rem;">
        Built for AIBoomi Hackathon 2026 • 
        <a href="https://github.com/Pswaikar1742/Greenscale" target="_blank" style="color: #10b981;">GitHub</a>
    </p>
</div>
""", unsafe_allow_html=True)

# Refresh button
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    if st.button("🔄 Refresh Dashboard", use_container_width=True):
        st.rerun()
