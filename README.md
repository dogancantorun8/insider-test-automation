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

**1. Local Test (Development)**
```bash
# Run tests on your local machine
cd insider/
python test-development/test-main.py
```

### 2. Docker Build & Push

```bash
chmod +x docker-operations/build_images.sh docker-operations/push_images.sh
./docker-operations/build_images.sh
./docker-operations/push_images.sh
```

**3. AWS Infrastructure Setup**
```bash
cd aws-infra-setup/ansible

# Create prerequisites (EC2, SSH Key, Security Group)
ansible-playbook 00-setup-aws-prerequisites.yml

# Install tools
ansible-playbook 02-install-tools.yml

# Create EKS cluster (~15-20 minutes)
ansible-playbook 03-create-eks-cluster.yml

# Deploy K8s resources
ansible-playbook 04-deploy-k8s-resources.yml
```

**4. Run Tests on Kubernetes**
```bash
# Connect to EC2
ssh -i ~/.ssh/your-key.pem ec2-user@YOUR_EC2_IP

# Navigate to project
cd insider/devops-kubernetes

# Run tests with 2 Chrome Nodes
python3 deploy_k8s.py --node-count 2

# Check status
python3 deploy_k8s.py --status

# Cleanup
python3 deploy_k8s.py --cleanup
```

## Project Components

### Test Development
Local test development and debugging.
- **Documentation**: [test-development/](test-development/)
- **Usage**: `python test-development/test-main.py`

### Kubernetes Deployment
Automated deployment and test orchestration.
- **Documentation**: [KUBERNETES_DEPLOYMENT_GUIDE.md](devops-kubernetes/KUBERNETES_DEPLOYMENT_GUIDE.md)
- **Controller**: [devops-k8s-controller/README.md](devops-kubernetes/devops-k8s-controller/README.md)
- **Manifests**: [k8s/README.md](devops-kubernetes/k8s/README.md)
- **Monitoring**: [KUBERNETES_CLUSTER_MONITORING_GUIDE.md](devops-kubernetes/docs/KUBERNETES_CLUSTER_MONITORING_GUIDE.md)
- **Usage**: `python3 deploy_k8s.py --node-count 3`

### Docker Operations
Build and push Docker images.
- **Documentation**: [docker-operations/README.md](docker-operations/README.md)
- **Usage**: `./docker-operations/build_images.sh && ./docker-operations/push_images.sh`

### AWS Infrastructure
Automated AWS EKS cluster setup with Ansible.
- **Documentation**: [aws-infra-setup/README.md](aws-infra-setup/README.md) | [ansible/README.md](aws-infra-setup/ansible/README.md)
- **Usage**: `ansible-playbook 03-create-eks-cluster.yml`

## Configuration

**Docker Hub Credentials**
```bash
export DOCKER_USERNAME=your_username
export DOCKER_PASSWORD=your_password
```

**AWS Configuration** (in `aws-infra-setup/ansible/group_vars/all.yml`)
```yaml
aws_region: eu-west-1
cluster_name: insider-test-cluster
node_type: t2.small
docker_image: your_username/insider-test-controller:latest
```

## Key Features

- **Service-Based Architecture**: Kubernetes Service handles automatic load balancing
- **Parallel Execution**: Run tests across 1-5 Chrome Nodes simultaneously
- **Session Tracking**: Track which pod executed each test
- **Automated Deployment**: Single command deployment via Python script
- **Scalable**: Easy horizontal scaling by adjusting node count
- **Comprehensive Monitoring**: Detailed logging and status tracking

## Important Notes

**Node Count Distinction**
- **EKS Worker Nodes**: Physical EC2 instances (set in `group_vars/all.yml`)
- **Chrome Pods**: Application-level test execution nodes (set via `--node-count`)

Example: 2 EKS worker nodes can host 5 Chrome Pods distributed by Kubernetes.

## Troubleshooting

For detailed troubleshooting, see component-specific documentation:

**kubectl not configured**
```bash
aws eks update-kubeconfig --region eu-west-1 --name insider-test-cluster
```

**Pod issues**
```bash
kubectl get pods -n test-automation
kubectl logs -n test-automation -l app=test-controller
kubectl describe pod -n test-automation <pod-name>
```

**More help**: See [KUBERNETES_DEPLOYMENT_GUIDE.md](devops-kubernetes/KUBERNETES_DEPLOYMENT_GUIDE.md) and [KUBERNETES_CLUSTER_MONITORING_GUIDE.md](devops-kubernetes/docs/KUBERNETES_CLUSTER_MONITORING_GUIDE.md)

## Cleanup

**Kubernetes Resources**
```bash
python3 deploy_k8s.py --cleanup
```

**EKS Cluster**
```bash
cd aws-infra-setup/ansible
ansible-playbook 05-cleanup.yml
```

**AWS Prerequisites**
```bash
ansible-playbook 00-cleanup-prerequisites.yml
```

## Requirements

- **Local Dev**: Python 3.8+, Chrome browser
- **Docker**: Docker 20.10+, Docker Hub account
- **AWS**: AWS account, AWS CLI, Ansible 2.9+
- **Kubernetes**: kubectl 1.28+, EKS cluster

## Documentation

**Core Guides**
- [Kubernetes Deployment Guide](devops-kubernetes/KUBERNETES_DEPLOYMENT_GUIDE.md) - Test execution guide
- [Cluster Monitoring Guide](devops-kubernetes/docs/KUBERNETES_CLUSTER_MONITORING_GUIDE.md) - Monitoring and debugging
- [AWS Infrastructure Setup](aws-infra-setup/ansible/README.md) - Complete infrastructure guide

**Component Documentation**
- [Test Controller](devops-kubernetes/devops-k8s-controller/README.md)
- [Kubernetes Manifests](devops-kubernetes/k8s/README.md)
- [Docker Operations](docker-operations/README.md)

## License

MIT

---
