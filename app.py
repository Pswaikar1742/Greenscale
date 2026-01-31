"""
GreenScale Frontend
As per INSTRUCTIONS.md, this Streamlit dashboard allows users to submit text prompts.
The app does NOT call the AI directly. It pushes prompts into the Redis 'jobs' list.
KEDA monitors the queue length and scales the worker deployment accordingly.
"""

import os
import streamlit as st
import redis
from dotenv import load_dotenv

# Task 1: Load environment variables from .env file
# As per INSTRUCTIONS.md, secrets are managed via .env (REDIS_HOST, REDIS_PORT)
load_dotenv()

# Load configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")  # Default to localhost for local development
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis client
# As per INSTRUCTIONS.md, app pushes jobs to the 'jobs' list in Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

print(f"[App] Initialized successfully.")
print(f"[App] Redis: {REDIS_HOST}:{REDIS_PORT}")


# Task 3: Set up the main Streamlit UI layout
# As per INSTRUCTIONS.md, UI allows users to submit prompts which are pushed to Redis 'jobs' list
st.set_page_config(page_title="GreenScale", layout="wide", initial_sidebar_state="expanded")

# Main title
st.title("🟢 GreenScale Dashboard")

# Subheader explaining the project
st.markdown("""
### Intelligent Autoscaler for AI/ML Workloads on Kubernetes
GreenScale enables **Scale-to-Zero** functionality to eliminate the cost of idle GPUs.
Submit prompts below, and our KEDA-powered autoscaler will automatically scale Kubernetes workers
to process your jobs efficiently, then scale back down when done.
""")

# Display current jobs queue length as a metric card
try:
    queue_length = redis_client.llen("jobs")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📊 Jobs in Queue", queue_length)
except Exception as e:
    st.error(f"Failed to fetch queue length: {str(e)}")


# Task 4: Create user input components
# As per INSTRUCTIONS.md, app receives prompt from user and pushes to Redis 'jobs' list
st.divider()
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
            # LPUSH the prompt to the 'jobs' list in Redis
            redis_client.lpush("jobs", user_prompt)
            st.success(f"✨ Job submitted successfully! Prompt: '{user_prompt}'")
            st.info("KEDA will automatically scale workers to process your job.")
            # Rerun the app to refresh metrics
            st.rerun()
        except Exception as e:
            st.error(f"Failed to submit job: {str(e)}")
