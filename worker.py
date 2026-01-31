"""
GreenScale Worker
As per INSTRUCTIONS.md, this script runs inside a Docker container deployed via Kubernetes.
It connects to Redis, watches the 'jobs' list, and processes each job using the OpenAI API.
When KEDA scales the Deployment to replicas: 1, this worker wakes up and begins processing.
"""

import os
import time
import redis
from openai import OpenAI
from dotenv import load_dotenv

# Task 1: Load environment variables from .env file
# As per INSTRUCTIONS.md, secrets are managed via .env (OPENAI_API_KEY, REDIS_HOST, REDIS_PORT)
load_dotenv()

# Load configuration from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST", "redis-service")  # Default to Kubernetes Redis service name
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Validate required secrets
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in .env or as an environment variable.")

# Initialize Redis client
# As per INSTRUCTIONS.md, worker pulls jobs from the 'jobs' list in Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

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
                
                # Call OpenAI Chat Completions API
                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": job_content}
                        ],
                        temperature=0.7,
                    )
                    
                    # Extract and print the response
                    assistant_message = response.choices[0].message.content
                    print(f"[Worker] OpenAI Response: {assistant_message}")
                    
                except Exception as e:
                    print(f"[Worker] Error calling OpenAI API: {str(e)}")
        
        except redis.ConnectionError as e:
            print(f"[Worker] Redis connection error: {str(e)}")
            print("[Worker] Attempting to reconnect in 5 seconds...")
            time.sleep(5)
        
        except Exception as e:
            print(f"[Worker] Unexpected error: {str(e)}")
            time.sleep(1)


if __name__ == "__main__":
    main()
