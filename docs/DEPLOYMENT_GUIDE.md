# 🌱 GreenScale Deployment Guide

**Version:** 1.0  
**Last Updated:** January 31, 2026  
**Author:** Prathmesh (Platform Engineer)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Option A: Kubernetes Deployment (Recommended)](#option-a-kubernetes-deployment-recommended)
4. [Option B: Local Development with Docker Compose](#option-b-local-development-with-docker-compose)
5. [Quick Reference Commands](#quick-reference-commands)
6. [Troubleshooting](#troubleshooting)

---

## Overview

GreenScale offers two deployment options:

| Option | Use Case | Scale-to-Zero | Production Ready |
|--------|----------|---------------|------------------|
| **Option A: Kubernetes** | Full demo with KEDA autoscaling | ✅ Yes | ✅ Yes |
| **Option B: Docker Compose** | Quick local testing | ❌ No | ❌ No |

### When to Use Each Option

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION FLOWCHART                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Do you want to demonstrate Scale-to-Zero?                      │
│       │                                                         │
│       ├── YES ──► Option A (Kubernetes + KEDA)                  │
│       │                                                         │
│       └── NO ───► Do you just need to test the UI?              │
│                        │                                        │
│                        ├── YES ──► Option B (Docker Compose)    │
│                        │                                        │
│                        └── NO ───► Option A (Kubernetes)        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Common Requirements (Both Options)

| Tool | Version | Installation |
|------|---------|--------------|
| **Docker** | v20.10+ | [Install Docker](https://docs.docker.com/get-docker/) |
| **Python** | 3.9+ | [Install Python](https://www.python.org/downloads/) |
| **pip** | Latest | Comes with Python |

### Option A Additional Requirements

| Tool | Version | Installation |
|------|---------|--------------|
| **Minikube** | v1.30+ | [Install Minikube](https://minikube.sigs.k8s.io/docs/start/) |
| **kubectl** | v1.27+ | [Install kubectl](https://kubernetes.io/docs/tasks/tools/) |

### Verify Prerequisites

```bash
# Check all tools
docker --version
python3 --version
pip --version

# For Option A only
minikube version
kubectl version --client
```

---

## Option A: Kubernetes Deployment (Recommended)

### 🎯 What You Get

- ✅ Full Scale-to-Zero demonstration
- ✅ KEDA event-driven autoscaling
- ✅ Production-like architecture
- ✅ Real worker pod scaling (0 → N → 0)
- ✅ Complete metrics visibility

### 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      MINIKUBE CLUSTER                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  greenscale-system namespace              │  │
│  │                                                           │  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │  │
│  │  │   Redis     │    │    KEDA     │    │   Worker    │   │  │
│  │  │  (Queue)    │◄───│  (Scaler)   │───►│   Pods      │   │  │
│  │  │             │    │             │    │  (0 to 5)   │   │  │
│  │  └──────┬──────┘    └─────────────┘    └─────────────┘   │  │
│  │         │                                                 │  │
│  └─────────┼─────────────────────────────────────────────────┘  │
│            │ port-forward :6379                                 │
└────────────┼────────────────────────────────────────────────────┘
             │
    ┌────────▼────────┐
    │   Streamlit     │
    │   Dashboard     │
    │  localhost:8501 │
    └─────────────────┘
```

### 🚀 Step-by-Step Instructions

#### Step 1: Start Minikube

```bash
minikube start --driver=docker --memory=4096
```

**Expected Output:**
```
😄  minikube v1.32.0 on Ubuntu 22.04
✨  Using the docker driver based on user configuration
📌  Using Docker driver with root privileges
🔥  Creating docker container (CPUs=2, Memory=4096MB) ...
🐳  Preparing Kubernetes v1.28.3 on Docker 24.0.7 ...
🔎  Verifying Kubernetes components...
🌟  Enabled addons: default-storageclass, storage-provisioner
🏄  Done! kubectl is now configured to use "minikube" cluster
```

**⏱️ Time:** ~2-3 minutes

---

#### Step 2: Install KEDA

```bash
kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml
```

**Expected Output:**
```
namespace/keda serverside-applied
customresourcedefinition.apiextensions.k8s.io/scaledobjects.keda.sh serverside-applied
deployment.apps/keda-operator serverside-applied
...
```

---

#### Step 3: Wait for KEDA

```bash
kubectl wait --for=condition=ready pod -l app=keda-operator -n keda --timeout=120s
```

**Expected Output:**
```
pod/keda-operator-xxxxxxxxxx-xxxxx condition met
```

**⏱️ Time:** ~1-2 minutes

---

#### Step 4: Build Docker Image

```bash
cd /home/psw/Projects/Greenscale
docker build -t greenscale-worker:latest .
```

**Expected Output:**
```
[+] Building 45.2s (10/10) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [1/5] FROM python:3.9-slim
 => [2/5] WORKDIR /app
 => [3/5] COPY requirements.txt .
 => [4/5] RUN pip install --no-cache-dir -r requirements.txt
 => [5/5] COPY src/worker.py .
 => exporting to image
 => => naming to docker.io/library/greenscale-worker:latest
```

---

#### Step 5: Load Image into Minikube

```bash
minikube image load greenscale-worker:latest
```

**⏱️ Time:** ~30 seconds

---

#### Step 6: Deploy Kubernetes Resources

```bash
kubectl apply -f k8s/
```

**Expected Output:**
```
namespace/greenscale-system created
deployment.apps/redis created
service/redis-service created
deployment.apps/greenscale-worker created
scaledobject.keda.sh/greenscale-scaler created
```

---

#### Step 7: Create API Secret

```bash
kubectl create secret generic neysa-secret \
  --from-literal=NEYSA_API_KEY=your-api-key-here \
  --from-literal=NEYSA_API_URL=https://boomai-llama.neysa.io/v1/chat/completions \
  -n greenscale-system --dry-run=client -o yaml | kubectl apply -f -
```

> 💡 **Tip:** Replace `your-api-key-here` with your actual Neysa API key from `.env` file

---

#### Step 8: Verify Deployment

```bash
kubectl get all -n greenscale-system
```

**Expected Output:**
```
NAME                         READY   STATUS    RESTARTS   AGE
pod/redis-xxxxxxxxxx-xxxxx   1/1     Running   0          30s

NAME                    TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
service/redis-service   ClusterIP   10.96.xxx.xxx   <none>        6379/TCP   30s

NAME                                READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/redis               1/1     1            1           30s
deployment.apps/greenscale-worker   0/0     0            0           30s  ← Scale-to-Zero!
```

```bash
kubectl get scaledobject -n greenscale-system
```

**Expected Output:**
```
NAME                SCALETARGETKIND      SCALETARGETNAME     MIN   MAX   TRIGGERS   AGE
greenscale-scaler   apps/v1.Deployment   greenscale-worker   0     5     redis      30s
```

---

#### Step 9: Port Forward Redis

> ⚠️ **Important:** Run this in a **separate terminal** and keep it running!

```bash
kubectl port-forward svc/redis-service -n greenscale-system 6379:6379
```

**Expected Output:**
```
Forwarding from 127.0.0.1:6379 -> 6379
Forwarding from [::1]:6379 -> 6379
```

---

#### Step 10: Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

#### Step 11: Run Streamlit Dashboard

```bash
streamlit run src/app.py
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

🎉 **Open http://localhost:8501 in your browser!**

---

### 🔄 One-Click Deployment Script

For convenience, use the automated script:

```bash
cd /home/psw/Projects/Greenscale
./scripts/run-greenscale.sh
```

This script runs all steps automatically and manages background processes.

---

## Option B: Local Development with Docker Compose

### 🎯 What You Get

- ✅ Quick setup (~2 minutes)
- ✅ Test UI and job submission
- ✅ Redis queue functionality
- ❌ No KEDA autoscaling
- ❌ No Scale-to-Zero demonstration

### 📊 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCKER COMPOSE                              │
│                                                                 │
│  ┌─────────────┐              ┌─────────────┐                  │
│  │   Redis     │◄─────────────│   Worker    │                  │
│  │  (Queue)    │              │ (Optional)  │                  │
│  │  :6379      │              │             │                  │
│  └──────┬──────┘              └─────────────┘                  │
│         │                                                       │
└─────────┼───────────────────────────────────────────────────────┘
          │ localhost:6379
          │
 ┌────────▼────────┐
 │   Streamlit     │
 │   Dashboard     │
 │  localhost:8501 │
 └─────────────────┘
```

### 🚀 Step-by-Step Instructions

#### Step 1: Navigate to Project

```bash
cd /home/psw/Projects/Greenscale
```

---

#### Step 2: Setup Environment File

```bash
cp .env.example .env
```

---

#### Step 3: Edit Environment Variables

```bash
nano .env
```

Update the following values:
```dotenv
REDIS_HOST=localhost
REDIS_PORT=6379
NEYSA_API_URL=https://boomai-llama.neysa.io/v1/chat/completions
NEYSA_API_KEY=your-actual-api-key-here
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

---

#### Step 4: Start Redis Container

```bash
docker-compose up -d redis
```

**Expected Output:**
```
[+] Running 2/2
 ✔ Network greenscale_default  Created
 ✔ Container greenscale-redis-1  Started
```

---

#### Step 5: Verify Redis is Running

```bash
docker-compose ps
```

**Expected Output:**
```
NAME                  IMAGE         STATUS          PORTS
greenscale-redis-1    redis:7-alpine   Up 10 seconds   0.0.0.0:6379->6379/tcp
```

---

#### Step 6: Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

#### Step 7: Run Streamlit Dashboard

```bash
streamlit run src/app.py
```

🎉 **Open http://localhost:8501 in your browser!**

---

#### Step 8: (Optional) Start Worker Container

If you want to process jobs locally:

```bash
docker-compose up -d worker
```

---

### 🛑 Stopping Option B

```bash
docker-compose down
```

---

## Quick Reference Commands

### Option A: Kubernetes

| Action | Command |
|--------|---------|
| Start everything | `./scripts/run-greenscale.sh` |
| Check pods | `kubectl get pods -n greenscale-system` |
| Watch scaling | `kubectl get pods -n greenscale-system -w` |
| View worker logs | `kubectl logs -n greenscale-system -l app=greenscale-worker -f` |
| Check queue | `kubectl exec -it -n greenscale-system deploy/redis -- redis-cli LLEN jobs` |
| Stop Minikube | `minikube stop` |
| Delete everything | `minikube delete` |

### Option B: Docker Compose

| Action | Command |
|--------|---------|
| Start Redis | `docker-compose up -d redis` |
| Start all | `docker-compose up -d` |
| View logs | `docker-compose logs -f` |
| Stop all | `docker-compose down` |
| Check Redis | `docker exec -it greenscale-redis-1 redis-cli ping` |

---

## Troubleshooting

### Common Issues

#### 1. "Connection refused" on Redis

**Symptoms:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Solution (Option A):**
```bash
# Make sure port-forward is running
kubectl port-forward svc/redis-service -n greenscale-system 6379:6379
```

**Solution (Option B):**
```bash
# Make sure Redis container is running
docker-compose up -d redis
```

---

#### 2. Worker pods not scaling up

**Symptoms:** Queue has jobs but worker stays at 0 replicas

**Solution:**
```bash
# Check KEDA operator
kubectl get pods -n keda
kubectl logs -n keda -l app=keda-operator

# Check ScaledObject
kubectl describe scaledobject greenscale-scaler -n greenscale-system
```

---

#### 3. Image not found in Minikube

**Symptoms:**
```
ErrImagePull or ImagePullBackOff
```

**Solution:**
```bash
# Rebuild and reload image
docker build -t greenscale-worker:latest .
minikube image load greenscale-worker:latest

# Restart deployment
kubectl rollout restart deployment/greenscale-worker -n greenscale-system
```

---

#### 4. Minikube out of memory

**Symptoms:** Pods stuck in Pending state

**Solution:**
```bash
# Delete and restart with more memory
minikube delete
minikube start --driver=docker --memory=6144
```

---

#### 5. Port 6379 already in use

**Symptoms:**
```
Unable to listen on port 6379
```

**Solution:**
```bash
# Find and kill process using port
sudo lsof -i :6379
sudo kill -9 <PID>

# Or use different port
kubectl port-forward svc/redis-service -n greenscale-system 6380:6379
# Update REDIS_PORT in .env to 6380
```

---

### Getting Help

1. Check logs:
   ```bash
   # Option A
   kubectl logs -n greenscale-system -l app=greenscale-worker
   
   # Option B
   docker-compose logs worker
   ```

2. View dashboard errors in browser console (F12)

3. Refer to [UI_METRICS_GUIDE.md](UI_METRICS_GUIDE.md) for metric explanations

---

## 📚 Related Documentation

| Document | Description |
|----------|-------------|
| [README.md](../README.md) | Project overview and quick start |
| [SETUP_AND_RUN_GUIDE.md](SETUP_AND_RUN_GUIDE.md) | Original setup guide |
| [UI_METRICS_GUIDE.md](UI_METRICS_GUIDE.md) | Dashboard metrics explanation |
| [INSTRUCTIONS.md](INSTRUCTIONS.md) | Quick reference |

---

*This document is part of the GreenScale project for AIBoomi Hackathon 2026.*
