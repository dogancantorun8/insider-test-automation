# Ansible Playbooks - AWS EKS Infrastructure

This folder contains Ansible playbooks for AWS EKS cluster setup and management.

## Folder Structure

```
ansible/
├── README.md                          # This file
├── ansible.cfg                        # Ansible configuration
├── inventory.yml                      # Host information (only)
├── requirements.yml                   # Ansible Galaxy requirements
├── environment.sh                     # Environment variables
│ 
│ # Playbooks
├── 00-setup-aws-prerequisites.yml     # Creates EC2, SSH Key, Security Group
├── 00-cleanup-prerequisites.yml       # Prerequisites cleanup
├── 01-setup-ec2.yml                   # EC2 SSH connection test
├── 02-install-tools.yml               # kubectl, eksctl, aws-cli installation
├── 03-create-eks-cluster.yml          # EKS cluster creation
├── 03a-upgrade-nodegroup.yml          # Worker node upgrade
├── 04-deploy-k8s-resources.yml        # K8s namespace, RBAC, ConfigMap
├── 05-cleanup.yml                     # EKS cluster cleanup
│ 
│ # Configuration
├── group_vars/
│   └── all.yml                        # Global variables (SINGLE SOURCE)
│ 
│ # Templates
└── templates/
    └── eks-cluster-config.yaml.j2     # EKS cluster config template
```

## Quick Start

### Prerequisite: AWS Credentials
```bash
aws configure
# Enter AWS Access Key ID, Secret Access Key, Region
```

### Fully Automated Deployment (From Scratch)

```bash
cd ansible

# 1. Create AWS prerequisites
ansible-playbook 00-setup-aws-prerequisites.yml

# 2. Install requirements
ansible-galaxy install -r requirements.yml

# 3. Test EC2 connection
ansible-playbook 01-setup-ec2.yml

# 4. Install tools
ansible-playbook 02-install-tools.yml

# 5. Create EKS cluster
ansible-playbook 03-create-eks-cluster.yml

# 6. Deploy K8s resources
ansible-playbook 04-deploy-k8s-resources.yml
```

**Total Time:** ~25-30 minutes

### Manual Test Execution

```bash
# Connect to EC2
ssh -i ~/.ssh/insider-test-key.pem ec2-user@<EC2_IP>

# Run tests
cd insider/devops-kubernetes
python3 deploy_k8s.py --node-count 2
```

## Playbook Details

### 00-setup-aws-prerequisites.yml
**Purpose:** Creates AWS resources (first time)

**What it does:**
- Creates EC2 instance (t2.small)
- Creates and saves SSH Key pair
- Creates Security Group (SSH, HTTP, HTTPS)
- Writes EC2 public IP to inventory.yml
- Saves SSH key to `.ssh/` folder

**Runs on:** localhost (with AWS CLI)

**Examples:**
```bash
# Run with user confirmation
ansible-playbook 00-setup-aws-prerequisites.yml

# Auto-approve (for CI/CD)
ansible-playbook 00-setup-aws-prerequisites.yml -e "auto_approve=yes"
```

**Created resources:**
- EC2 Instance: insider-test-ec2
- SSH Key: insider-test-key
- Security Group: insider-test-sg
- Local Key: `.ssh/insider-test-key.pem`

---

### 00-cleanup-prerequisites.yml
**Purpose:** AWS prerequisites cleanup

**What it does:**
- Terminates EC2 instance
- Deletes Security Group
- Deletes SSH key pair (AWS + local)
- Cleans temporary files

**Runs on:** localhost

**Usage:**
```bash
# With user confirmation
ansible-playbook 00-cleanup-prerequisites.yml
```

---

### 01-setup-ec2.yml
**Purpose:** EC2 connection test

**What it does:**
- Tests SSH connection
- Verifies EC2 is accessible
- Checks if Python3 is installed

**Runs on:** ec2_instances

**Usage:**
```bash
ansible-playbook 01-setup-ec2.yml
```

---

### 02-install-tools.yml
**Purpose:** Installs required tools

**What it does:**
- kubectl installation (v1.28.0)
- eksctl installation (latest)
- AWS CLI installation (v2)
- Python3 and pip3 installation
- Git installation

**Runs on:** ec2_instances

**Installations:**
```bash
kubectl version --client
eksctl version
aws --version
python3 --version
```

---

### 03-create-eks-cluster.yml
**Purpose:** Creates EKS cluster

**What it does:**
- Creates EKS cluster (with eksctl)
- Creates Worker nodes
- Automatically configures kubectl
- Cluster health check
- Node readiness check

**Runs on:** ec2_instances

**Time:** ~15-20 minutes

