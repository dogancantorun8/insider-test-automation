# AWS Infrastructure Setup

This folder contains Ansible playbooks for AWS EKS cluster setup and management.

## Folder Structure

```
aws-infra-setup/
├── README.md                              # This file
└── ansible/
    ├── README.md                          # Ansible documentation
    ├── ansible.cfg                        # Ansible configuration
    ├── inventory.yml                      # Inventory file (host information only)
    ├── requirements.yml                   # Ansible requirements
    ├── environment.sh                     # Environment variables
    ├── 00-setup-aws-prerequisites.yml     # AWS prerequisites (EC2, SSH Key, Security Group)
    ├── 00-cleanup-prerequisites.yml       # Prerequisites cleanup
    ├── 01-setup-ec2.yml                   # EC2 SSH connection test
    ├── 02-install-tools.yml               # Tools installation (kubectl, eksctl, aws-cli)
    ├── 03-create-eks-cluster.yml          # EKS cluster creation
    ├── 03a-upgrade-nodegroup.yml          # EKS nodegroup upgrade
    ├── 04-deploy-k8s-resources.yml        # Kubernetes resources deployment
    ├── 05-cleanup.yml                     # EKS cluster cleanup
    ├── group_vars/
    │   └── all.yml                        # Global variables (single source)
    └── templates/
        └── eks-cluster-config.yaml.j2     # EKS cluster configuration template
```

## Quick Start

### 1. Prerequisites
- AWS account and credentials (`aws configure`)
- Ansible installed (on local machine)
- AWS CLI installed

### 2. AWS Prerequisites Setup (First Time)
```bash
cd ansible

# Create EC2 instance, SSH Key and Security Group
ansible-playbook 00-setup-aws-prerequisites.yml

# Test EC2 connection
ansible-playbook 01-setup-ec2.yml
```

### 3. Tools Installation (On EC2)
```bash
# Install kubectl, eksctl, aws-cli
ansible-playbook 02-install-tools.yml
```

### 4. EKS Cluster Creation
```bash
# Create EKS cluster (15-20 minutes)
ansible-playbook 03-create-eks-cluster.yml
```

### 5. Kubernetes Resources Deployment
```bash
# Create Namespace, RBAC, ConfigMap
ansible-playbook 04-deploy-k8s-resources.yml
```

### 6. Manual Test Execution
```bash
# Connect to EC2
ssh -i ~/.ssh/insider-test-key.pem ec2-user@<EC2_IP>

# Run tests
cd insider/devops-kubernetes
python3 deploy_k8s.py --node-count 2
```

### 7. Cleanup
```bash
# EKS cluster cleanup
ansible-playbook 05-cleanup.yml

# AWS prerequisites cleanup (EC2, SSH Key, SG)
ansible-playbook 00-cleanup-prerequisites.yml
```

## Features

### Infrastructure Only Setup
- Only AWS EKS infrastructure is prepared
- Tests are not run automatically
- Infrastructure ready for manual test execution

### Automatic kubectl Configuration
- kubectl is automatically configured after EKS cluster creation
- `aws eks update-kubeconfig` command runs automatically
- Cluster connection is verified

### Manual Test Execution
- Tests are run manually after infrastructure is ready
- Test execution with `python3 deploy_k8s.py --node-count X` command
- Scalable test execution with node count parameter

### Centralized Configuration
- All variables in `group_vars/all.yml` file
- `inventory.yml` contains only host information
- Template-based EKS cluster configuration

## Deployment Steps

### 1. AWS Prerequisites
- Create EC2 instance (t2.small)
- Create and save SSH Key pair
- Create Security Group (SSH, HTTP, HTTPS)
- Save EC2 public IP to inventory.yml

### 2. Tools Installation
- kubectl installation (v1.28.0)
- eksctl installation (latest)
- AWS CLI installation (v2)
- Python3 and pip installation

### 3. EKS Cluster Creation
- Create AWS EKS cluster
- Create Worker nodes (t2.small, node_count)
- Automatic kubectl configuration
- Verify cluster connection

