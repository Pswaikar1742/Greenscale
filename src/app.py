import os
import redis
import json
from dotenv import load_dotenv
import streamlit as st
import uuid
import time
import logging

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
        background-color: #1e1e1e;
        color: #d4d4d4;
    }
    .stButton>button {
        background-color: #2e7d32;
        color: white;
        border-radius: 5px;
        font-size: 16px;
    }
    .stButton>button:hover {
        background-color: #1b5e20;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Update the theme toggle function to include background color changes for light and dark modes
def set_theme():
    if 'theme' not in st.session_state:
        st.session_state['theme'] = 'dark'  # Default theme is dark

    # Toggle theme
    if st.sidebar.button("🌙" if st.session_state['theme'] == 'light' else "☀️"):
        st.session_state['theme'] = 'light' if st.session_state['theme'] == 'dark' else 'dark'

    # Apply theme-specific styles, including background colors
    if st.session_state['theme'] == 'dark':
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
    else:
        st.markdown(
            """
            <style>
            body {
                background: linear-gradient(135deg, #ffffff, #e8f5e9, #c8e6c9);
                color: #333333;
                font-family: 'Arial', sans-serif;
            }
            .stButton>button {
                background-color: #81c784;
                color: white;
                border-radius: 8px;
                font-size: 16px;
                padding: 10px 20px;
                border: none;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }
            .stButton>button:hover {
                background-color: #66bb6a;
                color: #ffffff;
            }
            .stMetric {
                background-color: #ffffff;
                border-radius: 12px;
                padding: 15px;
                color: #388e3c;
                box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
            }
            .stTextInput>div>div>input {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #81c784;
                border-radius: 5px;
                padding: 10px;
            }
            .stTextInput>div>div>input:focus {
                border-color: #4caf50;
                outline: none;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

# Call the theme toggle function
set_theme()

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

# Redesign metrics display as an instrument gauge cluster
GPU_COST_PER_HR = 4.0  # Cost per hour for a GPU
queue_length = 0  # Placeholder for queue length
active_workers = 0  # Placeholder for active workers

# Calculate cost savings dynamically
total_time_saved_hours = 0  # Placeholder for total time saved
current_savings_value = total_time_saved_hours * GPU_COST_PER_HR

# Create a visually appealing layout with 3 columns
col1, col2, col3 = st.columns(3)

# Display metrics with tooltips
with col1:
    st.metric(
        label="📊 Jobs in Queue",
        value=queue_length,
        help="Number of jobs currently waiting in the queue to be processed."
    )

with col2:
    st.metric(
        label="⚡ Active Workers",
        value=active_workers,
        help="Number of workers currently processing jobs."
    )

with col3:
    st.metric(
        label="💰 Est. Savings",
        value=f"${current_savings_value:.2f}/hr",
        delta=f"+${(current_savings_value / 100):.2f}",
        help="Estimated cost savings per hour based on GPU usage reduction."
    )

# Display real-time key metrics
try:
    # Fetch metrics from Redis
    queue_length = redis_client.llen("jobs")
    active_workers = 1 if queue_length > 0 else 0  # Placeholder logic for active workers
    estimated_savings = f"${queue_length * GPU_COST_PER_HR:.2f}/hr"  # Dynamic savings calculation

    # Create a 3-column layout
    col1, col2, col3 = st.columns(3)

    # Display metrics in columns
    with col1:
        st.metric("📊 Jobs in Queue", queue_length)
    with col2:
        st.metric("⚡ Active Workers", active_workers)
    with col3:
        st.metric("💰 Estimated Savings", estimated_savings, "+$0.25")

except redis.ConnectionError:
    st.error("Failed to connect to Redis. Please check your connection settings.")
    logging.error("Redis connection error while fetching metrics.")
except Exception as e:
    st.error(f"An error occurred while fetching metrics: {str(e)}")
    logging.error("Error fetching metrics: %s", e)

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

# Real-time polling for job results with detailed status updates
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

                    # Clear the active job ID from session state
                    del st.session_state['active_job_id']

                    # Refresh the dashboard
                    st.rerun()
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