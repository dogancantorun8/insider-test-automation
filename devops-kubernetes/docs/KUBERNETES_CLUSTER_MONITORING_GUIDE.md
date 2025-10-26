# Kubernetes Cluster Monitoring Guide

This guide helps you monitor test executions, pods, services, and cluster health in your Kubernetes environment.

## What Can Be Monitored?

**Test Execution**
- Test results and statuses
- Which pod executed each test (session tracking)
- Execution times and success rates
- Service-based load distribution

**Pod & Container**
- Pod statuses and logs
- Resource usage (CPU, Memory)
- Container lifecycle events

**Network & Services**
- Service endpoints and load balancing
- Service connectivity
- DNS resolution

**Cluster Health**
- Node statuses
- Kubernetes events
- Job execution status

---

## Test Controller Monitoring

**View all controller logs**
```bash
kubectl logs -n test-automation -l app=test-controller
```

**Live log following**
```bash
kubectl logs -n test-automation -l app=test-controller -f
```

**Last 100 lines**
```bash
kubectl logs -n test-automation -l app=test-controller --tail=100
```

**Test execution summary**
```bash
kubectl logs -n test-automation -l app=test-controller | grep -A 15 "TEST EXECUTION SUMMARY"
```

Example output:
```
TEST EXECUTION SUMMARY
================================================================================
[PASS] Ana Sayfa Kontrolu: PASSED (5.66s)
[PASS] Careers Sayfasi Kontrolu: PASSED (5.39s)
[PASS] QA Jobs Filtreleme: PASSED (3.47s)
[PASS] Is Detaylari Dogrulama: PASSED (3.62s)
[FAIL] Lever Redirection: PASSED (3.37s)
--------------------------------------------------------------------------------
Total Tests: 5
Passed: 5
Failed: 0
Errors: 0
Success Rate: 100.0%
```

---

## Service-Based Test Distribution Monitoring

The new controller uses Kubernetes Service for load balancing. Track which pod executed each test:

**View test distribution (session tracking)**
```bash
kubectl logs -n test-automation -l app=test-controller | grep "Test.*PASSED on"
```

Example output:
```
Test 'Ana Sayfa Kontrolu' PASSED on chrome-node-5448bfbfd5-j8vqf (5.66s)
Test 'Careers Sayfasi Kontrolu' PASSED on chrome-node-5448bfbfd5-4q6s9 (5.39s)
Test 'QA Jobs Filtreleme' PASSED on chrome-node-5448bfbfd5-j8vqf (3.47s)
```

**Service execution mode**
```bash
kubectl logs -n test-automation -l app=test-controller | grep "SERVICE"
```

**Session tracking**
```bash
kubectl logs -n test-automation -l app=test-controller | grep "Found session"
```

---

## Chrome Node Monitoring

**All Chrome Node logs**
```bash
kubectl logs -n test-automation -l app=chrome-node --all-containers
```

**Specific pod logs**
```bash
kubectl logs -n test-automation <chrome-node-pod-name>
```

**Live monitoring**
```bash
kubectl logs -n test-automation <chrome-node-pod-name> -f
```

**Count sessions per pod**
```bash
for pod in $(kubectl get pods -n test-automation -l app=chrome-node -o name | cut -d'/' -f2); do
  echo "=== $pod ==="
  kubectl logs -n test-automation $pod 2>/dev/null | grep -c "session"
done
```

---

## Pod Status Monitoring

**List all pods**
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

**Watch pod status live**
```bash
# Pod readiness and liveness status
kubectl get pods -n test-automation -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'
```

---

## Service & Network Monitoring

**List services**
```bash
kubectl get services -n test-automation
```

**Check service endpoints (which pods are connected)**
```bash
kubectl get endpoints -n test-automation chrome-node-service
```

Example output:
```
NAME                 ENDPOINTS                               AGE
chrome-node-service  192.168.33.144:4444,192.168.39.206:4444 10m
```

**Service details**
```bash
kubectl describe service -n test-automation chrome-node-service
```

**Test service connectivity**
```bash
kubectl exec -n test-automation -it <controller-pod> -- curl http://chrome-node-service:4444/wd/hub/status
```

**DNS resolution check**
```bash
kubectl run -it --rm debug --image=busybox --restart=Never -n test-automation -- nslookup chrome-node-service
```

---

## Job Execution Monitoring

**List jobs**
```bash
kubectl get jobs -n test-automation
```

**Job details**
```bash
kubectl describe job -n test-automation test-controller-job
```

**Job logs**
```bash
kubectl logs -n test-automation job/test-controller-job
```

---

## Resource Usage Monitoring

**Pod resource usage**
```bash
kubectl top pods -n test-automation
```

