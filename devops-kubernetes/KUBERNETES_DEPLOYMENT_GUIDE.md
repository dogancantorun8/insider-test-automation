# Kubernetes Deployment Guide - Test Execution

This guide allows you to **deploy test automation infrastructure to your Kubernetes cluster and run your tests**.

## Importance of This Document

This document contains **all steps for test execution in Kubernetes**:
- Chrome Node Pods deployment
- Test Controller Pod creation
- Test execution and parallel running
- Resource management and scaling
- Deployment lifecycle management

**Without this guide:** You cannot run tests in Kubernetes.
**With this guide:** You can perform parallel test execution with 1-5 Chrome Nodes using a single command.

---

## Quick Start

### Basic Usage
```bash
# Run tests with 2 Chrome Nodes
python3 deploy_k8s.py --node-count 2

# Run tests with 3 Chrome Nodes
python3 deploy_k8s.py --node-count 3

# Run tests with 5 Chrome Nodes
python3 deploy_k8s.py --node-count 5

# Check deployment status
python3 deploy_k8s.py --status

# Cleanup
python3 deploy_k8s.py --cleanup
```

---

## What Does deploy_k8s.py Do?

### 1. Infrastructure Deployment
- Creates namespace (test-automation)
- RBAC setup (ServiceAccount, Role, RoleBinding)
- Creates ConfigMap
- Creates Chrome Node Service (inter-pod communication)
- Creates Chrome Node Deployment (N replicas)
- Creates Test Controller Job (test orchestration)

### 2. Health Checks
- Pod readiness wait
- Selenium Hub status check
- Network connectivity test
- Resource availability validation

### 3. Test Execution
- Distributes tests to Chrome Nodes
- Parallel test execution
- Test result collection
- Report generation (JSON/PDF)

### 4. Cleanup
- Deletes Pods
- Deletes Services
- Cleans up Jobs
- Preserves Namespace (optional)

---

## Parameters

```bash
python3 deploy_k8s.py [OPTIONS]

Required:
  --node-count N        # Number of Chrome Nodes (1-10)

Optional:
  --namespace NAME      # Kubernetes namespace (default: test-automation)
  --kubeconfig PATH     # Kubeconfig file path
  --cleanup             # Cleanup all resources
  --status              # Show deployment status
  --timeout SECONDS     # Pod readiness timeout (default: 300)
  --image IMAGE         # Custom controller image
```

---

## Detailed Usage Examples

### 1. First Deployment (2 Chrome Nodes)
```bash
python3 deploy_k8s.py --node-count 2
```

**What happens?**
1. Namespace is checked/created
2. Chrome Node Service is created
3. 2 Chrome Node Pods are deployed
4. Waits for Pods to be ready
5. Test Controller Job is created
6. Tests are executed
7. Results are collected

**Output:**
```
[2025-10-23 12:00:00] INFO - Starting Kubernetes Test Deployment
[2025-10-23 12:00:01] INFO - Namespace 'test-automation' is ready
[2025-10-23 12:00:02] INFO - Chrome Node Service created
[2025-10-23 12:00:03] INFO - Chrome Node Deployment created (2 replicas)
[2025-10-23 12:00:05] INFO - Waiting for Chrome Nodes... (0/2 ready)
[2025-10-23 12:00:15] INFO - Waiting for Chrome Nodes... (1/2 ready)
[2025-10-23 12:00:25] INFO - All Chrome Nodes are ready! (2/2)
[2025-10-23 12:00:26] INFO - Test Controller Job created
[2025-10-23 12:00:27] INFO - Waiting for Test Controller...
[2025-10-23 12:00:35] INFO - Test Controller is running!

DEPLOYMENT SUCCESSFUL!
Total Pods: 3 (2 Chrome Nodes + 1 Controller)
Running: 3
Status: Ready for test execution
```

### 2. Large Scale Deployment (5 Chrome Nodes)
```bash
python3 deploy_k8s.py --node-count 5
```

**Usage Scenario:**
- Many test cases
- Fast test execution needed
- Parallel execution desired

**Created Resources:**
- 5x Chrome Node Pods
- 1x Test Controller Job
- 1x Chrome Node Service
- **Total: 6 Pods**

### 3. Deployment with Different Namespace
```bash
python3 deploy_k8s.py --node-count 3 --namespace staging-tests
```

**When to use?**
- Different environments (dev, staging, prod)
- Isolated test execution
- Multi-tenant setup

### 4. Deployment with Custom Timeout
```bash
python3 deploy_k8s.py --node-count 3 --timeout 600
```

**When to use?**
- Slow cluster
- Large images
- Resource constraints

### 5. Deployment Status Check
```bash
python3 deploy_k8s.py --status
```

