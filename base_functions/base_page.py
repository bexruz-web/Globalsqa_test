import os
import time

from datetime import datetime

from colorama import init
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.logger import get_test_name, configure_logging

from selenium.common.exceptions import (
    WebDriverException, NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException, JavascriptException)

from utils.exeption import (
    ElementNotFoundError, ElementStaleError,
    ScrollError, JavaScriptError,
    ElementInteractionError, ElementVisibilityError,
    ElementNotClickableError)


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

    def take_screenshot(self, filename=None):
        """Fayl nomiga vaqt va test nomini qo'shib, screenshotni saqlash"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_name = self.test_name if self.test_name != "unknown_test" else "default"

            # Fayl nomini yasash
            if filename:
                filename = f"{test_name}_{timestamp}_{filename}"
            else:
                filename = f"{test_name}_{timestamp}"

            screenshot_dir = "screenshot"
            os.makedirs(screenshot_dir, exist_ok=True)

            screenshot_path = os.path.join(screenshot_dir, f"{filename}.png")
            self.driver.save_screenshot(screenshot_path)
            self.logger.info(f"Screenshot saved at {screenshot_path}")

        except Exception as e:
            self.logger.error(f"❌ Screenshot olishda xatolik: {str(e)}")

    def _click(self, element, locator=None, retry=False, error_message=True):
        """Oddiy click funksiyasi"""
        page_name = self.__class__.__name__
        try:
            element.click()
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

    def _scroll_to_element(self, element, locator, timeout=None):
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

    # ==============================================================================================

    def wait_for_element(self, locator, timeout=None, wait_type="presence", error_message=True, screenshot=False):
        """Umumiy kutish funksiyasi:
        * "presence" - DOMda mavjudligini kutadi
        * "visibility" = Ko'rinadigan holatga kelishini kutadi
        * "clickable" - Bosiladigan holatga kelishini kutadi
        """

        page_name = self.__class__.__name__
        timeout = timeout or self.default_timeout

        wait_types = {
            "presence": EC.presence_of_element_located,
            "visibility": EC.visibility_of_element_located,
            "clickable": EC.element_to_be_clickable
        }

        if wait_type not in wait_types:
            raise ValueError(f"Notogri wait_type: '{wait_type}'. Faqat 'presence', 'visibility', yoki 'clickable', bo'lishi mumkin.")

        try:
            element = WebDriverWait(self.driver, timeout).until(wait_types[wait_type](locator))
            return element

        except StaleElementReferenceException as e:
            message = f"Element {wait_type} kutishida DOM yangilandi."
            if error_message:
                self.logger.warning(f"❗ {page_name}: {message}: {locator}: {str(e)}")
                raise ElementStaleError(message, locator, e)

        except TimeoutException as e:
            message = f"Element {timeout}s ichida {wait_type}shartiga yetmadi."
            if error_message:
                self.logger.warning(f"{page_name}: {message}: {locator}: {str(e)}")
            if screenshot:
                self.take_screenshot(f"{page_name}_{screenshot}")

            if wait_type == "visibility":
                raise ElementVisibilityError(message, locator, e)
            elif wait_type == "clickable":
                raise ElementNotClickableError(message, locator, e)
            else:
                raise ElementNotFoundError(message, locator, e)

        except Exception as e:
            message = f"Element {wait_type} kutishida kutilmagan xatolik"
            if error_message:
                self.logger.warning(f"❗  {page_name}: {message}: {locator}: {str(e)}")
            raise ElementInteractionError(message, locator, e)

    # ===============================================================================================

    def click(self, locator, retries=3, retry_delay=3):
        """Asosiy click funksiyasi"""
        page_name = self.__class__.__name__
        self.logger.debug(f"{page_name}: Running click: {locator}")

        attempt = 0
        while attempt < retries:
            try:
                element_dom = self.wait_for_element(locator, wait_type="presence")
                self._scroll_to_element(element_dom, locator)
                self.wait_for_element(locator, wait_type='visibility')
                element_clickable = self.wait_for_element(locator, wait_type='clickable')
                if element_clickable and self._click(element_clickable, locator):
                    return True

                time.sleep(retry_delay)
                self.logger.info("Retry Click sinab ko'riladi")
                element_clickable = self.wait_for_element(locator, wait_type='clickable')
                if element_clickable and self._click(element_clickable, locator, retry=True):
                    return True

                time.sleep(retry_delay)
                self.logger.info("Majburiy JS Click sinab ko'riladi")
                element_dom = self.wait_for_element(locator, wait_type="presence")
                if element_dom and self._js_click(element_dom, locator):
                    return True

            except (ElementStaleError, ScrollError, JavaScriptError) as e:
                self.logger.warning(f"❗ Kutilmagan xatolik: {str(e)}: {locator}")
                self.take_screenshot(f"{page_name.lower()}_click_error")
                raise

            attempt += 1

        message = f"Element barcha usullar bilan ham bosilmadi ({attempt}/{retries})"
        self.logger.warning(f"❗ {page_name}: {message}: {locator}")
        self.take_screenshot(f"{page_name.lower()}_click_all_error")
        raise ElementInteractionError(message, locator)

    # ==============================================================================================

    def wait_for_element_visible(self, locator, retries=3, retry_delay=2):
        """Elementni ko'rinishini kutish"""
        page_name = self.__class__.__name__
        self.logger.debug(f"{page_name}: Running -> wait_for_element_visible: {locator}")

        time.sleep(1)
        attempt = 0
        while attempt < retries:
            try:
                element_dom = self.wait_for_element(locator, wait_type='presence')
                self._scroll_to_element(element_dom, locator)
                element = self.wait_for_element(locator, wait_type='visibility')

                if element:
                    self.logger.info(f"⏺ {page_name}: Element topildi: {locator}")
                    return element

            except (ElementStaleError, ScrollError, JavaScriptError) as e:
                self.logger.warning(f"❗ {page_name}: {e.message}, qayta urinish ({attempt + 1}/{retries})")
                time.sleep(retry_delay)

            except Exception as e:
                self.logger.warning(f"❗ Kutilmagan xatolik: {str(e)}: {locator}")
                self.take_screenshot(f"{page_name.lower()}_visible_error")
                raise

            attempt += 1

        message = f"Element barcha usullar bilan ham topilmadi ({attempt}/{retries})"
        self.logger.warning(f"{page_name}: {message}: {locator}")
        self.take_screenshot(f"{page_name.lower()}_visible_all_error")
        raise ElementInteractionError(message, locator)

    # ==============================================================================================

    def _wait_for_presence_all(self, locator, timeout=None, visible_only=False):
        """Elementlar ro'yxatini kutish"""
        page_name = self.__class__.__name__
        timeout = timeout or self.default_timeout

        try:
            elements = WebDriverWait(self.driver, timeout).until(EC.presence_of_all_elements_located(locator))
            if visible_only:
                elements = [element for element in elements if element.is_displayed()]
            return elements

        except StaleElementReferenceException as e:
            message = "Elementlar ro'yxati DOMda yangilandi"
            self.logger.warning(f"❗ {page_name}: {message}: {locator}")
            raise ElementStaleError(message, locator, e)

        except TimeoutException as e:
            message = "Elementlar ro'yxati topilmadi"
            self.logger.error(f"❌ {page_name}: {message}: {locator}")
            raise ElementNotFoundError(message, locator, e)

        except Exception as e:
            message = "Elementlar ro'yxatini qidirishda kutilmagan xatolik"
            self.logger.error(f"❌ {page_name}: {message}: {locator}")
            raise ElementInteractionError(message, locator, e)

    # ============================================================================================

    def _wait_for_invisibility_of_element(self, element, timeout=None, error_message=None):
        """Element ni ko'rinmas bo'lishini kutish"""
        timeout = timeout or self.default_timeout

        try:
            return WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element(element))
        except TimeoutException as e:
            if error_message:
                self.logger.error(f"❌ Element interfeysdan yo'qolmadi: {e}")
            return False

    # ===============================================================================================

    def _wait_for_invisibility_of_locator(self, locator, timeout=None, raise_error=True):
        """Locator ko'rinmas bo'lishini kutish"""
        page_name = self.__class__.__name__
        timeout = timeout or self.default_timeout

        try:
            WebDriverWait(self.driver, timeout).until(EC.invisibility_of_element_located(locator))
            return True

        except StaleElementReferenceException as e:
            message = "Element DOM da yangilandi"
            self.logger.warning(f"❗ {page_name}: {message}: {locator}")
            raise ElementStaleError(message, locator, e)

        except TimeoutException as e:
            message = "Element ko'rinmas bo'lmadi"
            self.logger.warning(f"❗ {page_name}: {message}: {locator}")
            if raise_error:
                raise ElementVisibilityError(message, locator, e)
            else:
                return False

        except Exception as e:
            message = "Element kutishda kutilmagan xato"
            self.logger.warning(f"{page_name}: {message}: {locator}: {str(e)}")
            raise ElementInteractionError(message, locator, e)

        # =======================================================================================

    def input_text(self, locator, text=None, retries=3, retry_delay=2, check=False, get_value=False):
        """Elementni topish va matn kiritish funksiyasi"""
        page_name = self.__class__.__name__
        self.logger.debug(f"{page_name}: Running -> input_text: {locator}")

        attempt = 0
        while attempt < retries:
            try:
                if get_value:
                    element_dom = self.wait_for_element(locator, wait_type='presence')
                    value = element_dom.get_attribute("value")
                    self.logger.info(f'⏺ Input: get_value -> "{value}"')
                    return value

                if text:
                    element_dom = self.wait_for_element(locator, wait_type='presence')
                    self._scroll_to_element(element_dom, locator)
                    element_clickable = self.wait_for_element(locator, wait_type='clickable')

                    element_clickable.clear()
                    element_clickable.send_keys(text)
                    self.logger.info(f"Input: send_key -> '{text}'")

                if check:
                    element_dom = self.wait_for_element(locator, wait_type='presence')
                    check_text = self.driver.execute_script("return arguments[0].value;", element_dom)
                    self.logger.info(f"Check Input Value: -> '{check_text}'")
                    if check_text != text:
                        self.driver.execute_script(f"arguments[0].value = '{text}';", element_dom)
                return True

            except ElementStaleError:
                self.logger.warning(f"❗ Input yangilandi, qayta urinish ({attempt + 1})")
                attempt += 1
                time.sleep(retry_delay)

            except Exception as e:
                self.logger.error(f"Matn kiritishda xatolik: {str(e)}: {locator}")
                self.take_screenshot(f"{page_name.lower()}_input_error")
                raise

    # ==============================================================================================

    def clear_element(self, locator, retries=3, retry_delay=2):
        """Elementni tozalash"""
        page_name = self.__class__.__name__
        self.logger.debug(f"{page_name}: Running -> clear_element: {locator}")

        attempt = 0
        while attempt < retries:
            try:
                element_dom = self.wait_for_element(locator, wait_type="presence")
                self._scroll_to_element(element_dom, locator)
                element = self.wait_for_element(locator, wait_type="clickable")

                # Element readonly yoki disable emasligini tekshiramiz
                if not element.is_enabled() or element.get_attribute('readonly'):
                    self.logger.warning(f"❗ Elementni tozalab bolmadi, u readonly yoki disabled. {locator}")
                    return False

                # Elementni ko'rinasdiganligini tekshirish
                if not element.is_displayed():
                    self.logger.warning(f"❗ Element ko‘rinmayapti, JS orqali tozalaymiz: {locator}")
                    self.driver.execute_script("arguments[0].value = '';", element)
                    return True

                element.clear()
                self.logger.info(f"Element muvaffaqiyatli tozalandi: {locator}")
                return True

            except ElementStaleError:
                self.logger.warning(f"❗ Element yangilandi, qayta urinish: ({attempt + 1})")
                attempt += 1
                time.sleep(retry_delay)

            except Exception as e:
                self.logger.error(f"Element textni o'chirishda kutilmagan xato: {str(e)}")

        message = f"❗ Element {retries} urinishdan keyin ham tozalanmadi: {locator}"
        self.logger.warning(message)
        raise ElementInteractionError(message)

    # =================================================================================================

    def upload_file(self, locator, file_path):
        """Fayl yuklash funksiyasi"""
        page_name = self.__class__.__name__

        # Fayl borligini tekshiramiz
        if not os.path.isfile(file_path):
            message = f"❌ Fayl topilmadi: {file_path}"
            self.logger.error(f"{page_name}: {message}")
            raise FileNotFoundError(message)

        try:
            file_input = self.driver.find_element(*locator)

            if not file_input.is_displayed():
                self._scroll_to_element(file_input)

            file_input.send_keys(file_path)
            self.logger.info(f"✅ Fayl muvaffaqiyatli yuklandi: {file_path}")

        except NoSuchElementException as e:
            message = "Fayl input elementi topilmadi"
            self.logger.error(f"{page_name}: {message}: {str(e)}")
            raise

        except JavaScriptError as e:
            message = "Scroll qilishda xatolik"
            self.logger.error(f"❌ {page_name}: {message}: {str(e)}")
            raise

    # ==============================================================================================

