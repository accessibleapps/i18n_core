from __future__ import annotations

import inspect
import locale as _pylocale
import os
import sys
import threading
from dataclasses import dataclass
from logging import getLogger
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from babel import support

logger = getLogger("i18n_core.registry")


DEFAULT_LOCALE = "en_US"


@dataclass(frozen=True)
class Provider:
    domain: str
    path: str
    priority: int
    source: str  # e.g., module name registering


def _normalize_lang(lang: Optional[str]) -> Optional[str]:
    if not lang:
        return None
    lang = lang.replace("-", "_").strip()
    if "_" in lang:
        ll, cc = lang.split("_", 1)
        return f"{ll.lower()}_{cc.upper()}"
    return lang.lower()


def _language_chain(locale_id: Optional[str], languages: Optional[Iterable[str]]) -> Optional[List[str]]:
    if languages:
        chain = []
        for l in languages:
            n = _normalize_lang(l)
            if n and n not in chain:
                chain.append(n)
        return chain or None
    locale_id = _normalize_lang(locale_id)
    if not locale_id:
        return None
    chain: List[str] = [locale_id]
    if "_" in locale_id:
        base = locale_id.split("_", 1)[0]
        if base not in chain:
            chain.append(base)
    else:
        chain.append(f"{locale_id}_{locale_id.upper()}")
    return chain


class _Registry:
    def __init__(self) -> None:
        self._providers: Dict[str, List[Provider]] = {}
        self._module_domain: Dict[str, str] = {}
        self._default_domain: Optional[str] = None
        self._locale_id: str = DEFAULT_LOCALE
        self._languages: Optional[List[str]] = None
        self._cache: Dict[Tuple[str, Tuple[str, ...]], support.NullTranslations] = {}
        self._lock = threading.RLock()
        self._listeners: List[Callable[[str], None]] = []

    # Registration ---------------------------------------------------------
    def register_domain(self, domain: str, path: str, priority: int = 50, source: Optional[str] = None) -> None:
        path = os.fspath(path)
        with self._lock:
            providers = self._providers.setdefault(domain, [])
            src = source or "<unknown>"
            # Idempotent: avoid duplicate provider entries
            for p in providers:
                if p.path == path and p.priority == priority and p.source == src:
                    logger.debug(
                        "i18n: provider already registered: domain=%s source=%s path=%s priority=%s",
                        domain, src, path, priority,
                    )
                    return
            providers.append(Provider(domain=domain, path=path, priority=priority, source=src))
            # Keep stable order, but sort by priority (tie resolved by insertion order)
            providers.sort(key=lambda p: p.priority)
            logger.info(
                "i18n: registered provider: domain=%s source=%s path=%s priority=%s (total=%d)",
                domain, src, path, priority, len(providers),
            )
            self._clear_cache_locked()

    def set_module_domain(self, module_name: str, domain: str) -> None:
        with self._lock:
            self._module_domain[module_name] = domain

    def get_module_domain(self, module_name: str) -> Optional[str]:
        return self._module_domain.get(module_name)

    def set_default_domain(self, domain: Optional[str]) -> None:
        with self._lock:
            self._default_domain = domain
            logger.debug("i18n: default domain set: %s", domain)

    def get_default_domain(self) -> Optional[str]:
        return self._default_domain

    def providers_for(self, domain: str) -> List[Provider]:
        return list(self._providers.get(domain, ()))

    # Locale handling ------------------------------------------------------
    def set_locale(self, locale_id: Optional[str], languages: Optional[Iterable[str]] = None) -> str:
        with self._lock:
            if locale_id is None:
                locale_id = self._locale_id
            normalized = _normalize_lang(locale_id) or DEFAULT_LOCALE
            self._locale_id = normalized
            self._languages = _language_chain(normalized, languages)
            self._clear_cache_locked()
            logger.info("i18n: locale set: %s chain=%s", self._locale_id, self._languages)
            for cb in list(self._listeners):
                try:
                    cb(self._locale_id)
                except Exception:  # pragma: no cover
                    logger.exception("Error in on_locale_change callback")
            return self._locale_id

    def get_locale(self) -> str:
        return self._locale_id

    def get_languages(self) -> Optional[List[str]]:
        return list(self._languages) if self._languages else None

    def on_locale_change(self, callback: Callable[[str], None]) -> Callable[[], None]:
        with self._lock:
            self._listeners.append(callback)

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._listeners:
                    self._listeners.remove(callback)

        return unsubscribe

    # Translation resolution ----------------------------------------------
    def get_domain_translations(self, domain: str) -> support.NullTranslations:
        with self._lock:
            chain_tuple: Tuple[str, ...] = tuple(self._languages or [])
            key = (domain, chain_tuple)
            cached = self._cache.get(key)
            if cached is not None:
                logger.debug("i18n: cache hit for domain=%s chain=%s", domain, chain_tuple)
                return cached
            logger.debug(
                "i18n: cache miss for domain=%s chain=%s providers=%d",
                domain, chain_tuple, len(self._providers.get(domain, [])),
            )
            providers = self._providers.get(domain, [])
            translations: Optional[support.NullTranslations] = None
            for prov in providers:
                logger.debug(
                    "i18n: loading translations: domain=%s path=%s locales=%s",
                    domain, prov.path, self._languages,
                )
                try:
                    t = support.Translations.load(prov.path, locales=self._languages, domain=domain)
                except Exception:
                    logger.exception("i18n: error loading translations: domain=%s path=%s", domain, prov.path)
                    continue
                # Skip NullTranslations with no content
                if isinstance(t, support.NullTranslations) and not getattr(t, "_catalog", None):
                    logger.debug("i18n: empty translations: domain=%s path=%s", domain, prov.path)
                    continue
                if translations is None:
                    translations = t
                else:
                    # Overlay: lower priority merged first, higher overrides
                    try:
                        translations.merge(t)  # type: ignore[attr-defined]
                        logger.debug("i18n: merged translations for domain=%s from %s", domain, prov.path)
                    except Exception:
                        # Fall back: add as domain catalog to keep accessibility via d* functions
                        try:
                            translations.add(t)  # type: ignore[attr-defined]
                            logger.debug("i18n: added domain catalog for domain=%s from %s", domain, prov.path)
                        except Exception:
                            logger.exception("i18n: failed to merge/add translations: domain=%s", domain)

            if translations is None:
                translations = support.NullTranslations()

            self._cache[key] = translations
            logger.debug("i18n: cached translations for domain=%s chain=%s", domain, chain_tuple)
            return translations

    def _clear_cache_locked(self) -> None:
        self._cache.clear()


