import contextlib
import locale
from logging import getLogger

logger = getLogger("i18n_core.reset_locale")

# context manager to reset the locale


@contextlib.contextmanager
def reset_locale():
    locale_name = locale.getlocale()
    yield
    logger  .debug("Resetting locale to %s" % str(locale_name))
    if len(locale_name) == 2:
        locale_name = locale_name[0]
    locale.setlocale(locale.LC_ALL, locale_name)
