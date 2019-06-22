from logging import getLogger, NullHandler

logger = getLogger("i18n_core")
logger.addHandler(NullHandler())

try:
    import __builtin__
except ImportError:
    import builtins as __builtin__
import ctypes
import datetime
import locale
import os
import platform
import sys


from platform_utils import paths
import pickle
import babel.core

if paths.is_frozen():
    import pytz

    pytz.resource_exists = lambda name: False
    with open(
        os.path.join(paths.embedded_data_path(), "babel", "global.dat"), "rb"
    ) as fp:
        babel.core._global_data = pickle.load(fp)
from babel import support
import babel.localedata

if paths.is_frozen():
    babel.localedata._dirname = os.path.join(paths.embedded_data_path(), "locale-data")

DEFAULT_LOCALE = "en_US"
CURRENT_LOCALE = DEFAULT_LOCALE

active_translation = support.Translations()
application_locale_path = None


def install_global_translation(domain=None, locale_id=None, locale_path=None):
    global active_translation
    global application_locale_path
    if locale_id is None:
        locale_id = get_system_locale()
    new_translation = support.Translations.load(locale_path, [locale_id], domain)
    active_translation.merge(new_translation)
    active_translation.install()
    install_translation_into_module()
    set_locale(locale_id)
    active_translation.set_output_charset(locale.getlocale()[1])
    application_locale_path = locale_path
    logger.info("Installed translation %s for application %s" % (locale_id, domain))
    return locale_id


def install_module_translation(
    domain=None, locale_id=None, locale_path=None, module=None
):
    if module in sys.modules:
        module = sys.modules[module]
    if active_translation is None:
        logger.warning(
            "Cannot install module translation if there is no global translation active"
        )
        return
    if locale_path is None:
        locale_path = get_locale_path(module)
    if locale_id is None:
        locale_id = CURRENT_LOCALE
    module_translation = support.Translations.load(locale_path, [locale_id], domain)
    active_translation.merge(module_translation)
    logger.debug(
        "Installed translation %s for domain %s into module %r"
        % (locale_id, domain, module)
    )


def install_translation_into_module(module=__builtin__):
    def lazy_gettext(string):
        return support.LazyProxy(lambda: active_translation.ugettext(string))

    module._ = active_translation.ugettext
    module.__ = lazy_gettext
    module.ngettext = lambda s1, s2, n: active_translation.ungettext(s1, s2, n)


mac_locales = {"0:0": "en_GB.utf-8", "0:3": "de_DE.utf-8"}


def get_system_locale():
    if platform.system() == "Windows":
        LCID = ctypes.windll.kernel32.GetUserDefaultLCID()
        try:
            return locale.windows_locale[LCID]
        except KeyError:
            logger.error("Unable to find locale %s" % LCID)
            return DEFAULT_LOCALE
    if "__CF_USER_TEXT_ENCODING" in os.environ:
        lang_code = os.environ["__CF_USER_TEXT_ENCODING"].split(":", 1)[1]
        current_locale = mac_locales.get(lang_code)
        if current_locale:
            return current_locale
    if "LC_ALL" in os.environ:
        return _locale.normalize(os.environ["LC_ALL"])
    current_locale = locale.getdefaultlocale()[0]
    if current_locale is None:
        current_locale = DEFAULT_LOCALE
    return current_locale


def get_locale_path(module=None):
    if not paths.is_frozen():
        return os.path.join(os.path.split(module.__file__)[0], "locale")
    return os.path.join(paths.embedded_data_path(), "locale")


def locale_decode(s):
    encoding = locale.getlocale()[1]
    if encoding is not None:
        s = s.decode(encoding)
    return s


def set_locale(locale_id):
    global CURRENT_LOCALE
    try:
        try:
            current_locale = locale.setlocale(locale.LC_ALL, locale_id)
        except locale.Error:
            current_locale = locale.setlocale(locale.LC_ALL, locale_id.split("_")[0])
    except locale.Error:
        current_locale = locale.setlocale(locale.LC_ALL, "")
        logger.warning("Set to default locale %s" % current_locale)
    # Set the windows locale for this thread to this locale.
    if platform.system() == "Windows":
        LCID = find_windows_LCID(locale_id)
        ctypes.windll.kernel32.SetThreadLocale(LCID)
    CURRENT_LOCALE = locale_id


def find_windows_LCID(locale_id):
    try:
        unicode
    except NameError:
        unicode = str
    # Windows > Vista is able to convert locale names to LCIDs
    func_LocaleNameToLCID = getattr(ctypes.windll.kernel32, "LocaleNameToLCID", None)
    if func_LocaleNameToLCID is not None:
        locale_id = locale_id.replace("_", "-")
        LCID = func_LocaleNameToLCID(unicode(locale_id), 0)
    else:  # Windows doesn't have this functionality, manually search Python's windows_locale dictionary for the LCID
        locale_id = locale.normalize(locale_id)
        if "." in locale_id:
            locale_id = locale_id.split(".")[0]
        LCList = [x[0] for x in locale.windows_locale.iteritems() if x[1] == locale_id]
        if len(LCList) > 0:
            LCID = LCList[0]
        else:
            LCID = 0
    return LCID


def locale_from_locale_id(locale_id):
    language, region = locale_id, None
    if "_" in locale_id:
        language, region = locale_id.split("_")
    return babel.core.Locale(language, region)


def get_available_locales(domain, locale_path=None):
    translations = get_available_translations(domain, locale_path)
    for translation_dir in translations:
        try:
            yield locale_from_locale_id(translation_dir)
        except babel.core.UnknownLocaleError:
            logger.warning(
                "Error retrieving locale for translation %r", translation_dir
            )
            continue


def get_available_translations(domain, locale_path=None):
    if locale_path is None:
        locale_path = application_locale_path
    for directory in os.listdir(locale_path):
        if os.path.exists(
            os.path.join(locale_path, directory, "lc_messages", "%s.mo" % domain)
        ):
            yield directory
    yield DEFAULT_LOCALE


def format_timestamp(timestamp):
    dt = timestamp
    if not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.fromtimestamp(timestamp)
    if dt.date() == dt.today().date():
        return locale_decode(format(dt, "%X"))
    return locale_decode(format(dt, "%c"))
