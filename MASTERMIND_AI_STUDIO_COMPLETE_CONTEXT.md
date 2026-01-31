# 🌱 GreenScale - Complete Project Context for AI Studio Analysis

**Project Date:** January 31, 2026  
**Team:** P (Prathmesh - Platform Engineer) & A (Ali - Application Engineer)  
**Status:** ✅ **PROJECT COMPLETE - v1.0 RELEASED**  
**Repository:** https://github.com/Pswaikar1742/Greenscale

---

## 🎉 PROJECT STATUS: COMPLETE & TESTED

### ✅ End-to-End Testing Results (Jan 31, 2026):
```
Test: LPUSH jobs '{"job_id": "test-001", "prompt": "What is 2+2?"}'
Result: GET result:test-001 → "2 + 2 = 4"
Status: ✅ PASSED
```

---

## 📋 EXECUTIVE SUMMARY

### What is GreenScale?
An intelligent **Scale-to-Zero autoscaler** for AI/ML workloads on Kubernetes. It eliminates the cost of idle GPUs by automatically scaling worker pods from 0 to N based on job queue length, then scaling back to 0 when idle.

### Tech Stack
- **Orchestrator:** Kubernetes (Minikube)
- **Autoscaler:** KEDA (Kubernetes Event-Driven Autoscaling)
- **Message Broker:** Redis
- **Language:** Python 3.9+
- **AI Engine:** Neysa Llama 3.3 70B Instruct API
- **Frontend:** Streamlit
- **Containerization:** Docker

### Architecture Flow
```
Streamlit UI (app.py)
    ↓
Redis Queue (jobs list)
    ↓
KEDA Scaler (watches Redis)
    ↓
Worker Pods (0→5 replicas)
    ↓
Neysa Llama API
    ↓
Results back to UI
```

---

## ✅ COMPLETED WORK (All Phases)

### Phase 1: Infrastructure Setup ✅
- ✅ Kubernetes namespace created: `greenscale-system`
- ✅ Redis deployed with service (`redis-service:6379`)
- ✅ KEDA installed and configured
- ✅ All K8s manifests created and deployed

### Phase 2: Neysa Integration ✅
- ✅ Switched from OpenAI API to Neysa Llama API
- ✅ Created Kubernetes secrets for API credentials
- ✅ Added host aliases for DNS resolution
- ✅ Updated worker deployment with proper environment variables

### Phase 3: Rebuild & Verification ✅
- ✅ Docker image rebuilt and optimized (165MB)
- ✅ Image loaded into Minikube
- ✅ KEDA ScaledObject deployed and active
- ✅ HPA created by KEDA (0-5 replicas range)
- ✅ All commits pushed to GitHub

### Phase 4: Frontend & Testing ✅
- ✅ Streamlit dashboard completed by Ali
- ✅ Fixed deprecated `st.experimental_rerun()` → `st.rerun()`
- ✅ Worker deployment updated to use `:latest` tag
- ✅ End-to-end testing PASSED
- ✅ All code pushed to `main` branch

---

## 🟢 FINAL STATUS - ALL SYSTEMS OPERATIONAL

### Infrastructure (P - Prathmesh) ✅
- ✅ Redis: 1/1 Running
- ✅ Worker Deployment: 0/0 (Scale-to-Zero ready)
- ✅ KEDA ScaledObject: Active, monitoring Redis
- ✅ HPA: Configured 0-5 replicas
- ✅ Docker Image: `greenscale-worker:latest` loaded in Minikube
- ✅ Secrets: `neysa-secret` configured

### Frontend (A - Ali) ✅
- ✅ Streamlit UI: Complete with real-time metrics
- ✅ Job Submission: UUID tracking implemented
- ✅ Results Polling: 60-second timeout with spinner
- ✅ Error Handling: Comprehensive exception handling

