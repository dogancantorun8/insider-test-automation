# Test Controller - Kubernetes

This folder contains the Controller Pod that manages test automation in the Kubernetes environment.

## Files

```
devops-k8s-controller/
├── controller.py              # Test Controller (Service-based)
├── Dockerfile.controller      # Docker image
├── requirements.txt           # Python dependencies 
```

## What It Does

The Controller Pod handles:
- Finding Chrome Node Pods using Kubernetes API
- Checking if the Service is ready
- Loading and executing test cases
- Distributing tests through Kubernetes Service (automatic load balancing)
- Tracking which pod runs each test (using session IDs)
- Collecting and reporting results
- Providing health check endpoints (`/health`, `/results`)

## Key Features

- **Service-Based**: Uses Kubernetes Service for automatic load balancing
- **Session Tracking**: Shows which pod executed each test
- **Auto Retry**: Automatically retries on failures using `tenacity`
- **Health Monitoring**: Flask endpoints for status checks
- **Dynamic Scaling**: Detects replica count automatically

## Docker Build & Push

```bash
# Build the image
docker build -f devops-k8s-controller/Dockerfile.controller -t insider-test-controller:latest .

# Tag for Docker Hub
docker tag insider-test-controller:latest YOUR_USERNAME/insider-test-controller:latest

# Push to registry
docker push YOUR_USERNAME/insider-test-controller:latest
```

## Environment Variables

The Controller Pod uses these environment variables:

```bash
NAMESPACE=test-automation                    # Kubernetes namespace
CHROME_NODE_SERVICE=chrome-node-service      # Service name
CHROME_NODE_PORT=4444                        # Selenium port
BASE_URL=https://useinsider.com             # Test URL
LOG_LEVEL=INFO                              # Logging level
```

## Test Execution Flow

```
1. Controller starts and launches Flask server on port 8080
2. Waits for Chrome Node Pods to be ready
3. Checks Chrome Node Service health
4. Loads test cases
5. For each test:
   - Creates Selenium session via Service URL
   - Service routes request to available Chrome Node
   - Finds which pod executed the test from logs
   - Collects test result
6. Generates summary report
7. Saves results to JSON file (/app/test_results/)
```

## API Endpoints

**Health Check**
```bash
GET /health
# Response: {"status": "healthy", "timestamp": "..."}
```

**Test Results**
```bash
GET /results
# Response: {"results": [...]}
```

## Adding New Tests

Edit the `get_test_cases()` method in `controller.py`:

```python
{
    'id': 'test_new',
    'name': 'New Test Name',
    'file': 'tests.test_module',
    'method': 'test_method_name',
    'priority': 1
}
```

## RBAC Permissions

The Controller Pod requires these permissions (defined in `rbac.yaml`):
- Pods: Read, List
- Deployments: Read
- Services: Read
- Pod Logs: Read (required for session tracking)

## Dependencies

```
kubernetes>=28.1.0          # Kubernetes API client
requests>=2.31.0            # HTTP requests
selenium>=4.25.0            # WebDriver
flask>=3.0.0                # Health endpoints
tenacity>=8.2.3             # Retry logic
```

## Troubleshooting

**Controller not starting**
```bash
kubectl logs -f -n test-automation -l app=test-controller
kubectl describe job test-controller-job -n test-automation
```

**Service connection issues**
```bash
kubectl get endpoints chrome-node-service -n test-automation
kubectl exec -it <pod> -n test-automation -- curl http://chrome-node-service:4444/wd/hub/status
```

**Session tracking not working**
```bash
kubectl logs <chrome-node-pod> -n test-automation | grep -i session
kubectl auth can-i get pods/log -n test-automation --as=system:serviceaccount:test-automation:test-controller-sa
```

## Architecture Benefits

**Service-Based Approach:**
- Kubernetes handles load balancing automatically (Round-Robin)
- Uses stable DNS names instead of dynamic Pod IPs
- Routes traffic only to healthy pods
- No need for manual pod selection logic
- Easy to scale without code changes

**Session Tracking:**
- Visibility into which pod executed each test
- Easy identification of problematic pods
- Verification that load balancing works correctly

---

This implementation uses service-based architecture for better load balancing and easier scalability.
