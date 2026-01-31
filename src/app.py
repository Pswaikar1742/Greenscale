import os
import redis
import json
from dotenv import load_dotenv
import streamlit as st
import uuid
import time

# Load environment variables from .env file
load_dotenv()

# Load Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Streamlit app configuration
st.set_page_config(page_title="🟢 GreenScale Dashboard", layout="wide", initial_sidebar_state="expanded")

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

# Display real-time key metrics
try:
    # Fetch metrics from Redis
    queue_length = redis_client.llen("jobs")
    active_workers = 1 if queue_length > 0 else 0  # Placeholder logic for active workers
    estimated_savings = "$4.25/hr"  # Placeholder value for estimated savings

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
except Exception as e:
    st.error(f"An error occurred while fetching metrics: {str(e)}")

# Section for job submission
st.subheader("📝 Submit a New Job")

# Text input for the user's prompt
user_prompt = st.text_area(
    label="Enter your prompt:",
    placeholder="Ask me anything! E.g., 'What is the capital of France?'",
    height=100
)

# Submit button
if st.button("✅ Submit Job to Queue", use_container_width=True):
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

            # Store the job ID in session state for tracking
            st.session_state['active_job_id'] = job_id

            # Show success message
            st.success(f"✨ Job submitted successfully! Job ID: `{job_id}`")

            # Refresh the dashboard
            st.rerun()
        except Exception as e:
            st.error(f"Failed to submit job: {str(e)}")

# Real-time polling for job results
if 'active_job_id' in st.session_state:
    job_id = st.session_state['active_job_id']
    with st.spinner("KEDA is waking up the AI worker... Please wait."):
        result = None
        for _ in range(60):  # Poll for up to 60 seconds
            try:
                result_key = f"result:{job_id}"
                result = redis_client.get(result_key)
                if result:
                    # Display the result
                    st.info(f"🎉 Job completed! Result: {result}")

                    # Clear the active job ID from session state
                    del st.session_state['active_job_id']

                    # Refresh the dashboard
                    st.rerun()
                time.sleep(1)  # Wait for 1 second before polling again
            except Exception as e:
                st.error(f"An error occurred while polling for results: {str(e)}")
                break
        else:
            # Timeout occurred
            st.error("⏳ Job timed out. Please try again later.")
            del st.session_state['active_job_id']
