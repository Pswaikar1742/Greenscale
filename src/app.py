import os
import redis
import json
from dotenv import load_dotenv
import streamlit as st
import uuid
import time
import zipfile
import io

# Load environment variables from .env file
load_dotenv()

# Load Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Streamlit app configuration
st.set_page_config(page_title="🟢 GreenScale Dashboard", layout="wide", initial_sidebar_state="expanded")

# Main title
st.title("🟢 GreenScale Dashboard")

# Subheader
st.subheader("Intelligent Autoscaler for AI/ML Workloads on Kubernetes")

# Introductory markdown text
st.markdown(
    """
    GreenScale enables **Scale-to-Zero** functionality to eliminate the cost of idle GPUs.
    Submit prompts below, and our KEDA-powered autoscaler will automatically scale Kubernetes workers
    to process your jobs efficiently, then scale back down when done.
    """
)

# Display real-time key metrics
try:
    # Fetch metrics from Redis
    queue_length = redis_client.llen("jobs")
    active_workers = 1 if queue_length > 0 else 0  # Placeholder logic for active workers
    estimated_savings = "$4.25/hr"  # Placeholder value for estimated savings

    # Create a 3-column layout
    col1, col2, col3 = st.columns(3)

    # Display metrics in columns
    with col1:
        st.metric("📊 Jobs in Queue", queue_length)
    with col2:
        st.metric("⚡ Active Workers", active_workers)
    with col3:
        st.metric("💰 Estimated Savings", estimated_savings, "+$0.25")

except redis.ConnectionError:
    st.error("Failed to connect to Redis. Please check your connection settings.")
except Exception as e:
    st.error(f"An error occurred while fetching metrics: {str(e)}")

# Section for job submission
st.subheader("📝 Submit a New Job")

# Text input for the user's prompt
user_prompt = st.text_area(
    label="Enter your prompt:",
    placeholder="Ask me anything! E.g., 'What is the capital of France?'",
    height=100
)

# Submit button
if st.button("✅ Submit Job to Queue", use_container_width=True):
    if not user_prompt.strip():
        st.warning("Please enter a prompt before submitting.")
    else:
        try:
            # Generate a unique Job ID
            job_id = str(uuid.uuid4())
            job_payload = {
                "job_id": job_id,
                "prompt": user_prompt.strip()
            }
            # Push the job to the Redis 'jobs' list
            redis_client.lpush("jobs", json.dumps(job_payload))

            # Store the job ID in session state for tracking
            st.session_state['active_job_id'] = job_id

            # Show success message
            st.success(f"✨ Job submitted successfully! Job ID: `{job_id}`")

            # Refresh the dashboard
            st.rerun()
        except Exception as e:
            st.error(f"Failed to submit job: {str(e)}")

# Real-time polling for job results
if 'active_job_id' in st.session_state:
    job_id = st.session_state['active_job_id']
    with st.spinner("KEDA is waking up the AI worker... Please wait."):
        result = None
        for _ in range(60):  # Poll for up to 60 seconds
            try:
                result_key = f"result:{job_id}"
                result = redis_client.get(result_key)
                if result:
                    # Display the result
                    st.info(f"🎉 Job completed! Result: {result}")

                    # Clear the active job ID from session state
                    del st.session_state['active_job_id']

                    # Refresh the dashboard
                    st.rerun()
                time.sleep(1)  # Wait for 1 second before polling again
            except Exception as e:
                st.error(f"An error occurred while polling for results: {str(e)}")
                break
        else:
            # Timeout occurred
            st.error("⏳ Job timed out. Please try again later.")
            del st.session_state['active_job_id']

# ============================================================================
# HELM CHART GENERATOR
# ============================================================================
st.divider()
st.subheader("📦 Helm Chart Generator")
st.markdown("Generate a customized Helm chart for deploying GreenScale to any Kubernetes cluster.")

with st.expander("⚙️ Configure Helm Chart", expanded=False):
    col1, col2 = st.columns(2)
    
    with col1:
        chart_name = st.text_input("Chart Name", value="greenscale")
        namespace = st.text_input("Namespace", value="greenscale-system")
        image_repo = st.text_input("Worker Image Repository", value="greenscale-worker")
        image_tag = st.text_input("Image Tag", value="latest")
        
    with col2:
        min_replicas = st.number_input("Min Replicas (Scale-to-Zero)", min_value=0, max_value=10, value=0)
        max_replicas = st.number_input("Max Replicas", min_value=1, max_value=100, value=5)
        cooldown = st.number_input("Cooldown Period (seconds)", min_value=10, max_value=600, value=30)
        polling_interval = st.number_input("Polling Interval (seconds)", min_value=1, max_value=60, value=5)
    
    st.subheader("Resource Limits")
    col3, col4 = st.columns(2)
    with col3:
        memory_request = st.text_input("Memory Request", value="256Mi")
        cpu_request = st.text_input("CPU Request", value="100m")
    with col4:
        memory_limit = st.text_input("Memory Limit", value="512Mi")
        cpu_limit = st.text_input("CPU Limit", value="500m")