**Template usage:**
- `templates/eks-cluster-config.yaml.j2` → `/tmp/eks-cluster-config.yaml`
- Template is dynamically filled:
  - cluster_name: insider-test-cluster
  - aws_region: eu-west-1
  - node_type: t2.small
  - node_count: 2

**Automatic checks:**
- Is cluster ACTIVE?
- Are nodes Ready?
- Is kubectl connection working?

---

### 03a-upgrade-nodegroup.yml
**Purpose:** Updates worker nodes

**What it does:**
- Deletes old nodegroup
- Creates new nodegroup
- Waits for node readiness

**Usage:**
```bash
# After changing node_type or node_count
ansible-playbook 03a-upgrade-nodegroup.yml
```

---

### 04-deploy-k8s-resources.yml
**Purpose:** Deploys Kubernetes resources

**What it does:**
- Creates Namespace (test-automation)
- RBAC setup (ServiceAccount, Role, RoleBinding)
- Creates ConfigMap
- Pulls Docker image
- Prepares deploy_k8s.py script

**Runs on:** ec2_instances

**Created resources:**
```bash
kubectl get namespace test-automation
kubectl get serviceaccount -n test-automation
kubectl get role -n test-automation
kubectl get rolebinding -n test-automation
kubectl get configmap -n test-automation
```

---

### 05-cleanup.yml
**Purpose:** EKS cluster cleanup

**What it does:**
- Deletes Namespace
- Deletes EKS cluster (with eksctl)
- Cleans local kubeconfig
- Deletes temporary files

**Runs on:** ec2_instances

**Time:** ~10-15 minutes

**Usage:**
```bash
ansible-playbook 05-cleanup.yml
```

## Configuration

### ansible.cfg
Ansible behavior settings:

```ini
[defaults]
host_key_checking = False          # No SSH confirmation
inventory = inventory.yml          # Default inventory
remote_user = ec2-user             # Default SSH user
timeout = 3600                     # 60 minute connection timeout
command_timeout = 7200             # 120 minute command timeout
stdout_callback = yaml             # YAML output format
pipelining = True                  # Acceleration

[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
# SSH connection reuse (acceleration)
```

### inventory.yml
Only host information (variables in group_vars/all.yml):

```yaml
all:
  children:
    ec2_instances:
      hosts:
        insider-test-ec2:
          ansible_host: "34.240.70.218"
          ansible_user: ec2-user
          ansible_ssh_private_key_file: "{{ ssh_key_path }}"
          ansible_python_interpreter: /usr/bin/python3
```

### group_vars/all.yml
All global variables (SINGLE SOURCE):

```yaml
# AWS Configuration
aws_region: eu-west-1
cluster_name: insider-test-cluster
node_type: t2.small                # EKS worker node instance type
node_count: 2                      # Number of EKS worker nodes
ssh_key_name: insider-test-key

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

# Security
ssh_key_path: "{{ lookup('env', 'SSH_KEY_PATH') | default('~/.ssh/id_rsa') }}"
ec2_public_ip: "{{ lookup('env', 'EC2_PUBLIC_IP') }}"
```

### environment.sh
Environment variables:

```bash
export EC2_PUBLIC_IP="34.240.70.218"
export SSH_KEY_PATH="~/.ssh/insider-test-key.pem"
```

**Usage:**
```bash
source environment.sh
```

## Features

