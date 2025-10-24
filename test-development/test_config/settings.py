"""
Bu dosya tum URL'ler, selector'lar ve ayarlari icerir   
"""

# URL Konfigurasyonu
URLS = {
    'home': 'https://useinsider.com/',
    'careers': 'https://useinsider.com/careers/',
    'qa_careers': 'https://useinsider.com/careers/quality-assurance/',
    'qa_jobs': 'https://useinsider.com/careers/open-positions/?department=qualityassurance'
}

# CSS Selector'lar
SELECTORS = {
    # Popup ve notification selector'lari
    'popup_selectors': [
        '.ins-notification-content',
        '.ins-element-link', 
        '[class*="ins-notification"]',
        '[class*="ins-element"]',
        '[class*="notification"]',
        '[class*="modal"]',
        '[class*="popup"]'
    ],
    
    'overlay_selectors': [
        '[class*="overlay"]',
        '[class*="backdrop"]'
    ],
    
    # Is karti selector'lari
    'job_card_selectors': [
        "#jobs-list .position-list-item",
        ".position-list-item", 
        "#jobs-list > div",
        "[data-position]",
        ".job-item",
        "[class*='position-item']",
        ".job-card",
        "[class*='job']",
        "div[class*='position']",
        "div[class*='job']"
    ],
    
    # XPath selector'lari
    'job_xpath_selectors': [
        "//div[@id='jobs-list']//div[contains(@class, 'position')]",
        "//div[contains(@class, 'position')]",
        "//div[contains(@class, 'job')]",
        "//div[@id='jobs-list']//div",
        "//*[contains(@class, 'position')]",
        "//*[contains(@class, 'job')]"
    ],
    
    # Is detayi selector'lari
    'position_selectors': ['.position-title', '.position-name', '[class*="title"]', 'h3', 'p'],
    'department_selectors': ['.position-department', '[class*="department"]', 'span'],
    'location_selectors': ['.position-location', '[class*="location"]', 'div'],
    
    # Kapat butonu selector'lari
    'close_button_selectors': [
        'button[aria-label*="close"]',
        '.close',
        '[class*="close"]',
        '[class*="dismiss"]',
        '[aria-label*="Close"]'
    ],
    
    # View Role butonu selector'lari
    'view_role_selectors': [
        "a[href*='lever.co']",
        ".//a[contains(@href, 'lever')]",
        ".//a[contains(text(), 'View Role')]"
    ],
    
    # Lever sayfasi selector'lari
    'lever_selectors': [
        '.postings-btn',
        '.posting-apply-button',
        'a[href*="apply"]'
    ]
}

# Test Ayarlari
TEST_CONFIG = {
    'wait_timeout': 25,
    'scroll_wait': 1,
    'filter_wait': 2,
    'page_load_wait': 3,
    'popup_close_wait': 0.3,
    'job_validation_count': 5
}

# Bekleme Sureleri (saniye)
WAIT_TIMES = {
    'short': 1,
    'medium': 2,
    'long': 3,
    'very_long': 5
}

# Filtre Secenekleri
FILTER_OPTIONS = {
    'location': 'Istanbul, Turkey',
    'department': 'Quality Assurance'
}

# Dogrulama Kriterleri
VALIDATION_CRITERIA = {
    'position_keywords': ['Quality Assurance', 'QA', 'quality'],
    'department_keywords': ['Quality Assurance', 'quality'],
    'location_keywords': ['Istanbul', 'istanbul', 'Turkey', 'turkey']
}

# Debug Ayarlari
DEBUG_CONFIG = {
    'enable_debug': True,
    'show_page_source': False,
    'verbose_logging': True
}