Example output:
```
NAME                           CPU(cores)   MEMORY(bytes)
chrome-node-5448bfbfd5-4q6s9   45m          380Mi
chrome-node-5448bfbfd5-j8vqf   50m          400Mi
```

**Node resource usage**
```bash
kubectl top nodes
```

**Resource requests and limits**
```bash
kubectl get pods -n test-automation -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].resources}{"\n"}{end}'
```

---

## Event Monitoring

**Recent events**
```bash
kubectl get events -n test-automation --sort-by='.lastTimestamp'
```

**Watch events live**
```bash
kubectl get events -n test-automation --watch
```

**Last 20 events**
```bash
kubectl get events -n test-automation --sort-by='.lastTimestamp' | tail -20
```

---

## Debugging & Troubleshooting

**Enter Chrome Node pod**
```bash
kubectl exec -n test-automation -it <chrome-node-pod> -- /bin/bash
```

**Check Selenium status**
```bash
kubectl exec -n test-automation -it <chrome-node-pod> -- curl http://localhost:4444/wd/hub/status
```

**View previous pod logs (if crashed)**
```bash
kubectl logs -n test-automation <pod-name> --previous
```

**Check pod restart count**
```bash
kubectl get pods -n test-automation -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[*].restartCount}{"\n"}{end}'
```

---

## Quick Reference Commands

**Test Results**
```bash
# Full test results
kubectl logs -n test-automation -l app=test-controller | grep "\[PASS\]\|\[FAIL\]"

# Test summary
kubectl logs -n test-automation -l app=test-controller | grep -A 15 "TEST EXECUTION SUMMARY"

# Failed tests only
kubectl logs -n test-automation -l app=test-controller | grep "\[FAIL\]"
```

**Test Distribution (Service-Based)**
```bash
# Which pod executed each test
kubectl logs -n test-automation -l app=test-controller | grep "PASSED on\|FAILED on"

# Session tracking
kubectl logs -n test-automation -l app=test-controller | grep "Found session"

# Service mode verification
kubectl logs -n test-automation -l app=test-controller | grep "via Service"
```

**Cluster Health**
```bash
# All resources
kubectl get all -n test-automation

# Cluster info
kubectl cluster-info

# Node status
kubectl get nodes
```

---

## Monitoring Best Practices

**Save test logs**
```bash
kubectl logs -n test-automation -l app=test-controller > test-results-$(date +%Y%m%d).log
```

**Monitor resource trends**
```bash
watch -n 5 'kubectl top pods -n test-automation'
```

**Check for failures**
```bash
if kubectl logs -n test-automation -l app=test-controller | grep -q "FAILED\|ERROR"; then
    echo "Test failures detected!"
fi
```

**Export test results**
```bash
# Get test results JSON from controller pod
kubectl exec -n test-automation <controller-pod> -- cat /app/test_results/results_*.json > test-results.json
```

---

## Summary Table

| What to Monitor | Command |
|-----------------|---------|
| **Test results** | `kubectl logs -n test-automation -l app=test-controller` |
| **Test summary** | `kubectl logs -n test-automation -l app=test-controller \| grep -A 15 "TEST EXECUTION SUMMARY"` |
| **Test distribution** | `kubectl logs -n test-automation -l app=test-controller \| grep "PASSED on"` |
| **Session tracking** | `kubectl logs -n test-automation -l app=test-controller \| grep "Found session"` |
| **Pod status** | `kubectl get pods -n test-automation -o wide` |
| **Chrome logs** | `kubectl logs -n test-automation <chrome-pod>` |
| **Service endpoints** | `kubectl get endpoints -n test-automation chrome-node-service` |
| **Resource usage** | `kubectl top pods -n test-automation` |
| **Events** | `kubectl get events -n test-automation --sort-by='.lastTimestamp'` |
| **Job status** | `kubectl get jobs -n test-automation` |
| **All resources** | `kubectl get all -n test-automation` |

---

## Service-Based Architecture Notes

The controller now uses **Kubernetes Service** for load balancing:

1. **Automatic Load Balancing**: Service routes requests via Round-Robin
2. **Session Tracking**: Controller tracks which pod handled each test via session IDs
3. **Service Discovery**: Uses stable DNS name (`chrome-node-service`)
4. **No Manual Distribution**: Kubernetes handles all routing

Monitor the service-based approach:
```bash
# Verify service is routing to all pods
kubectl get endpoints chrome-node-service -n test-automation

# Check load distribution
kubectl logs -n test-automation -l app=test-controller | grep "PASSED on" | sort | uniq -c
```

This shows how many tests each pod executed, confirming proper load balancing.
