# Selenium Test Automation on Kubernetes

This project is solution developed for **running Selenium test automation in a Kubernetes environment**.

## Architecture

```
┌───────────────────────────────────────────────────────────────────── ┐
│                    KUBERNETES TEST CLUSTER (EKS)                     │
│                                                                      │
│  ┌──────────────────────┐                                            │
│  │  Test Controller     │  Distributes tests and collects results    │
│  │       Job            │                                            │
│  └──────────┬───────────┘                                            │
│             │ HTTP Requests                                          │
│             │ (Selenium WebDriver Protocol)                          │
│             ▼                                                        │
│  ┌─────────────────────────────────────────┐                         │
│  │    Chrome Node Service                  │  Service Discovery      │
│  │    (ClusterIP: Load Balancer)           │  & Load Balancing       │
│  └────────────┬────────────────────────────┘                         │
│               │                                                      │
│    ┌──────────┼────────────┬────────────┐                            │
│    │          │            │            │                            │
│    ▼          ▼            ▼            ▼                            │
│  ┌─────┐   ┌─────┐      ┌─────┐      ┌─────┐                         │
│  │Chrome│   │Chrome│      │Chrome│      │Chrome│  Parallel Test      │
│  │Node 1│   │Node 2│  ... │Node N│      │Pod  │  Execution           │
│  │ Pod  │   │ Pod  │      │ Pod  │      │     │                      │
│  └──────┘   └──────┘      └──────┘      └─────┘                      │
│  Selenium    Selenium      Selenium     Selenium                     │
│  + Chrome    + Chrome      + Chrome     + Chrome                     │
│                                                                      │
│  ┌──────────────────────────────────────────────────────┐            │
│  │              Namespace: test-automation              │            │
│  │  RBAC: ServiceAccount, Role, RoleBinding            │             │
│  │  ConfigMap: Test configuration                      │             │
│  └──────────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
           ▲                                    │
           │                                    │
           │  kubectl                           │  Results
           │  commands                          │  (JSON/PDF)
           │                                    ▼
    ┌──────────────┐                    ┌──────────────┐
    │   EC2        │                    │  Test        │
    │   Instance   │                    │  Reports     │
    │   (Control)  │                    │              │
    └──────────────┘                    └──────────────┘
```

### Architecture Explanation:

1. **Test Controller Job**: Distributes tests to Chrome Nodes and collects results
2. **Chrome Node Service**: Provides load balancing and service discovery
3. **Chrome Node Pods**: Parallel test execution (Selenium + Chrome)
4. **Namespace**: Isolation and resource management
5. **RBAC**: Security and access control
6. **EC2 Instance**: Control plane managing the Kubernetes cluster

## Project Structure

```
insider/
│
├── test-development/                      # Test Development & Local Execution
│   ├── test-main.py                      # Local test runner (development)
│   ├── tests/                            # Test cases
│   │   ├── test_home_page.py            # Homepage and careers tests
│   │   └── test_qa_page.py              # QA position tests
│   ├── test_core/                        # Test framework base class
│   │   └── base_test.py                 # BaseTest class (setup/teardown)
│   └── test_config/                      # Test configuration
│       └── settings.py                   # URLs and test settings
│
├── devops-kubernetes/                     # Kubernetes Deployment & Orchestration
│   ├── deploy_k8s.py                     # Main deployment script (test runner)
│   ├── KUBERNETES_DEPLOYMENT_GUIDE.md    # Deployment guide (IMPORTANT)
│   ├── devops-k8s-controller/            # Test Controller Pod
│   │   ├── controller.py                # Test orchestration and distribution
│   │   ├── Dockerfile.controller        # Controller image build
│   │   ├── requirements.txt             # Controller dependencies
│   │   └── README.md                    # Controller documentation
│   ├── k8s/                              # Kubernetes manifests
│   │   ├── namespace.yaml               # test-automation namespace
│   │   ├── rbac.yaml                    # ServiceAccount, Role, RoleBinding
│   │   ├── configmap.yaml               # Test configuration
│   │   ├── chrome-node-service.yaml     # Service (load balancing)
│   │   ├── chrome-node-deployment.yaml  # Chrome Node deployment (N replicas)
│   │   ├── controller-deployment.yaml   # Controller deployment
│   │   ├── controller-job.yaml          # Controller job (one-time execution)
│   │   └── README.md                    # Manifests documentation
│   └── docs/
│       └── KUBERNETES_CLUSTER_MONITORING_GUIDE.md  # Monitoring guide
│
├── docker-operations/                    # Docker Image Operations
│   ├── build_images.sh                   # Build Docker images
│   ├── push_images.sh                    # Push to Docker Hub
│   └── README.md                         # Docker operations guide
│
├── aws-infra-setup/                       # AWS Infrastructure Setup
│   ├── README.md                         # AWS infrastructure overview
│   └── ansible/                          # Ansible playbooks
│       ├── 00-setup-aws-prerequisites.yml    # Create EC2, SSH Key, SG
│       ├── 00-cleanup-prerequisites.yml      # Cleanup prerequisites
│       ├── 01-setup-ec2.yml                  # EC2 connectivity test
│       ├── 02-install-tools.yml              # Install kubectl, eksctl, aws-cli
│       ├── 03-create-eks-cluster.yml         # Create EKS cluster
│       ├── 03a-upgrade-nodegroup.yml         # Upgrade worker nodes
│       ├── 04-deploy-k8s-resources.yml       # Deploy K8s namespace, RBAC, ConfigMap
│       ├── 05-cleanup.yml                    # EKS cluster cleanup
│       ├── ansible.cfg                       # Ansible configuration
│       ├── inventory.yml                     # Host information
│       ├── requirements.yml                  # Ansible Galaxy requirements
│       ├── environment.sh                    # Environment variables
│       ├── group_vars/
│       │   └── all.yml                      # Global variables (SINGLE SOURCE)
│       ├── templates/
│       │   └── eks-cluster-config.yaml.j2   # EKS cluster config template
│       └── README.md                         # Detailed Ansible playbooks guide
│
├── requirements.txt                       # Python dependencies (project-wide)
└── README.md                             # Main documentation (this file)
```

