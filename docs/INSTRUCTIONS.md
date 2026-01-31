# MISSION BRIEF: GREENSCALE (AIBOOMI HACKATHON)

## 1. PROJECT GOAL
We are building "GreenScale," an intelligent autoscaler for AI/ML workloads on Kubernetes. Our primary value proposition is enabling **"Scale-to-Zero"** to eliminate the cost of idle GPUs. We are a DevTool/Infrastructure project, not just a chatbot.

## 2. CORE TECHNOLOGY STACK
- **Orchestrator:** Kubernetes (running locally via Minikube).
- **Autoscaler:** KEDA (Kubernetes Event-Driven Autoscaling).
- **Message Broker:** Redis (running inside Kubernetes).
- **Language:** Python 3.9+.
- **Frontend:** Streamlit.
- **Containerization:** Docker.
- **AI Engine (for MVP):** OpenAI API.

## 3. APPLICATION ARCHITECTURE (The Data Flow)
1.  **The User Interface (`app.py`):** A Streamlit dashboard allows a user to submit a text prompt.
2.  **The Queue:** The Streamlit app does NOT call the AI directly. It pushes the prompt into a **Redis List** named `jobs`.
3.  **The Autoscaler (`scaledobject.yaml`):** KEDA is configured to monitor the length of the `jobs` list in Redis.
4.  **The Worker (`worker.py`):**
    - This is a Python script running inside a Docker container.
    - Its Kubernetes Deployment is configured with `replicas: 0` by default.
    - When KEDA detects `jobs` length > 0, it scales the Deployment to `replicas: 1`.
    - The `worker.py` script wakes up, connects to Redis, uses `RPOP` to pull a job, calls the OpenAI API to process it, and then loops to check for more jobs.
5.  **Scale-Down:** When the `jobs` list is empty, KEDA waits for a `cooldownPeriod` and scales the Deployment back to `replicas: 0`.

## 4. KEY VARIABLES & NAMING CONVENTIONS
- **Kubernetes Namespace:** `greenscale-system`
- **Redis Service Name (in K8s):** `redis-service`
- **Redis List Name:** `jobs`
- **Worker Deployment Name:** `greenscale-worker`
- **Frontend Python File:** `app.py`
- **Backend Python File:** `worker.py`
- **Secrets:** Handled via a `.env` file (`OPENAI_API_KEY`, `REDIS_HOST`, `REDIS_PORT`).

## 5. ROLES
- **P (Prathmesh):** Platform Engineer. Owns Kubernetes YAMLs (`k8s/`), `Dockerfile`, and Minikube setup.
- **A (Ali):** Application Engineer. Owns Python code (`app.py`, `worker.py`), Redis logic, and Streamlit UI.

---

## 6. DEVELOPMENT WORKFLOW

### For P (Platform Engineer):
```bash
# Test Docker build locally
docker build -t greenscale-worker:latest .

# Load image into Minikube
minikube image load greenscale-worker:latest

# Apply K8s manifests
kubectl apply -f k8s/ -n greenscale-system

# Watch scaling in action
kubectl get pods -n greenscale-system -w
```

### For A (Application Engineer):
```bash
# Local development with Redis
docker-compose up redis -d

# Run worker locally
python src/worker.py

# Run frontend
streamlit run src/app.py
```

## 7. DEBUGGING COMMANDS
```bash
# Check KEDA ScaledObject status
kubectl describe scaledobject greenscale-worker-scaler -n greenscale-system

# Check Redis queue length
kubectl exec -it deploy/redis -n greenscale-system -- redis-cli LLEN jobs

# View worker logs
kubectl logs -f deploy/greenscale-worker -n greenscale-system

# Check HPA created by KEDA
kubectl get hpa -n greenscale-system
```

---
# END OF BRIEF
