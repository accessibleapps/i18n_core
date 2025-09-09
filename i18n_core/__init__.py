from __future__ import absolute_import

import ctypes
import datetime
import locale
import os
import platform
import sys
from logging import getLogger
from types import ModuleType
from typing import Any, Callable, Iterable, Optional

import babel.core
from babel import support
from platform_utils import paths

from .registry import (
    DEFAULT_LOCALE,
    REGISTRY,
    ensure_inferred_provider,
    get_calling_module_name,
    infer_domain_from_module,
)

logger = getLogger("i18n_core")


try:
    import __builtin__ as builtins
except ImportError:
    import builtins


CURRENT_LOCALE: str = DEFAULT_LOCALE

# Back-compat placeholder; dynamically computed from default domain
active_translation: support.Translations = support.Translations()
application_locale_path: Optional[str] = None


def patch() -> None:
    from . import patches


# ---------------------------
# Core dynamic translation API
# ---------------------------

def _get_translator_for_domain(domain: str) -> support.NullTranslations:
    return REGISTRY.get_domain_translations(domain)


def _resolve_domain_for_call() -> str:
    mod_name = get_calling_module_name()
    if not mod_name:
        domain = REGISTRY.get_default_domain() or infer_domain_from_module("i18n_core")
        logger.debug("i18n: resolve domain: no caller, using %s", domain)
        return domain
    # explicit mapping?
    mapped = REGISTRY.get_module_domain(mod_name)
    if mapped:
        logger.debug("i18n: resolve domain: caller=%s mapped=%s", mod_name, mapped)
        return mapped
    # infer from module name; ensure provider registration once
    module_obj = sys.modules.get(mod_name)
    mod_file = getattr(module_obj, "__file__", None)
    domain = ensure_inferred_provider(mod_name, mod_file)
    # If we have no providers for the inferred domain, fall back to default
    if not REGISTRY.providers_for(domain):
        fallback = REGISTRY.get_default_domain() or domain
        logger.debug("i18n: resolve domain: caller=%s inferred=%s providers=0 fallback=%s", mod_name, domain, fallback)
        return fallback
    logger.debug("i18n: resolve domain: caller=%s inferred=%s", mod_name, domain)
    return domain or (REGISTRY.get_default_domain() or infer_domain_from_module(mod_name))


def _dynamic_gettext(message: str) -> str:
    domain = _resolve_domain_for_call()
    t = _get_translator_for_domain(domain)
    # Python 3 compatibility
    gettext_func = getattr(t, "gettext", getattr(t, "ugettext", None))
    if gettext_func is None:
        return message
    return gettext_func(message)


def _dynamic_ngettext(singular: str, plural: str, n: int) -> str:
    domain = _resolve_domain_for_call()
    t = _get_translator_for_domain(domain)
    ngettext_func = getattr(t, "ngettext", getattr(t, "ungettext", None))
    if ngettext_func is None:
        return singular if n == 1 else plural
    return ngettext_func(singular, plural, n)


def _dynamic_lazy_gettext(message: str) -> support.LazyProxy:
    try:
        return support.LazyProxy(lambda: _dynamic_gettext(message), enable_cache=False)  # type: ignore[call-arg]
    except TypeError:
        # Older Babel without enable_cache
        return support.LazyProxy(lambda: _dynamic_gettext(message))


def install_translation_into_module(module: ModuleType = builtins, domain: Optional[str] = None) -> None:
    """Install dynamic translation functions into a module.

    The installed functions resolve translations at call time and reflect
    the current locale and domain configuration.
    """

    bound_domain = domain
    if bound_domain is None:
        # infer from given module
        mod_name = getattr(module, "__name__", None)
        if mod_name:
            bound_domain = infer_domain_from_module(mod_name)
            # ensure an inferred provider exists so lookups work without explicit registration
            mod_file = getattr(module, "__file__", None)
            ensure_inferred_provider(mod_name, mod_file)
    logger.debug("i18n: installing wrappers into module=%s domain=%s", getattr(module, "__name__", None), bound_domain)

    def _mod_gettext(msg: str) -> str:
        d = bound_domain or _resolve_domain_for_call()
        t = _get_translator_for_domain(d)
        gf = getattr(t, "gettext", getattr(t, "ugettext", None))
        return gf(msg) if gf else msg

    def _mod_ngettext(s1: str, s2: str, n: int) -> str:
        d = bound_domain or _resolve_domain_for_call()
        t = _get_translator_for_domain(d)
        ngf = getattr(t, "ngettext", getattr(t, "ungettext", None))
        return ngf(s1, s2, n) if ngf else (s1 if n == 1 else s2)

    def _mod_lazy(msg: str) -> support.LazyProxy:
        try:
            return support.LazyProxy(lambda: _mod_gettext(msg), enable_cache=False)  # type: ignore[call-arg]
        except TypeError:
            return support.LazyProxy(lambda: _mod_gettext(msg))

    module._ = _mod_gettext
    module.__ = _mod_lazy
    module.ngettext = _mod_ngettext