### Testing Results ✅
- ✅ Manual Redis test: PASSED (`"2 + 2 = 4"`)
- ✅ Streamlit UI test: PASSED (`"The capital of China is Beijing"`)
- ✅ KEDA scaling: Workers scale 0→1→0 correctly
- ✅ Cooldown period: 30 seconds working as expected

---

## 📁 COMPLETE CODE SNAPSHOT

Using the **Mastermind Data Upload Protocol**:

---

### --- START OF FILE k8s/namespace.yaml ---

```yaml
# GreenScale Namespace
# Owner: P (Platform Engineer)
# As per INSTRUCTIONS.md: Kubernetes Namespace is 'greenscale-system'

apiVersion: v1
kind: Namespace
metadata:
  name: greenscale-system
  labels:
    app: greenscale
    environment: development
```

### --- END OF FILE ---

---

### --- START OF FILE k8s/redis.yaml ---

```yaml
# Redis Deployment and Service for GreenScale
# Owner: P (Platform Engineer)
# Create a Kubernetes Deployment and a ClusterIP Service for Redis.
# Namespace: greenscale-system
# Service Name: redis-service
# Port: 6379

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: greenscale-system
  labels:
    app: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          resources:
            requests:
              memory: "64Mi"
              cpu: "50m"
            limits:
              memory: "128Mi"
              cpu: "100m"
          readinessProbe:
            tcpSocket:
              port: 6379
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            tcpSocket:
              port: 6379
            initialDelaySeconds: 15
            periodSeconds: 20

---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: greenscale-system
  labels:
    app: redis
spec:
  selector:
    app: redis
  ports:
    - protocol: TCP
      port: 6379
      targetPort: 6379
  type: ClusterIP
```

### --- END OF FILE ---

---

### --- START OF FILE k8s/worker-deployment.yaml ---

```yaml
# GreenScale Worker Deployment
# Owner: P (Platform Engineer)
# Updated for Neysa Llama API with hostAliases for DNS resolution

apiVersion: apps/v1
kind: Deployment
metadata:
  name: greenscale-worker
  namespace: greenscale-system
  labels:
    app: greenscale-worker
spec:
  # CRITICAL: Start at 0 replicas for Scale-to-Zero
  replicas: 0
  selector:
    matchLabels:
      app: greenscale-worker
  template:
    metadata:
      labels:
        app: greenscale-worker
    spec:
      # Host alias for DNS resolution to Neysa endpoint
      hostAliases:
        - ip: "103.42.50.49"
          hostnames:
            - "boomai-llama.neysa.io"
      
      containers:
        - name: worker
          # Use local image (loaded via: minikube image load greenscale-worker:latest)
          image: greenscale-worker:latest
          imagePullPolicy: Never
          env:
            - name: NEYSA_API_KEY
              valueFrom:
                secretKeyRef:
                  name: neysa-secret
                  key: NEYSA_API_KEY
            - name: NEYSA_API_URL
              valueFrom:
                secretKeyRef:
                  name: neysa-secret
                  key: NEYSA_API_URL
            - name: REDIS_HOST
              value: "redis-service"
            - name: REDIS_PORT
              value: "6379"
            - name: REDIS_LIST_NAME
              value: "jobs"
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
      restartPolicy: Always
```

### --- END OF FILE ---

---

### --- START OF FILE k8s/keda-scaledobject.yaml ---

```yaml
# KEDA ScaledObject for GreenScale Worker
# Owner: P (Platform Engineer)
# Create a KEDA ScaledObject.
# It should scale the 'greenscale-worker' deployment.
# Trigger type is redis.
# The redis address is 'redis-service:6379' from the 'greenscale-system' namespace.
# The list to monitor is 'jobs'.
# Set cooldownPeriod to 30 seconds.
# Minimum replicas: 0. Maximum replicas: 5.

apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: greenscale-worker-scaler
  namespace: greenscale-system
spec:
  scaleTargetRef:
    name: greenscale-worker
  
  # Scale-to-Zero: Minimum replicas is 0
  minReplicaCount: 0
  # Maximum replicas: 5
  maxReplicaCount: 5
  
  # Wait 30 seconds of inactivity before scaling down
  cooldownPeriod: 30
  
  # How often to check the queue (seconds)
  pollingInterval: 5

  triggers:
    - type: redis
      metadata:
        # Redis address from greenscale-system namespace
        address: redis-service.greenscale-system.svc.cluster.local:6379
        # The list to monitor is 'jobs'
        listName: jobs
        # Scale when list length > 0
        listLength: "1"
        enableTLS: "false"
```