## Quick Start

### 1. Local Test (Development)

```bash
# Run tests on your local machine
cd insider/
python test-development/test-main.py
```

### 2. Docker Build & Push

```bash
# Build Docker images
chmod +x docker-operations/build_images.sh
./docker-operations/build_images.sh

# Push to Docker Hub
chmod +x docker-operations/push_images.sh
./docker-operations/push_images.sh
```

### 3. AWS Infrastructure Setup

```bash
cd aws-infra-setup/ansible

# 1. Create AWS prerequisites (EC2, SSH Key, Security Group)
ansible-playbook 00-setup-aws-prerequisites.yml

# 2. Test EC2 connectivity
ansible-playbook 01-setup-ec2.yml

# 3. Install tools (kubectl, eksctl, aws-cli)
ansible-playbook 02-install-tools.yml

# 4. Create EKS cluster (~15-20 minutes)
ansible-playbook 03-create-eks-cluster.yml

# 5. Deploy Kubernetes resources
ansible-playbook 04-deploy-k8s-resources.yml
```

### 4. Manual Test Execution

```bash
# Connect to EC2
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP

# Run tests
cd insider/devops-kubernetes

# Test with 2 Chrome Nodes
python3 deploy_k8s.py --node-count 2

# Test with 3 Chrome Nodes
python3 deploy_k8s.py --node-count 3

# Test with 5 Chrome Nodes
python3 deploy_k8s.py --node-count 5

# Check deployment status
python3 deploy_k8s.py --status

# Cleanup
python3 deploy_k8s.py --cleanup
```

## Project Categories

### 1. Test Development ([test-development/](test-development/))

**Purpose:** Local test development and execution

**Contents:**
- `test-main.py` - Local test runner
- `tests/` - Test case files
- `test_core/` - Base test class and utilities
- `test_config/` - Test settings and configuration

**Usage:**
```bash
python test-development/test-main.py
```

---

### 2. Kubernetes Deployment ([devops-kubernetes/](devops-kubernetes/))

**Purpose:** Kubernetes deployment and test orchestration

**Contents:**
- [`deploy_k8s.py`](devops-kubernetes/deploy_k8s.py) - Python deployment script
- [`devops-k8s-controller/`](devops-kubernetes/devops-k8s-controller/) - Test Controller Pod
- [`k8s/`](devops-kubernetes/k8s/) - Kubernetes YAML manifests (Chrome Node: selenium/standalone-chrome:latest)

**Documentation:**
- **[Kubernetes Deployment Guide](devops-kubernetes/KUBERNETES_DEPLOYMENT_GUIDE.md)** - Test execution guide
- **[Manifests README](devops-kubernetes/k8s/README.md)** - Kubernetes manifests
- **[Monitoring Guide](devops-kubernetes/docs/KUBERNETES_CLUSTER_MONITORING_GUIDE.md)** - Cluster monitoring

**Usage:**
```bash
python3 deploy_k8s.py --node-count 3
```

**Features:**
- Parallel test execution (1-5 Chrome Nodes)
- Automatic test distribution
- Pod health check and retry
- Test result collection

---

### 3. Docker Operations ([docker-operations/](docker-operations/))

