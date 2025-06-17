class ElementInteractionError(Exception):
    """Asosiy xatolik klassi"""

    def __init__(self, message, locator=None, original_error=None):
        self.message = message
        self.locator = locator
        self.original_error = original_error
        super().__init__(self.message)


class ElementNotFoundError(ElementInteractionError):
    """Element topilmasa"""
    def __init__(self, message="Element topilmadi", locator=None, original_error=None):
        super().__init__(message, locator, original_error)


class ElementStaleError(ElementInteractionError):
    """Element yangilanganda"""
    def __init__(self, message="Element bosilmaydigan holatda", locator=None, original_error=None):
        super().__init__(message, locator, original_error)


class ScrollError(ElementInteractionError):
    """Scroll qilishda xatolik"""
    def __init__(self, message="Scroll qilib bolmadi", locator=None, original_error=None):
        super().__init__(message, locator, original_error)


class LoaderTimeoutError(ElementInteractionError):
    """Sahifa yuklanishi xatoligi"""
    def __init__(self, message="Sahifa yuklanmadi", locator=None, original_error=None):
        super().__init__(message, locator, original_error)


class JavaScriptError(ElementInteractionError):
    """JS bajarilishi bilan bogliq xatolik"""
    def __init__(self, message="JS ishlatilganda xatolik yuz berdi", locator=None, original_error=None):
        super().__init__(message, locator, original_error)


def log_exeption_chain(logger, exception):
    """Berilgan exeption va uning sabablarini log qiluvchi funksiya"""
    current_exception = exception
    level = 0
    while current_exception:
        if level == 0:
            logger.error(f'❌ Xato: {current_exception}')
        else:
            logger.error(f'🟡 Sabab ({level}): {current_exception}')
        current_exception = current_exception.__cause__
        level +=1
