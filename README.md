# 🌱 GreenScale

**Intelligent Scale-to-Zero Autoscaler for AI/ML Workloads on Kubernetes**

> Eliminate the cost of idle GPUs with event-driven autoscaling powered by KEDA.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.25+-326CE5.svg)](https://kubernetes.io)
[![KEDA](https://img.shields.io/badge/KEDA-2.12+-orange.svg)](https://keda.sh)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎯 What is GreenScale?

GreenScale is an infrastructure project that enables **true Scale-to-Zero** for AI/ML workloads. When there's no work, your expensive GPU pods sleep (0 replicas). When jobs arrive, they wake up instantly.

**Key Benefits:**
- 💰 **Cost Savings**: Pay only when processing jobs
- ⚡ **Instant Scale-Up**: ~2 second cold start with KEDA
- 🔄 **Automatic Scale-Down**: 30 second cooldown to zero
- 🧠 **AI-Ready**: Integrated with Llama 3.3 70B API

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     STREAMLIT DASHBOARD                          │
│                         (src/app.py)                             │
│              • Submit prompts  • View results                    │
│              • Real-time metrics  • Job tracking                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          REDIS                                   │
│                    Message Broker                                │
│         ┌─────────────┐        ┌─────────────────┐              │
│         │ jobs (list) │        │ result:{id} (kv)│              │
│         └─────────────┘        └─────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
┌─────────────────────────┐      ┌─────────────────────────────────┐
│         KEDA            │      │      WORKER PODS                │
│   Event-Driven Scaler   │─────▶│     (src/worker.py)             │
│  • Monitors Redis queue │      │  • Replicas: 0 → N              │
│  • 30s cooldown         │      │  • Calls Llama 3.3 70B API      │
│  • 0-5 replicas         │      │  • Stores results in Redis      │
└─────────────────────────┘      └─────────────────────────────────┘
```

---

## 📁 Project Structure

```
greenscale/
├── src/
│   ├── app.py              # Streamlit frontend dashboard
│   └── worker.py           # K8s worker - processes AI jobs
├── k8s/
│   ├── namespace.yaml      # greenscale-system namespace
│   ├── redis.yaml          # Redis deployment + service
│   ├── worker-deployment.yaml  # Worker deployment (replicas: 0)
│   ├── keda-scaledobject.yaml  # KEDA autoscaling config
│   └── openai-secret.yaml  # API key secret
├── Dockerfile              # Worker container image
├── docker-compose.yaml     # Local development setup
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
└── docs/                   # Additional documentation
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** (for building images)
- **Minikube** (local Kubernetes cluster)
- **kubectl** (Kubernetes CLI)
- **KEDA** (installed on cluster)
- **Neysa API Key** (for Llama 3.3 70B)

### 1️⃣ Start Minikube

```bash
minikube start --driver=docker --memory=4096
```

### 2️⃣ Install KEDA

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
```

### 3️⃣ Build & Load Docker Image

```bash
# Build the worker image
docker build -t greenscale-worker:latest .

# Load into Minikube
minikube image load greenscale-worker:latest
```

### 4️⃣ Configure Secrets

Edit `k8s/openai-secret.yaml` with your API key (base64 encoded):

```bash
echo -n "your-api-key" | base64
```

### 5️⃣ Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/openai-secret.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/worker-deployment.yaml
kubectl apply -f k8s/keda-scaledobject.yaml

# Verify deployment
kubectl get pods -n greenscale-system
```

### 6️⃣ Run Frontend (Port Forward Redis)

```bash
# Terminal 1: Port forward Redis
kubectl port-forward svc/redis-service -n greenscale-system 6379:6379

# Terminal 2: Run Streamlit
pip install -r requirements.txt
streamlit run src/app.py
```

Open http://localhost:8501 🎉

---

## 🧪 Testing Scale-to-Zero

### Watch the magic happen:

```bash
# Terminal 1: Watch pods (should show 0 worker pods initially)
kubectl get pods -n greenscale-system -w

# Terminal 2: Submit a job
kubectl exec -n greenscale-system deployment/redis -- \
  redis-cli LPUSH jobs '{"job_id":"test-001","prompt":"What is 2+2?"}'

# Watch Terminal 1: Worker scales 0→1, processes job, then 1→0 after 30s
```

### Check result:

```bash
kubectl exec -n greenscale-system deployment/redis -- \
  redis-cli GET result:test-001
```

---

## ⚙️ Configuration

### KEDA ScaledObject

| Parameter | Value | Description |
|-----------|-------|-------------|
| `minReplicaCount` | 0 | Enable Scale-to-Zero |
| `maxReplicaCount` | 5 | Max parallel workers |
| `cooldownPeriod` | 30 | Seconds before scale-down |
| `pollingInterval` | 5 | Queue check frequency |
| `listLength` | 1 | Scale up when ≥1 job |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEYSA_API_KEY` | Llama API authentication | Required |
| `NEYSA_API_URL` | AI endpoint URL | `https://boomai-llama.neysa.io/v1/chat/completions` |
| `REDIS_HOST` | Redis hostname | `redis-service` |
| `REDIS_PORT` | Redis port | `6379` |

---

## 🔧 Development

### Local Development with Docker Compose

```bash
# Start Redis locally
docker-compose up -d redis

# Run worker locally (for testing)
export REDIS_HOST=localhost
python src/worker.py

# Run frontend
streamlit run src/app.py
```

### Rebuild After Changes

```bash
docker build --no-cache -t greenscale-worker:latest .
minikube image load greenscale-worker:latest
kubectl rollout restart deployment/greenscale-worker -n greenscale-system
```

---

## 📊 Monitoring

### Check KEDA Status

```bash
kubectl get scaledobject -n greenscale-system
kubectl describe scaledobject greenscale-worker-scaler -n greenscale-system
```

### View Worker Logs

```bash
kubectl logs -n greenscale-system -l app=greenscale-worker -f
```

### Redis Queue Status

```bash
kubectl exec -n greenscale-system deployment/redis -- redis-cli LLEN jobs
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Worker shows "Error" after termination | This is normal - KEDA terminates pods gracefully |
| Worker not scaling up | Check KEDA: `kubectl get scaledobject -n greenscale-system` |
| Redis connection failed | Verify Redis is running: `kubectl get pods -n greenscale-system` |
| API errors | Check secret is correct and API endpoint is reachable |

---

## 👥 Team

- **Prathmesh (P)** - Platform Engineer: Kubernetes, Docker, Infrastructure
- **Ali (A)** - Application Engineer: Python, Redis, Streamlit UI

---

## 📜 License

MIT License - Built for **AIBoomi Hackathon 2026**

---

<p align="center">
  <b>🌱 GreenScale - Because idle GPUs shouldn't cost you money</b>
</p>
