# Kubernetes Manifests

This folder contains YAML manifests to deploy Selenium test automation on Kubernetes.

## Files

```
k8s/
├── namespace.yaml                  # test-automation namespace
├── rbac.yaml                       # ServiceAccount, Role, RoleBinding
├── configmap.yaml                  # Test configuration
├── chrome-node-service.yaml        # Chrome Node Service (ClusterIP)
├── chrome-node-deployment.yaml     # Chrome Node Deployment (1-5 replicas)
├── controller-deployment.yaml      # Test Controller Deployment (deprecated)
└── controller-job.yaml             # Test Controller Job (recommended)
```

## Components

**Namespace**
- File: `namespace.yaml`
- Creates `test-automation` namespace for all resources

**RBAC**
- File: `rbac.yaml`
- ServiceAccount: `test-controller-sa`
- Permissions: Read/list/watch Pods, Read/update Deployments, Access Pod logs

**ConfigMap**
- File: `configmap.yaml`
- Contains test URLs and environment variables

**Chrome Node Service**
- File: `chrome-node-service.yaml`
- Type: ClusterIP
- Port: 4444 (Selenium WebDriver)
- Load balances across Chrome Node Pods

**Chrome Node Deployment**
- File: `chrome-node-deployment.yaml`
- Image: `selenium/standalone-chrome:latest` (official Selenium image)
- Replicas: 1-5 (configurable)
- Resources: 256Mi-512Mi memory, 250m-500m CPU
- Includes readiness and liveness probes

**Test Controller Job**
- File: `controller-job.yaml`
- Image: `dogancan4040/insider-test-controller:latest`
- Type: Kubernetes Job (runs once, no restarts)
- TTL: 3600s (auto-cleanup after 1 hour)
- BackoffLimit: 3 retries on failure
- Avoids CrashLoopBackOff issues

**Test Controller Deployment** (deprecated)
- File: `controller-deployment.yaml`
- Not recommended due to CrashLoopBackOff after job completion
- Use controller-job.yaml instead

## Quick Start

**Using Python Script (Recommended)**

```bash
# Deploy with 2 Chrome Nodes
python deploy_k8s.py --node-count 2

# Check status
python deploy_k8s.py --status

# Cleanup
python deploy_k8s.py --cleanup
```

**Using kubectl**

```bash
# Apply all manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/chrome-node-service.yaml
kubectl apply -f k8s/chrome-node-deployment.yaml
kubectl apply -f k8s/controller-job.yaml

# Check pod status
kubectl get pods -n test-automation -o wide

# Scale Chrome Nodes
kubectl scale deployment chrome-node -n test-automation --replicas=3
```

## Monitoring

**Pod Status**
```bash
kubectl get pods -n test-automation -o wide
```

**View Logs**
```bash
# Controller logs
kubectl logs -f -n test-automation -l app=test-controller

# Chrome Node logs
kubectl logs -f -n test-automation -l app=chrome-node

# Specific pod
kubectl logs -f <pod-name> -n test-automation
```

**Pod Details**
```bash
kubectl describe pod <pod-name> -n test-automation
```

**Service & Endpoints**
```bash
kubectl get svc -n test-automation
kubectl get endpoints chrome-node-service -n test-automation
```

**Cluster Events**
```bash
kubectl get events -n test-automation --sort-by='.lastTimestamp'
```

## Troubleshooting

**Pod stuck in Pending**
```bash
kubectl describe pod <pod-name> -n test-automation
kubectl top nodes
```
Check for insufficient resources or scheduling issues.

**ImagePullBackOff**
```bash
kubectl describe pod <pod-name> -n test-automation
```
Verify the image exists in Docker Hub and the name is correct in the YAML file.

**CrashLoopBackOff**
```bash
kubectl logs <pod-name> -n test-automation --previous
```
Use controller-job.yaml instead of controller-deployment.yaml to avoid this.

**Service not reachable**
```bash
kubectl get endpoints chrome-node-service -n test-automation
kubectl exec -it <pod> -n test-automation -- curl http://chrome-node-service:4444/wd/hub/status
```
Ensure Chrome Node Pods are running and the Service has endpoints.

**DNS issues**
```bash
kubectl run -it --rm debug --image=busybox --restart=Never -n test-automation -- nslookup chrome-node-service
```

## Cleanup

**Remove all resources**
```bash
# Using Python script
python deploy_k8s.py --cleanup

# Or manually delete namespace
kubectl delete namespace test-automation
```

**Delete specific resources**
```bash
kubectl delete deployment chrome-node -n test-automation
kubectl delete job test-controller-job -n test-automation
```

## Important Notes

1. Update Docker Hub username in `controller-job.yaml` if using your own image
2. Resource limits can be adjusted based on cluster capacity
3. Chrome Nodes can scale from 1 to 5 replicas
4. Always cleanup resources after testing to avoid costs
5. Use controller-job.yaml instead of controller-deployment.yaml

## Related Documentation

- `../deploy_k8s.py` - Automated deployment script
- `../devops-k8s-controller/controller.py` - Test Controller implementation
- `../devops-k8s-controller/README.md` - Controller documentation
- Main project README for complete setup guide
