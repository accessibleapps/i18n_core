from logging import getLogger
logger = getLogger('i18n_core.gui')
import wx
import i18n_core

def set_wx_locale(locale_path, domain, locale_id):
 wx_lang = wx.Locale.FindLanguageInfo(locale_id)
 if wx_locale is None:
  logger.warning("Unable to find wx locale %s, falling back to default." % locale_id)
  wx_lang = wx.Locale.FindLanguageInfo(locale_id)
  wx_lang = wx.Locale.FindLanguageInfo(i18n_core.DEFAULT_LOCALE)
 wx_locale = wx.Locale(wx_lang.Language)
 wx_locale.AddCatalogLookupPathPrefix(locale_path)
 wx_locale.AddCatalog(domain)
