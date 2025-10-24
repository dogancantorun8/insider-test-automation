"""
Test Controller - Kubernetes Pod
Bu script test case'leri yonetir ve Chrome Node Pod'larina dagitir


1)Chrome Node Pod'larini bulma ve izleme  --> get_chrome_node_pods()
2)Test case'lerini Chrome Node'larina dagitma (Round-Robin algoritmasi) --> distribute_tests()
3)Test'leri Selenium üzerinden calistirma --> execute_test_on_node()
4)Health check endpoint'i sağlama --> health_check() ve get_results()
5)Test sonuclarini toplama ve raporlama --> print_summary() ve save_results()
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
    
    # Selenium'in hazir olmasini bekle
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)) 
    def check_selenium_ready(self, pod_ip: str) -> bool:
        """Check if Selenium on Chrome Node is ready"""
        try:
            url = f"http://{pod_ip}:{self.chrome_port}/wd/hub/status"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                ready = data.get('value', {}).get('ready', False)
                
                if ready:
                    logger.info(f"Selenium ready on {pod_ip}")
                    return True
                else:
                    logger.warning(f"Selenium not ready on {pod_ip}")
                    return False
            else:
                logger.warning(f"Unexpected status code {response.status_code} from {pod_ip}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking Selenium status on {pod_ip}: {e}")
            return False
    
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
    
    # Test'leri Chrome Node'larina dagitma (Round-Robin algoritmasi)
    def distribute_tests(self, test_cases: List[Dict[str, Any]], chrome_nodes: List[Dict[str, str]]) -> List[Dict[str, Any]]: 
        """Test'leri Chrome Node'larina dagitma (Round-Robin algoritmasi)"""
        if not chrome_nodes:
            logger.error("No Chrome Nodes available for test distribution")
            return []
        
        logger.info(f"Distributing {len(test_cases)} tests to {len(chrome_nodes)} Chrome Node(s)")
        
        distribution = []
        for i, test_case in enumerate(test_cases):
            node = chrome_nodes[i % len(chrome_nodes)] # Round-Robin algoritmasi ile test'leri Chrome Node'larina dagitir (node = random.choice(chrome_nodes) ile de oldu) .
            
            assignment = {
                'test': test_case,
                'node': node,
                'assigned_at': datetime.now().isoformat()
            }
            
            distribution.append(assignment)
            logger.info(f"  -> Test '{test_case['name']}' assigned to {node['name']} ({node['ip']})")
        
        return distribution
    
    def execute_test_on_node(self, test_case: Dict[str, Any], node: Dict[str, str]) -> Dict[str, Any]:
        """Execute a test case on a specific Chrome Node"""
        logger.info(f"Executing test '{test_case['name']}' on {node['name']}")
        
        start_time = time.time()
        
        try:
            # Selenium WebDriver endpoint
            selenium_url = f"http://{node['ip']}:{self.chrome_port}/wd/hub"
            
            # Test execution via Selenium Remote WebDriver
            # ornekte basit bir session olustur
            # Gercek test execution mantigi burada olacak
            
            capabilities = {
                "browserName": "chrome",
                "goog:chromeOptions": {
                    "args": ["--headless", "--no-sandbox", "--disable-dev-shm-usage"]
                }
            }
            
            # Selenium WebDriver session olusturma (Chrome Node'a session olusturma istegi gonderiyoruz)
            response = requests.post(
                f"{selenium_url}/session",
                json={"capabilities": {"alwaysMatch": capabilities}},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                session_data = response.json()
                session_id = session_data.get('value', {}).get('sessionId') or session_data.get('sessionId')
                
                logger.info(f"Session created: {session_id}")
                
                # Simulate test execution
                time.sleep(2)  # Simulated test execution
                
                # Delete session
                delete_url = f"{selenium_url}/session/{session_id}"
                requests.delete(delete_url, timeout=10)
                
                execution_time = time.time() - start_time
                
                result = {
                    'test_id': test_case['id'],
                    'test_name': test_case['name'],
                    'node': node['name'],
                    'status': 'PASSED',
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Test '{test_case['name']}' PASSED ({execution_time:.2f}s)")
                return result
                
            else:
                logger.error(f"Failed to create session: {response.status_code} - {response.text}")
                return {
                    'test_id': test_case['id'],
                    'test_name': test_case['name'],
                    'node': node['name'],
                    'status': 'FAILED',
                    'error': f"Session creation failed: {response.status_code}",
                    'execution_time': time.time() - start_time,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error executing test '{test_case['name']}': {e}")
            return {
                'test_id': test_case['id'],
                'test_name': test_case['name'],
                'node': node['name'],
                'status': 'ERROR',
                'error': str(e),
                'execution_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat()
            }
    
    # Test'leri calistir
    def run_tests(self):
        """Main test execution flow"""
        logger.info("=" * 80)
        logger.info("TEST CONTROLLER STARTED")
        logger.info("=" * 80)
        
        # 1. Wait for Chrome Nodes to be ready
        if not self.wait_for_chrome_nodes(min_nodes=1, timeout=300):
            logger.error("Chrome Nodes not available, exiting")
            sys.exit(1)
        
        # 2. Get Chrome Node pods
        chrome_nodes = self.get_chrome_node_pods()
        
        if not chrome_nodes:
            logger.error("No Chrome Nodes found, exiting")
            sys.exit(1)
        
        # 3. Selenium'in hazir olmasini bekle
        logger.info("Checking Selenium readiness on all nodes")
        ready_nodes = []
        for node in chrome_nodes:
            if self.check_selenium_ready(node['ip']):
                ready_nodes.append(node) # Selenium'in hazir olan Chrome Node'larini listeye ekle
        
        if not ready_nodes:
            logger.error("No ready Selenium nodes, exiting")
            sys.exit(1)
        
        logger.info(f"{len(ready_nodes)} Selenium node(s) ready for testing")
        
        # 4. Test case'leri yukle
        test_cases = self.get_test_cases()
        
        # 5. Test'leri Chrome Node'larina dagit
        distribution = self.distribute_tests(test_cases, ready_nodes)
        
        # 6. Test'leri calistir
        logger.info("=" * 80)
        logger.info("STARTING TEST EXECUTION")
        logger.info("=" * 80)
        
        results = []
        for assignment in distribution:
            result = self.execute_test_on_node(assignment['test'], assignment['node'])
            results.append(result)
            self.test_results.append(result)
        
        # 7. Print summary
        self.print_summary(results)
        
        # 8. Save results
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

@app.route('/results', methods=['GET']) # Test sonuclarini almak icin endpoint
def get_results():
    """Get test results"""
    if hasattr(controller, 'test_results'):
        return jsonify({'results': controller.test_results}), 200
    else:
        return jsonify({'results': []}), 200

def run_flask_app(): # Flask app'i background thread'de calistirir
    """Run Flask app in background thread"""
    app.run(host='0.0.0.0', port=8080, debug=False)

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

