# Kubernetes Deployment Guide

This guide shows how to deploy and run test automation in Kubernetes.

## Quick Start

```bash
# Deploy with 2 Chrome Nodes
python3 deploy_k8s.py --node-count 2

# Check status
python3 deploy_k8s.py --status

# Cleanup
python3 deploy_k8s.py --cleanup
```

## What It Does

The `deploy_k8s.py` script handles the complete deployment:

**Infrastructure Setup**
- Creates namespace (test-automation)
- Sets up RBAC (ServiceAccount, Role, RoleBinding)
- Creates ConfigMap for test configuration
- Deploys Chrome Node Service (load balancing)
- Deploys Chrome Node Pods (1-5 replicas)
- Creates Test Controller Job

**Health Checks**
- Waits for pods to be ready
- Checks Selenium Hub status
- Validates network connectivity

**Test Execution**
- Distributes tests via Kubernetes Service
- Executes tests in parallel
- Collects results and generates reports

**Cleanup**
- Removes all deployed resources
- Preserves namespace and RBAC (optional)

## Parameters

```bash
python3 deploy_k8s.py [OPTIONS]

--node-count N        # Number of Chrome Nodes (1-5, required)
--namespace NAME      # Kubernetes namespace (default: test-automation)
--kubeconfig PATH     # Custom kubeconfig file
--cleanup             # Remove all resources
--status              # Show deployment status
--timeout SECONDS     # Pod readiness timeout (default: 300)
```

## Usage Examples

**Basic Deployment**
```bash
python3 deploy_k8s.py --node-count 2
```

Output:
```
[2025-10-23 12:00:00] INFO - Starting Kubernetes Test Deployment
[2025-10-23 12:00:01] INFO - Namespace 'test-automation' ready
[2025-10-23 12:00:02] INFO - Chrome Node Service created
[2025-10-23 12:00:03] INFO - Chrome Node Deployment created (2 replicas)
[2025-10-23 12:00:25] INFO - All Chrome Nodes ready (2/2)
[2025-10-23 12:00:26] INFO - Test Controller Job created
[2025-10-23 12:00:35] INFO - Test Controller running

DEPLOYMENT SUCCESSFUL
Total Pods: 3 (2 Chrome Nodes + 1 Controller)
```

**Check Status**
```bash
python3 deploy_k8s.py --status
```

Output:
```
DEPLOYMENT STATUS
Namespace: test-automation
Total Pods: 3
Running: 3

Pod Details:
  • chrome-node-5448bfbfd5-abc12: Running (192.168.33.144)
  • chrome-node-5448bfbfd5-def34: Running (192.168.51.36)
  • test-controller-job-xyz89: Completed (192.168.55.91)
```

**Cleanup Resources**
```bash
python3 deploy_k8s.py --cleanup
```

**Custom Namespace**
```bash
python3 deploy_k8s.py --node-count 3 --namespace staging-tests
```

**Extended Timeout**
```bash
python3 deploy_k8s.py --node-count 5 --timeout 600
```

## Typical Workflow

**First Time Setup**
```bash
# 1. Connect to EC2
ssh -i ~/.ssh/insider-test-key.pem ec2-user@<EC2_IP>

# 2. Navigate to project
cd insider/devops-kubernetes

# 3. Deploy and run tests
python3 deploy_k8s.py --node-count 2

# 4. View results
python3 deploy_k8s.py --status

# 5. Cleanup
python3 deploy_k8s.py --cleanup
```

**Testing Different Scales**
```bash
# Small suite (1-2 nodes)
python3 deploy_k8s.py --node-count 1

# Medium suite (3 nodes)
python3 deploy_k8s.py --node-count 3

# Large suite (5 nodes)
python3 deploy_k8s.py --node-count 5
```

## Node Count Guidelines

**Choosing Node Count**

Each Chrome Node can run one test at a time. The script distributes tests across available nodes.

