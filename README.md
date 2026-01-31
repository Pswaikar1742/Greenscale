# 🌱 GreenScale

**Intelligent Scale-to-Zero Autoscaler for AI/ML Workloads on Kubernetes**

> Eliminate the cost of idle GPUs with event-driven autoscaling powered by KEDA.

## 🎯 What is GreenScale?

GreenScale is a DevTool/Infrastructure project that enables **Scale-to-Zero** for AI/ML workloads. When there's no work to do, your expensive GPU pods sleep. When jobs arrive, they wake up instantly.

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────┐     ┌──────────────────┐
│   Streamlit UI  │────▶│    Redis    │◀────│      KEDA        │
│    (app.py)     │     │   (jobs)    │     │  (ScaledObject)  │
└─────────────────┘     └──────┬──────┘     └────────┬─────────┘
                               │                     │
                               │    ┌────────────────┘
                               ▼    ▼
                        ┌──────────────────┐
                        │  Worker Pod(s)   │
                        │   (worker.py)    │
                        │  replicas: 0→N   │
                        └──────────────────┘
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Orchestrator | Kubernetes (Minikube) |
| Autoscaler | KEDA |
| Message Broker | Redis |
| Language | Python 3.9+ |
| Frontend | Streamlit |
| Containerization | Docker |
| AI Engine | OpenAI API |

## 📁 Project Structure

```
greenscale/
├── k8s/                          # Kubernetes manifests (P)
│   ├── namespace.yaml
│   ├── redis-deployment.yaml
│   ├── redis-service.yaml
│   ├── worker-deployment.yaml
│   ├── scaledobject.yaml
│   └── secrets.yaml
├── src/
│   ├── app.py                    # Streamlit frontend (A)
│   └── worker.py                 # Job processor (A)
├── Dockerfile                    # Worker container (P)
├── docker-compose.yaml           # Local dev environment
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Minikube
- kubectl
- KEDA installed on cluster

### 1. Start Minikube
```bash
minikube start --driver=docker
```

### 2. Install KEDA
```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda --create-namespace
```

### 3. Deploy GreenScale
```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Deploy Redis
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# Deploy secrets (update with your API key first!)
kubectl apply -f k8s/secrets.yaml

# Deploy worker (starts at 0 replicas)
kubectl apply -f k8s/worker-deployment.yaml

# Enable KEDA autoscaling
kubectl apply -f k8s/scaledobject.yaml
```

### 4. Run the Frontend (locally)
```bash
pip install -r requirements.txt
streamlit run src/app.py
```

## 👥 Team

- **P (Prathmesh)** - Platform Engineer: K8s, Docker, Infrastructure
- **A (Ali)** - Application Engineer: Python, Redis, Streamlit UI

## 📜 License

MIT License - Built for AIBoomi Hackathon 2026 