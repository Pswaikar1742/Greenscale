"""
GreenScale Worker
As per INSTRUCTIONS.md, this script runs inside a Docker container deployed via Kubernetes.
It connects to Redis, watches the 'jobs' list, and processes each job using the Neysa Llama API.
When KEDA scales the Deployment to replicas: 1, this worker wakes up and begins processing.
"""

import os
import time
import redis
import requests
import json  # Import json to parse the incoming job_content
from dotenv import load_dotenv

# Task 1: Load environment variables from .env file
load_dotenv()

# Load configuration from environment variables
NEYSA_API_URL = os.getenv("NEYSA_API_URL", "https://boomai-llama.neysa.io/v1/chat/completions")
NEYSA_API_KEY = os.getenv("NEYSA_API_KEY", "2d0c490f-c41a-ff22-eb7d-4445372c574d")
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")  # Default to Kubernetes Redis service name
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

print(f"[Worker] Initialized successfully.")
print(f"[Worker] Redis: {REDIS_HOST}:{REDIS_PORT}")
print(f"[Worker] Using Neysa Llama 3.3 endpoint: {NEYSA_API_URL}")
print(f"[Worker] Listening for jobs on 'jobs' list...")

# Task 4: Main processing loop
def main():
    """
    Main worker loop that continuously processes jobs from the Redis queue.
    Uses blocking pop (blpop) to avoid busy-looping and efficiently wait for tasks.
    """
    while True:
        job_id = None  # Initialize job_id outside try-block for error handling
        job_json_string = None  # Initialize for error handling
        try:
            # Use blpop with 5-second timeout for efficient blocking
            result = redis_client.blpop("jobs", timeout=5)
            
            if result is None:
                # Timeout occurred, no job received
                print("[Worker] Waiting for work...")
            else:
                # result is a tuple: (list_name, job_content)
                # job_content is a JSON string: {"job_id": "...", "prompt": "..."}
                _, job_json_string = result
                print(f"[Worker] Received raw task: {job_json_string}")
                
                # CRITICAL FIX: Parse the JSON string to get job_id and prompt
                job_data = json.loads(job_json_string)
                job_id = job_data.get("job_id")
                prompt = job_data.get("prompt")

                if not job_id or not prompt:
                    print(f"[Worker] ERROR: Invalid job format received. Skipping. Data: {job_json_string}")
                    continue  # Skip to next loop iteration
                
                print(f"[Worker] Processing Job ID: {job_id}, Prompt: '{prompt}'")

                # Call Neysa Llama 3.3 API
                try:
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {NEYSA_API_KEY}"
                    }
                    
                    payload = {
                        "model": "meta-llama/Llama-3.3-70B-Instruct",
                        "messages": [
                            {"role": "user", "content": prompt}  # CRITICAL FIX: Use the extracted 'prompt'
                        ],
                        "temperature": 0.7,
                        "max_tokens": 200  # Limit response size for performance
                    }
                    
                    response = requests.post(NEYSA_API_URL, headers=headers, json=payload, timeout=60)
                    response.raise_for_status()
                    
                    # Extract and print the response
                    result_json = response.json()
                    assistant_message = result_json["choices"][0]["message"]["content"]
                    print(f"[Worker] Llama Response for Job ID {job_id}: {assistant_message}")
                    
                    # Save the result back to Redis
                    redis_client.set(f"result:{job_id}", assistant_message, ex=300)  # Save with job_id for frontend
                    print(f"[Worker] Result saved for Job ID {job_id}.")

                except requests.exceptions.RequestException as e:
                    error_message = f"Error calling Neysa API: {str(e)}"
                    print(f"[Worker] {error_message}")
                    if job_id:  # Only save error if we have a job_id
                        redis_client.set(f"result:{job_id}", error_message, ex=300)
                except (KeyError, IndexError) as e:
                    error_message = f"Error parsing API response: {str(e)}. Response: {response.text if 'response' in locals() else 'No response'}"
                    print(f"[Worker] {error_message}")
                    if job_id:
                        redis_client.set(f"result:{job_id}", error_message, ex=300)
        
        except json.JSONDecodeError as e:
            print(f"[Worker] ERROR: Failed to parse Redis job content as JSON: {str(e)}. Raw content: {job_json_string}")
            # Do not save result for malformed jobs
        except redis.ConnectionError as e:
            print(f"[Worker] Redis connection error: {str(e)}")
            print("[Worker] Attempting to reconnect in 5 seconds...")
            time.sleep(5)
        
        except Exception as e:
            print(f"[Worker] Unexpected error: {str(e)}")
            time.sleep(1)


if __name__ == "__main__":
    main()
