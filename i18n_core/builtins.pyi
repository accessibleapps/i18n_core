"""Type stubs for i18n_core's builtin injection.

This module provides type information for the translation functions
that i18n_core injects into Python's builtins at runtime via
install_translation_into_module(builtins).

These functions are available globally without import after i18n_core
initializes the translation system.
"""

from babel.support import LazyProxy

def _(message: str) -> str:
    """Immediate translation function.

    Translates the message immediately and returns a string.
    Uses the current locale and domain context.

    Args:
        message: The message string to translate

    Returns:
        The translated string
    """
    ...

def __(message: str) -> LazyProxy:
    """Lazy translation function.

    Returns a LazyProxy that delays translation until the string is actually used.
    Useful when the locale might not be known at function definition time.

    Args:
        message: The message string to translate

    Returns:
        A LazyProxy object that evaluates to the translated string when used
    """
    ...

def ngettext(singular: str, plural: str, n: int) -> str:
    """Plural forms translation function.

    Selects the appropriate plural form based on the count and locale.

    Args:
        singular: The singular form message
        plural: The plural form message
        n: The count to determine which form to use

    Returns:
        The appropriate translated string based on the count
    """
    ...
