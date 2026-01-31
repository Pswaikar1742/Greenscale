#!/bin/bash

# GreenScale Infrastructure Test Script
# Pushes a JSON job directly to the Redis queue inside Kubernetes.

NAMESPACE="greenscale-system"
JOB_ID=$(uuidgen)
PROMPT="Write a short story about a Kubernetes pod that dreams of scaling to zero."

echo "--- GreenScale E2E Test ---"
echo "▶️  Watching for pod changes in namespace: $NAMESPACE"

# Start watching in the background
kubectl get pods -n $NAMESPACE -w &
WATCH_PID=$!

echo "▶️  Pushing test job to Redis..."
echo "   Job ID: $JOB_ID"
echo "   Prompt: '$PROMPT'"

# Construct the JSON payload
JSON_PAYLOAD="{\"job_id\": \"$JOB_ID\", \"prompt\": \"$PROMPT\"}"

# Find the Redis pod and execute the lpush command
REDIS_POD=$(kubectl get pods -n $NAMESPACE -l app=redis -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli lpush jobs "$JSON_PAYLOAD"

echo "✅ Job Pushed. KEDA should now trigger a scale-up."
echo "👀 Waiting for worker pod to start and finish..."

# Give it some time to process
sleep 45

echo "▶️  Checking for result in Redis..."
RESULT=$(kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli get "result:$JOB_ID")

if [ -z "$RESULT" ]; then
    echo "❌ TEST FAILED: No result found in Redis for Job ID $JOB_ID."
else
    echo "✅ TEST PASSED! Worker responded:"
    echo "---------------------------------"
    echo "$RESULT"
    echo "---------------------------------"
fi

# Cleanup the background watch process
kill $WATCH_PID 2>/dev/null
echo "--- Test Complete ---"

