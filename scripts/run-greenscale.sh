#!/bin/bash

# ============================================================================
# 🌱 GreenScale - One-Click Deployment Script
# ============================================================================
# This script sets up and runs the complete GreenScale infrastructure
# Author: Prathmesh (Platform Engineer)
# Date: January 31, 2026
# ============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# PID file to track background processes
PID_FILE="$PROJECT_ROOT/.greenscale_pids"

# ============================================================================
# Helper Functions
# ============================================================================

print_banner() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║   🌱 GreenScale - Scale-to-Zero AI/ML Autoscaler              ║"
    echo "║                                                               ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

log_step() {
    echo -e "\n${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}▶ STEP $1: $2${NC}"
    echo -e "${PURPLE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
    log_success "$1 is available"
}

cleanup() {
    log_warning "Cleaning up background processes..."
    if [ -f "$PID_FILE" ]; then
        while read pid; do
            if kill -0 $pid 2>/dev/null; then
                kill $pid 2>/dev/null || true
                log_info "Stopped process $pid"
            fi
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    log_success "Cleanup complete"
}

# Trap for cleanup on script exit
trap cleanup EXIT

# ============================================================================
# Main Script
# ============================================================================

print_banner

cd "$PROJECT_ROOT"
log_info "Working directory: $PROJECT_ROOT"

# ============================================================================
# Step 0: Setup Environment File
# ============================================================================
log_step "0" "Setting Up Environment Configuration"

if [ ! -f "$PROJECT_ROOT/.env" ]; then
    log_warning ".env file not found. Creating from template..."
    
    if [ -f "$PROJECT_ROOT/.env.example" ]; then
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        log_success ".env file created from .env.example"
    else
        log_info "Creating new .env file..."
        cat > "$PROJECT_ROOT/.env" << 'EOF'
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Neysa AI API Configuration
NEYSA_API_URL=https://boomai-llama.neysa.io/v1/chat/completions
NEYSA_API_KEY=your-api-key-here
EOF
        log_success ".env file created"
    fi
    
    echo ""
    log_info "Please enter your Neysa API Key (or press Enter to use default for testing):"
    read -p "API Key: " user_api_key
    
    if [ -n "$user_api_key" ]; then
        # Replace the API key in .env file
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s|NEYSA_API_KEY=.*|NEYSA_API_KEY=$user_api_key|" "$PROJECT_ROOT/.env"
        else
            # Linux
            sed -i "s|NEYSA_API_KEY=.*|NEYSA_API_KEY=$user_api_key|" "$PROJECT_ROOT/.env"
        fi
        log_success "API key configured in .env file"
    else
        log_warning "Using default API key (may have rate limits)"
    fi
    echo ""
else
    log_success ".env file already exists"
fi

# ============================================================================
# Step 1: Check Prerequisites
# ============================================================================
log_step "1" "Checking Prerequisites"

check_command docker
check_command minikube
check_command kubectl
check_command python3
check_command pip

# ============================================================================
# Step 2: Start Minikube
# ============================================================================
log_step "2" "Starting Minikube Cluster"

if minikube status | grep -q "Running"; then
    log_success "Minikube is already running"
else
    log_info "Starting Minikube with 4GB memory..."
    minikube start --driver=docker --memory=4096
    log_success "Minikube started successfully"
fi

# ============================================================================
# Step 3: Install KEDA
# ============================================================================
log_step "3" "Installing KEDA (Event-Driven Autoscaler)"

if kubectl get namespace keda &> /dev/null; then
    log_success "KEDA namespace exists"
else
    log_info "Installing KEDA v2.12.0..."
    kubectl apply --server-side -f https://github.com/kedacore/keda/releases/download/v2.12.0/keda-2.12.0.yaml
fi

log_info "Waiting for KEDA operator to be ready (this may take 1-2 minutes)..."
kubectl wait --for=condition=ready pod -l app=keda-operator -n keda --timeout=180s || {
    log_warning "KEDA operator taking longer than expected, continuing..."
}
log_success "KEDA is ready"

