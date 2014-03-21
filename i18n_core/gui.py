from logging import getLogger
logger = getLogger('i18n_core.gui')
import locale

import wx
import i18n_core
import babel.core

def set_wx_locale(locale_path, domain, locale_id):
 locale_id = locale_id.split('.')[0]
 wx_lang = wx.Locale.FindLanguageInfo(locale_id)
 wx.Locale.AddCatalogLookupPathPrefix(locale_path)
 wx_locale = wx.Locale()
 wx_locale.AddCatalog('wxstd')
 wx_locale.Init(wx_lang.Language)
 return wx_locale