**Purpose:** Docker image build and registry operations

**Contents:**
- `build_images.sh` - Build Docker images
- `push_images.sh` - Push to Docker Hub

**Documentation:**
- **[Docker Operations README](docker-operations/README.md)** - Build and push guide

**Usage:**
```bash
./docker-operations/build_images.sh
./docker-operations/push_images.sh
```

**Built image:**
- `YOUR_DOCKERHUB_USERNAME/insider-test-controller:latest`

**Pre-built image used:**
- `selenium/standalone-chrome:latest` (Docker Hub - Selenium official)

---

### 4. AWS Infrastructure ([aws-infra-setup/](aws-infra-setup/))

**Purpose:** AWS EKS cluster setup and management

**Contents:**
- [`ansible/`](aws-infra-setup/ansible/) - Ansible playbooks
- EKS cluster configuration templates
- Global variables (`group_vars/all.yml`)

**Documentation:**
- **[AWS Infrastructure README](aws-infra-setup/README.md)** - Overview
- **[Ansible Playbooks README](aws-infra-setup/ansible/README.md)** - Detailed guide

**Usage:**
```bash
cd aws-infra-setup/ansible
ansible-playbook 00-setup-aws-prerequisites.yml
ansible-playbook 03-create-eks-cluster.yml
```

**Features:**
- Fully automated AWS infrastructure setup
- EC2 instance management
- EKS cluster creation and upgrade
- Automatic kubectl configuration

## Configuration

### Environment Variables

```bash
# Docker Hub (for docker-operations)
export DOCKER_USERNAME=your_username
export DOCKER_PASSWORD=your_password

# AWS (for aws-infra-setup)
export EC2_PUBLIC_IP="YOUR_EC2_PUBLIC_IP"
export SSH_KEY_PATH="~/.ssh/your-key.pem"

# Kubernetes (for devops-kubernetes)
export NAMESPACE=test-automation
export CHROME_NODE_SERVICE=chrome-node-service
export CHROME_NODE_PORT=4444
```

### Ansible Variables (group_vars/all.yml)

```yaml
# AWS Configuration
aws_region: YOUR_AWS_REGION              # Example: us-east-1, eu-west-1
cluster_name: your-cluster-name          # Example: my-test-cluster
node_type: t2.small                      # EKS worker node instance type
node_count: 2                            # Number of EKS worker nodes
ssh_key_name: your-ssh-key-name          # Example: my-key

# Project Configuration
namespace: test-automation
docker_image: YOUR_DOCKERHUB_USERNAME/insider-test-controller:latest
```

### Docker Image Configuration

Update image name in `k8s/controller-deployment.yaml`:
```yaml
image: YOUR_DOCKERHUB_USERNAME/insider-test-controller:latest
```

## Test Execution Flow

```
1. Local Development
   └─> test-development/test-main.py
       └─> Test cases run locally

2. Docker Build
   └─> docker-operations/build_images.sh
       └─> Controller and Chrome Node images are built

3. Docker Push
   └─> docker-operations/push_images.sh
       └─> Images are pushed to Docker Hub

4. AWS Infrastructure Setup
   └─> aws-infra-setup/ansible/
       └─> EC2 instance and EKS cluster are created

5. Kubernetes Deploy
   └─> devops-kubernetes/deploy_k8s.py
       └─> Chrome Node and Controller Pods are deployed

6. Test Execution
   └─> Controller Pod
       └─> Distributes tests to Chrome Nodes
           └─> Parallel test execution

7. Results Collection
   └─> Controller Pod
       └─> Collects test results
           └─> Generates JSON/PDF report
```

## Node Count Difference

### EKS Worker Node Count
```yaml
# group_vars/all.yml
node_count: 2    # 2 EC2 worker nodes (infrastructure level)
```
- Number of **physical EC2 instances** in the EKS cluster
- Set by Ansible
- Infrastructure level

### Chrome Pod Count
```bash
python3 deploy_k8s.py --node-count 5   # 5 Chrome Pods (application level)
```
- Number of **Chrome Pods** in test execution
- Set during deployment
- Application level

**Example:**
- 2 worker nodes in EKS
- 5 Chrome Pods can run
- Pods are distributed to worker nodes by Kubernetes

## Adding New Test Cases

### 1. Create Test File

```python
# test-development/tests/test_new.py

from test_development.test_core.base_test import BaseTest
from test_development.test_config.settings import URLS

class NewTest(BaseTest):
    def test_new_feature(self):
        """New feature test"""
        self.driver.get(URLS['home'])
        # Your test code
        pass
```

### 2. Add to Controller

