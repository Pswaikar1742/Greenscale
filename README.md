# 🌱 GreenScale

**Intelligent Scale-to-Zero Autoscaler for AI/ML Workloads on Kubernetes**

> Eliminate the cost of idle GPUs with event-driven autoscaling powered by KEDA.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-1.25+-326CE5.svg)](https://kubernetes.io)
[![KEDA](https://img.shields.io/badge/KEDA-2.12+-orange.svg)](https://keda.sh)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🎬 Product Demo

| Resource | Link |
|----------|------|
| 🎥 **Demo Video** | [Watch Demo](https://drive.google.com/file/d/12IZwp1OVbmJUocjHKuo9kEB3Bkq5FRvj/view?usp=drive_link) |
| 📊 **Live Presentation** | [View Slides](https://drive.google.com/file/d/1iT0e_xwR-3lJLyux35Hz4fF4ixFNuKZ2/view?usp=sharing) |
| 🌐 **Hosted App** | *Run locally with one command (see below)* |

> **Quick Demo:** Run `./scripts/run-greenscale.sh` and open http://localhost:8501

---

## 🎯 Problem Statement

### The $2.7 Billion Problem

Organizations running AI/ML workloads on Kubernetes face a critical cost challenge:

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE IDLE GPU PROBLEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   💰 A100 GPU Cost: $3.50/hour = $2,520/month                   │
│   📊 Average AI Workload Utilization: Only 5-15%                │
│   🔥 Wasted Cost: Up to $2,394/month PER GPU                    │
│                                                                 │
│   "GPUs sit idle 85-95% of the time, but you pay 100%"         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Why does this happen?**
- Traditional Kubernetes keeps minimum replicas running 24/7
- Batch AI jobs are sporadic (inference requests, model training)
- No native "scale to zero" for GPU workloads
- Manual scaling is error-prone and slow

---

## 💡 Our Solution: GreenScale

GreenScale is an **event-driven autoscaling platform** that enables true **Scale-to-Zero** for AI/ML workloads:

| Feature | Traditional K8s | GreenScale |
|---------|-----------------|------------|
| Minimum Replicas | 1+ (always on) | **0** (truly off) |
| GPU Cost at Idle | $2,520/month | **$0/month** |
| Scale-up Time | Manual / HPA lag | **~2 seconds** |
| Scale Trigger | CPU/Memory metrics | **Event-driven (queue)** |

### How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   No Jobs    │     │  Job Arrives │     │  Processing  │
│              │     │              │     │              │
│  Workers: 0  │────▶│  Workers: 1  │────▶│  Workers: N  │
│  Cost: $0    │     │  (2s cold)   │     │  (auto-scale)│
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                     ┌──────────────┐           │
                     │  Job Done    │◀──────────┘
                     │              │   30s cooldown
                     │  Workers: 0  │
                     │  Cost: $0    │
                     └──────────────┘
```

### Real-World Savings Calculator

| Scenario | Traditional | GreenScale | Monthly Savings |
|----------|-------------|------------|-----------------|
| Dev/Test (5% util) | $2,520 | $126 | **$2,394** |
| Staging (15% util) | $2,520 | $378 | **$2,142** |
| Production (30% util) | $2,520 | $756 | **$1,764** |

---

## 🛠️ Technology Stack

### Core Technologies

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Orchestration** | Kubernetes | Container orchestration |
| **Autoscaling** | KEDA | Event-driven scale-to-zero |
| **Message Queue** | Redis | Job queue & result storage |
| **AI Backend** | Llama 3.3 70B (Neysa) | LLM inference API |
| **Frontend** | Streamlit | Real-time dashboard |
| **Containerization** | Docker | Worker containerization |

### Architecture Diagram

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
│              • Real-time metrics  • Cost tracking                │
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
│  • Monitors Redis queue │      │  • Replicas: 0 → 5              │
│  • 30s cooldown         │      │  • Calls Llama 3.3 70B API      │
│  • Instant scale-up     │      │  • Stores results in Redis      │
└─────────────────────────┘      └─────────────────────────────────┘
```

### Key Components

| Component | File | Description |
|-----------|------|-------------|
| Dashboard | `src/app.py` | Streamlit UI with real-time metrics |
| Worker | `src/worker.py` | Processes jobs from Redis queue |
| KEDA Config | `k8s/keda-scaledobject.yaml` | Scale-to-zero configuration |
| Redis | `k8s/redis.yaml` | Message queue deployment |

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
├── scripts/
│   ├── run-greenscale.sh   # ⭐ One-click deployment script
│   └── test-queue.sh       # E2E test script
├── docs/
│   ├── DEPLOYMENT_GUIDE.md # Comprehensive deployment guide
│   ├── UI_METRICS_GUIDE.md # Dashboard metrics explanation
│   └── ...                 # Additional documentation
├── Dockerfile              # Worker container image
├── docker-compose.yaml     # Local development setup
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## 🚀 Quick Start (One Command)

### Prerequisites

- **Docker** (v20.10+)
- **Minikube** (v1.30+)
- **kubectl** (v1.27+)
- **Python** (3.9+)

### One-Click Deployment

```bash
# Clone the repository
git clone https://github.com/Pswaikar1742/Greenscale.git
cd Greenscale

# Run everything with one command!
./scripts/run-greenscale.sh
```

This script automatically:
1. ✅ Starts Minikube cluster
2. ✅ Installs KEDA autoscaler
3. ✅ Builds Docker image
4. ✅ Deploys all Kubernetes resources
5. ✅ Sets up Redis port-forwarding
6. ✅ Launches Streamlit dashboard

**Open http://localhost:8501** and start submitting AI jobs! 🎉

> 📚 For detailed setup options, see [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)

---

## 🧪 See Scale-to-Zero in Action

### Watch the magic happen:

```bash
# Terminal 1: Watch pods (should show 0 worker pods initially)
kubectl get pods -n greenscale-system -w

# Terminal 2: Submit a job via dashboard or CLI
kubectl exec -n greenscale-system deployment/redis -- \
  redis-cli LPUSH jobs '{"job_id":"test-001","prompt":"What is 2+2?"}'

# Watch Terminal 1: Worker scales 0→1, processes job, then 1→0 after 30s
```

**Expected behavior:**
```
NAME                                 READY   STATUS    
redis-xxxxxxxxxx-xxxxx               1/1     Running   
greenscale-worker-xxxxxxxxxx-xxxxx   0/1     Pending   ← Job arrives
greenscale-worker-xxxxxxxxxx-xxxxx   1/1     Running   ← Processing
greenscale-worker-xxxxxxxxxx-xxxxx   0/1     Terminating ← 30s cooldown
(no worker pods)                                       ← Scale-to-Zero!
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

## 📊 Dashboard Features

The Streamlit dashboard provides real-time visibility:

| Metric | Description |
|--------|-------------|
| 📥 **Queue** | Jobs waiting in Redis |
| ⚡ **Workers** | Active worker pods (0-5) |
| ✅ **Processed** | Total completed jobs |
| 💰 **Savings** | Estimated cost savings |

> 📚 For detailed metrics explanation, see [docs/UI_METRICS_GUIDE.md](docs/UI_METRICS_GUIDE.md)

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Worker not scaling up | Check KEDA: `kubectl get scaledobject -n greenscale-system` |
| Redis connection failed | Ensure port-forward is running |
| API errors | Verify API key in secret |

> 📚 For more issues, see [docs/DEPLOYMENT_GUIDE.md#troubleshooting](docs/DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 👥 Team

| Member | Role | Responsibilities |
|--------|------|------------------|
| **Prathmesh (P)** | Platform Engineer | Kubernetes, Docker, KEDA, Infrastructure |
| **Ali (A)** | Application Engineer | Python, Redis, Streamlit UI |

---

## 📜 License

MIT License - Built for **AIBoomi Hackathon 2026**

---

## 🔗 Links

| Resource | URL |
|----------|-----|
| 📂 GitHub Repo | [github.com/Pswaikar1742/Greenscale](https://github.com/Pswaikar1742/Greenscale.git) |
| 🎥 Demo Video | [Watch Demo](https://drive.google.com/file/d/12IZwp1OVbmJUocjHKuo9kEB3Bkq5FRvj/view?usp=drive_link) |
| 📊 Presentation | [View Slides](https://drive.google.com/file/d/1iT0e_xwR-3lJLyux35Hz4fF4ixFNuKZ2/view?usp=sharing) |

---

<p align="center">
  <b>🌱 GreenScale - Because idle GPUs shouldn't cost you money</b>
  <br><br>
  <i>Built with ❤️ for AIBoomi Hackathon 2026</i>
</p>
