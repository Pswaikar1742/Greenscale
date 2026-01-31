import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import redis
import json
from dotenv import load_dotenv
import streamlit as st
import uuid
import time
import logging
from src.dashboard_elements import display_metric_card

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis client
try:
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    redis_client.ping()
    logging.info("Connected to Redis successfully.")
except redis.ConnectionError as e:
    logging.error("Failed to connect to Redis: %s", e)
    st.error("Failed to connect to Redis. Please check your connection settings.")
    st.stop()

# Streamlit app configuration
st.set_page_config(page_title="GreenScale", layout="wide", initial_sidebar_state="collapsed")

# Inject custom CSS for a dark-themed dashboard
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: #e0e0e0;
        font-family: 'Arial', sans-serif;
    }
    .stButton>button {
        background-color: #4caf50;
        color: white;
        border-radius: 8px;
        font-size: 16px;
        padding: 10px 20px;
        border: none;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.2);
    }
    .stButton>button:hover {
        background-color: #388e3c;
        color: #ffffff;
    }
    .stMetric {
        background-color: #1e1e1e;
        border-radius: 12px;
        padding: 15px;
        color: #a5d6a7;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.3);
    }
    .stTextInput>div>div>input {
        background-color: #2e2e2e;
        color: #e0e0e0;
        border: 1px solid #4caf50;
        border-radius: 5px;
        padding: 10px;
    }
    .stTextInput>div>div>input:focus {
        border-color: #81c784;
        outline: none;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Main title
st.title("🟢 GreenScale Dashboard")

# Subheader
st.subheader("Intelligent Autoscaler for AI/ML Workloads on Kubernetes")

# Introductory markdown text
st.markdown(
    """
    GreenScale enables **Scale-to-Zero** functionality to eliminate the cost of idle GPUs.
    Submit prompts below, and our KEDA-powered autoscaler will automatically scale Kubernetes workers
    to process your jobs efficiently, then scale back down when done.
    """
)

# Dynamic status indicator
current_status = "IDLE"  # Initialize the current status
current_savings = "$0.00/hr"  # Placeholder for current savings

# Update the main status banner dynamically
if 'active_job_id' in st.session_state:
    if 'result' in st.session_state:
        current_status = "COMPLETE: Results displayed, scaling down"
    else:
        current_status = "PROCESSING: AI inference in progress"
else:
    current_status = "IDLE: Ready for new tasks"

# Update the status container
status_container = st.container()
with status_container:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 🚦 Current Status: **{current_status}**")
    with col2:
        st.markdown(f"### 💰 Savings: **{current_savings}**")

# Fetch metrics from Redis before displaying them
try:
    queue_length = redis_client.llen("jobs")
    active_workers = 1 if queue_length > 0 else 0  # Placeholder logic for active workers
except redis.ConnectionError:
    st.error("Failed to connect to Redis. Please check your connection settings.")
    logging.error("Redis connection error while fetching metrics.")
    queue_length = 0
    active_workers = 0
except Exception as e:
    st.error(f"An error occurred while fetching metrics: {str(e)}")
    logging.error("Error fetching metrics: %s", e)
    queue_length = 0
    active_workers = 0

# Replace native Streamlit metrics with custom HTML-based metric cards
# Display metrics with custom metric cards
GPU_COST_PER_HR = 4.0  # Cost per hour for a GPU
AVG_JOB_PROCESS_TIME_SECONDS = 30  # Average job processing time in seconds

# Initialize session state variables if not present
if 'total_jobs_processed' not in st.session_state:
    st.session_state['total_jobs_processed'] = 0

if 'total_savings_usd' not in st.session_state:
    st.session_state['total_savings_usd'] = 0.0

# Update the metrics display with refined savings calculation
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        display_metric_card(
            label="Jobs in Queue",
            value=queue_length,
            delta=None,
            icon="📊"
        ),
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        display_metric_card(
            label="Active Workers",
            value=active_workers,
            delta=None,
            icon="⚡"
        ),
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        display_metric_card(
            label="Total Savings",
            value=f"${st.session_state['total_savings_usd']:.2f}",
            delta=None,
            icon="💰"
        ),
        unsafe_allow_html=True
    )

# Update savings dynamically when a job completes
if 'active_job_id' in st.session_state:
    job_id = st.session_state['active_job_id']
    with st.spinner("Processing Job..."):
        result = None
        for i in range(60):  # Poll for up to 60 seconds
            try:
                result_key = f"result:{job_id}"
                result = redis_client.get(result_key)
                if result:
                    # Display the result
                    st.success("🎉 Job complete! Here is the result:")
                    st.code(result, language="json")

                    # Increment total jobs processed
                    st.session_state['total_jobs_processed'] += 1

                    # Calculate cost saved per job
                    cost_saved_per_job = (GPU_COST_PER_HR / 3600) * AVG_JOB_PROCESS_TIME_SECONDS

                    # Update total savings
                    st.session_state['total_savings_usd'] += cost_saved_per_job

                    # Clear the active job ID from session state
                    del st.session_state['active_job_id']

                    # Refresh the dashboard to update metrics
                    st.experimental_rerun()

                time.sleep(1)  # Wait for 1 second before polling again
            except redis.ConnectionError:
                st.error("Failed to connect to Redis. Please check your connection settings.")
                logging.error("Redis connection error during result polling.")
                break
            except Exception as e:
                st.error(f"An error occurred while polling for results: {str(e)}")
                logging.error("Error during result polling: %s", e)
                break
        else:
            # Timeout occurred
            st.error("⏳ Job timed out. Please try again later.")
            del st.session_state['active_job_id']
            logging.warning("Job timed out after 60 seconds.")

# Section for job submission with improved visual feedback
st.subheader("📝 Submit a New Job")

# Use st.form for cleaner grouping of inputs and button
with st.form(key="job_submission_form"):
    user_prompt = st.text_area(
        label="Enter your prompt:",
        placeholder="Ask me anything! E.g., 'What is the capital of France?'",
        height=100
    )
    submit_button = st.form_submit_button(label="✅ Submit Job to Queue")

if submit_button:
    if not user_prompt.strip():
        st.warning("Please enter a prompt before submitting.")
    else:
        try:
            # Generate a unique Job ID
            job_id = str(uuid.uuid4())
            job_payload = {
                "job_id": job_id,
                "prompt": user_prompt.strip()
            }
            # Push the job to the Redis 'jobs' list
            redis_client.lpush("jobs", json.dumps(job_payload))

            # Set an expiry for the job result key
            redis_client.expire(f"result:{job_id}", 3600)  # Expire in 1 hour

            # Update the current status
            current_status = "QUEUED"

            # Store the job ID in session state for tracking
            st.session_state['active_job_id'] = job_id

            # Show success message
            st.success(f"✨ Job submitted successfully! Job ID: `{job_id}`. KEDA is responding...")

            # Refresh the dashboard
            st.rerun()
        except redis.ConnectionError:
            st.error("Failed to connect to Redis. Please check your connection settings.")
            logging.error("Redis connection error during job submission.")
        except Exception as e:
            st.error(f"Failed to submit job: {str(e)}")
            logging.error("Error during job submission: %s", e)