MAC_LOCALES = {"0:0": "en_GB.utf-8", "0:3": "de_DE.utf-8"}


def get_system_locale() -> str:
    """Attempts to return the current system locale as an LCID"""
    if platform.system() == "Windows":
        LCID = ctypes.windll.kernel32.GetUserDefaultLCID()
        try:
            return locale.windows_locale[LCID]
        except KeyError:
            logger.error("Unable to find locale %s", LCID)
            return DEFAULT_LOCALE
    if "__CF_USER_TEXT_ENCODING" in os.environ:
        lang_code = os.environ["__CF_USER_TEXT_ENCODING"].split(":", 1)[1]
        current_locale = MAC_LOCALES.get(lang_code)
        if current_locale:
            return current_locale
    if "LC_ALL" in os.environ:
        return locale.normalize(os.environ["LC_ALL"])
    current_locale = locale.getdefaultlocale()[0]
    if current_locale is None:
        current_locale = DEFAULT_LOCALE
    return current_locale


def get_locale_path(module: Optional[ModuleType] = None) -> str:
    """

    Args:
      module: (Default value = None)

    Returns:

    """
    if not paths.is_frozen():
        return os.path.join(os.path.split(module.__file__)[0], "locale")
    return os.path.join(paths.embedded_data_path(), "locale")


def locale_decode(s: Any) -> str:
    """

    Args:
      s: The string to decode

    Returns:

    """
    encoding = locale.getlocale()[1]
    if encoding is not None:
        s = s.decode(encoding)
    return s  # type: ignore[return-value]


def set_locale(locale_id: str) -> str:
    """

    Args:
      locale_id:

    Returns:

    """
    global CURRENT_LOCALE, active_translation
    try:
        try:
            current_locale = locale.setlocale(locale.LC_ALL, locale_id)
        except locale.Error:
            current_locale = locale.setlocale(locale.LC_ALL, locale_id.split("_")[0])
    except locale.Error:
        current_locale = locale.setlocale(locale.LC_ALL, "")
        logger.warning("Set to default locale %s", current_locale)
    # Set the windows locale for this thread to this locale.
    if platform.system() == "Windows":
        LCID = find_windows_LCID(locale_id)
        try:
            ctypes.windll.kernel32.SetThreadLocale(LCID)
            logger.debug("i18n: Set Windows thread locale LCID=%s", LCID)
        except Exception:
            logger.exception("i18n: failed to set Windows thread locale LCID=%s", LCID)
    CURRENT_LOCALE = locale_id
    # Update registry locale and active_translation view
    resolved = REGISTRY.set_locale(locale_id)
    default_domain = REGISTRY.get_default_domain()
    if default_domain:
        active_translation = REGISTRY.get_domain_translations(default_domain)
    return resolved


def find_windows_LCID(locale_id: str) -> int:
    """
    Find the windows LCID for the given locale identifier

    Args:
      locale_id:

    Returns:

    """
    # Windows > Vista is able to convert locale names to LCIDs
    func_LocaleNameToLCID = getattr(ctypes.windll.kernel32, "LocaleNameToLCID", None)
    if func_LocaleNameToLCID is not None:
        locale_id = locale_id.replace("_", "-")
        LCID = func_LocaleNameToLCID(str(locale_id), 0)
    else:  # Windows doesn't have this functionality, manually search Python's windows_locale dictionary for the LCID
        locale_id = locale.normalize(locale_id)
        if "." in locale_id:
            locale_id = locale_id.split(".")[0]
        LCList = [x[0] for x in locale.windows_locale.items() if x[1] == locale_id]
        if LCList:
            LCID = LCList[0]
        else:
            LCID = 0
    return LCID


def locale_from_locale_id(locale_id: str) -> babel.core.Locale:
    """

    Args:
      locale_id:

    Returns:

    """
    language, region = locale_id, None
    if "_" in locale_id:
        language, region = locale_id.split("_")
    return babel.core.Locale(language, region)


def get_available_locales(domain: str, locale_path: Optional[str] = None) -> Iterable[babel.core.Locale]:
    """

    Args:
      domain:
      locale_path: (Default value = None)

    Returns:

    """
    translations = get_available_translations(domain, locale_path)
    for translation_dir in translations:
        try:
            yield locale_from_locale_id(translation_dir)
        except babel.core.UnknownLocaleError:
            logger.warning(
                "Error retrieving locale for translation %r", translation_dir
            )
            continue