### 1. Centralized Configuration
- All variables in `group_vars/all.yml` (single source)
- `inventory.yml` only host information
- DRY (Don't Repeat Yourself) principle

### 2. Idempotency
- All playbooks can be re-run
- Retry on error
- State-controlled tasks

### 3. Error Handling
- Error checking at each step
- Retry mechanism
- Detailed error messages
- Graceful failures

### 4. Template-Based Configuration
- Jinja2 templates
- Dynamic configuration
- Environment-specific variables

### 5. Automatic Verification
- Cluster health check
- Node readiness check
- Connection validation
- Resource verification

## Deployment Order

```
1. 00-setup-aws-prerequisites.yml  → Create EC2, SSH Key, SG
   ↓
2. 01-setup-ec2.yml                → Test EC2 connection
   ↓
3. 02-install-tools.yml            → Install kubectl, eksctl, aws-cli
   ↓
4. 03-create-eks-cluster.yml       → Create EKS cluster
   ↓
5. 04-deploy-k8s-resources.yml     → Deploy K8s resources
   ↓
6. Manual: python3 deploy_k8s.py   → Run tests
```

## Cleanup Order

```
1. 05-cleanup.yml                  → Delete EKS cluster
   ↓
2. 00-cleanup-prerequisites.yml    → Delete EC2, SSH Key, SG
```

## Node Count Difference

### EKS Worker Node Count
```yaml
# group_vars/all.yml
node_count: 2    # 2 EC2 worker nodes
```
- Number of **physical EC2 instances** in EKS cluster
- Infrastructure level
- Set by Ansible

### Test Chrome Pod Count
```bash
python3 deploy_k8s.py --node-count 5   # 5 Chrome Pods
```
- Number of **Chrome Pods** in test execution
- Application level
- Set during deployment

**Example:**
- 2 worker nodes in EKS
- 5 Chrome Pods can run (pods distributed to nodes)

## Troubleshooting

### SSH Connection Error
```bash
# Problem
fatal: [insider-test-ec2]: UNREACHABLE!

# Solution
ansible-playbook 01-setup-ec2.yml
ssh -i ~/.ssh/insider-test-key.pem ec2-user@<IP>

# Security Group check
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=insider-test-sg" \
  --region eu-west-1
```

### EKS Cluster Creation Error
```bash
# Check cluster status
aws eks describe-cluster \
  --name insider-test-cluster \
  --region eu-west-1

# Check log
cat /tmp/eks-cluster-config.yaml

# Manual cluster creation
eksctl create cluster --config-file=/tmp/eks-cluster-config.yaml
```

### kubectl Connection Error
```bash
# Check kubeconfig
kubectl config view

# Check context
kubectl config current-context

# Manual update
aws eks update-kubeconfig \
  --region eu-west-1 \
  --name insider-test-cluster
```

### Timeout Error
```bash
# Increase timeouts in ansible.cfg
timeout = 7200
command_timeout = 14400

# Or re-run playbook
ansible-playbook 03-create-eks-cluster.yml
```

## Best Practices

### 1. AWS Credentials Security
```bash
# Use ~/.aws/credentials
aws configure

# Don't use environment variables (security risk)
# export AWS_ACCESS_KEY_ID=...
```

### 2. SSH Key Management
```bash
# Store in .ssh/ folder
~/.ssh/insider-test-key.pem

# Set correct permissions
chmod 600 ~/.ssh/insider-test-key.pem

# Add to .gitignore
echo "*.pem" >> .gitignore
```

### 3. Idempotent Playbooks
```yaml
# Each task should be idempotent
- name: "Create namespace"
  command: kubectl create namespace test-automation
  register: namespace_creation
  failed_when: false  # Idempotent
  changed_when: namespace_creation.rc == 0
```

### 4. Error Handling
```yaml
# Retry mechanism
retries: 5
delay: 10
until: result.rc == 0

# Graceful failure
failed_when: false
ignore_errors: yes
```

### 5. Cleanup
```bash
# Always cleanup (cost)
ansible-playbook 05-cleanup.yml
ansible-playbook 00-cleanup-prerequisites.yml
```

## Example Usage Scenarios

### Scenario 1: First Time Setup
```bash
cd ansible

# 1. Prerequisites
ansible-playbook 00-setup-aws-prerequisites.yml

# 2. Full deployment
ansible-playbook 01-setup-ec2.yml
ansible-playbook 02-install-tools.yml
ansible-playbook 03-create-eks-cluster.yml
ansible-playbook 04-deploy-k8s-resources.yml

# 3. Test
ssh -i ~/.ssh/insider-test-key.pem ec2-user@<IP>
cd insider/devops-kubernetes
python3 deploy_k8s.py --node-count 3
```

### Scenario 2: EKS Update Only
```bash
# node_type: t2.small → t2.medium changed
# Update group_vars/all.yml

# Upgrade nodes
ansible-playbook 03a-upgrade-nodegroup.yml
```

### Scenario 3: Cleanup and Reinstall
```bash
# 1. Cleanup
ansible-playbook 05-cleanup.yml
ansible-playbook 00-cleanup-prerequisites.yml

# 2. Reinstall
ansible-playbook 00-setup-aws-prerequisites.yml
ansible-playbook 01-setup-ec2.yml
# ...
```

## Support

For any issues:

1. **Check playbook logs**
   ```bash
   ansible-playbook 03-create-eks-cluster.yml -vvv
   ```

2. **Manual check on EC2 instance**
   ```bash
   ssh -i ~/.ssh/insider-test-key.pem ec2-user@<IP>
   kubectl get nodes
   kubectl get pods -n test-automation
   ```

3. **AWS Console check**
   - https://eu-west-1.console.aws.amazon.com/ec2/
   - https://eu-west-1.console.aws.amazon.com/eks/

4. **Ansible inventory check**
   ```bash
   ansible-inventory --list
   ansible all -m ping
   ```

5. **Debug mode**
   ```bash
   ANSIBLE_DEBUG=1 ansible-playbook 03-create-eks-cluster.yml
   ```

## References

- **Ansible Documentation:** https://docs.ansible.com/
- **eksctl Documentation:** https://eksctl.io/
- **AWS EKS Documentation:** https://docs.aws.amazon.com/eks/
- **kubectl Documentation:** https://kubernetes.io/docs/reference/kubectl/
