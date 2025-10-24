# Kubernetes Deployment Guide

This folder contains all YAML manifest files required to run Selenium test automation in Kubernetes.

## File Structure

```
k8s/
├── namespace.yaml                  # test-automation namespace
├── rbac.yaml                       # ServiceAccount, Role, RoleBinding
├── configmap.yaml                  # Test configuration
├── chrome-node-service.yaml        # Chrome Node ClusterIP Service
├── chrome-node-deployment.yaml     # Chrome Node Deployment (1-5 replicas)
├── controller-deployment.yaml      # Test Controller Deployment (deprecated)
└── controller-job.yaml             # Test Controller Job (recommended - no CrashLoopBackOff)
```

## Components

### 1. Namespace
- **File:** `namespace.yaml`
- **Namespace:** `test-automation`
- All resources are created within this namespace

### 2. RBAC (Role-Based Access Control)
- **File:** `rbac.yaml`
- **ServiceAccount:** `test-controller-sa`
- **Permissions:**
  - Read, list, watch Pods
  - Read, update, scale Deployments
  - Access Pod logs

### 3. ConfigMap
- **File:** `configmap.yaml`
- Contains test URLs and configurations
- Environment variables

### 4. Chrome Node Service
- **File:** `chrome-node-service.yaml`
- **Type:** ClusterIP
- **Ports:**
  - `4444`: Selenium WebDriver

### 5. Chrome Node Deployment
- **File:** `chrome-node-deployment.yaml`
- **Image:** `selenium/standalone-chrome:latest` (recommended)
  - Pre-built Selenium image, no build required
  - Headless Chrome pre-installed
  - ChromeDriver pre-installed
- **Custom Image (Optional):** `../chrome-node/Dockerfile.chrome`
  - Use if custom configuration is needed
- **Replicas:** 1 (default), max 5
- **Resources:**
  - Memory: 256Mi request, 512Mi limit (optimized for t2.small)
  - CPU: 250m request, 500m limit
- **Ports:**
  - 4444: Selenium WebDriver
- **Environment Variables:**
  - `SE_NODE_MAX_SESSIONS`: "1"
  - `SE_NODE_SESSION_TIMEOUT`: "300"
  - `SE_SCREEN_WIDTH`: "1920"
  - `SE_SCREEN_HEIGHT`: "1080"
- **Probes:**
  - Readiness probe: `/wd/hub/status`
  - Liveness probe: `/wd/hub/status`

### 6. Test Controller Job (Recommended)
- **File:** `controller-job.yaml`
- **Type:** Kubernetes Job (runs once, completes)
- **Image:** `dogancan4040/insider-test-controller:latest`
- **RestartPolicy:** Never (no CrashLoopBackOff problem)
- **TTL:** 3600s (auto-cleanup after 1 hour)
- **BackoffLimit:** 3 (retries 3 times on failure)
- **Resources:**
  - Memory: 256Mi request, 512Mi limit
  - CPU: 200m request, 500m limit
- **Features:**
  - Automatically reads deployment replica count
  - Waits for all Chrome nodes to be ready
  - 10 second Selenium stabilization wait
  - Stays in Completed state after test (no restart)

### 6b. Test Controller Deployment (Deprecated)
- **File:** `controller-deployment.yaml`
- **Status:** Not used (CrashLoopBackOff issue)
- **Recommended:** Use `controller-job.yaml`

## Deployment

### Option 1: Python Script (Recommended)

```bash
# Deploy with 1 Chrome Node
python deploy_k8s.py --node-count 1

# Deploy with 3 Chrome Nodes
python deploy_k8s.py --node-count 3

# Status check
python deploy_k8s.py --status

# Cleanup
python deploy_k8s.py --cleanup
```

### Option 2: Manual Kubectl

```bash
# 1. Create namespace
kubectl apply -f k8s/namespace.yaml

# 2. Setup RBAC
kubectl apply -f k8s/rbac.yaml

# 3. Create ConfigMap
kubectl apply -f k8s/configmap.yaml

# 4. Create Chrome Node Service
kubectl apply -f k8s/chrome-node-service.yaml

# 5. Chrome Node deployment
kubectl apply -f k8s/chrome-node-deployment.yaml

# 6. Test Controller deployment
kubectl apply -f k8s/controller-deployment.yaml

# 7. Check pod status
kubectl get pods -n test-automation -o wide

# 8. Scale Chrome Nodes (example: 3 replicas)
kubectl scale deployment chrome-node -n test-automation --replicas=3
```

## Monitoring

### Pod Status
```bash
kubectl get pods -n test-automation -o wide
```

### Pod Logs
```bash
# Controller logs
kubectl logs -f deployment/test-controller -n test-automation

# Chrome Node logs
kubectl logs -f deployment/chrome-node -n test-automation

# Specific pod logs
kubectl logs -f <pod-name> -n test-automation
```

### Pod Description
```bash
kubectl describe pod <pod-name> -n test-automation
```

### Service Status
```bash
kubectl get services -n test-automation
```

### Events
```bash
kubectl get events -n test-automation --sort-by='.lastTimestamp'
```

## Troubleshooting

### Pod in Pending State
```bash
# Check pod details
kubectl describe pod <pod-name> -n test-automation

# Check node resources
kubectl top nodes
kubectl describe nodes
```

### ImagePullBackOff Error
```bash
# Check if image was pushed to Docker Hub
# Update image name in controller-deployment.yaml
```

### CrashLoopBackOff
```bash
# Check pod logs
kubectl logs <pod-name> -n test-automation --previous

# Enter pod
kubectl exec -it <pod-name> -n test-automation -- /bin/bash
```

### Service Connection Issues
```bash
# Check service endpoints
kubectl get endpoints chrome-node-service -n test-automation

# DNS test
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup chrome-node-service.test-automation.svc.cluster.local
```

## Cleanup

### Delete all resources
```bash
# With Python script
python deploy_k8s.py --cleanup

# Or manually
kubectl delete namespace test-automation
```

### Delete only deployments
```bash
kubectl delete deployment --all -n test-automation
```

## Notes

1. **Image Name:** Update your Docker Hub username in `controller-deployment.yaml`
2. **Resources:** Pod resource limits can be adjusted based on your cluster
3. **Scaling:** Chrome Nodes can be scaled between 1-5
4. **Free Tier:** AWS EKS is not free tier, calculate costs
5. **Cleanup:** Always cleanup after tests

## Related Files

- `../deploy_k8s.py` - Deployment script
- `../devops-k8s-controller/controller.py` - Test Controller code
- `../test-main.py` - Local test runner (development)
- `../tests/` - Test cases
- `../test_core/` - Test framework (Base class)
- `../test_config/` - Test configuration
