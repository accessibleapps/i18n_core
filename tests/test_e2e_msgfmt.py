import os
import sys
import shutil
import subprocess
from textwrap import dedent

import pytest


msgfmt = shutil.which("msgfmt")
if msgfmt is None:
    pytest.skip("msgfmt not available; skipping i18n e2e tests", allow_module_level=True)


def write_file(path: os.PathLike, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_mo(locale_root: os.PathLike, domain: str, locale: str, entries: dict) -> None:
    po_path = os.path.join(locale_root, locale, "LC_MESSAGES", f"{domain}.po")
    mo_path = os.path.join(locale_root, locale, "LC_MESSAGES", f"{domain}.mo")
    header = dedent(
        f"""
        msgid ""
        msgstr ""
        "Project-Id-Version: test\n"
        "POT-Creation-Date: 2024-01-01 00:00+0000\n"
        "PO-Revision-Date: 2024-01-01 00:00+0000\n"
        "Language: {locale}\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=UTF-8\n"
        "Content-Transfer-Encoding: 8bit\n"
        "Plural-Forms: nplurals=2; plural=(n != 1);\n"\n
        """
    )
    body_lines = [header]
    for k, v in entries.items():
        if isinstance(v, tuple):
            singular, plural = v
            body_lines.append(f"msgid \"{k}\"\nmsgid_plural \"{plural}\"\nmsgstr[0] \"{singular}\"\nmsgstr[1] \"{plural}\"\n")
        else:
            body_lines.append(f"msgid \"{k}\"\nmsgstr \"{v}\"\n")
    write_file(po_path, "\n".join(body_lines))
    subprocess.run([msgfmt, "-o", mo_path, po_path], check=True)


def create_pkg(tmp_path, name: str, with_locale: bool = True):
    pkg_dir = tmp_path / name
    (pkg_dir / name).mkdir(parents=True)
    # __init__.py
    write_file(pkg_dir / name / "__init__.py", "")
    # foo.py
    write_file(
        pkg_dir / name / "foo.py",
        dedent(
            """
            from i18n_core import _

            def get_text():
                return _("Hello")
            """
        ),
    )
    if with_locale:
        (pkg_dir / name / "locale").mkdir()
    sys.path.insert(0, str(pkg_dir))
    return pkg_dir / name


def test_builtin_inference_and_locale_switch(tmp_path, monkeypatch):
    import i18n_core

    libA_dir = create_pkg(tmp_path, "libA", with_locale=True)
    # locales for libA
    locale_root = libA_dir / "locale"
    build_mo(locale_root, "libA", "en_US", {"Hello": "A-EN"})
    build_mo(locale_root, "libA", "de", {"Hello": "A-DE"})

    # Start in en_US
    i18n_core.set_locale("en_US")
    from libA import foo as foo_en

    assert foo_en.get_text() == "A-EN"

    # Switch to de_DE (should fallback to 'de')
    i18n_core.set_locale("de_DE")
    from importlib import reload

    reload(foo_en)
    assert foo_en.get_text() == "A-DE"


def test_finalize_app_default_domain(tmp_path):
    import i18n_core

    app_dir = create_pkg(tmp_path, "app", with_locale=True)
    locale_root = app_dir / "locale"
    build_mo(locale_root, "app", "en_US", {"Welcome": "App-EN"})

    # Make app the default domain
    i18n_core.finalize_i18n(locale_id="en_US", app_domain="app", app_locale_path=str(locale_root))
    # Builtins used from this test module (domain inference likely 'tests') should fall back to default domain
    from i18n_core import _

    assert _("Welcome") == "App-EN"


def test_install_module_translation_registers_module(tmp_path):
    import i18n_core

    libB_dir = create_pkg(tmp_path, "libB", with_locale=True)
    locale_root = libB_dir / "locale"
    build_mo(locale_root, "libB", "en_US", {"Hello": "B-EN"})

    from libB import foo
    # Explicit registration should bind the module's domain
    i18n_core.install_module_translation("libB", module=sys.modules["libB.foo"]) 
    i18n_core.set_locale("en_US")
    assert foo.get_text() == "B-EN"


def test_available_translations_lists_locales(tmp_path):
    import i18n_core

    libC_dir = create_pkg(tmp_path, "libC", with_locale=True)
    locale_root = libC_dir / "locale"
    build_mo(locale_root, "libC", "en_US", {"Hello": "C-EN"})
    build_mo(locale_root, "libC", "de_DE", {"Hello": "C-DE"})

    # Register implicitly by importing and calling _ once
    from libC import foo  # noqa: F401
    locs = list(i18n_core.get_available_translations("libC"))
    assert "en_US" in locs
    assert "de_DE" in locs

