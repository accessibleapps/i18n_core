from logging import getLogger
logger = getLogger('i18n_core')

import __builtin__
import ctypes
import gettext
import locale
import platform
import os
import speaklater

__version__ = 0.1
__author__ = 'Christopher Toth <q@q-continuum.net>'
__doc__ = """Internationalization and localization setup and support utilities."""

DEFAULT_LOCALE = 'en_US'

def prepare_internationalization(locale_path, domain, locale_id, use_gui=False):
 try:
  translation = gettext.translation(domain, localedir=locale_path, languages=[locale_id])
  logger.debug("Initialized gettext translation for locale %s" % locale_id)
 except IOError:
  translation = gettext.translation(domain, fallback=True)
 install_translation(translation)
 set_locale(locale_id)
 if use_gui:
  import gui
  gui.set_wx_locale(locale_path, domain, locale_id)

def install_translation(translation=None):
 if translation is None:
  translation = gettext.translation('', fallback=True)
  logger.debug("Creating fallback translation")
 translation.install(unicode=True)
 lgettext = lambda s: speaklater.make_lazy_string(translation.ugettext, s)
 lngettext = lambda x, y, z, **k: speaklater.make_lazy_string(translation.ungettext, x, y, z, **k)
 setattr(__builtin__, 'lgettext', lgettext)
 setattr(__builtin__, 'lngettext', lngettext)
 setattr(__builtin__, '__', lgettext)

def set_locale(locale_id):
 try:
  try:
   locale.setlocale(locale.LC_ALL, locale_id)
  except locale.Error:
   locale.setlocale(locale.LC_ALL, locale_id.split('_')[0])
 except locale.Error:
  locale.setlocale(locale.LC_ALL, '')
 #Set the windows locale for this thread to this locale.
 if platform.system() == 'Windows':
  LCID = find_windows_LCID(locale_id)
  ctypes.windll.kernel32.SetThreadLocale(LCID)

def find_windows_LCID(locale_id):
 #Windows Vista is able to convert locale names to LCIDs
 func_LocaleNameToLCID = getattr(ctypes.windll.kernel32, 'LocaleNameToLCID', None)
 if func_LocaleNameToLCID is not None:
  locale_id = locale_id.replace('_','-')
  LCID=func_LocaleNameToLCID(unicode(locale_id), 0)
 else: #Windows doesn't have this functionality, manually search Python's windows_locale dictionary for the LCID
  locale_id = locale.normalize(locale_id)
  if '.' in locale_id:
   locale_id = locale_id.split('.')[0]
  LCList=[x[0] for x in locale.windows_locale.iteritems() if x[1] == locale_id]
  if len(LCList)>0:
   LCID=LCList[0]
  else:
   LCID=0
 return LCID

mac_locales = {
 '0:0':  'en_GB.utf-8',
 '0:3':  'de_DE.utf-8',
}

def get_system_locale():
 if platform.system() == 'Windows':
  LCID = ctypes.windll.kernel32.GetUserDefaultUILanguage()
  return locale.windows_locale[LCID]
 if '__CF_USER_TEXT_ENCODING' in os.environ:
  lang_code = os.environ['__CF_USER_TEXT_ENCODING'].split( ':', 1 )[1]
  current_locale = mac_locales.get( lang_code)
  if current_locale:
   return current_locale
 if 'LC_ALL' in os.environ:
  return _locale.normalize(os.environ['LC_ALL'])
  current_locale = locale.getdefaultlocale()[0]
 if current_locale is None:
  logger.warning("Unable to detect the system's default current_locale. Defaulting to %s" % DEFAULT_LOCALE)
  current_locale = DEFAULT_LOCALE
 return current_locale

def detect_available_languages(locale_path, domain):
 """Searches the provided locale path for compiled languages and returns them"""
 results = set()
 results.add(DEFAULT_LOCALE)
 if not os.path.exists(locale_path):
  return results
 for directory in os.listdir(locale_path):
  if gettext.find(domain, locale_path, languages=[directory]):
   results.add(directory)
 return results

def find_locale_by_name(locale_name):
 #Not currently working
 return locale_name
