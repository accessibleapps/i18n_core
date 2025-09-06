"""Tests for install_module_translation function."""

import sys
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import pytest
from babel import support

import i18n_core


class TestInstallModuleTranslation:
    """Test cases for the install_module_translation function."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock module for testing
        self.mock_module = Mock()
        self.mock_module.__file__ = "/fake/path/module.py"
        self.mock_module.__name__ = "test_module"
        
        # Mock active translation
        self.mock_translation = Mock(spec=support.Translations)
        i18n_core.active_translation = self.mock_translation
        
        # Store original state
        self.original_active_translation = i18n_core.active_translation
    
    def teardown_method(self):
        """Clean up after tests."""
        # Restore original state
        i18n_core.active_translation = self.original_active_translation
    
    def test_module_as_string(self):
        """Test passing module name as string."""
        with patch.dict(sys.modules, {'test_module': self.mock_module}):
            with patch('i18n_core.get_locale_path') as mock_get_path:
                with patch.object(support.Translations, 'load') as mock_load:
                    mock_get_path.return_value = "/fake/locale"
                    mock_load.return_value = Mock()
                    
                    i18n_core.install_module_translation(
                        domain="test_domain",
                        module="test_module"
                    )
                    
                    # Verify module was resolved from string
                    mock_get_path.assert_called_once_with(self.mock_module)
                    mock_load.assert_called_once()
                    self.mock_translation.merge.assert_called_once()
    
    def test_module_as_object(self):
        """Test passing module object directly."""
        with patch('i18n_core.get_locale_path') as mock_get_path:
            with patch.object(support.Translations, 'load') as mock_load:
                mock_get_path.return_value = "/fake/locale"  
                mock_load.return_value = Mock()
                
                i18n_core.install_module_translation(
                    domain="test_domain",
                    module=self.mock_module
                )
                
                # Verify module object was used directly
                mock_get_path.assert_called_once_with(self.mock_module)
                mock_load.assert_called_once()
                self.mock_translation.merge.assert_called_once()
    
    def test_module_none_uses_calling_module(self):
        """Test that module=None resolves to calling module."""
        with patch('i18n_core.get_locale_path') as mock_get_path:
            with patch.object(support.Translations, 'load') as mock_load:
                with patch('inspect.currentframe') as mock_frame:
                    with patch('inspect.getmodule') as mock_getmodule:
                        # Mock the frame and getmodule call
                        mock_frame_obj = Mock()
                        mock_frame_obj.f_back = Mock()
                        mock_frame.return_value = mock_frame_obj
                        mock_getmodule.return_value = self.mock_module
                        
                        mock_get_path.return_value = "/fake/locale"
                        mock_load.return_value = Mock()
                        
                        i18n_core.install_module_translation(
                            domain="test_domain",
                            module=None  # Should resolve to calling module
                        )
                        
                        # Verify calling module was determined
                        mock_frame.assert_called_once()
                        mock_getmodule.assert_called_once_with(mock_frame_obj.f_back)
                        mock_get_path.assert_called_once_with(self.mock_module)
    
    def test_no_active_translation_returns_early(self):
        """Test that function returns early if no active translation."""
        i18n_core.active_translation = None
        
        with patch('i18n_core.logger.warning') as mock_warning:
            result = i18n_core.install_module_translation(
                domain="test_domain",
                module=self.mock_module
            )
            
            # Should log warning and return None
            mock_warning.assert_called_once_with(
                "Cannot install module translation if there is no global translation active"
            )
            assert result is None
    
    def test_uses_current_locale_by_default(self):
        """Test that CURRENT_LOCALE is used when locale_id is None."""
        original_locale = i18n_core.CURRENT_LOCALE
        i18n_core.CURRENT_LOCALE = "test_locale"
        
        try:
            with patch('i18n_core.get_locale_path') as mock_get_path:
                with patch.object(support.Translations, 'load') as mock_load:
                    mock_get_path.return_value = "/fake/locale"
                    mock_load.return_value = Mock()
                    
                    i18n_core.install_module_translation(
                        domain="test_domain",
                        module=self.mock_module,
                        locale_id=None  # Should use CURRENT_LOCALE
                    )
                    
                    # Verify CURRENT_LOCALE was used
                    mock_load.assert_called_once_with(
                        "/fake/locale", ["test_locale"], "test_domain"
                    )
        finally:
            i18n_core.CURRENT_LOCALE = original_locale
    
    def test_custom_locale_path_used(self):
        """Test that custom locale_path is used when provided."""
        custom_path = "/custom/locale/path"
        
        with patch.object(support.Translations, 'load') as mock_load:
            mock_load.return_value = Mock()
            
            i18n_core.install_module_translation(
                domain="test_domain",
                module=self.mock_module,
                locale_path=custom_path
            )
            
            # Verify custom path was used (get_locale_path should not be called)
            mock_load.assert_called_once_with(
                custom_path, [i18n_core.CURRENT_LOCALE], "test_domain"
            )
    
    def test_translation_merge_and_logging(self):
        """Test that translation is merged and logged correctly."""
        mock_module_translation = Mock()
        
        with patch('i18n_core.get_locale_path') as mock_get_path:
            with patch.object(support.Translations, 'load') as mock_load:
                with patch('i18n_core.logger.debug') as mock_debug:
                    mock_get_path.return_value = "/fake/locale"
                    mock_load.return_value = mock_module_translation
                    
                    i18n_core.install_module_translation(
                        domain="test_domain",
                        module=self.mock_module,
                        locale_id="en_US"
                    )
                    
                    # Verify translation was merged
                    self.mock_translation.merge.assert_called_once_with(mock_module_translation)
                    
                    # Verify debug log was called
                    mock_debug.assert_called_once_with(
                        "Installed translation %s for domain %s into module %r",
                        "en_US", "test_domain", self.mock_module
                    )