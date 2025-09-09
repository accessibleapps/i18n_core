"""Tests for install_module_translation function (registry-based)."""

import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import i18n_core


class TestInstallModuleTranslation:
    def setup_method(self):
        self.mock_module = SimpleNamespace()
        self.mock_module.__file__ = "/fake/path/module.py"
        self.mock_module.__name__ = "test_module.unit"

    def test_module_as_string_registers_and_installs(self):
        with patch.dict(sys.modules, {"test_module": self.mock_module}):
            with patch("i18n_core.get_locale_path") as mock_get_path:
                mock_get_path.return_value = "/fake/locale"
                with patch.object(i18n_core, "REGISTRY") as mock_reg:
                    i18n_core.install_module_translation(domain="test_domain", module="test_module")
                    mock_get_path.assert_called_once_with(self.mock_module)
                    mock_reg.register_domain.assert_called_once()

    def test_module_as_object_registers_and_installs(self):
        with patch("i18n_core.get_locale_path") as mock_get_path:
            mock_get_path.return_value = "/fake/locale"
            with patch.object(i18n_core, "REGISTRY") as mock_reg:
                i18n_core.install_module_translation(domain="test_domain", module=self.mock_module)
                mock_get_path.assert_called_once_with(self.mock_module)
                mock_reg.register_domain.assert_called_once()

    def test_module_none_uses_calling_module(self):
        with patch("i18n_core.get_locale_path") as mock_get_path, \
            patch("inspect.currentframe") as mock_frame, \
            patch("inspect.getmodule") as mock_getmodule, \
            patch.object(i18n_core, "REGISTRY") as mock_reg:

            frame_obj = Mock()
            frame_obj.f_back = Mock()
            mock_frame.return_value = frame_obj
            mock_getmodule.return_value = self.mock_module
            mock_get_path.return_value = "/fake/locale"

            i18n_core.install_module_translation(domain="test_domain", module=None)
            mock_getmodule.assert_called_once_with(frame_obj.f_back)
            mock_get_path.assert_called_once_with(self.mock_module)
            mock_reg.register_domain.assert_called_once()

    def test_custom_locale_path_used(self):
        with patch.object(i18n_core, "REGISTRY") as mock_reg:
            i18n_core.install_module_translation(
                domain="test_domain", module=self.mock_module, locale_path="/custom/locale"
            )
            mock_reg.register_domain.assert_called_once()

    def test_installs_wrappers_into_module(self):
        i18n_core.install_module_translation(domain="test_domain", module=self.mock_module, locale_path="/custom/locale")
        assert callable(getattr(self.mock_module, "_"))
        assert callable(getattr(self.mock_module, "__"))
        assert callable(getattr(self.mock_module, "ngettext"))