**Output:**
```
DEPLOYMENT STATUS
================================================================================
Namespace: test-automation
Total Pods: 4
Running: 4
Pending: 0
Failed: 0

Pod Details:
  • chrome-node-5448bfbfd5-abc12: Running (IP: 192.168.33.144)
  • chrome-node-5448bfbfd5-def34: Running (IP: 192.168.51.36)
  • chrome-node-5448bfbfd5-ghi56: Running (IP: 192.168.42.78)
  • test-controller-job-xyz89: Running (IP: 192.168.55.91)

Service Status:
  • chrome-node-service: Active (ClusterIP: 10.100.200.50)

Recent Events:
  • Pod chrome-node-5448bfbfd5-abc12 created
  • Pod chrome-node-5448bfbfd5-def34 created
  • Service chrome-node-service created
```

### 6. Cleanup
```bash
python3 deploy_k8s.py --cleanup
```

**What gets deleted?**
- Chrome Node Deployment
- Test Controller Job
- Chrome Node Service
- ConfigMap (optional)
- Namespace (preserved)
- RBAC (preserved)

---

## Workflow - Typical Usage

### Scenario 1: First Time Test Execution
```bash
# 1. Prepare infrastructure (with Ansible)
cd aws-infra-setup/ansible
ansible-playbook 00-setup-aws-prerequisites.yml
ansible-playbook 03-create-eks-cluster.yml
ansible-playbook 04-deploy-k8s-resources.yml

# 2. Connect to EC2
ssh -i ~/.ssh/insider-test-key.pem ec2-user@<EC2_IP>

# 3. Go to project folder
cd insider/devops-kubernetes

# 4. Run tests
python3 deploy_k8s.py --node-count 2

# 5. Check results
python3 deploy_k8s.py --status

# 6. Cleanup
python3 deploy_k8s.py --cleanup
```

### Scenario 2: Testing with Different Node Counts
```bash
# Small test suite
python3 deploy_k8s.py --node-count 1

# Cleanup
python3 deploy_k8s.py --cleanup

# Medium test suite
python3 deploy_k8s.py --node-count 3

# Cleanup
python3 deploy_k8s.py --cleanup

# Large test suite
python3 deploy_k8s.py --node-count 5
```

### Scenario 3: Debugging and Troubleshooting
```bash
# 1. Deploy
python3 deploy_k8s.py --node-count 2

# 2. Check status
python3 deploy_k8s.py --status

# 3. Manually check Pods
kubectl get pods -n test-automation

# 4. Review logs
kubectl logs -n test-automation -l app=test-controller

# 5. If error, cleanup and retry
python3 deploy_k8s.py --cleanup
python3 deploy_k8s.py --node-count 2
```

---

## How to Determine Node Count?

### Chrome Node Pod Count
`--node-count` parameter determines **Chrome Node Pod count**.

**Each Chrome Node:**
- 1 Selenium standalone instance
- 1 Chrome browser
- 1 test execution capacity

### Example Calculation
```bash
python3 deploy_k8s.py --node-count 3
```

**Created Resources:**
- 3x Chrome Node Pods
- 1x Test Controller Job
- 1x Chrome Node Service
- **Total: 4 Pods**

**Test Distribution:**
- 5 test cases available
- 3 Chrome Nodes available
- Test 1 → Node 1
- Test 2 → Node 2
- Test 3 → Node 3
- Test 4 → Node 1
- Test 5 → Node 2

### Optimal Node Count

| Test Suite Size | Recommended Node Count |
|----------------|------------------------|
| 1-5 tests | 1-2 nodes |
| 6-10 tests | 2-3 nodes |
| 11-20 tests | 3-5 nodes |
| 21+ tests | 5-10 nodes |

**Note:** Node count depends on EKS worker node capacity.

---

## Script Features

### Automatic Features
- **Namespace creation** (if not exists)
- **Service discovery** (via DNS)
- **Health checking** (readiness and liveness probes)
- **Retry mechanism** (on error)
- **Error handling** (comprehensive error management)
- **Resource management** (limits and requests)
- **Inter-pod communication** (via Service)
- **Graceful shutdown** (cleanup)

### Deployment Features
- Controller doesn't start until Chrome Nodes are ready
- Detailed logs at each step
- Automatic rollback on failed deployment
- Resource limits and requests defined
- Liveness and readiness probes
- Rolling update strategy
- Pod anti-affinity (distribution)

### Test Execution Features
- Test distribution (load balancing)
- Parallel test execution
- Test result aggregation
- JSON/PDF report generation
- Screenshot capture
- Error handling and retry
- Test timing and metrics

---

## Error Situations and Solutions