def get_available_translations(domain: str, locale_path: Optional[str] = None) -> Iterable[str]:
    """

    Args:
      domain:
      locale_path: (Default value = None)

    Returns:

    """
    paths_to_scan = []
    if locale_path is not None:
        paths_to_scan.append(locale_path)
    else:
        # scan all registered providers for this domain
        for prov in REGISTRY.providers_for(domain):
            if prov.path not in paths_to_scan:
                paths_to_scan.append(prov.path)
        # also include last application locale path for backward-compat
        if application_locale_path and application_locale_path not in paths_to_scan:
            paths_to_scan.append(application_locale_path)
    seen = set()
    for base in paths_to_scan:
        if not base or not os.path.isdir(base):
            continue
        try:
            dirs = os.listdir(base)
        except OSError:
            continue
        for directory in dirs:
            if directory in seen:
                continue
            lc_dir = os.path.join(base, directory, "LC_MESSAGES", f"{domain}.mo")
            lc_dir_lower = os.path.join(base, directory, "lc_messages", f"{domain}.mo")
            if os.path.exists(lc_dir) or os.path.exists(lc_dir_lower):
                seen.add(directory)
                logger.debug("i18n: found available translation: domain=%s locale=%s in %s", domain, directory, base)
                yield directory
    # Always include a default fallback
    if DEFAULT_LOCALE not in seen:
        yield DEFAULT_LOCALE


def format_timestamp(timestamp: Any) -> str:
    """

    Args:
      timestamp:

    Returns:

    """
    dt = timestamp
    if not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.fromtimestamp(timestamp)
    if dt.date() == dt.today().date():
        return locale_decode(format(dt, "%X"))
    return locale_decode(format(dt, "%c"))


# ---------------------------
# New public API
# ---------------------------

def finalize_i18n(
    locale_id: Optional[str] = None,
    languages: Optional[Iterable[str]] = None,
    app_domain: Optional[str] = None,
    app_locale_path: Optional[str] = None,
    install_into_builtins: bool = True,
    priority: int = 100,
) -> str:
    if app_domain and app_locale_path:
        REGISTRY.register_domain(app_domain, app_locale_path, priority=priority, source="finalize_i18n")
        REGISTRY.set_default_domain(app_domain)
        global application_locale_path
        application_locale_path = app_locale_path
    if install_into_builtins:
        install_translation_into_module(builtins, domain=app_domain)
    # Locale handling
    final_locale = locale_id or get_system_locale()
    REGISTRY.set_locale(final_locale, languages=languages)
    set_locale(final_locale)
    logger.info("Activated i18n for domain=%s locale=%s", app_domain, final_locale)
    return final_locale


def install_global_translation(domain: str, locale_id: Optional[str] = None, locale_path: Optional[str] = None) -> str:
    """Register a global/default application translation.

    Backward-compatible shim: registers the domain provider, installs builtins
    wrappers, sets the default domain, and sets locale if provided.
    """
    if locale_path is None:
        # Try to infer a reasonable path from the caller
        mod_name = get_calling_module_name() or __name__
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "__file__"):
            locale_path = get_locale_path(mod)
    REGISTRY.register_domain(domain, os.fspath(locale_path) if locale_path else "", priority=100, source="install_global_translation")
    REGISTRY.set_default_domain(domain)
    install_translation_into_module(builtins, domain=domain)
    global application_locale_path
    application_locale_path = locale_path
    if locale_id is None:
        locale_id = get_system_locale()
    set_locale(locale_id)
    logger.info("Installed translation %s for application %s", locale_id, domain)
    return locale_id


def install_module_translation(
    domain: Optional[str] = None,
    locale_id: Optional[str] = None,
    locale_path: Optional[str] = None,
    module: Optional[ModuleType] = None,
    priority: int = 50,
) -> None:
    """Register a module's translation and install wrappers into that module.

    - If module is None, resolves to the calling module.
    - If locale_path is None, infers <module_dir>/locale (or embedded path when frozen).
    - Registers domain provider (idempotent) and binds _/__ in that module.
    """
    # Handle string module names
    if isinstance(module, str):
        module = sys.modules[module]
    elif module is None:
        import inspect

        frame = inspect.currentframe().f_back
        module = inspect.getmodule(frame)

    if module is None:
        logger.warning("install_module_translation called without resolvable module")
        return None
    if domain is None:
        domain = infer_domain_from_module(module.__name__)
    if locale_path is None:
        locale_path = get_locale_path(module)
    # Register provider and module-domain mapping
    REGISTRY.register_domain(domain, locale_path, priority=priority, source=module.__name__)
    REGISTRY.set_module_domain(module.__name__, domain)
    install_translation_into_module(module, domain=domain)
    if locale_id is None:
        logger.debug("No locale ID specified, falling back to current locale %s", CURRENT_LOCALE)
        locale_id = CURRENT_LOCALE
    logger.debug("Installed translation %s for domain %s into module %r", locale_id, domain, module)
    return None


# Install dynamic builtins by default on import
install_translation_into_module(builtins)
REGISTRY.set_locale(CURRENT_LOCALE)
