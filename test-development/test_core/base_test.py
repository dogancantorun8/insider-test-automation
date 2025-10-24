"""
Base Test Class - Ortak fonksiyonlar
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import time
from functools import wraps
from test_config.settings import URLS, SELECTORS, TEST_CONFIG, WAIT_TIMES, FILTER_OPTIONS, VALIDATION_CRITERIA, DEBUG_CONFIG


class BaseTest:
    """Tum testler icin ortak base class"""
    
    def __init__(self):
        """WebDriver baslat"""
        print("WebDriver baslatiliyor...")
        options = webdriver.ChromeOptions()
        
        # Docker icin headless mode ayarlari   #Lokal test icin kapali
        #options.add_argument('--headless')
        #options.add_argument('--no-sandbox')
        #options.add_argument('--disable-dev-shm-usage')
        #options.add_argument('--disable-gpu')
        
        # Lokal test icin headless mode kapali
        # options.add_argument('--headless')  # Docker icin gerekli, lokal icin kapali
        options.add_argument('--start-maximized')
        options.add_argument('--window-size=1920,1080')
        
        # Diger ayarlar
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-notifications')
        
        # TensorFlow Lite hatasi icin
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        self.wait = WebDriverWait(self.driver, TEST_CONFIG['wait_timeout'])
        self.test_results = {}
        print("WebDriver basariyla baslatildi\n")
    
    def close_popups(self):
        """Popup ve notification kapat"""
        try:
            popup_selectors = SELECTORS['popup_selectors']
            overlay_selectors = SELECTORS['overlay_selectors']
            
            for selector in popup_selectors:
                try:
                    popups = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for popup in popups:
                        try:
                            close_buttons = popup.find_elements(By.CSS_SELECTOR, 
                                ', '.join(SELECTORS['close_button_selectors']))
                            
                            if close_buttons:
                                close_buttons[0].click()
                            else:
                                popup.send_keys(Keys.ESCAPE)
                        except:
                            self.driver.execute_script("arguments[0].remove();", popup)
                except:
                    continue
            
            for selector in overlay_selectors:
                try:
                    overlays = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for overlay in overlays:
                        try:
                            self.driver.execute_script("arguments[0].remove();", overlay)
                        except:
                            pass
                except:
                    continue
        except:
            pass
    
    def retry_on_exception(self, max_retries=3):
        """Hata durumunda tekrar dene"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return func(*args, **kwargs)
                    except (StaleElementReferenceException, ElementClickInterceptedException) as e:
                        if attempt < max_retries - 1:
                            time.sleep(1)
                            continue
                        raise e
                return None
            return wrapper
        return decorator
    
    def safe_click(self, element, use_js=False):
        """Guvenli tiklama - popup'lari kapatarak"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.close_popups()
                
                if use_js:
                    self.driver.execute_script("arguments[0].click();", element)
                else:
                    element.click()
                return True
            except (ElementClickInterceptedException, StaleElementReferenceException):
                if attempt < max_attempts - 1:
                    time.sleep(0.5)
                    self.close_popups()
                    continue
                else:
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
        return False
    
    def __del__(self):
        """Tarayiciyi kapat"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except:
            pass
    
    def print_test_summary(self):
        """Test sonuclarini yazdir"""
        print("\n" + "=" * 60)
        print("TEST SONUCLARI OZETI")
        print("=" * 60)
        
        for test_name, result in self.test_results.items():
            status = "BASARILI" if result else "BASARISIZ"
            print(f"{test_name}: {status}")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results.values() if r)
        failed = total - passed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print("\n" + "-" * 60)
        print(f"Toplam Test: {total}")
        print(f"Basarili: {passed}")
        print(f"Basarisiz: {failed}")
        print(f"Basari Orani: {success_rate:.1f}%")
        print("=" * 60)

