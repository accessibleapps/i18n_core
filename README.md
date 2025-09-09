# i18n_core: Internationalization Utilities

`i18n_core` is a lightweight, order-agnostic i18n layer on top of Babel.
It lets apps and libraries register translations at any time, and all lookups
react to locale changes without re-registration.

## Features

- Dynamic lookups: `_`, `__`, `ngettext` reflect the current locale.
- Order-agnostic: libraries can register before or after the app; no merge-by-call-order.
- Domain-aware: no cross-domain bleed; use per-domain catalogs with explicit precedence.
- System locale detection and Windows LCID support.
- WxPython helpers: `i18n_core.gui.set_wx_locale`.
- Frozen env support (works with embedded data paths).

## Installation

```bash
pip install i18n_core
```

## Dependencies

- Babel (>= 2.15, < 3.0)
- platform_utils

## Quickstart (App)

Use `finalize_i18n` once at startup to set the default domain and locale.

```python
import os
from i18n_core import finalize_i18n, get_system_locale, _

locale_dir = os.path.join(os.path.dirname(__file__), "locale")
finalize_i18n(
    locale_id=get_system_locale(),
    app_domain="my_app",           # matches your .mo domain
    app_locale_path=locale_dir,     # <locale>/<LCID>/LC_MESSAGES/my_app.mo
)

print(_("Hello, world!"))
```

Change locale anytime — all lookups update automatically:

```python
from i18n_core import set_locale

set_locale("de_DE")
```

## Libraries

Two options — both are safe and idempotent:

- Rely on inference (zero code): just `from i18n_core import _` and call it.
  The top-level package name becomes your domain, and `<pkg>/locale` is used.

- Explicit registration (recommended for clarity/perf):

```python
import sys
import i18n_core

i18n_core.install_module_translation(
    domain="my_lib",                 # your .mo domain
    module=sys.modules[__name__],
    # locale_path=<path>              # optional; defaults to <pkg>/locale
)

print(_("A library string"))
```

## WxPython Integration

```python
import wx
import i18n_core.gui

app = wx.App()
wx_locale = i18n_core.gui.set_wx_locale(locale_path, locale_id)
```

## APIs

- `finalize_i18n(locale_id=None, languages=None, app_domain=None, app_locale_path=None, install_into_builtins=True, priority=100) -> str`
  - Configure default app domain/locale; install builtins wrappers.
- `install_module_translation(domain=None, locale_id=None, locale_path=None, module=None, priority=50) -> None`
  - Register a provider for a domain and install wrappers into a specific module.
- `install_global_translation(domain, locale_id=None, locale_path=None) -> str`
  - Back-compat shim: registers default domain and sets locale.
- `set_locale(locale_id: str) -> str`
  - Normalize and apply process/Windows locale; updates i18n registry.
- `get_available_translations(domain, locale_path=None) -> Iterable[str]`
  - List available locales for a domain across registered paths.
- `get_available_locales(domain, locale_path=None) -> Iterable[babel.core.Locale]`
- `reset_locale()` context manager: temporarily adjust process locale.

## Precedence & Domains

- Precedence is explicit: higher `priority` overrides lower within a domain
  (default: app=100, libraries=50). Ties resolve by first-registration order.
- Lookups are domain-aware; module wrappers use their bound domain, and builtins
  use the default domain (or fall back to caller inference).

## Backward Compatibility Notes

- The legacy global-merge behavior is replaced by per-domain composites.
  `active_translation` now reflects the default domain, not a cross-domain merge.
- `install_global_translation` and `install_module_translation` still exist but
  are now order-agnostic and idempotent.
- Builtins `_`, `__`, `ngettext` are installed at import-time.
  If you previously used `try: __; except NameError: install_global_translation(...)`,
  switch to `finalize_i18n` in the app entry point.

## License

This project is licensed under the terms of the LICENSE file.
