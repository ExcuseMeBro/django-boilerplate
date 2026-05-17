"""DRF exception handler with active Django language.

LocaleMiddleware activates language from Accept-Language before DRF handles errors.
This handler keeps responses JSON-only and lets lazy translation strings render in active language.
"""

from rest_framework.views import exception_handler


def localized_exception_handler(exc, context):
    return exception_handler(exc, context)
