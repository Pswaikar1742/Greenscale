"""
GreenScale Worker
As per INSTRUCTIONS.md, this script runs inside a Docker container deployed via Kubernetes.
It connects to Redis, watches the 'jobs' list, and processes each job using the OpenAI API.
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
# As per INSTRUCTIONS.md, secrets are managed via .env (NEYSA_API_URL, NEYSA_API_KEY, REDIS_HOST, REDIS_PORT)
load_dotenv()

# Load configuration from environment variables
NEYSA_API_URL = os.getenv("NEYSA_API_URL")
NEYSA_API_KEY = os.getenv("NEYSA_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")  # Default to Kubernetes Redis service name
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Validate required secrets
if not NEYSA_API_URL:
    raise ValueError("NEYSA_API_URL not found in environment variables. Please set it in .env or as an environment variable.")
if not NEYSA_API_KEY:
    raise ValueError("NEYSA_API_KEY not found in environment variables. Please set it in .env or as an environment variable.")

# Initialize Redis client
# As per INSTRUCTIONS.md, worker pulls jobs from the 'jobs' list in Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

print(f"[Worker] Initialized successfully.")
print(f"[Worker] Redis: {REDIS_HOST}:{REDIS_PORT}")
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
                
                try:
                    # Parse the task from JSON string into a Python dictionary
                    job_data = json.loads(job_content)
                    job_id = job_data.get("job_id")
                    prompt = job_data.get("prompt")
                    
                    if not job_id or not prompt:
                        print(f"[Worker] Invalid job format. Missing 'job_id' or 'prompt'.")
                        continue
                    
                    print(f"[Worker] Processing job_id: {job_id}, Prompt: {prompt}")
                    
                    # Call Neysa Llama 3.3 endpoint via HTTP
                    try:
                        # Prepare headers with Bearer token authentication
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {NEYSA_API_KEY}"
                        }
                        
                        # Prepare payload for Neysa Llama 3.3 endpoint
                        payload = {
                            "model": "meta-llama/Llama-3.3-70B-Instruct",
                            "messages": [
                                {"role": "user", "content": prompt}
                            ],
                            "max_tokens": 200
                        }
                        
                        # Send POST request to Neysa API
                        response = requests.post(NEYSA_API_URL, json=payload, headers=headers)
                        response.raise_for_status()  # Raise exception for HTTP errors
                        
                        # Extract the answer from the response
                        answer = response.json()['choices'][0]['message']['content']
                        print(f"[Worker] Neysa Response: {answer}")
                        
                        # Save the result to Redis with job_id as key
                        result_key = f"result:{job_id}"
                        redis_client.set(result_key, answer, ex=300)
                        print(f"[Worker] Result saved to Redis key: {result_key}")
                        
                    except requests.exceptions.HTTPError as e:
                        print(f"[Worker] HTTP error calling Neysa API: {str(e)}")
                        if response.text:
                            print(f"[Worker] Response body: {response.text}")
                    except Exception as e:
                        print(f"[Worker] Error calling Neysa API: {str(e)}")
                
                except json.JSONDecodeError as e:
                    print(f"[Worker] Failed to parse job as JSON: {str(e)}")
        
        except redis.ConnectionError as e:
            print(f"[Worker] Redis connection error: {str(e)}")
            print("[Worker] Attempting to reconnect in 5 seconds...")
            time.sleep(5)
        
        except Exception as e:
            print(f"[Worker] Unexpected error: {str(e)}")
            time.sleep(1)


if __name__ == "__main__":
    main()
