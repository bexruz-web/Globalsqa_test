import os
import time
from datetime import datetime

from colorama import init
from selenium.webdriver import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
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

    def click_input_by_text(self, locator, element_text, input_type='checkbox'):
        """
        Texti bo‘yicha input (checkbox yoki radio) ni topib bosadi
        """
        page_name = self.__class__.__name__

        elements = self._wait_for_presence_all(locator, visible_only=True)
        if not elements:
            message = f"{input_type}lar topilmadi yoki ko‘rinmayapti"
            self.logger.warning(f"{page_name}: {message}: {locator}")
            raise ElementNotFoundError(message, locator)

        for element in elements:
            text = element.text.strip()
            if text == element_text:
                self.logger.info(f"{page_name}: '{element_text}' topildi – tanlanmoqda...")
                input_element = element.find_element(By.TAG_NAME, 'input')

                if not input_element.is_displayed():
                    self._scroll_to_element(input_element, locator)

                status = input_element.is_selected()
                if not status:
                    input_element.click()
                self.logger.info(f"{page_name}: '{element_text}' {'tanlandi' if not status else 'avvaldan tanlangan'}")
                return True

        message = f"'{element_text}' matnli {input_type} topilmadi."
        self.logger.warning(f"{page_name}: {message}: {locator}")
        raise ElementNotFoundError(message, locator)

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

    def get_text(self, locator, retries=3, retry_delay=2):
        """Elementning matnini olish"""

        page_name = self.__class__.__name__
        self.logger.debug(f"{page_name}: Running -> get_text: {locator}")

        attempt = 0
        while attempt < retries:
            try:
                element_dom = self.wait_for_element(locator, wait_type='presence')
                self._scroll_to_element(element_dom, locator)
                element = self.wait_for_element(locator, wait_type='visibility')

                self.logger.info(f"{page_name}: Element text -> '{element.text}'")
                return element.text if element else None

            except ElementStaleError:
                self.logger.warning(f"Element yangilandi, qayta urinish ({attempt + 1})")
                attempt += 1
                time.sleep(retry_delay)

            except Exception as e:
                self.logger.error(f"Element matnini olishda xato: {str(e)}")
                raise

    # ================================================================================================

    def _is_choose_dropdown_option(self, input_locator, element_text):
        input_element = self.wait_for_element(input_locator, wait_type='visibility')
        selected_text = input_element.get_attribute("value")
        if selected_text == element_text:
            self.logger.info(f"Option avvaldan tanlangan: {selected_text}")
            return True
        else:
            self.logger.info("Input tozalanmoqda....")
            self.clear_element(input_locator)
            return False

    # ==================================================================================================

    def _find_and_click_option(self, element, options, options_locator):
        """Element topish va bosish funksiyasi"""
        element_str = str(element).strip()

        for option in options:
            for _ in range(3):
                option_text = option.text.strip()
                if option_text:
                    break
                self.logger.warning(f"Option text topilmadi, qayta uriniladi...")
                time.sleep(1)

            if option_text == element_str:
                self.logger.info(f"Element topildi: '{option_text}', click qilinadi...")
                if self.click(option, options_locator) or self._click(option, options_locator, retry=True):
                    return True
        return False

    # ================================================================================================================

    def click_options(self, input_locator, options_locator, element_text, screenshot=True):
        """Dropdown bilan ishlash funksiyasi. <select> ichidan <option> ni tanlaydi"""
        page_name = self.__class__.__name__
        self.logger.debug(f"{page_name}: Running -> click_options: {element_text} - {input_locator}")

        try:
            # Avvaldan tanlanganligini tekshirish
            if self._is_choose_dropdown_option(input_locator, element_text):
                return True

            # Select elementini kutish, kerak bolsa scroll qilish

            select_element = self.wait_for_element(input_locator, wait_type='visibility')
            if not select_element.is_displayed():
                self._scroll_to_element(select_element, input_locator)

            options = select_element.find_elements(By.TAG_NAME, 'option')
            if not options:
                message = "❗ Optionlar ro'yxati bo'sh!"
                self.logger.warning(f"{page_name}: {message}: {input_locator}")
                raise ElementNotFoundError(message, input_locator)

            if self._find_and_click_option(element_text, options, options_locator):
                return True

            message = f"'{element_text}' option topilmadi <select> ichidan"
            self.logger.warning(message)
            raise ElementNotFoundError(message, input_locator)

        except Exception as e:
            message = f"{page_name}: option tanlashda da kutilmagan xatolik - {str(e)}"
            self.logger.error(message)
            self.take_screenshot(f"{page_name.lower()}_click_options_error")
            raise

    # ========================================================================================================

    def _check_dropdown_closed(self, options_locator, retry_count=3):
        """Dropdown yopilganini tekshirish"""
        page_name = self.__class__.__name__

        if self._wait_for_invisibility_of_locator(options_locator, timeout=2, raise_error=False):
            self.logger.info("Dropdown yopildi!")
            return True

        for attempt in range(retry_count):
            try:
                self.logger.warning(f"❗ Dropdown yopilmadi, urinish: {attempt + 1}/{retry_count}")
                self.logger.info("Sahifani bosh joyiga bosiladi")
                self.driver.execute_script("document.body.click();")
                if self._wait_for_invisibility_of_locator(options_locator, timeout=2, raise_error=True):
                    self.logger.info("Dropdown yopildi! (Sahifani bo'sh qismiga bosish orqali)")
                    return True

                self.logger.warning("Dropdown yopilmadi, ESCAPE bosiladi...")
                body = self.wait_for_element((By.TAG_NAME, 'body'), wait_type='presence')
                body.send_keys(Keys.ESCAPE)
                if self._wait_for_invisibility_of_locator(options_locator, timeout=2, raise_error=False):
                    self.logger.info("Dropdown yopildi! (ESCAPE bosish orqali)")
                    return True

            except (ElementNotFoundError, ElementStaleError) as ee:
                self.logger.warning(f"ESCAPE bosishda xatolik: {str(ee)}")
                continue

            except ElementVisibilityError as eve:
                self.logger.warning(f"Dropdown yopilmadi! {str(eve)}")
                continue

        self.logger.error(f"Dropdown yopilmadi ({retry_count} marta urinishdan keyin ham)")
        self.take_screenshot(f"{page_name.lower()}_dropdown_close_error")
        return False

    # =============================================================================================================

    def close_ads(self, timeout=5):

        page_name = self.__class__.__name__

        ad_close_xpaths = [
            "//span[text() = 'Close']",
            "//div[@id='dismiss-button']"
        ]

        for xpath in ad_close_xpaths:
            locator = (By.XPATH, xpath)
            try:
                close_btn = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
                self._js_click(close_btn, locator)
                self.logger.info(f"{page_name}: Reklama yopildi: {xpath}")
                return True

            except TimeoutException:
                self.logger.debug(f"{page_name}: Reklama topilmadi yoki {timeout} soniya ichida chiqmadi: {xpath}")

            except Exception as e:
                self.logger.warning(f"{page_name}: Reklama yopishda xatolik: {xpath}: {str(e)}")
                self.take_screenshot(f"{page_name.lower()}_unexpected_ad_error")
                continue

        self.logger.debug(f"{page_name}: Hech qanday reklama topilmadi.")
        return False

    # ==================================================================================================================

    def handle_alert(self, accept=True, second_alert=True, timeout=10):
        """
        Alert oynasini boshqarish
        accept=True - OK bosiladi, aks holda Cancel
        handle_followup=True - Keyingi alert chiqsa avtomatik OK bosadi
        """
        page_name = self.__class__.__name__

        try:
            WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
            alert = self.driver.switch_to.alert
            self.logger.info(f"{page_name}: Alert matni: '{alert.text.strip()}'")

            action = 'accept' if accept else 'dismiss'
            getattr(alert, action)()
            self.logger.info(f"{page_name}: {'OK' if accept else 'Cancel'} bosildi.")

            # Keyingi alert (Agar chiqsa, OK qilish)
            if second_alert:
                try:
                    WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
                    second = self.driver.switch_to.alert
                    self.logger.info(f"{page_name}: Keyingi alert matni: '{second.text.strip()}'")
                    second.accept()
                    self.logger.info(f"{page_name}: Keyingi alert OK bosildi.")
                except TimeoutException:
                    self.logger.debug(f"{page_name}: Keyingi alert chiqmadi.")
            return True

        except TimeoutException:
            self.logger.debug(f"{page_name}: Alert {timeout} soniya ichida chiqmadi")

        except Exception as e:
            self.logger.error(f"{page_name}: Alert boshqarishda xatolik: {str(e)}")
            self.take_screenshot(f"{page_name.lower()}_alert_error")
            raise



