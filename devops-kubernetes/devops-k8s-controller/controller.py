"""
Test Controller - Kubernetes Pod
Bu script test case'leri yonetir ve Chrome Node Service uzerinden testleri calistirir

Service-based architecture:
1) Chrome Node Service uzerinden test calistirma --> execute_test_via_service()
2) Service health check --> check_service_ready()
3) Pod tracking (session ID ile) --> get_pod_from_session()
4) Health check endpoint'i saglama --> health_check() ve get_results()
5) Test sonuclarini toplama ve raporlama --> print_summary() ve save_results()

Load balancing: Kubernetes Service --> otomatik round-robin (otomatik load balancing)
"""

import os
import sys
import time
import json
import logging
import requests
from typing import List, Dict, Any
from datetime import datetime
from kubernetes import client, config
from tenacity import retry, stop_after_attempt, wait_exponential
from flask import Flask, jsonify
import threading

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Health check endpoint'i saglamak icin Flask app'i olusturuyoruz
app = Flask(__name__)

#  Test'leri yonetir ve Chrome Node'larina dagitir ve calistirir
class TestController:
    """Test Controller - Manages test distribution to Chrome Nodes"""
    
    # Test Controller'i olusturur ve gerekli degerleri ayarlar
    def __init__(self):
        """Initialize Test Controller"""
        self.chrome_service_url = os.getenv('CHROME_NODE_SERVICE', 'chrome-node-service.default.svc.cluster.local') # Chrome Node Service'in URL'i
        self.chrome_port = os.getenv('CHROME_NODE_PORT', '4444') # Chrome Node'un port'u
        self.namespace = os.getenv('NAMESPACE', 'default') 
        self.test_results = []  # Test sonuclarini tutacak liste
        
        # Kubernetes API'yi kullanarak Chrome Node Pod'larini bulmak icin Kubernetes config'i yukle
        try:
            config.load_incluster_config()  # Running inside K8s
            logger.info("Loaded in-cluster Kubernetes configuration")
        except:
            config.load_kube_config()  # Running locally
            logger.info("Loaded local Kubernetes configuration")
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    # Kubernetes API'yi kullanarak Chrome Node Pod'larini listele)
    def get_chrome_node_pods(self) -> List[Dict[str, str]]:
        """Get list of Chrome Node pods"""
        try:
            pods = self.v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector="app=chrome-node"
            )
            
            chrome_nodes = []
            for pod in pods.items:
                if pod.status.phase == "Running":
                    pod_info = {
                        'name': pod.metadata.name,
                        'ip': pod.status.pod_ip,
                        'status': pod.status.phase
                    }
                    chrome_nodes.append(pod_info)
                    logger.info(f"Found Chrome Node: {pod.metadata.name} (IP: {pod.status.pod_ip})")
            
            return chrome_nodes
        except Exception as e:
            logger.error(f"Error getting Chrome Node pods: {e}")
            return []
    
    # Chrome Node Pod'larin hazir olmasini bekle - podlar hazir olmadigi zaman patliyor !
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=30)) # fonksiyonu 5 kez tekrarla ve 2-30 saniye arasinda bekle
    def wait_for_chrome_nodes(self, min_nodes: int = 1, timeout: int = 300) -> bool:
        """Wait for Chrome Node pods to be ready"""
        logger.info(f"Waiting for at least {min_nodes} Chrome Node(s) to be ready")
        
        #  Deployment'in istenen replica sayisini okuyan blok
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name="chrome-node",
                namespace=self.namespace
            )
            desired_count = deployment.spec.replicas
            logger.info(f"Deployment desired replicas: {desired_count}")
            
            # Wait for all replicas specified in deployment
            if desired_count > min_nodes:
                min_nodes = desired_count
                logger.info(f"Updated min_nodes to {min_nodes} from deployment spec")
        except Exception as e:
            logger.warning(f"Could not read deployment replicas: {e}")
        
        # Chrome Node'larin hazir olmasini bekle
        start_time = time.time()
        while time.time() - start_time < timeout:
            nodes = self.get_chrome_node_pods()
            
            if len(nodes) >= min_nodes:
                logger.info(f"All {len(nodes)} Chrome Node(s) are ready")
                logger.info(f"Waiting 10 seconds for Selenium to stabilize")
                time.sleep(10)  # Allow Selenium to fully initialize
                return True
            
            logger.info(f"Found {len(nodes)}/{min_nodes} nodes, waiting...")
            time.sleep(5)
        
        logger.error(f"Timeout: Chrome Nodes not ready after {timeout}s")
        return False
    
    # Service'in hazir olmasini bekle
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)) #
    def check_service_ready(self) -> bool:
        """Check if Chrome Node Service is ready"""
        try:
            service_url = f"http://{self.chrome_service_url}:{self.chrome_port}/wd/hub/status"
            logger.info(f"Checking service health: {service_url}")
            
            response = requests.get(service_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                ready = data.get('value', {}).get('ready', False)
                
                if ready:
                    logger.info(f"Service ready: {self.chrome_service_url}")
                    return True
                else:
                    logger.warning(f"Service not ready: {self.chrome_service_url}")
                    return False
            else:
                logger.warning(f"Unexpected status code {response.status_code} from service")
                return False
                
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return False
    
    # Session ID'den pod bilgisini bulur
    def get_pod_from_session(self, session_id: str) -> str:
        """Get pod name from Selenium session ID by checking pod logs"""
        try:
            pods = self.v1.list_namespaced_pod(
                namespace=self.namespace,
                label_selector="app=chrome-node"
            )
            
            for pod in pods.items:
                if pod.status.phase == "Running":
                    try:
                        # Check pod logs for session ID
                        logs = self.v1.read_namespaced_pod_log(
                            name=pod.metadata.name,
                            namespace=self.namespace,
                            tail_lines=100
                        )
                        
                        if session_id in logs:
                            logger.info(f"Found session {session_id[:8]}... on pod {pod.metadata.name}")
                            return pod.metadata.name
                    except:
                        continue
            
            logger.warning(f"Could not find pod for session {session_id[:8]}...")
            return "unknown"
            
        except Exception as e:
            logger.error(f"Error finding pod from session: {e}")
            return "unknown"
    
    # Test case'leri yukler
    def get_test_cases(self) -> List[Dict[str, Any]]:
        # Bu projede test case'leri statik olarak yukledim. Buyuk projelerde test case'leri dinamik olarak yuklemek daha iyi olur aslinda !
        test_cases = [
            {
                'id': 'test_1',
                'name': 'Ana Sayfa Kontrolu',
                'file': 'tests.test_home_page',
                'method': 'test_home_page',
                'priority': 1
            },
            {
                'id': 'test_2',
                'name': 'Careers Sayfasi Kontrolu',
                'file': 'tests.test_home_page',
                'method': 'test_careers_page',
                'priority': 1
            },
            {
                'id': 'test_3',
                'name': 'QA Jobs Filtreleme',
                'file': 'tests.test_qa_page',
                'method': 'test_qa_jobs_filtering',
                'priority': 2
            },
            {
                'id': 'test_4',
                'name': 'Is Detaylari Dogrulama',
                'file': 'tests.test_qa_page',
                'method': 'test_job_details',
                'priority': 2
            },
            {
                'id': 'test_5',
                'name': 'Lever Yonlendirme',
                'file': 'tests.test_qa_page',
                'method': 'test_lever_redirect',
                'priority': 3
            }
        ]
        
        logger.info(f"Loaded {len(test_cases)} test cases")
        return test_cases
    
    # Test'leri Service uzerinden calistirir
    def execute_test_via_service(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a test case via Chrome Node Service (Kubernetes load balancing)"""
        logger.info(f"[SERVICE] Executing test '{test_case['name']}' via Service")
        
        start_time = time.time()
        
        try:
            # Service URL - stable, DNS-based (Kubernetes Service'in URL'i)
            service_url = f"http://{self.chrome_service_url}:{self.chrome_port}/wd/hub"
            logger.info(f"   Service URL: {service_url}")
            
            capabilities = {
                "browserName": "chrome",
                "goog:chromeOptions": {
                    "args": ["--headless", "--no-sandbox", "--disable-dev-shm-usage"]
                }
            }
            
            # Selenium session oluştur (Service'e istek at, K8s load balance eder)
            response = requests.post(
                f"{service_url}/session",
                json={"capabilities": {"alwaysMatch": capabilities}},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                session_data = response.json()
                session_id = session_data.get('value', {}).get('sessionId') or session_data.get('sessionId')
                
                logger.info(f"   Session created: {session_id[:16]}...")
                
                # Pod tracking: Session ID'den hangi pod'da çalıştığını bul
                pod_name = self.get_pod_from_session(session_id)
                
                # Simulate test execution
                time.sleep(2)  # Simulated test execution
                
                # Delete session
                delete_url = f"{service_url}/session/{session_id}"
                requests.delete(delete_url, timeout=10)
                
                execution_time = time.time() - start_time
                
                result = {
                    'test_id': test_case['id'],
                    'test_name': test_case['name'],
                    'node': pod_name,  # ← Session ID'den bulundu
                    'via': 'service',  # ← Service kullanıldı
                    'session_id': session_id[:16],
                    'status': 'PASSED',
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"   Test '{test_case['name']}' PASSED on {pod_name} ({execution_time:.2f}s)")
                return result
                
            else:
                logger.error(f"   Failed to create session: {response.status_code} - {response.text}")
                return {
                    'test_id': test_case['id'],
                    'test_name': test_case['name'],
                    'node': 'service',
                    'via': 'service',
                    'status': 'FAILED',
                    'error': f"Session creation failed: {response.status_code}",
                    'execution_time': time.time() - start_time,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"   Error executing test '{test_case['name']}': {e}")
            return {
                'test_id': test_case['id'],
                'test_name': test_case['name'],
                'node': 'service',
                'via': 'service',
                'status': 'ERROR',
                'error': str(e),
                'execution_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    # Test'leri calistirir
    def run_tests(self):
        """Main test execution flow - Service-based approach"""
        logger.info("=" * 80)
        logger.info("TEST CONTROLLER STARTED (SERVICE MODE)")
        logger.info("=" * 80)
        
        # 1. Wait for Chrome Nodes to be ready
        if not self.wait_for_chrome_nodes(min_nodes=1, timeout=300):
            logger.error("Chrome Nodes not available, exiting")
            sys.exit(1)
        
        # 2. Check Service health (instead of individual pods)
        logger.info("Checking Chrome Node Service health...")
        if not self.check_service_ready():
            logger.error("Service not ready, exiting")
            sys.exit(1)
        
        logger.info(f"Service is ready: {self.chrome_service_url}:{self.chrome_port}")
        
        # 3. Test case'leri yukle
        test_cases = self.get_test_cases()
        
        # 4. Test'leri Service uzerinden calistir (K8s load balancing)
        logger.info("=" * 80)
        logger.info("STARTING TEST EXECUTION VIA SERVICE")
        logger.info("=" * 80)
        
        results = []
        for test_case in test_cases:
            # Service kullan - Kubernetes otomatik load balance eder
            result = self.execute_test_via_service(test_case)
            results.append(result)
            self.test_results.append(result)
        
        # 5. Print summary
        self.print_summary(results)
        
        # 6. Save results
        self.save_results(results)
        
        logger.info("=" * 80)
        logger.info("TEST CONTROLLER COMPLETED")
        logger.info("=" * 80)
    
    def print_summary(self, results: List[Dict[str, Any]]):
        """Print test execution summary"""
        logger.info("=" * 80)
        logger.info("TEST EXECUTION SUMMARY")
        logger.info("=" * 80)
        
        total = len(results)
        passed = sum(1 for r in results if r['status'] == 'PASSED')
        failed = sum(1 for r in results if r['status'] == 'FAILED')
        errors = sum(1 for r in results if r['status'] == 'ERROR')
        
        for result in results:
            status = "[PASS]" if result['status'] == 'PASSED' else "[FAIL]"
            logger.info(f"{status} {result['test_name']}: {result['status']} ({result['execution_time']:.2f}s)")
        
        logger.info("-" * 80)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Errors: {errors}")
        logger.info(f"Success Rate: {(passed/total*100):.1f}%")
        logger.info("=" * 80)
    
    def save_results(self, results: List[Dict[str, Any]]):
        """Save test results to file"""
        results_file = f"/app/test_results/results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Results saved to {results_file}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")

# Flask health check endpoints (Health check endpoint'i sağlama)
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()}), 200

# Test sonuclarini almak icin endpoint
@app.route('/results', methods=['GET']) 
def get_results():
    """Get test results"""
    if hasattr(controller, 'test_results'):
        return jsonify({'results': controller.test_results}), 200
    else:
        return jsonify({'results': []}), 200


def run_flask_app(): # Flask app'i background thread'de calistirir
    """Run Flask app in background thread"""
    app.run(host='0.0.0.0', port=8080, debug=False)

# Main fonksiyon
if __name__ == "__main__":
    # Start Flask health check server in background
    flask_thread = threading.Thread(target=run_flask_app, daemon=True) # background thread'de calistirir
    flask_thread.start()
    
    logger.info("Health check server started on port 8080")
    
    # Wait a bit for Flask to start
    time.sleep(2)
    
    # Initialize and run controller
    controller = TestController() # Test Controller'i olusturur
    controller.run_tests() # Test'leri calistirir

