from logging import getLogger

import wx

from .reset_locale import reset_locale

logger = getLogger("i18n_core.gui")


def set_wx_locale(locale_path, locale_id):
    """

    Args:
      locale_path: Path to translations
      locale_id: 

    Returns:

    """
    with reset_locale():
        wx_lang = find_wx_lang(locale_id)
        if wx_lang is None:
            logger.warning("No wx translation found for locale %s", locale_id)
            return
        wx.Locale.AddCatalogLookupPathPrefix(locale_path)
        wx_locale = wx.Locale()
        wx_locale.AddCatalog("wxstd")
        wx_locale.Init(wx_lang.Language)
        return wx_locale


def find_wx_lang(locale_id):
    """

    Args:
      locale_id: 

    Returns:

    """
    original_locale_id = locale_id
    wx_lang = wx.Locale.FindLanguageInfo(locale_id)
    if wx_lang is not None:
        logger.debug("Perfect match: Found wx locale for %s", locale_id)
    else:
        locale_id = locale_id.split(".")[0]
        wx_lang = wx.Locale.FindLanguageInfo(locale_id)
        locale_id = locale_id.split("_")[0]
        wx_lang = wx.Locale.FindLanguageInfo(locale_id)
        if wx_lang is not None:
            logger.warn(
                "Secondary fallback: Found wx locale for %s", locale_id)
        else:
            logger.error("No wx language for %s found", original_locale_id)
            return
    return wx_lang
