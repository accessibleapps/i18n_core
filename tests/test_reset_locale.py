"""Locale restoration must survive failure in the managed setup operation."""

import locale
from unittest.mock import patch

import pytest

from i18n_core.reset_locale import reset_locale


def test_restores_locale_after_normal_exit():
    with patch("i18n_core.reset_locale.locale.getlocale", return_value=("en_US", "UTF-8")), patch(
        "i18n_core.reset_locale.locale.setlocale"
    ) as setlocale:
        with reset_locale():
            setlocale.assert_not_called()

        setlocale.assert_called_once_with(locale.LC_ALL, "en_US")


def test_restores_locale_and_preserves_setup_exception():
    failure = RuntimeError("locale setup failed")
    with patch("i18n_core.reset_locale.locale.getlocale", return_value=("en_US", "UTF-8")), patch(
        "i18n_core.reset_locale.locale.setlocale"
    ) as setlocale:
        with pytest.raises(RuntimeError) as caught:
            with reset_locale():
                raise failure

        assert caught.value is failure
        setlocale.assert_called_once_with(locale.LC_ALL, "en_US")
