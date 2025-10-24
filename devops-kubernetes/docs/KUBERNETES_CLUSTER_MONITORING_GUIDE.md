# Kubernetes Cluster Monitoring Guide

This guide allows you to **monitor and track all resources, pods, test executions, and system statuses** in your Kubernetes cluster.

## What Can Be Monitored?

### Test Execution Monitoring
- Test results and execution statuses
- Test distribution (which test ran on which node)
- Test execution times
- Pass/Fail ratios and success rate

### Pod and Container Monitoring
- Pod statuses (Running, Completed, Failed)
- Container logs and error messages
- Resource usage (CPU, Memory)
- Pod lifecycle events

### Network Monitoring
- Service discovery and endpoints
- Inter-pod communication
- Service routing and load balancing

### Cluster Health Monitoring
- Node statuses and resource capacity
- Kubernetes events
- Job execution status
- Namespace resource usage

---

## 1. Test Controller Monitoring (Test Results)

### All test controller logs:
```bash
kubectl logs -n test-automation -l app=test-controller
```

### Show last 100 lines:
```bash
kubectl logs -n test-automation -l app=test-controller --tail=100
```

### Live log tracking (follow):
```bash
kubectl logs -n test-automation -l app=test-controller -f
```

### Specific pod logs:
```bash
# Find pod name
kubectl get pods -n test-automation -l app=test-controller

# Show pod logs
kubectl logs -n test-automation test-controller-job-xxxxx
```

### Auto-find pod and show logs:
```bash
kubectl logs -n test-automation $(kubectl get pods -n test-automation -l app=test-controller -o name | head -1)
```

---

## 2. Chrome Node Monitoring (Selenium Logs)

### All Chrome node logs:
```bash
kubectl logs -n test-automation -l app=chrome-node --all-containers
```

### Specific Chrome node logs:
```bash
# List pod names
kubectl get pods -n test-automation -l app=chrome-node

# Show specific pod logs
kubectl logs -n test-automation chrome-node-xxxxx-xxxxx
```

### Show last 50 lines:
```bash
kubectl logs -n test-automation chrome-node-xxxxx-xxxxx --tail=50
```

### Live Chrome node monitoring:
```bash
kubectl logs -n test-automation chrome-node-xxxxx-xxxxx -f
```

---

## 3. Test Distribution Monitoring (Which Test on Which Node?)

### WORKING COMMAND: Show test execution logs
```bash
kubectl logs -n test-automation -l app=test-controller | grep "Executing test"
```

**Example Output:**
```
Executing test 'Homepage Check' on chrome-node-5448bfbfd5-frl99
Executing test 'Careers Page Check' on chrome-node-5448bfbfd5-hslf8
Executing test 'QA Jobs Filtering' on chrome-node-5448bfbfd5-frl99
Executing test 'Job Details Verification' on chrome-node-5448bfbfd5-hslf8
Executing test 'Lever Redirection' on chrome-node-5448bfbfd5-frl99
```

### Alternative: View full controller log
```bash
# Show full controller log - test distribution is visible here
kubectl logs -n test-automation -l app=test-controller
```

---

### Test execution summary:
```bash
kubectl logs -n test-automation -l app=test-controller | grep -A 15 "TEST EXECUTION SUMMARY"
```

**Example Output:**
```
TEST EXECUTION SUMMARY
================================================================================
[PASS] Homepage Check: PASSED (5.82s)
[PASS] Careers Page Check: PASSED (5.71s)
[PASS] QA Jobs Filtering: PASSED (3.37s)
[PASS] Job Details Verification: PASSED (3.31s)
[PASS] Lever Redirection: PASSED (3.37s)
--------------------------------------------------------------------------------
Total Tests: 5
Passed: 5
Failed: 0
Errors: 0
Success Rate: 100.0%
================================================================================
```

### JSON test results:
```bash
# Connect to controller pod
kubectl exec -n test-automation -it $(kubectl get pods -n test-automation -l app=test-controller -o name | head -1) -- sh

# Read result file
cat /app/test_results/results_*.json | jq .
```

---

## 4. Pod Status Monitoring

### List all pods:
```bash
kubectl get pods -n test-automation
```

**Example Output:**
```
NAME                           READY   STATUS      RESTARTS   AGE
chrome-node-5448bfbfd5-frl99   1/1     Running     0          5m
chrome-node-5448bfbfd5-hslf8   1/1     Running     0          5m
test-controller-job-2lrk8      0/1     Completed   0          5m
```