### --- END OF FILE ---

---

### --- START OF FILE Dockerfile ---

```dockerfile
# GreenScale Worker Dockerfile
# Owner: P (Platform Engineer)
# Use python:3.9-slim as the base.
# Copy requirements.txt and worker.py.
# Install requirements.
# Set the CMD to run worker.py.

FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker.py into the container
COPY worker.py .

# The final command
CMD ["python", "worker.py"]
```

### --- END OF FILE ---

---

### --- START OF FILE worker.py ---

```python
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
```

### --- END OF FILE ---

---

### --- START OF FILE requirements.txt ---

```
# GreenScale Application Layer Dependencies
# Deployed across both frontend (app.py) and backend (worker.py)

# UI Framework - Streamlit dashboard for user interaction
streamlit>=1.28.0

# Queue Connector - Redis client for job queue management
redis>=4.5.0

# AI SDK - OpenAI API for LLM inference
openai>=1.0.0

# Secrets Manager - Load environment variables from .env
python-dotenv>=1.0.0

# Data Validation & Settings Management
pydantic

# HTTP Client - General purpose requests library
requests
```

### --- END OF FILE ---

---

### --- START OF FILE .env.example ---

```
# GreenScale Environment Variables
# Copy this file to .env and fill in your values

# Redis Configuration
# REDIS_HOST=localhost
# REDIS_PORT=6379

# Neysa Llama API Configuration
NEYSA_API_URL="https://boomai-llama.neysa.io/v1/chat/completions"
NEYSA_API_KEY="2d0c490f-c41a-ff22-eb7d-4445372c574d"
```

### --- END OF FILE ---

---

### --- START OF FILE src/worker.py (STUB - needs completion by A) ---

```python
# GreenScale Worker - Job Processor
# Owner: A (Ali) - Application Engineer
# As per INSTRUCTIONS.md: Worker that pulls jobs from Redis and calls Neysa API

# TODO (A): Implement the worker
# - Connect to Redis
# - Use RPOP to pull jobs from 'jobs' list
# - Call Neysa API to process
# - Store results back in Redis
# - Loop until queue is empty

pass
```

### --- END OF FILE ---

---

### --- START OF FILE src/app.py (STUB - BLOCKING ITEM) ---

```python
# GreenScale Frontend - Streamlit UI
# Owner: A (Ali) - Application Engineer
# As per INSTRUCTIONS.md: Streamlit dashboard that pushes prompts to Redis 'jobs' list

# TODO (A): Implement the Streamlit UI
# - Create input field for prompts
# - Connect to Redis and push jobs
# - Display queue status
# - Show processed results

pass
```

### --- END OF FILE ---

---

## 🔍 DEPLOYMENT VERIFICATION

### Current Kubernetes Status (as of Jan 31, 2026):

```bash
NAME                         READY   STATUS    RESTARTS   AGE
pod/redis-868c544d54-8x6r4   1/1     Running   0          139m

NAME                    TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)    AGE
service/redis-service   ClusterIP   10.102.239.109   <none>        6379/TCP   139m

deployment.apps/greenscale-worker   0/0     0            0           27m
deployment.apps/redis               1/1     1            1           139m

HPA STATUS:
keda-hpa-greenscale-worker-scaler   Deployment/greenscale-worker   0 replicas   (waiting for jobs)
```