### Error 1: kubectl not configured
```bash
ERROR: Cannot connect to Kubernetes cluster
```

**Solution:**
```bash
aws eks update-kubeconfig --region eu-west-1 --name insider-test-cluster
kubectl cluster-info
```

### Error 2: Node count not specified
```bash
ERROR: --node-count parameter is required
```

**Solution:**
```bash
python3 deploy_k8s.py --node-count 2
```

### Error 3: Pod not starting (ImagePullBackOff)
```bash
kubectl get pods -n test-automation
# chrome-node-xxx: ImagePullBackOff
```

**Solution:**
```bash
# Check image name
kubectl describe pod -n test-automation chrome-node-xxx

# Is image available on Docker Hub?
# image: dogancan4040/chrome-node:latest
```

### Error 4: Pod timeout (Pod not ready)
```bash
ERROR: Chrome Nodes not ready after 300s
```

**Solution:**
```bash
# Increase timeout
python3 deploy_k8s.py --node-count 2 --timeout 600

# Or manually check pods
kubectl get pods -n test-automation
kubectl describe pod -n test-automation chrome-node-xxx
```

### Error 5: Service not found
```bash
ERROR: Service 'chrome-node-service' not found
```

**Solution:**
```bash
# Manually create service
kubectl apply -f k8s/chrome-node-service.yaml

# Or re-run deployment
python3 deploy_k8s.py --cleanup
python3 deploy_k8s.py --node-count 2
```

### Error 6: Insufficient resources
```bash
ERROR: 0/2 nodes are available: insufficient cpu/memory
```

**Solution:**
```bash
# Check node capacity
kubectl describe nodes

# Reduce resource limits (in YAML)
# Or reduce node count
python3 deploy_k8s.py --node-count 1
```

---

## Advanced Usage

### 1. Deployment with Custom Image
```bash
python3 deploy_k8s.py --node-count 3 --image myuser/custom-controller:v2.0
```

### 2. With Different Kubeconfig
```bash
python3 deploy_k8s.py --node-count 2 --kubeconfig ~/.kube/staging-config
```

### 3. Environment-Specific Deployment
```bash
# Development
python3 deploy_k8s.py --node-count 1 --namespace dev-tests

# Staging
python3 deploy_k8s.py --node-count 3 --namespace staging-tests

# Production
python3 deploy_k8s.py --node-count 5 --namespace prod-tests
```

### 4. Load Testing
```bash
# Load test with 10 Chrome Nodes
python3 deploy_k8s.py --node-count 10 --timeout 900
```

---

## Manual Kubernetes Control

### Check Pods
```bash
kubectl get pods -n test-automation
kubectl get pods -n test-automation -o wide
kubectl describe pod -n test-automation <pod-name>
```

### Check Services
```bash
kubectl get services -n test-automation
kubectl describe service -n test-automation chrome-node-service
```

### Check Deployments
```bash
kubectl get deployments -n test-automation
kubectl describe deployment -n test-automation chrome-node
```

### Check Jobs
```bash
kubectl get jobs -n test-automation
kubectl describe job -n test-automation test-controller-job
```

### Review Logs
```bash
# Test Controller logs
kubectl logs -n test-automation -l app=test-controller

# Chrome Node logs
kubectl logs -n test-automation -l app=chrome-node

# Specific pod log
kubectl logs -n test-automation <pod-name> -f
```

---

## Best Practices

### 1. Node Count Selection
- Optimize based on test count
- Don't exceed worker node capacity
- Start small, then scale

### 2. Resource Management
- Define resource limits
- Use pod anti-affinity
- Use node selector (if necessary)

### 3. Cleanup
- Cleanup after each test execution
- Don't leave unnecessary pods
- Optimize resource usage

### 4. Monitoring
- Regularly check pod statuses
- Follow logs
- Monitor resource usage

### 5. Error Handling
- Debug failed pods immediately
- Use retry mechanism
- Set timeouts appropriately

---

## Monitoring and Troubleshooting

For detailed monitoring:
- **[Kubernetes Cluster Monitoring Guide](docs/KUBERNETES_CLUSTER_MONITORING_GUIDE.md)**

---

## Summary

With this guide, you can **deploy test execution infrastructure in Kubernetes and run your tests**.

**Basic Flow:**
1. `deploy_k8s.py --node-count N` → Deploy
2. `deploy_k8s.py --status` → Check
3. Test execution starts automatically
4. `deploy_k8s.py --cleanup` → Cleanup

**More information:**
- Kubernetes manifests: `k8s/` folder
- Controller code: `devops-k8s-controller/controller.py`
- Chrome Node: `chrome-node/Dockerfile.chrome`