# Generate Helm Chart Templates
def generate_chart_yaml(name):
    return f"""apiVersion: v2
name: {name}
description: GreenScale - Intelligent Scale-to-Zero Autoscaler for AI/ML Workloads
type: application
version: 1.0.0
appVersion: "1.0.0"
keywords:
  - kubernetes
  - keda
  - autoscaling
  - ai
  - ml
  - scale-to-zero
maintainers:
  - name: GreenScale Team
    email: team@greenscale.io
"""

def generate_values_yaml(config):
    return f"""# GreenScale Helm Chart Values
# Generated by GreenScale Dashboard

replicaCount: {config['min_replicas']}

image:
  repository: {config['image_repo']}
  tag: {config['image_tag']}
  pullPolicy: IfNotPresent

namespace: {config['namespace']}

redis:
  enabled: true
  image: redis:7-alpine
  port: 6379
  serviceName: redis-service

worker:
  resources:
    requests:
      memory: {config['memory_request']}
      cpu: {config['cpu_request']}
    limits:
      memory: {config['memory_limit']}
      cpu: {config['cpu_limit']}

keda:
  enabled: true
  minReplicaCount: {config['min_replicas']}
  maxReplicaCount: {config['max_replicas']}
  cooldownPeriod: {config['cooldown']}
  pollingInterval: {config['polling_interval']}
  trigger:
    type: redis
    listName: jobs
    listLength: "1"

secrets:
  # Base64 encoded API key (replace with your own)
  neysaApiKey: ""
  neysaApiUrl: "https://boomai-llama.neysa.io/v1/chat/completions"
"""

def generate_deployment_yaml():
    return """apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-worker
  namespace: {{ .Values.namespace }}
  labels:
    app: greenscale-worker
    chart: {{ .Chart.Name }}-{{ .Chart.Version }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: greenscale-worker
  template:
    metadata:
      labels:
        app: greenscale-worker
    spec:
      containers:
        - name: worker
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          env:
            - name: NEYSA_API_KEY
              valueFrom:
                secretKeyRef:
                  name: {{ .Release.Name }}-secret
                  key: NEYSA_API_KEY
            - name: NEYSA_API_URL
              valueFrom:
                secretKeyRef:
                  name: {{ .Release.Name }}-secret
                  key: NEYSA_API_URL
            - name: REDIS_HOST
              value: "{{ .Values.redis.serviceName }}"
            - name: REDIS_PORT
              value: "{{ .Values.redis.port }}"
          resources:
            requests:
              memory: {{ .Values.worker.resources.requests.memory }}
              cpu: {{ .Values.worker.resources.requests.cpu }}
            limits:
              memory: {{ .Values.worker.resources.limits.memory }}
              cpu: {{ .Values.worker.resources.limits.cpu }}
      restartPolicy: Always
"""

def generate_redis_yaml():
    return """{{- if .Values.redis.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: {{ .Values.namespace }}
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
          image: {{ .Values.redis.image }}
          ports:
            - containerPort: {{ .Values.redis.port }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ .Values.redis.serviceName }}
  namespace: {{ .Values.namespace }}
spec:
  selector:
    app: redis
  ports:
    - port: {{ .Values.redis.port }}
      targetPort: {{ .Values.redis.port }}
{{- end }}
"""

def generate_scaledobject_yaml():
    return """{{- if .Values.keda.enabled }}
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: {{ .Release.Name }}-scaler
  namespace: {{ .Values.namespace }}
spec:
  scaleTargetRef:
    name: {{ .Release.Name }}-worker
  minReplicaCount: {{ .Values.keda.minReplicaCount }}
  maxReplicaCount: {{ .Values.keda.maxReplicaCount }}
  cooldownPeriod: {{ .Values.keda.cooldownPeriod }}
  pollingInterval: {{ .Values.keda.pollingInterval }}
  triggers:
    - type: {{ .Values.keda.trigger.type }}
      metadata:
        address: {{ .Values.redis.serviceName }}.{{ .Values.namespace }}.svc.cluster.local:{{ .Values.redis.port }}
        listName: {{ .Values.keda.trigger.listName }}
        listLength: {{ .Values.keda.trigger.listLength | quote }}
        enableTLS: "false"
{{- end }}
"""

