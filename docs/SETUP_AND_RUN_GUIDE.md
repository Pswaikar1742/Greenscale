# 🌱 GreenScale - Setup & Run Guide

**Scale-to-Zero Autoscaler for AI/ML Workloads on Kubernetes**

---

## 📋 Prerequisites

Before running GreenScale, ensure you have:

- **Docker** (v20.10+)
- **Minikube** (v1.30+) or any Kubernetes cluster
- **kubectl** (v1.27+)
- **KEDA** (v2.10+) installed on your cluster
- **Python** (3.9+) with pip

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Start Minikube

```bash
minikube start --driver=docker --memory=4096
```

### Step 2: Install KEDA

```bash
kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml
```

Wait for KEDA to be ready:
```bash
kubectl wait --for=condition=ready pod -l app=keda-operator -n keda --timeout=120s
```

### Step 3: Build & Load Docker Image

```bash
cd /home/psw/Projects/Greenscale

# Build the worker image
docker build -t greenscale-worker:latest .

# Load into Minikube
minikube image load greenscale-worker:latest
```

### Step 4: Deploy Kubernetes Resources

```bash
# Apply all manifests
kubectl apply -f k8s/

# Create the Neysa API secret (if not exists)
# Replace <REPLACE_WITH_NEYSA_API_KEY> with your real key (do not commit keys).
kubectl create secret generic neysa-secret \
  --from-literal=NEYSA_API_KEY=<REPLACE_WITH_NEYSA_API_KEY> \
  --from-literal=NEYSA_API_URL=https://boomai-llama.neysa.io/v1/chat/completions \
  -n greenscale-system --dry-run=client -o yaml | kubectl apply -f -
```

### Step 5: Verify Deployment

```bash
# Check all resources
kubectl get all -n greenscale-system

# Expected output:
# - redis pod: Running
# - greenscale-worker deployment: 0/0 (Scale-to-Zero)
# - redis-service: ClusterIP

# Check KEDA ScaledObject
kubectl get scaledobject -n greenscale-system
```

### Step 6: Port Forward Redis

```bash
# In a separate terminal, keep this running:
kubectl port-forward svc/redis-service -n greenscale-system 6379:6379
```

### Step 7: Run Streamlit Dashboard

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run src/app.py
```

The dashboard will open at: **http://localhost:8501**

---

## 🖥️ Using the Dashboard

1. **View Metrics**: See real-time queue length, active workers, and cost savings
2. **Submit a Job**: Enter a prompt (e.g., "What is the capital of France?")
3. **Click Submit**: Job is pushed to Redis queue
4. **Watch KEDA Scale**: Worker pods scale from 0 → 1
5. **Get Results**: Response appears in the dashboard
6. **Auto Scale-Down**: After 30s of inactivity, workers scale back to 0

---

## 🔧 Manual Testing (Without UI)

### Push a Job to Redis

```bash
# Connect to Redis
kubectl exec -it -n greenscale-system deploy/redis -- redis-cli

# Push a test job
LPUSH jobs '{"job_id": "test-001", "prompt": "What is 2+2?"}'

# Check queue length
LLEN jobs

# Exit Redis CLI
exit
```

### Watch Worker Pods Scale

```bash
kubectl get pods -n greenscale-system -w
```

### Check Worker Logs

```bash
kubectl logs -n greenscale-system -l app=greenscale-worker -f
```

### Get Results

```bash
kubectl exec -it -n greenscale-system deploy/redis -- redis-cli GET result:test-001
```

---

## 📁 Project Structure

```
Greenscale/
├── src/
│   ├── app.py          # Streamlit frontend
│   └── worker.py       # Job processor (runs in K8s)
├── k8s/
│   ├── namespace.yaml  # greenscale-system namespace
│   ├── redis.yaml      # Redis deployment & service
│   ├── worker-deployment.yaml  # Worker deployment (0-5 replicas)
│   ├── keda-scaledobject.yaml  # KEDA autoscaler config
│   └── openai-secret.yaml      # API secrets
├── Dockerfile          # Worker container image
├── docker-compose.yaml # Local development setup
├── requirements.txt    # Python dependencies
└── README.md
```

---

## 🐳 Running with Docker Compose (Local Dev)

For local development without Kubernetes:

```bash
# Set environment variables (replace placeholder with your key)
export NEYSA_API_KEY=<REPLACE_WITH_NEYSA_API_KEY>
export NEYSA_API_URL=https://boomai-llama.neysa.io/v1/chat/completions

# Start all services
docker-compose up --build

# In another terminal, run Streamlit
streamlit run src/app.py
```

---

## 🔍 Troubleshooting

### Workers Not Scaling Up

```bash
# Check KEDA operator logs
kubectl logs -n keda -l app=keda-operator

# Verify ScaledObject status
kubectl describe scaledobject greenscale-worker-scaler -n greenscale-system
```

### Worker Pods Crashing

```bash
# Check worker logs
kubectl logs -n greenscale-system -l app=greenscale-worker --tail=100

# Verify image is loaded
minikube image ls | grep greenscale
```

### Redis Connection Issues

```bash
# Verify Redis is running
kubectl get pods -n greenscale-system -l app=redis

# Test Redis connectivity
kubectl exec -it -n greenscale-system deploy/redis -- redis-cli PING
# Should return: PONG
```

### Streamlit Errors

```bash
# Ensure port-forward is running
kubectl port-forward svc/redis-service -n greenscale-system 6379:6379

# Check Python dependencies
pip install --upgrade streamlit redis python-dotenv
```

---

## 📊 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│   Redis Queue   │────▶│  KEDA Scaler    │
│   (localhost)   │     │   (K8s Pod)     │     │  (Watches Redis)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Llama Response │◀────│  Worker Pod(s)  │◀────│ Scale 0 → 5     │
│  (via Neysa)    │     │  (K8s Pods)     │     │ (Auto-scaling)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## 🎯 Key Commands Reference

| Action | Command |
|--------|---------|
| Start Minikube | `minikube start` |
| Build Image | `docker build -t greenscale-worker:latest .` |
| Load to Minikube | `minikube image load greenscale-worker:latest` |
| Deploy All | `kubectl apply -f k8s/` |
| Check Pods | `kubectl get pods -n greenscale-system` |
| Watch Scaling | `kubectl get pods -n greenscale-system -w` |
| Port Forward | `kubectl port-forward svc/redis-service -n greenscale-system 6379:6379` |
| Run Dashboard | `streamlit run src/app.py` |
| Worker Logs | `kubectl logs -n greenscale-system -l app=greenscale-worker -f` |
| Delete All | `kubectl delete -f k8s/` |

---

## ✅ Success Checklist

- [ ] Minikube running
- [ ] KEDA installed
- [ ] Docker image built and loaded
- [ ] K8s resources deployed
- [ ] Redis port-forwarded (6379)
- [ ] Streamlit dashboard accessible (8501)
- [ ] Jobs processing successfully
- [ ] Workers scaling up/down

---

**Created:** January 31, 2026  
**Team:** P (Platform) & A (Application)  
**Repository:** https://github.com/Pswaikar1742/Greenscale
