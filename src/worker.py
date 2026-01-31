"""
GreenScale Worker - Event-Driven AI Job Processor

This worker runs in a Kubernetes pod that scales from 0→N based on Redis queue length.
KEDA monitors the 'jobs' list in Redis and automatically scales this deployment.

Flow:
1. User submits prompt via Streamlit UI → pushed to Redis 'jobs' list
2. KEDA detects items in queue → scales worker deployment from 0 to 1+
3. Worker processes job using Neysa Llama 3.3 70B API
4. Result stored in Redis with key 'result:{job_id}'
5. Queue empty + 30s cooldown → KEDA scales back to 0 (Scale-to-Zero)
"""

import os
import sys
import time
import signal
import redis
import requests
import json
from dotenv import load_dotenv

# ============================================================================
# GRACEFUL SHUTDOWN HANDLING
# ============================================================================
# When KEDA scales down, Kubernetes sends SIGTERM. We handle this gracefully
# to avoid "Error" status on pod termination.

shutdown_requested = False


def handle_shutdown(signum, frame):
    """Handle SIGTERM from Kubernetes for graceful shutdown."""
    global shutdown_requested
    print("[Worker] Received shutdown signal (SIGTERM). Shutting down gracefully...")
    shutdown_requested = True


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# ============================================================================
# CONFIGURATION
# ============================================================================
load_dotenv()

NEYSA_API_URL = os.getenv("NEYSA_API_URL", "https://boomai-llama.neysa.io/v1/chat/completions")
NEYSA_API_KEY = os.getenv("NEYSA_API_KEY")  # Required - set via K8s Secret
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

if not NEYSA_API_KEY:
    print("[Worker] ERROR: NEYSA_API_KEY environment variable not set!")
    sys.exit(1)

# ============================================================================
# REDIS CONNECTION
# ============================================================================
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

print("[Worker] ====================================")
print("[Worker] GreenScale Worker Started")
print(f"[Worker] Redis: {REDIS_HOST}:{REDIS_PORT}")
print(f"[Worker] API: {NEYSA_API_URL}")
print("[Worker] Waiting for jobs...")
print("[Worker] ====================================")


# ============================================================================
# JOB PROCESSING
# ============================================================================
def process_job(job_id: str, prompt: str) -> str:
    """
    Process a single job by calling Neysa Llama 3.3 70B API.
    
    Args:
        job_id: Unique identifier for the job
        prompt: User's prompt to send to the AI
        
    Returns:
        AI response text or error message
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {NEYSA_API_KEY}"
    }
    
    payload = {
        "model": "meta-llama/Llama-3.3-70B-Instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 200
    }
    
    response = requests.post(NEYSA_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    return result["choices"][0]["message"]["content"]


# ============================================================================
# MAIN LOOP
# ============================================================================
def main():
    """
    Main worker loop - continuously processes jobs from Redis queue.
    Uses blocking pop (blpop) to efficiently wait for jobs without busy-looping.
    Handles graceful shutdown when KEDA scales down to 0 replicas.
    """
    global shutdown_requested
    
    while not shutdown_requested:
        try:
            # Blocking pop with 5s timeout - allows checking shutdown flag regularly
            result = redis_client.blpop("jobs", timeout=5)
            
            if result is None:
                continue  # Timeout, loop again to check shutdown flag
            
            # Parse job from Redis
            _, job_json = result
            job_data = json.loads(job_json)
            job_id = job_data.get("job_id")
            prompt = job_data.get("prompt")
            
            if not job_id or not prompt:
                print(f"[Worker] Invalid job format, skipping: {job_json}")
                continue
            
            print(f"[Worker] Processing job {job_id}: '{prompt[:50]}...'")
            
            try:
                # Call AI API
                response = process_job(job_id, prompt)
                print(f"[Worker] Job {job_id} completed successfully")
                
                # Store result in Redis (expires in 5 minutes)
                redis_client.set(f"result:{job_id}", response, ex=300)
                
            except requests.exceptions.RequestException as e:
                error_msg = f"API Error: {str(e)}"
                print(f"[Worker] Job {job_id} failed: {error_msg}")
                redis_client.set(f"result:{job_id}", error_msg, ex=300)
                
            except (KeyError, IndexError) as e:
                error_msg = f"Response parsing error: {str(e)}"
                print(f"[Worker] Job {job_id} failed: {error_msg}")
                redis_client.set(f"result:{job_id}", error_msg, ex=300)
                
        except json.JSONDecodeError as e:
            print(f"[Worker] Invalid JSON in job: {str(e)}")
            
        except redis.ConnectionError as e:
            print(f"[Worker] Redis connection lost: {str(e)}")
            print("[Worker] Reconnecting in 5 seconds...")
            time.sleep(5)
            
        except Exception as e:
            print(f"[Worker] Unexpected error: {str(e)}")
            time.sleep(1)
    
    # Clean exit
    print("[Worker] Graceful shutdown complete. Goodbye!")
    sys.exit(0)


if __name__ == "__main__":
    main()