def generate_secret_yaml():
    return """apiVersion: v1
kind: Secret
metadata:
  name: {{ .Release.Name }}-secret
  namespace: {{ .Values.namespace }}
type: Opaque
data:
  NEYSA_API_KEY: {{ .Values.secrets.neysaApiKey | b64enc }}
  NEYSA_API_URL: {{ .Values.secrets.neysaApiUrl | b64enc }}
"""

def generate_namespace_yaml():
    return """apiVersion: v1
kind: Namespace
metadata:
  name: {{ .Values.namespace }}
"""

def generate_notes_txt():
    return """
🌱 GreenScale has been deployed!

1. Get the application status:
   kubectl get pods -n {{ .Values.namespace }}

2. Watch autoscaling in action:
   kubectl get pods -n {{ .Values.namespace }} -w

3. Submit a test job:
   kubectl exec -n {{ .Values.namespace }} deployment/redis -- \\
     redis-cli LPUSH jobs '{"job_id":"test","prompt":"Hello!"}'

4. Check KEDA ScaledObject:
   kubectl get scaledobject -n {{ .Values.namespace }}

📊 Monitor your Scale-to-Zero savings!
"""

def generate_helpers_tpl():
    return """{{/*
Common labels
*/}}
{{- define "greenscale.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
"""

# Generate and Download Button
if st.button("🚀 Generate Helm Chart", use_container_width=True):
    config = {
        'name': chart_name,
        'namespace': namespace,
        'image_repo': image_repo,
        'image_tag': image_tag,
        'min_replicas': min_replicas,
        'max_replicas': max_replicas,
        'cooldown': cooldown,
        'polling_interval': polling_interval,
        'memory_request': memory_request,
        'cpu_request': cpu_request,
        'memory_limit': memory_limit,
        'cpu_limit': cpu_limit,
    }
    
    # Create ZIP file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Chart.yaml
        zf.writestr(f"{chart_name}/Chart.yaml", generate_chart_yaml(chart_name))
        # values.yaml
        zf.writestr(f"{chart_name}/values.yaml", generate_values_yaml(config))
        # templates/
        zf.writestr(f"{chart_name}/templates/deployment.yaml", generate_deployment_yaml())
        zf.writestr(f"{chart_name}/templates/redis.yaml", generate_redis_yaml())
        zf.writestr(f"{chart_name}/templates/scaledobject.yaml", generate_scaledobject_yaml())
        zf.writestr(f"{chart_name}/templates/secret.yaml", generate_secret_yaml())
        zf.writestr(f"{chart_name}/templates/namespace.yaml", generate_namespace_yaml())
        zf.writestr(f"{chart_name}/templates/NOTES.txt", generate_notes_txt())
        zf.writestr(f"{chart_name}/templates/_helpers.tpl", generate_helpers_tpl())
    
    zip_buffer.seek(0)
    
    st.success("✅ Helm chart generated successfully!")
    
    st.download_button(
        label="📥 Download Helm Chart (.zip)",
        data=zip_buffer,
        file_name=f"{chart_name}-helm-chart.zip",
        mime="application/zip",
        use_container_width=True
    )
    
    # Show preview
    with st.expander("👀 Preview Generated Files"):
        tab1, tab2, tab3, tab4 = st.tabs(["Chart.yaml", "values.yaml", "deployment.yaml", "scaledobject.yaml"])
        
        with tab1:
            st.code(generate_chart_yaml(chart_name), language="yaml")
        with tab2:
            st.code(generate_values_yaml(config), language="yaml")
        with tab3:
            st.code(generate_deployment_yaml(), language="yaml")
        with tab4:
            st.code(generate_scaledobject_yaml(), language="yaml")
    
    st.info("""
    **To deploy:**
    ```bash
    unzip greenscale-helm-chart.zip
    helm install greenscale ./greenscale -n greenscale-system --create-namespace
    ```
    """)

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        🌱 GreenScale v1.0 | Built for AIBoomi Hackathon 2026 | 
        <a href='https://github.com/Pswaikar1742/Greenscale' target='_blank'>GitHub</a>
    </div>
    """,
    unsafe_allow_html=True
)