```python
# devops-kubernetes/devops-k8s-controller/controller.py

def get_test_cases(self):
    test_cases = [
        # ... existing tests
        {
            'id': 'test_new',
            'name': 'New Feature Test',
            'file': 'test_development.tests.test_new',
            'class': 'NewTest',
            'method': 'test_new_feature',
            'priority': 1
        }
    ]
    return test_cases
```

### 3. Rebuild Docker Image

```bash
./docker-operations/build_images.sh
./docker-operations/push_images.sh
```

## Troubleshooting

### Import Error

```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run as Python module
python -m test_development.test_main
```

### Docker Build Error

```bash
# Check paths
ls devops-kubernetes/devops-k8s-controller/Dockerfile.controller
ls devops-kubernetes/chrome-node/Dockerfile.chrome

# Review build logs
docker build --no-cache -f Dockerfile.controller .
```

### Kubernetes Pod Not Starting

```bash
# Check pod status
kubectl get pods -n test-automation

# View pod logs
kubectl logs -f deployment/test-controller -n test-automation

# Describe pod details
kubectl describe pod <pod-name> -n test-automation

# Check events
kubectl get events -n test-automation --sort-by='.lastTimestamp'
```

### EKS Cluster Connection Error

```bash
# Check kubectl config
kubectl config view
kubectl config current-context

# EKS cluster status
aws eks describe-cluster --name insider-test-cluster --region eu-west-1

# Update kubeconfig
aws eks update-kubeconfig --region eu-west-1 --name insider-test-cluster
```

### SSH Connection Error

```bash
# Check EC2 instance status
aws ec2 describe-instances --instance-ids <INSTANCE_ID> --region eu-west-1

# Check Security Group
aws ec2 describe-security-groups --group-names insider-test-sg --region eu-west-1

# SSH key permissions
chmod 600 ~/.ssh/insider-test-key.pem

# Test SSH
ssh -vvv -i ~/.ssh/insider-test-key.pem ec2-user@<EC2_IP>
```

## Cleanup

### Kubernetes Resources

```bash
# Delete pods and deployments
python3 deploy_k8s.py --cleanup

# Or with kubectl
kubectl delete namespace test-automation
```

### EKS Cluster

```bash
cd aws-infra-setup/ansible

# Delete EKS cluster
ansible-playbook 05-cleanup.yml
```

### AWS Prerequisites

```bash
# Delete EC2, SSH Key, Security Group
ansible-playbook 00-cleanup-prerequisites.yml
```

## Documentation

### Main Documents

- **[README.md](README.md)** - This file (project overview and quick start)
- **[test-development/](test-development/)** - Test development folder
- **[KUBERNETES_DEPLOYMENT_GUIDE.md](devops-kubernetes/KUBERNETES_DEPLOYMENT_GUIDE.md)** - Kubernetes deployment and test execution guide **(IMPORTANT)**
- **[Kubernetes Manifests README](devops-kubernetes/k8s/README.md)** - Kubernetes manifests documentation
- **[Controller README](devops-kubernetes/devops-k8s-controller/README.md)** - Test Controller documentation
- **[Cluster Monitoring Guide](devops-kubernetes/docs/KUBERNETES_CLUSTER_MONITORING_GUIDE.md)** - Kubernetes cluster monitoring guide
- **[Docker Operations README](docker-operations/README.md)** - Docker image build and push guide
- **[AWS Infrastructure README](aws-infra-setup/README.md)** - AWS infrastructure setup overview
- **[Ansible Playbooks README](aws-infra-setup/ansible/README.md)** - Detailed Ansible playbooks guide

### Quick Reference

**Test Development:**
```bash
# Run local tests
python test-development/test-main.py
```

**Docker Operations:**
```bash
# Build and push images
./docker-operations/build_images.sh
./docker-operations/push_images.sh
```

**AWS Infrastructure:**
```bash
# Full deployment
cd aws-infra-setup/ansible
ansible-playbook 00-setup-aws-prerequisites.yml
ansible-playbook 01-setup-ec2.yml
ansible-playbook 02-install-tools.yml
ansible-playbook 03-create-eks-cluster.yml
ansible-playbook 04-deploy-k8s-resources.yml
```

**Kubernetes Deployment:**
```bash
# Test execution
python3 deploy_k8s.py --node-count 3
python3 deploy_k8s.py --status
python3 deploy_k8s.py --cleanup
```


## Requirements

### Local Development
- Python 3.8+
- Chrome/Chromium browser
- pip3

### Docker Operations
- Docker 20.10+
- Docker Hub account

### AWS Infrastructure
- AWS account
- AWS CLI configured
- Ansible 2.9+

### Kubernetes Deployment
- kubectl 1.28+
- EKS cluster
- Docker images on registry

## License

MIT

---
