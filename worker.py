"""
GreenScale Worker
As per INSTRUCTIONS.md, this script runs inside a Docker container deployed via Kubernetes.
It connects to Redis, watches the 'jobs' list, and processes each job using the Neysa Llama API.
When KEDA scales the Deployment to replicas: 1, this worker wakes up and begins processing.
"""

import os
import time
import json
import uuid
import redis
import requests
from dotenv import load_dotenv

# Task 1: Load environment variables from .env file
# As per INSTRUCTIONS.md, secrets are managed via .env
load_dotenv()

# Load configuration from environment variables
NEYSA_API_URL = os.getenv("NEYSA_API_URL", "https://boomai-llama.neysa.io/v1/chat/completions")
NEYSA_API_KEY = os.getenv("NEYSA_API_KEY", "2d0c490f-c41a-ff22-eb7d-4445372c574d")
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")  # Default to Kubernetes Redis service name
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis client
# As per INSTRUCTIONS.md, worker pulls jobs from the 'jobs' list in Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

print(f"[Worker] Initialized successfully.")
print(f"[Worker] Redis: {REDIS_HOST}:{REDIS_PORT}")
print(f"[Worker] Using Neysa Llama 3.3 endpoint: {NEYSA_API_URL}")
print(f"[Worker] Listening for jobs on 'jobs' list...")


# Task 4: Main processing loop
# As per INSTRUCTIONS.md, worker uses RPOP to pull jobs from Redis 'jobs' list.
# We use blpop (blocking left pop) with a 5-second timeout for efficient waiting.
def main():
    """
    Main worker loop that continuously processes jobs from the Redis queue.
    Uses blocking pop (blpop) to avoid busy-looping and efficiently wait for tasks.
    """
    while True:
        try:
            # Use blpop with 5-second timeout for efficient blocking
            result = redis_client.blpop("jobs", timeout=5)
            
            if result is None:
                # Timeout occurred, no job received
                print("[Worker] Waiting for work...")
            else:
                # result is a tuple: (list_name, job_content)
                _, job_content = result
                print(f"[Worker] Received task: {job_content}")
                
                # Call Neysa Llama 3.3 API
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {NEYSA_API_KEY}"
                    }
                    
                    payload = {
                        "model": "meta-llama/Llama-3.3-70B-Instruct",
                        "messages": [
                            {"role": "user", "content": job_content}
                        ],
                        "temperature": 0.7
                    }
                    
                    response = requests.post(NEYSA_API_URL, headers=headers, json=payload, timeout=60)
                    response.raise_for_status()
                    
                    # Extract and print the response
                    result_json = response.json()
                    assistant_message = result_json["choices"][0]["message"]["content"]
                    print(f"[Worker] Llama Response: {assistant_message}")
                    
                except requests.exceptions.RequestException as e:
                    print(f"[Worker] Error calling Neysa API: {str(e)}")
                except (KeyError, IndexError) as e:
                    print(f"[Worker] Error parsing API response: {str(e)}")
        
        except redis.ConnectionError as e:
            print(f"[Worker] Redis connection error: {str(e)}")
            print("[Worker] Attempting to reconnect in 5 seconds...")
            time.sleep(5)
        
        except Exception as e:
            print(f"[Worker] Unexpected error: {str(e)}")
            time.sleep(1)


if __name__ == "__main__":
    main()