| Test Suite Size | Recommended Nodes |
|----------------|-------------------|
| 1-5 tests      | 1-2 nodes        |
| 6-10 tests     | 2-3 nodes        |
| 11-20 tests    | 3-5 nodes        |
| 21+ tests      | 5+ nodes         |

**Example Distribution**
```bash
python3 deploy_k8s.py --node-count 3
```
- 5 test cases
- 3 Chrome Nodes
- Distribution: Test 1,4 → Node 1 | Test 2,5 → Node 2 | Test 3 → Node 3

## Troubleshooting

**kubectl not configured**
```bash
ERROR: Cannot connect to Kubernetes cluster

# Solution
aws eks update-kubeconfig --region eu-west-1 --name insider-test-cluster
kubectl cluster-info
```

**ImagePullBackOff**
```bash
kubectl get pods -n test-automation
# chrome-node-xxx: ImagePullBackOff

# Solution
kubectl describe pod -n test-automation <pod-name>
# Verify image name in controller-job.yaml
```

**Pod not ready (timeout)**
```bash
ERROR: Chrome Nodes not ready after 300s

# Solution - increase timeout
python3 deploy_k8s.py --node-count 2 --timeout 600

# Or check pod status
kubectl get pods -n test-automation
kubectl describe pod -n test-automation <pod-name>
```

**Service not found**
```bash
ERROR: Service 'chrome-node-service' not found

# Solution
kubectl apply -f k8s/chrome-node-service.yaml
# Or redeploy
python3 deploy_k8s.py --cleanup
python3 deploy_k8s.py --node-count 2
```

**Insufficient resources**
```bash
ERROR: 0/2 nodes available: insufficient cpu/memory

# Solution
kubectl describe nodes  # Check capacity
python3 deploy_k8s.py --node-count 1  # Reduce nodes
```

## Manual Kubernetes Commands

**Check Resources**
```bash
# All resources
kubectl get all -n test-automation

# Pods
kubectl get pods -n test-automation -o wide

# Services
kubectl get services -n test-automation

# Jobs
kubectl get jobs -n test-automation
```

**View Logs**
```bash
# Controller logs
kubectl logs -n test-automation -l app=test-controller

# Chrome Node logs
kubectl logs -n test-automation -l app=chrome-node

# Specific pod
kubectl logs -n test-automation <pod-name> -f
```

**Pod Details**
```bash
kubectl describe pod -n test-automation <pod-name>
```

**Service Endpoints**
```bash
kubectl get endpoints -n test-automation chrome-node-service
```

## Key Features

**Automatic**
- Namespace creation
- Service discovery (DNS-based)
- Health checking (readiness/liveness probes)
- Retry mechanism on failures
- Resource management (limits/requests)
- Graceful cleanup

**Service-Based Architecture**
- Kubernetes Service handles load balancing
- Round-Robin distribution across Chrome Nodes
- Session tracking (which pod ran which test)
- Stable DNS naming
- High availability

**Test Execution**
- Parallel execution across nodes
- Automatic test distribution
- Result aggregation
- JSON report generation

## Best Practices

1. **Start small** - Test with 1-2 nodes first
2. **Cleanup after tests** - Free up cluster resources
3. **Monitor resources** - Check node capacity before scaling
4. **Review logs** - Always check controller logs for results
5. **Use appropriate timeouts** - Adjust based on cluster speed

## More Information

- **Monitoring Guide**: [KUBERNETES_CLUSTER_MONITORING_GUIDE.md](docs/KUBERNETES_CLUSTER_MONITORING_GUIDE.md)
- **Kubernetes Manifests**: [k8s/README.md](k8s/README.md)
- **Controller Documentation**: [devops-k8s-controller/README.md](devops-k8s-controller/README.md)

## Summary

**Basic Flow:**
1. Deploy: `python3 deploy_k8s.py --node-count N`
2. Monitor: `python3 deploy_k8s.py --status`
3. View logs: `kubectl logs -n test-automation -l app=test-controller`
4. Cleanup: `python3 deploy_k8s.py --cleanup`

The script handles everything from infrastructure setup to test execution and cleanup.
