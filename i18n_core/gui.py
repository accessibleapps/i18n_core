import wx

def set_wx_locale(locale_path, domain, locale_id):
 wx_lang = wx.Locale.FindLanguageInfo(locale_id)
 wx_locale = wx.Locale(wx_lang.Language)
 wx_locale.AddCatalogLookupPathPrefix(locale_path)
 wx_locale.AddCatalog(domain)