### 4. Kubernetes Resources
- Create Namespace (test-automation)
- RBAC setup (ServiceAccount, Role, RoleBinding)
- Create ConfigMap
- Pull Docker image

### 5. Manual Test Execution
- Test execution with `devops-kubernetes/deploy_k8s.py` script
- Scalable deployment with node count parameter
- Test distribution with inter-pod communication

## Configuration

### Environment Variables (environment.sh)
```bash
export EC2_PUBLIC_IP="34.240.70.218"          # EC2 public IP
export SSH_KEY_PATH="~/.ssh/insider-test-key.pem"  # SSH private key path
```

### Global Variables (group_vars/all.yml)
```yaml
# AWS Configuration
aws_region: eu-west-1                         # AWS region
cluster_name: insider-test-cluster            # EKS cluster name
node_type: t2.small                           # EC2 instance type (for worker nodes)
node_count: 2                                 # Number of EKS worker nodes
ssh_key_name: insider-test-key                # SSH key pair name

# Tools Versions
kubectl_version: "v1.28.0"
eksctl_version: "latest"
aws_cli_version: "2"

# Project Configuration
project_name: insider-test-automation
namespace: test-automation
docker_image: dogancan4040/insider-test-controller:latest

# Paths (on EC2)
project_path: /home/ec2-user/insider
devops_k8s_path: /home/ec2-user/insider/devops-kubernetes
```

### Inventory (inventory.yml)
```yaml
# Only host information (variables in group_vars/all.yml)
all:
  children:
    ec2_instances:
      hosts:
        insider-test-ec2:
          ansible_host: "34.240.70.218"       # EC2 public IP
          ansible_user: ec2-user
          ansible_ssh_private_key_file: "{{ ssh_key_path }}"
          ansible_python_interpreter: /usr/bin/python3
```

### NOTE: Test Execution Node Count
```bash
# EKS worker node count: defined in group_vars/all.yml (node_count: 2)
# Test Chrome Pod count: Determined during deployment:
python3 deploy_k8s.py --node-count 3   # 3 Chrome Pods
python3 deploy_k8s.py --node-count 5   # 5 Chrome Pods
```

## Playbook Descriptions

| Playbook | Description | Runs On |
|----------|----------|--------------|
| `00-setup-aws-prerequisites.yml` | Creates EC2, SSH Key, Security Group | localhost |
| `00-cleanup-prerequisites.yml` | Deletes EC2, SSH Key, Security Group | localhost |
| `01-setup-ec2.yml` | Tests EC2 connection | ec2_instances |
| `02-install-tools.yml` | Installs kubectl, eksctl, aws-cli | ec2_instances |
| `03-create-eks-cluster.yml` | Creates EKS cluster | ec2_instances |
| `03a-upgrade-nodegroup.yml` | Updates worker nodes | ec2_instances |
| `04-deploy-k8s-resources.yml` | Creates K8s namespace, RBAC, ConfigMap | ec2_instances |
| `05-cleanup.yml` | Deletes EKS cluster | ec2_instances |

## Troubleshooting

### SSH Connection Problem
```bash
# Test
ansible-playbook 01-setup-ec2.yml

# Manual SSH test
ssh -i ~/.ssh/insider-test-key.pem ec2-user@<EC2_IP>
```

### EKS Cluster Creation Error
```bash
# Check cluster status
aws eks describe-cluster --name insider-test-cluster --region eu-west-1

# Check nodes
kubectl get nodes

# Check kubectl config on EC2
kubectl config view
```

### Cleanup Problem
```bash
# First delete EKS cluster
ansible-playbook 05-cleanup.yml

# Then delete EC2 and other resources
ansible-playbook 00-cleanup-prerequisites.yml

# Manual AWS Console check
# https://eu-west-1.console.aws.amazon.com/ec2/
```

## Best Practices

1. **Single Source Principle:** All variables in `group_vars/all.yml` file
2. **Idempotency:** All playbooks can be re-run
3. **Error Handling:** Detailed error checking in each playbook
4. **Security:** SSH keys in `.ssh/` folder, in gitignore
5. **Cleanup:** Always cleanup to prevent unnecessary costs