✅ **All infrastructure components are running and ready**

---

## 📊 GIT COMMIT HISTORY

```
154c75c (HEAD -> infra-backend, origin/infra-backend) 
  feat(infra): Phase 2 & 3 updates - Neysa integration

3bc2ab5 
  refactor(worker): switch from OpenAI to Neysa Llama API via direct HTTP requests

b1a368b 
  Merge main into infra-backend: resolve requirements.txt conflict

3b100b1 (origin/main, origin/HEAD) 
  Merge pull request #1 from Pswaikar1742/triggs

e960345 (origin/triggs) 
  feat(app): build initial UI and worker logic
```

---

## 🎯 WHAT HAPPENS NEXT

### For Google AI Studio Analysis:

1. **Verify All Files**: Check that all YAML manifests are valid
2. **Docker Image**: Confirm Dockerfile is optimized
3. **Worker Logic**: Validate worker.py handles all edge cases
4. **Deployment**: Ensure all env vars and secrets are properly set

### What We Need From You (AI Studio):

1. Are there any errors in the K8s manifests?
2. Is the worker code robust against API failures?
3. Are there any security issues in the configuration?
4. What improvements would you recommend?
5. Is everything ready for production-scale testing?

### What We're Waiting For:

- **Ali (A)**: Complete `src/app.py` with Streamlit UI
  - Must connect to Redis
  - Must push jobs to 'jobs' list
  - Must display results
  - Must show queue status

---

## 🚀 DEPLOYMENT COMMANDS (Already Executed)

```bash
# 1. Kubernetes resources deployed
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/keda-scaledobject.yaml

# 2. Secrets created in cluster
kubectl create secret generic neysa-secret \
  --from-literal=NEYSA_API_KEY=2d0c490f-c41a-ff22-eb7d-4445372c574d \
  --from-literal=NEYSA_API_URL=https://boomai-llama.neysa.io/v1/chat/completions \
  -n greenscale-system

# 3. Docker image built and loaded
docker build -t greenscale-worker:latest .
minikube image load greenscale-worker:latest

# 4. All deployed and verified
kubectl get all -n greenscale-system
kubectl get hpa -n greenscale-system
```

---

## 📞 KEY CONTACTS

- **P (Prathmesh)**: Platform Engineer - Infrastructure, Kubernetes, Docker
- **A (Ali)**: Application Engineer - Python, Redis, Streamlit UI
- **Repository**: https://github.com/Pswaikar1742/Greenscale

---



## 🔄 PROGRESS UPDATE (31 January 2026 - CURRENT SESSION)

### Actions Completed by P (Prathmesh - Platform Engineer):

#### 1. **Code Integration** ✅
   - Pulled latest changes from `main` branch
   - Merged into `infra-backend` branch without conflicts
   - Commit: `24a0978` - "Merge main into infra-backend: resolved conflicts"

#### 2. **Merge Conflict Resolution** ✅
   - **File**: `src/worker.py`
   - **Conflict Points**:
     - Import statements: Added `uuid` import from main
     - Job parsing logic: Kept enhanced parsing with JSON decoding
     - Error handling: Maintained job_id tracking and result saving
     - API payload: Kept improved prompt extraction
   - **Resolution Strategy**: Kept infra-backend improvements + merged main's additions
   - **Result**: File now has best of both branches

#### 3. **Docker Build & Verification** ✅
   - Command: `docker build -t greenscale-worker:latest .`
   - Build Status: **SUCCESS** (38.0s build time)
   - Image Size: **165MB** (optimized)
   - Architecture: **amd64 (Linux)**
   - Dependencies Installed: redis, requests, python-dotenv, pydantic
   - Multiple versions available: v1, v2, latest

#### 4. **Git Status** ✅
   - Current Branch: `infra-backend`
   - Tracking: `origin/infra-backend`
   - Status: All changes committed
   - No uncommitted changes

