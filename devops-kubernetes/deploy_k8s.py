#!/usr/bin/env python3
"""
Kubernetes Deployment Script for Selenium Test Automation
This script deploys and manages Test Controller and Chrome Node pods
"""

import os
import sys
import time
import argparse
import logging
from typing import Optional, Dict, Any
from kubernetes import client, config
from kubernetes.client.rest import ApiException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# KubernetesTestDeployer class'i - Kubernetes deployment'i yonetir
class KubernetesTestDeployer:
    
    def __init__(self, namespace: str = "test-automation", kubeconfig: Optional[str] = None):
        """
            namespace: Kubernetes namespace to use
            kubeconfig: Path to kubeconfig file (None for in-cluster config)
        """
        self.namespace = namespace
        self.kubeconfig = kubeconfig
        
        # Load Kubernetes config
        try:
            if kubeconfig:
                config.load_kube_config(config_file=kubeconfig)
                logger.info(f"Loaded kubeconfig from {kubeconfig}")
            else:
                try:
                    config.load_incluster_config()
                    logger.info("Loaded in-cluster Kubernetes configuration")
                except:
                    config.load_kube_config()
                    logger.info("Loaded local Kubernetes configuration")
        except Exception as e:
            logger.error(f"Failed to load Kubernetes config: {e}")
            sys.exit(1)
        
        # Initialize API clients
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.rbac_v1 = client.RbacAuthorizationV1Api()
    
    # Namespace olustur
    def create_namespace(self) -> bool:
        """Create namespace if it doesn't exist"""
        try:
            self.core_v1.read_namespace(name=self.namespace)
            logger.info(f"Namespace '{self.namespace}' already exists")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Creating namespace '{self.namespace}'")
                try:
                    namespace = client.V1Namespace(
                        metadata=client.V1ObjectMeta(
                            name=self.namespace,
                            labels={"name": self.namespace, "app": "selenium-tests"}
                        )
                    )
                    self.core_v1.create_namespace(body=namespace)
                    logger.info(f"Namespace '{self.namespace}' created successfully")
                    return True
                except ApiException as create_error:
                    logger.error(f"Failed to create namespace: {create_error}")
                    return False
            else:
                logger.error(f"Error checking namespace: {e}")
                return False
    
    # YAML manifest'leri uygula
    def apply_yaml_manifests(self) -> bool:
        """Apply all YAML manifests from k8s/ directory"""
        logger.info("Applying Kubernetes manifests")
        
        k8s_dir = "k8s"
        if not os.path.exists(k8s_dir):
            logger.error(f"k8s directory not found: {k8s_dir}")
            return False
        
        # Order of manifest application
        manifest_order = [
            "namespace.yaml",
            "rbac.yaml",
            "configmap.yaml",
            "chrome-node-service.yaml",
            "chrome-node-deployment.yaml",
            "controller-job.yaml"  # controller-deployment.yaml kullanilmiyor CrashLoopBackOff sorunu oldu
        ]
        
        
        for manifest_file in manifest_order:
            manifest_path = os.path.join(k8s_dir, manifest_file)
            if os.path.exists(manifest_path):
                logger.info(f"  Applying {manifest_file}")
                try:
                    # Use kubectl apply (simpler than parsing YAML in Python)
                    import subprocess
                    result = subprocess.run(
                        ["kubectl", "apply", "-f", manifest_path],
                        capture_output=True,
                        text=True
                    )
                    if result.returncode == 0:
                        logger.info(f"    Applied {manifest_file} successfully")
                    else:
                        logger.error(f"    Failed to apply {manifest_file}: {result.stderr}")
                        return False
                except Exception as e:
                    logger.error(f"    Error applying {manifest_file}: {e}")
                    return False
            else:
                logger.warning(f"  Manifest not found: {manifest_file}")
        
        return True
    
    # Chrome Node'larin sayisini scale et
    def scale_chrome_nodes(self, node_count: int) -> bool:
        """
            node_count: Number of Chrome Node replicas (1-5)
        """
        if not 1 <= node_count <= 5:
            logger.error(f"Invalid node_count: {node_count}. Must be between 1 and 5")
            return False
        
        logger.info(f"Scaling Chrome Nodes to {node_count} replica(s)")
        
        try:
            # Get deployment
            deployment = self.apps_v1.read_namespaced_deployment(
                name="chrome-node",
                namespace=self.namespace
            )
            
            # Update replicas
            deployment.spec.replicas = node_count
            
            # Patch deployment
            self.apps_v1.patch_namespaced_deployment(
                name="chrome-node",
                namespace=self.namespace,
                body=deployment
            )
            
            logger.info(f"Chrome Node deployment scaled to {node_count} replica(s)")
            return True
            
        except ApiException as e:
            logger.error(f"Failed to scale Chrome Nodes: {e}")
            return False
    
    # Podlar hazir olana kadar bekle
    def wait_for_pods_ready(self, label_selector: str, expected_count: int, timeout: int = 300) -> bool:
        """
            label_selector: Label selector for pods (e.g., "app=chrome-node")
            expected_count: Expected number of ready pods
            timeout: Timeout in seconds
        """
        logger.info(f"Waiting for {expected_count} pod(s) with selector '{label_selector}' to be ready")
        
        # Podlar hazir olana kadar bekle
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                pods = self.core_v1.list_namespaced_pod(
                    namespace=self.namespace,
                    label_selector=label_selector
                )
                
                ready_pods = 0
                for pod in pods.items:
                    # For Jobs, accept both Running and Succeeded states
                    if pod.status.phase in ["Running", "Succeeded"]:
                        # Check if all containers are ready or terminated successfully
                        if pod.status.container_statuses:
                            all_ready = all(
                                container.ready or (container.state.terminated and container.state.terminated.exit_code == 0)
                                for container in pod.status.container_statuses
                            )
                            if all_ready:
                                ready_pods += 1
                        elif pod.status.phase == "Succeeded":
                            # Job completed successfully
                            ready_pods += 1
                
                logger.info(f"  Ready pods: {ready_pods}/{expected_count}")
                
                if ready_pods >= expected_count:
                    logger.info(f"All {expected_count} pod(s) are ready")
                    return True
                
                time.sleep(5)
                
            except ApiException as e:
                logger.error(f"Error checking pod status: {e}")
                return False
        
        logger.error(f"Timeout: Pods not ready after {timeout}s")
        return False
    
    #Podlarin logu icn 
    def get_pod_logs(self, pod_name: str, tail_lines: int = 50) -> Optional[str]:
        """Get logs from a pod"""
        try:
            logs = self.core_v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                tail_lines=tail_lines
            )
            return logs
        except ApiException as e:
            logger.error(f"Failed to get logs from pod {pod_name}: {e}")
            return None
    
    # Tum pod'larin statusunu al
    def get_pod_status(self) -> Dict[str, Any]:
        """Get status of all pods in namespace"""
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=self.namespace)
            
            status = {
                "total": len(pods.items),
                "running": 0,
                "pending": 0,
                "failed": 0,
                "pods": []
            }
            
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "node": pod.spec.node_name
                }
                status["pods"].append(pod_info)
                
                if pod.status.phase == "Running":
                    status["running"] += 1
                elif pod.status.phase == "Pending":
                    status["pending"] += 1
                elif pod.status.phase == "Failed":
                    status["failed"] += 1
            
            return status
            
        except ApiException as e:
            logger.error(f"Failed to get pod status: {e}")
            return {}
    
    # Tum kaynaklari sil
    def cleanup(self) -> bool:
        """Delete all resources in namespace"""
        logger.info(f"Cleaning up resources in namespace '{self.namespace}'")
        
        try:
            # Delete namespace (this will delete all resources in it)
            self.core_v1.delete_namespace(
                name=self.namespace,
                body=client.V1DeleteOptions(
                    propagation_policy="Foreground"
                )
            )
            logger.info(f"Namespace '{self.namespace}' deleted")
            
            # Wait for namespace deletion
            logger.info("Waiting for namespace to be deleted")
            timeout = 60
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    self.core_v1.read_namespace(name=self.namespace)
                    time.sleep(2)
                except ApiException as e:
                    if e.status == 404:
                        logger.info("Namespace deleted successfully")
                        return True
            
            logger.warning("Namespace deletion timed out")
            return False
            
        except ApiException as e:
            logger.error(f"Failed to cleanup: {e}")
            return False
    
    # Deployment workflow blogum
    def deploy(self, node_count: int = 1) -> bool:
        """
            node_count: Number of Chrome Node replicas (1-5)
        """
        logger.info("=" * 80)
        logger.info("STARTING KUBERNETES DEPLOYMENT")
        logger.info("=" * 80)
        
        # Step 1: Create namespace
        if not self.create_namespace():
            logger.error("Failed to create namespace")
            return False
        
        # Step 2: Apply manifests
        if not self.apply_yaml_manifests():
            logger.error("Failed to apply manifests")
            return False
        
        # Step 3: Scale Chrome Nodes
        if not self.scale_chrome_nodes(node_count):
            logger.error("Failed to scale Chrome Nodes")
            return False
        
        # Step 4: Wait for Chrome Nodes to be ready
        if not self.wait_for_pods_ready("app=chrome-node", node_count, timeout=300):
            logger.error("Chrome Nodes not ready")
            return False
        
        # Step 5: Wait for Controller to be ready
        if not self.wait_for_pods_ready("app=test-controller", 1, timeout=300):
            logger.error("Test Controller not ready")
            return False
        
        # Step 6: Show pod status
        logger.info("\n" + "=" * 80)
        logger.info("DEPLOYMENT STATUS")
        logger.info("=" * 80)
        
        status = self.get_pod_status()
        logger.info(f"Total Pods: {status.get('total', 0)}")
        logger.info(f"Running: {status.get('running', 0)}")
        logger.info(f"Pending: {status.get('pending', 0)}")
        logger.info(f"Failed: {status.get('failed', 0)}")
        
        logger.info("\nPod Details:")
        for pod in status.get('pods', []):
            logger.info(f"  - {pod['name']}: {pod['status']} (IP: {pod['ip']}, Node: {pod['node']})")
        
        logger.info("\n" + "=" * 80)
        logger.info("DEPLOYMENT COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
        # Show logs from controller
        logger.info("\nTest Controller Logs (last 50 lines):")
        logger.info("-" * 80)
        controller_pods = [p for p in status.get('pods', []) if 'test-controller' in p['name']]
        if controller_pods:
            logs = self.get_pod_logs(controller_pods[0]['name'], tail_lines=50)
            if logs:
                print(logs)
        
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Deploy Selenium tests to Kubernetes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Deploy with 1 Chrome Node
  python deploy_k8s.py --node-count 1
  
  # Deploy with 3 Chrome Nodes
  python deploy_k8s.py --node-count 3
  
  # Deploy with custom namespace
  python deploy_k8s.py --node-count 2 --namespace custom-namespace
  
  # Cleanup resources
  python deploy_k8s.py --cleanup
  
  # Check status
  python deploy_k8s.py --status
        """
    )
    
    # Chrome Node sayisini belirle ,giris argumanlari
    parser.add_argument(
        '--node-count',
        type=int,
        default=1,
        choices=[1, 2, 3, 4, 5],
        help='Number of Chrome Node replicas (default: 1)'
    )
    
    parser.add_argument(
        '--namespace',
        type=str,
        default='test-automation',
        help='Kubernetes namespace (default: test-automation)'
    )
    
    parser.add_argument(
        '--kubeconfig',
        type=str,
        help='Path to kubeconfig file (optional)'
    )
    
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Cleanup all resources'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show deployment status'
    )
    
    args = parser.parse_args()
    
    # Initialize deployer
    deployer = KubernetesTestDeployer(
        namespace=args.namespace,
        kubeconfig=args.kubeconfig
    )
    
    # Handle cleanup
    if args.cleanup:
        logger.info("Cleanup mode activated")
        success = deployer.cleanup()
        sys.exit(0 if success else 1)
    
    # Handle status check
    if args.status:
        logger.info("Status check mode")
        status = deployer.get_pod_status()
        
        print("\n" + "=" * 80)
        print("DEPLOYMENT STATUS")
        print("=" * 80)
        print(f"Namespace: {args.namespace}")
        print(f"Total Pods: {status.get('total', 0)}")
        print(f"Running: {status.get('running', 0)}")
        print(f"Pending: {status.get('pending', 0)}")
        print(f"Failed: {status.get('failed', 0)}")
        
        print("\nPod Details:")
        for pod in status.get('pods', []):
            print(f"  - {pod['name']}: {pod['status']} (IP: {pod['ip']})")
        
        sys.exit(0)
    
    # Handle deployment
    success = deployer.deploy(node_count=args.node_count)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

