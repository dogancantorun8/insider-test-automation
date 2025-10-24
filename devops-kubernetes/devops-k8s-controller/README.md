# DevOps - Kubernetes Controller

This folder contains the necessary files for the **Controller Pod that manages test automation in a Kubernetes environment**.

## Contents

```
devops-k8s-controller/
├── controller.py              # Test Controller - Main logic
├── Dockerfile.controller      # Dockerfile for Docker image
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## What Does It Do?

### `controller.py`
Runs inside the Test Controller Pod and does the following:
- Finds Chrome Node Pods from Kubernetes API
- Checks if Selenium Grid is ready
- Loads test cases
- Distributes tests to Chrome Nodes (with Round-Robin algorithm)
- Executes tests
- Collects and reports results
- Provides health check endpoint (Flask)

### `Dockerfile.controller`
Creates Docker image for Test Controller:
- Python 3.9 slim base image
- Kubernetes Python client
- Test files and dependencies
- Health check endpoint (port 8080)

## Docker Image Build

```bash
# Build
docker build -f devops-k8s-controller/Dockerfile.controller -t insider-test-controller:latest .

# Tag for Docker Hub
docker tag insider-test-controller:latest YOUR_USERNAME/insider-test-controller:latest

# Push
docker push YOUR_USERNAME/insider-test-controller:latest
```

## Environment Variables

Controller Pod uses these environment variables:

```bash
NAMESPACE=test-automation                    # Kubernetes namespace
CHROME_NODE_SERVICE=chrome-node-service      # Chrome Node service name
CHROME_NODE_PORT=4444                        # Selenium port
BASE_URL=https://useinsider.com             # Test URL
LOG_LEVEL=INFO                              # Log level
```

## Test Execution Flow

```
1. Controller Pod starts
   ↓
2. Lists Chrome Node Pods from Kubernetes API
   ↓
3. Checks if Selenium is ready on each Chrome Node
   ↓
4. Loads test cases from get_test_cases() method
   ↓
5. Distributes tests to Chrome Nodes with distribute_tests()
   ↓
6. Executes each test with execute_test_on_node()
   ↓
7. Collects test results
   ↓
8. Creates summary report
   ↓
9. Saves results to JSON file
```

## Controller API Endpoints

Controller Pod provides health check endpoints with Flask:

### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00"
}
```

### Test Results
```bash
GET /results

Response:
{
  "results": [
    {
      "test_id": "test_1",
      "test_name": "Homepage Check",
      "status": "PASSED",
      "execution_time": 3.45
    }
  ]
}
```

## Adding Test Cases

To add a new test case, edit the `get_test_cases()` method in `controller.py`:

```python
def get_test_cases(self) -> List[Dict[str, Any]]:
    test_cases = [
        {
            'id': 'test_1',
            'name': 'Homepage Check',
            'file': 'tests.test_home_page',
            'method': 'test_home_page',
            'priority': 1
        },
        # Add new test
        {
            'id': 'test_new',
            'name': 'New Test',
            'file': 'tests.test_new',
            'method': 'test_new_method',
            'priority': 2
        }
    ]
    return test_cases
```

## Kubernetes Integration

Controller Pod uses Kubernetes API to:
- List Pods: `list_namespaced_pod()`
- Scale Deployments: `patch_namespaced_deployment()`
- Get Pod IPs: `pod.status.pod_ip`
- Service discovery: Access Chrome Node Service via DNS

### RBAC Permissions
Controller Pod has these permissions (rbac.yaml):
- Read, list Pods
- Read, update Deployments
- Read Services
- Access Pod logs

## Dependencies

```
kubernetes>=28.1.0          # Kubernetes Python client
requests>=2.31.0            # HTTP requests
selenium>=4.25.0            # Selenium WebDriver
flask>=3.0.0                # Health check endpoint
python-dotenv>=1.0.0        # Environment variables
colorlog>=6.8.0             # Colored logging
tenacity>=8.2.3             # Retry logic
```

## Troubleshooting

### Controller Pod not starting
```bash
# Check logs
kubectl logs -f deployment/test-controller -n test-automation

# Pod details
kubectl describe pod <controller-pod-name> -n test-automation
```

### Chrome Node not found
```bash
# Service check
kubectl get svc chrome-node-service -n test-automation

# Endpoints check
kubectl get endpoints chrome-node-service -n test-automation

# DNS test
kubectl exec -it <controller-pod> -n test-automation -- nslookup chrome-node-service
```

## Conclusion

This folder is specifically prepared for **DevOps/Kubernetes deployment**.