### Code Quality Improvements from Merged Branches:

**From `main` branch (A's work)**:
- Added `uuid` import (future use for job IDs)
- Improved comments documenting the process

**Preserved from `infra-backend` (P's work)**:
- ✅ JSON parsing of job content: `job_data = json.loads(job_json_string)`
- ✅ Job ID extraction: `job_id = job_data.get("job_id")`
- ✅ Prompt extraction: `prompt = job_data.get("prompt")`
- ✅ Validation logic for job format
- ✅ Result caching with job_id: `redis_client.set(f"result:{job_id}", ...)`
- ✅ Error handling with job_id tracking
- ✅ Comprehensive logging

### Docker Image Analysis:

```
Image: greenscale-worker:latest
ID: b6995a272366
Size: 165MB
Architecture: amd64
Os: linux
Build Layers:
  [1/5] Base image: python:3.9-slim
  [2/5] WORKDIR /app
  [3/5] COPY requirements.txt
  [4/5] RUN pip install
  [5/5] COPY src/worker.py
Status: ✅ Ready for deployment
```

---

## � PROJECT COMPLETE - FINAL SUMMARY

### ✅ All Objectives Achieved:

| Objective | Status | Details |
|-----------|--------|---------|
| Scale-to-Zero | ✅ DONE | Workers scale 0→5 based on queue |
| KEDA Integration | ✅ DONE | ScaledObject monitoring Redis |
| Neysa Llama API | ✅ DONE | 70B model processing prompts |
| Streamlit Dashboard | ✅ DONE | Real-time metrics & job submission |
| Job Tracking | ✅ DONE | UUID-based job IDs with results |
| Docker Optimization | ✅ DONE | 165MB slim image |
| End-to-End Testing | ✅ PASSED | Manual + UI tests successful |

### 📊 Final Test Results:

```
┌─────────────────────────────────────────────────────────────┐
│ TEST 1: Manual Redis CLI                                     │
├─────────────────────────────────────────────────────────────┤
│ Input:  LPUSH jobs '{"job_id":"test-001","prompt":"2+2?"}'  │
│ Output: GET result:test-001 → "2 + 2 = 4"                   │
│ Status: ✅ PASSED                                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TEST 2: Streamlit UI                                         │
├─────────────────────────────────────────────────────────────┤
│ Input:  "What is capital of china"                          │
│ Output: "The capital of China is Beijing."                  │
│ Status: ✅ PASSED                                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ TEST 3: KEDA Scaling                                         │
├─────────────────────────────────────────────────────────────┤
│ Before: greenscale-worker 0/0 replicas                      │
│ During: greenscale-worker 1/1 Running                       │
│ After:  greenscale-worker 0/0 (scaled down after 30s)       │
│ Status: ✅ PASSED                                            │
└─────────────────────────────────────────────────────────────┘
```

### 🚀 Deployment Artifacts:

- **GitHub Repository**: https://github.com/Pswaikar1742/Greenscale
- **Branch**: `main` (production-ready)
- **Docker Image**: `greenscale-worker:latest`
- **Documentation**: `SETUP_AND_RUN_GUIDE.md`

### 📞 Team Credits:

| Role | Name | Contributions |
|------|------|---------------|
| Platform Engineer | **P (Prathmesh)** | K8s, KEDA, Docker, Redis, Worker deployment |
| Application Engineer | **A (Ali)** | Streamlit UI, Job submission, Results polling |

---

**🏁 PROJECT STATUS: COMPLETE**  
**📅 Completion Date: January 31, 2026**  
**🔖 Version: 1.0.0**

---

## 🎨 UI DASHBOARD v2.0 - PLOTLY GAUGE CLUSTER

### Dashboard Features (Updated Jan 31, 2026)

The GreenScale dashboard has been completely redesigned with a modern car dashboard-inspired gauge cluster using Plotly.

#### Primary Gauge Metrics:

| Gauge | Color | Data Source | Range |
|-------|-------|-------------|-------|
| 📥 **QUEUE** | Blue (#3b82f6) | `redis_client.llen("jobs")` | 0-10 |
| ⚡ **WORKERS** | Emerald (#10b981) | Queue inference | 0-5 |
| ✅ **PROCESSED** | Purple (#8b5cf6) | `redis_client.keys("result:*")` | 0-50 |
| 💰 **SAVINGS** | Amber (#f59e0b) | Time-based calculation | $0-$20 |

#### Secondary Metrics Row:

| Metric | Source | Description |
|--------|--------|-------------|
| 🕐 Uptime | Session timer | Browser session duration |
| ⏱️ Avg Response | Empirical | ~3s average (cold: 5-8s, warm: 2-3s) |
| 📊 Scale Events | jobs_processed | Correlates with KEDA scaling |
| 💾 Memory | K8s spec | 256MB worker allocation |
| 🔥 GPU Util | Worker state | 0% (idle) or 78% (active) |

#### Savings Calculation Formula:
```python
GPU_COST_PER_HOUR = 3.50  # A100 GPU pricing

def calculate_savings(jobs_processed):
    active_time_hours = (jobs_processed * 5) / 3600  # 5s per job
    session_hours = (current_time - session_start) / 3600
    idle_hours = max(0, session_hours - active_time_hours)
    return idle_hours * GPU_COST_PER_HOUR
```

#### Real Metrics vs Estimates:

| Metric | Type | Accuracy |
|--------|------|----------|
| Queue | ✅ Real | Direct Redis LLEN |
| Processed | ✅ Real | Redis KEYS count |
| Redis Status | ✅ Real | Ping check |
| Uptime | ✅ Real | Session timer |
| Workers | ⚠️ Estimate | Inferred from queue |
| Savings | ⚠️ Estimate | Time-based model |
| GPU Util | ⚠️ Estimate | Binary (0/78%) |
| Avg Response | ❌ Static | Placeholder ~3s |
| Resource Bars | ❌ Static | Representative values |

### Additional UI Features:

1. **Job History** - Last 10 jobs with response times
2. **System Monitor** - Component status indicators
3. **Resource Bars** - CPU/Memory/GPU/Network visualization
4. **Helm Chart Generator** - Custom Helm chart creation

### UI Tech Stack:
- **Framework**: Streamlit
- **Charts**: Plotly (gauge indicators)
- **Styling**: Custom CSS (Inter font, glassmorphism)
- **Theme**: Dark gradient with emerald/blue/purple accents

---

## ⚠️ SYSTEM DO'S AND DON'TS

### ✅ DO's:

1. **DO** run `kubectl port-forward svc/redis-service -n greenscale-system 6379:6379` before starting the UI
2. **DO** wait 30 seconds after last job for workers to scale down (KEDA cooldown)
3. **DO** monitor Queue gauge - if consistently >5, increase KEDA maxReplicaCount
4. **DO** refresh the dashboard manually to see updated metrics
5. **DO** use the Helm Chart Generator for production deployments
6. **DO** check the green "System Online" badge before submitting jobs
7. **DO** allow 5-8 seconds for cold start when scaling from 0 workers

### ❌ DON'Ts:

1. **DON'T** rely on Savings metric for actual billing (it's a demonstration estimate)
2. **DON'T** assume GPU Util% is real telemetry (it's derived from worker state)
3. **DON'T** submit hundreds of jobs at once (5-replica limit by default)
4. **DON'T** expect results to persist forever (Redis is in-memory)
5. **DON'T** close the terminal running port-forward
6. **DON'T** use for production without: persistent Redis, proper secrets, GPU nodes
7. **DON'T** modify KEDA ScaledObject without understanding cooldownPeriod implications

---

**Document Generated:** January 31, 2026  
**Platform Engineer:** Prathmesh (P)  
**Status:** Ready for AI Studio Review
