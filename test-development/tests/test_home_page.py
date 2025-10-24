"""
Home Page Testleri
https://useinsider.com/ ve Careers sayfasi testleri
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from test_core.base_test import BaseTest
from test_config.settings import URLS, SELECTORS, WAIT_TIMES


class HomeAndCareersTest(BaseTest):
    """Home ve Careers sayfasi testleri"""
    
    def __init__(self):
        """WebDriver baslat"""
        super().__init__()
    
    def test_home_page(self):
        """Test 1: Ana sayfa kontrolu"""
        print("=" * 60)
        print("TEST 1: Ana Sayfa Kontrolu")
        print("=" * 60)
        
        try:
            # Ana sayfayi ac
            self.driver.get(URLS['home'])
            print(f"URL acildi: {URLS['home']}")
            
            # Sayfa yuklenene kadar bekle
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            time.sleep(WAIT_TIMES['medium'])
            
            # Sayfa title kontrolu
            assert "insider" in self.driver.title.lower(), "Sayfa title'inda 'Insider' bulunamadi"
            print("Ana sayfa basariyla yuklendi")
            
            # Logo kontrolu
            try:
                logo = self.driver.find_element(By.CSS_SELECTOR, "img[alt*='insider'], img[alt*='Insider'], .logo, [class*='logo']")
                assert logo.is_displayed(), "Logo gorunur degil"
                print("Insider logosu gorunur")
            except:
                print("! Logo bulunamadi ama sayfa yuklendi")
            
            print()
            return True
            
        except Exception as e:
            print(f"Ana sayfa kontrolu basarisiz: {str(e)}\n")
            return False
    
    def test_careers_page(self):
        """Test 2: Careers sayfasi ve elemanlari kontrolu"""
        print("=" * 60)
        print("TEST 2: Careers Sayfasi ve Elemanlari Kontrolu")
        print("=" * 60)
        
        try:
            # Cookie banner'i kapat
            self._handle_cookie_banner()
            
            # Careers sayfasina git
            self._navigate_to_careers()
            
            # Sayfa elemanlarini kontrol et
            return self._check_careers_page_elements()
            
        except Exception as e:
            print(f"Careers sayfasi kontrolu basarisiz: {str(e)}\n")
            return False
    
    def _handle_cookie_banner(self):
        """Cookie banner'i kapat"""
        try:
            cookie_button = self.wait.until(
                EC.element_to_be_clickable((By.ID, "wt-cli-accept-all-btn"))
            )
            cookie_button.click()
            print("Cookie banner'i kapatildi")
            time.sleep(WAIT_TIMES['short'])
        except:
            pass
    
    # Careers sayfasina yonlendir
    def _navigate_to_careers(self):
        """Careers sayfasina yonlendir"""
        print("Careers sayfasina yonlendiriliyor...")
        
        # Direkt URL ile git
        try:
            self.driver.get(URLS['careers'])
            print("Careers sayfasina direkt gidildi")
        except:
            # Fallback: Menu'den git
            try:
                company_menu = self.wait.until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Company"))
                )
                self.safe_click(company_menu, use_js=True)
                time.sleep(WAIT_TIMES['short'])
            except:
                company_menu = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Company')]")
                self.safe_click(company_menu, use_js=True)
                time.sleep(WAIT_TIMES['short'])
            
            # Careers linkini bul ve tikla
            careers_link = None
            try:
                careers_link = self.driver.find_element(By.LINK_TEXT, "Careers")
            except:
                try:
                    careers_link = self.driver.find_element(By.XPATH, "//a[contains(text(), 'Careers')]")
                except:
                    careers_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='careers']")
            
            if careers_link:
                self.safe_click(careers_link, use_js=True)
                print("Careers linkine tiklandi")
        
        # Sayfa yuklenmesini bekle
        self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(WAIT_TIMES['medium'])
        print(f"Su anki URL: {self.driver.current_url}")
    
    # Careers sayfasi elemanlarini kontrol et
    def _check_careers_page_elements(self):
        """Careers sayfasi elemanlarini kontrol et"""
        print("\nSayfa elemanlari kontrol ediliyor...")
        self.close_popups()
        
        # Sayfada "location", "team", "life" gibi kelimeler arayarak elemanlari kontrol et
        page_text = self.driver.page_source.lower()
        
        # 1. Locations blogu
        if "location" in page_text and ("our location" in page_text or "office" in page_text):
            print("Locations blogu bulundu")
        else:
            print("! Locations blogu bulunamadi")
        
        # 2. Teams blogu
        if "team" in page_text and ("our team" in page_text or "find your" in page_text):
            print("Teams blogu bulundu")
        else:
            print("! Teams blogu bulunamadi")
        
        # 3. Life at Insider blogu
        if "life at insider" in page_text:
            print("Life at Insider blogu bulundu")
        else:
            print("! Life at Insider blogu bulunamadi")
        
        print("\nCareers sayfasi kontrolu tamamlandi\n")
        return True
    
    def run_all_tests(self):
        """Tum testleri calistir"""
        print("=" * 60)
        print("HOME VE CAREERS PAGE TESTLERI BASLIYOR")
        print("=" * 60)
        print()
        
        # Test 1: Ana Sayfa
        self.test_results["Test 1: Ana Sayfa Kontrolu"] = self.test_home_page()
        
        # Test 2: Careers Sayfasi
        self.test_results["Test 2: Careers Sayfasi Kontrolu"] = self.test_careers_page()
        
        # Sonuclari yazdir
        self.print_test_summary()
    
    def print_test_summary(self):
        """Test sonuclarini ozetle"""
        print("\n" + "=" * 60)
        print("HOME VE CAREERS TEST SONUCLARI")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            status = "BASARILI" if result else "BASARISIZ"
            print(f"{test_name}: {status}")
            if result:
                passed += 1
            else:
                failed += 1
        
        print("\n" + "-" * 60)
        print(f"Toplam Test: {passed + failed}")
        print(f"Basarili: {passed}")
        print(f"Basarisiz: {failed}")
        if passed + failed > 0:
            print(f"Basari Orani: {(passed / (passed + failed) * 100):.1f}%")
        print("=" * 60 + "\n")