REGISTRY = _Registry()


def infer_domain_from_module(module_name: str) -> str:
    # Map module name like 'package.sub.module' to top-level 'package'
    return module_name.split(".")[0]


def get_calling_module_name() -> Optional[str]:
    # Inspect the stack to find the first non-i18n_core module
    for frame_info in inspect.stack()[2:]:  # skip our wrapper and its immediate caller
        frame = frame_info.frame
        mod_name = frame.f_globals.get("__name__")
        if not mod_name:
            continue
        if mod_name.startswith("i18n_core"):
            continue
        return mod_name
    return None


def ensure_inferred_provider(module_name: str, module_file: Optional[str]) -> Optional[str]:
    """Ensure that a provider exists for the inferred domain.

    Returns the inferred domain name if registration happened or was already present.
    """
    domain = infer_domain_from_module(module_name)
    existing = REGISTRY.providers_for(domain)
    if existing:
        return domain
    # Try to infer path from module file
    if not module_file:
        mod = sys.modules.get(module_name)
        module_file = getattr(mod, "__file__", None)
    if not module_file:
        return domain
    pkg_dir = os.path.dirname(module_file)
    locale_path = os.path.join(pkg_dir, "locale")
    # Only register if a locale directory exists
    if os.path.isdir(locale_path):
        logger.debug("i18n: inferred provider: module=%s domain=%s path=%s", module_name, domain, locale_path)
        REGISTRY.register_domain(domain, locale_path, priority=50, source=module_name)
    else:
        logger.debug("i18n: no locale directory to infer: module=%s path=%s", module_name, locale_path)
    return domain
