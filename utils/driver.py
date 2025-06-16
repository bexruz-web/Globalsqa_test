from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def get_driver(url, headless=False):

    driver_path = ChromeDriverManager().install()
    service = ChromeService(driver_path)

    options = Options()

    if headless:
        options.add_argument("--headless=new")

    # Faqat kerakli va qulay local sozlamalar
    options.add_argument("--start-maximized")               # Brauzerni to‘liq ochish
    options.add_argument("--disable-notifications")         # Bildirishnomalarni o‘chirish
    options.add_argument("--disable-infobars")              # "Chrome is being controlled" banneri chiqmasin
    options.add_argument("--disable-extensions")            # Keraksiz extensionlar bloklansin
    options.add_experimental_option("excludeSwitches", ["enable-logging"])  # Terminal loglar kam bo‘lsin

    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(60)
    driver.get(url)
    return driver