# ============================================================================
# Step 4: Build Docker Image
# ============================================================================
log_step "4" "Building Worker Docker Image"

log_info "Building greenscale-worker:latest..."
docker build -t greenscale-worker:latest "$PROJECT_ROOT"
log_success "Docker image built"

log_info "Loading image into Minikube..."
minikube image load greenscale-worker:latest
log_success "Image loaded into Minikube"

# ============================================================================
# Step 5: Deploy Kubernetes Resources
# ============================================================================
log_step "5" "Deploying Kubernetes Resources"

log_info "Applying K8s manifests from k8s/ directory..."
kubectl apply -f "$PROJECT_ROOT/k8s/"
log_success "K8s resources deployed"

# ============================================================================
# Step 6: Create API Secret
# ============================================================================
log_step "6" "Creating Neysa API Secret"

# Load environment from .env file
source "$PROJECT_ROOT/.env"
log_info "Loaded environment from .env file"

# Use environment variable or fallback
NEYSA_API_KEY="${NEYSA_API_KEY}"
NEYSA_API_URL="${NEYSA_API_URL:-https://boomai-llama.neysa.io/v1/chat/completions}"

kubectl create secret generic neysa-secret \
    --from-literal=NEYSA_API_KEY="$NEYSA_API_KEY" \
    --from-literal=NEYSA_API_URL="$NEYSA_API_URL" \
    -n greenscale-system --dry-run=client -o yaml | kubectl apply -f -
log_success "API secret created/updated"

# ============================================================================
# Step 6: Verify Deployment
# ============================================================================
log_ste7: Verify Deployment
# ============================================================================
log_step "7aiting for Redis to be ready..."
kubectl wait --for=condition=ready pod -l app=redis -n greenscale-system --timeout=120s
log_success "Redis is running"

log_info "Current resources in greenscale-system namespace:"
kubectl get all -n greenscale-system

log_info "KEDA ScaledObject status:"
kubectl get scaledobject -n greenscale-system

# ============================================================================
# Step 7: Start Port Forward (Background)
# ============================================================================
log_ste8: Start Port Forward (Background)
# ============================================================================
log_step "8existing port-forward on 6379
pkill -f "kubectl port-forward.*6379:6379" 2>/dev/null || true
sleep 1

log_info "Starting port-forward to Redis (background process)..."
kubectl port-forward svc/redis-service -n greenscale-system 6379:6379 &> /tmp/port-forward.log &
PORT_FORWARD_PID=$!
echo $PORT_FORWARD_PID >> "$PID_FILE"
sleep 3

# Verify port-forward is working
if kill -0 $PORT_FORWARD_PID 2>/dev/null; then
    log_success "Port-forward started (PID: $PORT_FORWARD_PID)"
else
    log_error "Port-forward failed to start. Check /tmp/port-forward.log"
    exit 1
fi

# ============================================================================
# Step 8: Install Python Dependencies
# ============================================================================
log_ste9: Install Python Dependencies
# ============================================================================
log_step "9nstalling requirements..."
pip install -r "$PROJECT_ROOT/requirements.txt" --quiet
log_success "Python dependencies installed"

# ============================================================================
# Step 9: Launch Streamlit Dashboard
# ============================================================================
log_ste10: Launch Streamlit Dashboard
# ============================================================================
log_step "10${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║   🚀 GreenScale is Ready!                                     ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║   Dashboard URL: ${CYAN}http://localhost:8501${GREEN}                      ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}║   Press Ctrl+C to stop all services                           ║${NC}"
echo -e "${GREEN}║                                                               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}\n"

log_info "Starting Streamlit dashboard..."
log_info "Port-forward logs: /tmp/port-forward.log"
echo ""

# Run Streamlit in foreground (this blocks until Ctrl+C)
streamlit run "$PROJECT_ROOT/src/app.py" --server.headless true

# Script will reach here when user presses Ctrl+C
log_info "Shutting down GreenScale..."