### Show pod details:
```bash
kubectl describe pod -n test-automation test-controller-job-xxxxx
```

### Pod IP addresses and node placement:
```bash
kubectl get pods -n test-automation -o wide
```

**Example Output:**
```
NAME                           IP              NODE
chrome-node-5448bfbfd5-frl99   192.168.33.144  ip-192-168-40-19.eu-west-1
chrome-node-5448bfbfd5-hslf8   192.168.51.36   ip-192-168-40-19.eu-west-1
```

### Pod health check:
```bash
# Pod readiness and liveness status
kubectl get pods -n test-automation -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'
```

---

## 5. Job Execution Monitoring

### List jobs:
```bash
kubectl get jobs -n test-automation
```

**Example Output:**
```
NAME                  COMPLETIONS   DURATION   AGE
test-controller-job   1/1           43s        5m
```

### Show job details:
```bash
kubectl describe job -n test-automation test-controller-job
```

### Job execution history:
```bash
kubectl get jobs -n test-automation --sort-by=.status.startTime
```

---

## 6. Service and Network Monitoring

### List services:
```bash
kubectl get services -n test-automation
```

### Show service details:
```bash
kubectl describe service -n test-automation chrome-node-service
```

### Endpoint monitoring (which pods are connected to service):
```bash
kubectl get endpoints -n test-automation chrome-node-service
```

### Service connectivity test:
```bash
# Test access to Chrome service from controller pod
kubectl exec -n test-automation -it $(kubectl get pods -n test-automation -l app=test-controller -o name | head -1) -- curl chrome-node-service:4444/wd/hub/status
```

---

## 7. Resource Usage Monitoring

### Pod resource usage:
```bash
kubectl top pods -n test-automation
```

**Example Output:**
```
NAME                           CPU(cores)   MEMORY(bytes)
chrome-node-5448bfbfd5-frl99   50m          400Mi
chrome-node-5448bfbfd5-hslf8   45m          380Mi
```

### Node resource usage:
```bash
kubectl top nodes
```

### Namespace resource quotas:
```bash
kubectl describe quota -n test-automation
```

### Resource limits and requests:
```bash
kubectl get pods -n test-automation -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources}{"\n"}{end}'
```

---

## 8. Real-Time Monitoring

### Watch pod status live:
```bash
kubectl get pods -n test-automation --watch
```

### List all resources:
```bash
kubectl get all -n test-automation
```

### Event monitoring:
```bash
kubectl get events -n test-automation --sort-by='.lastTimestamp'
```

### Real-time event watching:
```bash
kubectl get events -n test-automation --watch
```

### Multi-resource monitoring:
```bash
watch -n 2 'kubectl get pods,jobs,services -n test-automation'
```

---

## 9. Debugging and Troubleshooting

### Enter pod:
```bash
# Enter Chrome node
kubectl exec -n test-automation -it chrome-node-xxxxx-xxxxx -- /bin/bash

# Enter controller (won't work if completed)
kubectl exec -n test-automation -it test-controller-job-xxxxx -- /bin/sh
```

### Selenium Hub Status monitoring:
```bash
# Get pod IP
POD_IP=$(kubectl get pod -n test-automation chrome-node-xxxxx-xxxxx -o jsonpath='{.status.podIP}')

# Status check
curl http://$POD_IP:4444/wd/hub/status | jq .
```

### Container logs (previous):
```bash
# Show previous logs of crashed pod
kubectl logs -n test-automation chrome-node-xxxxx-xxxxx --previous
```

### Pod restart monitoring:
```bash
# Check restart count
kubectl get pods -n test-automation -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[*].restartCount}{"\n"}{end}'
```

---

## 10. Quick Summary Commands

### Quickly show test results:
```bash
kubectl logs -n test-automation -l app=test-controller | grep "\[PASS\]\|\[FAIL\]"
```

### Which test on which node (WORKING):
```bash
kubectl logs -n test-automation -l app=test-controller | grep "Executing test"
```

### Test summary (WORKING):
```bash
kubectl logs -n test-automation -l app=test-controller | grep -A 15 "TEST EXECUTION SUMMARY"
```

### Total test time:
```bash
kubectl logs -n test-automation -l app=test-controller | grep "Total Tests\|Passed:\|Failed:\|Success Rate"
```

