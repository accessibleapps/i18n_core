# i18n_core: Internationalization Utilities

`i18n_core` provides a set of utilities to simplify the process of internationalization (i18n) and localization (l10n) for Python applications. It builds upon the standard `locale` module and the powerful `babel` library to offer a streamlined way to manage translations.

## Features

*   **Global & Module Translations:** Easily load translations for your main application and individual component libraries or modules.
*   **System Locale Detection:** Automatically detects the user's system locale on Windows, macOS, and Linux.
*   **Babel Integration:** Leverages `babel` for handling `.mo` translation files and locale data.
*   **WxPython Support:** Includes helpers specifically for integrating translations with WxPython applications (`i18n_core.gui`).
*   **Frozen Environment Support:** Patches `babel` to correctly locate locale data when running in frozen environments (e.g., PyInstaller).
*   **Context Manager:** Provides a `reset_locale` context manager to temporarily change the locale.

## Installation

```bash
pip install i18n_core
```
*(Assuming the package is available on PyPI. If it's local, adjust accordingly)*

## Dependencies

*   [Babel](https://babel.pocoo.org/)
*   [platform_utils](https://github.com/your_org/platform_utils) *(Assuming this is another internal or specific library)*

## Usage

### Initializing Global Translation

Typically, in your application's entry point, you'll install the global translation. This sets up the primary language and translation domain for your app.

```python
import i18n_core
import os

# Assuming your locale files are in a 'locale' subdirectory
locale_dir = os.path.join(os.path.dirname(__file__), 'locale')
app_domain = 'my_app' # Corresponds to my_app.mo files

# Detect system locale or specify one, e.g., 'es_ES'
# Loads translations from locale_dir/<locale_id>/LC_MESSAGES/my_app.mo
current_locale = i18n_core.install_global_translation(
    domain=app_domain,
    locale_path=locale_dir
    # locale_id='fr_FR' # Optionally force a locale
)

print(f"Application locale set to: {current_locale}")

# Now you can use the standard gettext functions globally
print(_("Hello, world!"))
```

### Loading Module Translations

If you have separate libraries or modules with their own translations, you can merge them into the active global translation.

```python
import i18n_core
import my_module
import os

# Assuming my_module has its own 'locale' subdirectory
module_locale_dir = os.path.join(os.path.dirname(my_module.__file__), 'locale')
module_domain = 'my_module' # Corresponds to my_module.mo

i18n_core.install_module_translation(
    domain=module_domain,
    locale_path=module_locale_dir,
    module=my_module # Or provide module name as string 'my_module'
    # Uses the currently active global locale by default
)

# Strings from my_module's domain are now also available via _()
print(_("Module-specific string"))
```

### WxPython Integration

The `i18n_core.gui` module helps initialize WxPython's internal translation mechanisms.

```python
import wx
import i18n_core
import i18n_core.gui
import os

app = wx.App()

# After installing global translation with i18n_core.install_global_translation...
locale_dir = i18n_core.application_locale_path # Get path used by global install
current_locale = i18n_core.CURRENT_LOCALE

# Initialize wx.Locale
wx_locale = i18n_core.gui.set_wx_locale(locale_dir, current_locale)

if not wx_locale:
    print("Failed to set Wx locale.")

# ... proceed with your WxPython application setup ...

app.MainLoop()
```

## Locale Management

*   `get_system_locale()`: Detects the OS locale.
*   `set_locale(locale_id)`: Sets the locale for the current process/thread.
*   `get_available_locales(domain, locale_path)`: Lists available `babel.Locale` objects based on found translation files.
*   `reset_locale()`: A context manager to temporarily change the locale and restore it afterwards.

```python
from i18n_core import reset_locale, set_locale

print(f"Current locale: {i18n_core.CURRENT_LOCALE}")

with reset_locale():
    set_locale('fr_FR')
    print(f"Locale inside context: {i18n_core.CURRENT_LOCALE}")
    # Perform operations requiring French locale

print(f"Locale after context: {i18n_core.CURRENT_LOCALE}")
```

## Contributing

Please refer to CONTRIBUTING.md for details. *(Optional: Create this file if needed)*

## License

This project is licensed under the terms of the LICENSE file.
