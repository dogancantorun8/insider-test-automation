from tests.test_home_page import HomeAndCareersTest
from tests.test_qa_page import InsiderTest

if __name__ == "__main__":
    print("=" * 60)
    print("INSIDER TEST OTOMASYONU - LOCAL RUNNER")
    print("=" * 60)
    print()
    print("Mod: Local Development")
    print("Browser: Local Chrome")
    print()
    
    # Tum testleri calistir - tek tarayici ile
    print("Home ve Careers testleri calistiriliyor...")
    home_test = HomeAndCareersTest()
    home_test.run_all_tests()
    
    print("\nQA sayfasi testleri calistiriliyor...")
    qa_test = InsiderTest()
    qa_test.run_all_tests()
    
    # Son tarayici kapatma mesaji
    print("\nTum testler tamamlandi!")
    