### Session monitoring (per node):
```bash
# Node 1
kubectl logs -n test-automation chrome-node-xxxxx-xxxxx | grep "Session created"

# How many sessions created
kubectl logs -n test-automation chrome-node-xxxxx-xxxxx | grep "Session created" | wc -l
```

### Failed tests monitoring:
```bash
kubectl logs -n test-automation -l app=test-controller | grep "\[FAIL\]"
```

### Test execution times:
```bash
kubectl logs -n test-automation -l app=test-controller | grep -E "PASSED \([0-9]|FAILED \([0-9]"
```

### Count sessions per node (WORKING):
```bash
for pod in $(kubectl get pods -n test-automation -l app=chrome-node -o name | cut -d'/' -f2); do
  echo "=== $pod ==="
  SESSION_COUNT=$(kubectl logs -n test-automation $pod 2>/dev/null | grep -i "session.*created" | wc -l)
  echo "Sessions: $SESSION_COUNT"
done
```

---

## 11. Cluster Health Monitoring

### Cluster info:
```bash
kubectl cluster-info
```

### Cluster nodes:
```bash
kubectl get nodes -o wide
```

### Node conditions:
```bash
kubectl describe nodes | grep -A 5 "Conditions:"
```

### Namespace status:
```bash
kubectl get namespace test-automation -o yaml
```

### API server health:
```bash
kubectl get --raw /healthz
kubectl get --raw /readyz
```

---

## 12. PowerShell/Windows Commands (via WSL)

```powershell
# Test controller logs (full)
wsl -e bash -c "ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP 'kubectl logs -n test-automation -l app=test-controller'"

# Which test on which node (WORKING)
wsl -e bash -c "ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP 'kubectl logs -n test-automation -l app=test-controller | grep \"Executing test\"'"

# Test summary (WORKING)
wsl -e bash -c "ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP 'kubectl logs -n test-automation -l app=test-controller | grep -A 15 \"TEST EXECUTION SUMMARY\"'"

# Pod statuses
wsl -e bash -c "ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP 'kubectl get pods -n test-automation -o wide'"

# Real-time monitoring
wsl -e bash -c "ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP 'kubectl get pods -n test-automation --watch'"
```

---

## 13. Summary Table - WORKING COMMANDS

| What to Monitor | Command |
|------------------|-------|
| **Test results (full)** | `kubectl logs -n test-automation -l app=test-controller` |
| **Test distribution** | `kubectl logs -n test-automation -l app=test-controller \| grep "Executing test"` |
| **Test summary** | `kubectl logs -n test-automation -l app=test-controller \| grep -A 15 "TEST EXECUTION SUMMARY"` |
| **Pod statuses** | `kubectl get pods -n test-automation` |
| **Pod details** | `kubectl get pods -n test-automation -o wide` |
| **Chrome logs** | `kubectl logs -n test-automation <chrome-pod-name>` |
| **Job status** | `kubectl get jobs -n test-automation` |
| **Resource usage** | `kubectl top pods -n test-automation` |
| **Service status** | `kubectl get services -n test-automation` |
| **Service endpoints** | `kubectl get endpoints -n test-automation chrome-node-service` |
| **Events** | `kubectl get events -n test-automation --sort-by='.lastTimestamp'` |
| **Live monitoring** | `kubectl get pods -n test-automation --watch` |
| **Cluster health** | `kubectl cluster-info` |
| **Node status** | `kubectl get nodes` |
| **All resources** | `kubectl get all -n test-automation` |

---

## 14. Monitoring Best Practices

### 1. Regular Health Checks
```bash
# Daily cluster health check
kubectl get nodes
kubectl get pods -n test-automation
kubectl top nodes
```

### 2. Log Retention
```bash
# Save important logs
kubectl logs -n test-automation -l app=test-controller > test-results-$(date +%Y%m%d).log
```

### 3. Resource Monitoring
```bash
# Resource usage trends
watch -n 5 'kubectl top pods -n test-automation'
```

### 4. Event Tracking
```bash
# Save events from last hour
kubectl get events -n test-automation --sort-by='.lastTimestamp' | head -50 > events-$(date +%Y%m%d-%H%M).log
```

### 5. Automated Alerts
```bash
# Check for failed tests
if kubectl logs -n test-automation -l app=test-controller | grep -q "FAILED"; then
    echo "Test failure detected!"
    # Send alert
fi
```