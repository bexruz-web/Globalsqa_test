from colorama import init
from selenium.common.exceptions import WebDriverException, NoSuchElementException, StaleElementReferenceException, \
    TimeoutException, JavascriptException
from selenium.webdriver.common.action_chains import ActionChains

from utils.exeption import ElementNotFoundError, ElementStaleError, ScrollError, JavaScriptError, \
    ElementInteractionError
from utils.logger import get_test_name, configure_logging

init(autoreset=True)


class BasePage:
    # =======================================================================================
    def __init__(self, driver):
        self.driver = driver
        self.test_name = get_test_name()
        self.logger = configure_logging(self.test_name)
        self.default_timeout = 30
        self.default_page_load_timeout = 120
        self.actions = ActionChains

    # =========================================================================================

    def _click(self, element, locator=None, retry=False, error_message=True):
        """Oddiy click funksiyasi"""
        page_name = self.__class__.__name__
        try:
            element.click
            self.logger.info(f"⏺ {page_name}: {'Retry' if retry else ''}Click: {locator}")
            return True
        except WebDriverException:
            if error_message:
                self.logger.warning(f"❗ {'Retry' if retry else ''}Click ishlamadi: {locator}")
            return False

    # =======================================================================

    def _js_click(self, element, locator=None, retry=False):
        """JS orqali majburish bosamiz"""
        page_name = self.__class__.__name__
        try:
            self.driver.execute_script("arguments[0].click();", element)
            self.logger.info(f"⏺ {page_name}: {'Retry' if retry else ''}JS Click: {locator}")
            return True
        except WebDriverException:
            self.logger.warning(f"❗ {'Retry' if retry else ''}JS Click ishlamadi: {locator}")

    # ===============================================================================================================

    def scroll_to_element(self, element, locator, timeout=None):
        """Scroll qilish funksiyasi"""
        page_name = self.__class__.__name__
        timeout = timeout or self.default_timeout

        try:
            if element is None:
                raise ElementNotFoundError(message="Element topilmadi. Scroll qilishni iloji yuq", locator=locator)
            if element.is_displayed():
                return element

            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", element)

            if element.is_displayed():
                self.logger.info(f"⏺ {page_name}: Scroll muvaffaqiyatli bajarildi: {locator}")
                return element

        except NoSuchElementException as e:
            message = f"Element topilmadi, scroll ishlamadi."
            self.logger.warning(f"❗ {page_name}: {message}: {locator}: {str(e)}")
            raise ElementNotFoundError(message, locator, e)

        except StaleElementReferenceException as e:
            message = f"Element DOM da yangilandi (scroll)"
            self.logger.warning(f"❗ {page_name}: {message}: {locator}: {str(e)}")
            raise ElementStaleError(message, locator, e)

        except TimeoutException as e:
            message = f"Element {timeout}s ichida sahifada korinmadi (scroll)"
            self.logger.warning(f"❗ {page_name}: {message}: {locator}: {str(e)}")
            raise ScrollError(message, locator, e)

        except JavascriptException as je:
            message = "JavaScript scrollIntoView xatoligi (scroll)."
            self.logger.warning(f"❗ {page_name}: {message}: {locator}: {str(je)}")
            raise JavaScriptError(message, locator, je)

        except Exception as e:
            message = f"Scroll qilishda kutilmagan xatolik"
            self.logger.warning(f"❗ {page_name}: {message}: {locator}: {str(e)}")
            raise ElementInteractionError(message, locator, e)

        # ==========================================================================================
