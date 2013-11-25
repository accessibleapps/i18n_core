from logging import getLogger
logger = getLogger('i18n_core')

import __builtin__
import ctypes
import locale
import os
import platform


from platform_utils import paths

from babel import support

DEFAULT_LOCALE = 'en_US'


active_translation = None
application_locale_path = None

def install_global_translation(domain=None, locale_id=None, locale_path=None):
 global active_translation
 global application_locale_path
 if locale_id is None:
  locale_id = get_system_locale()
 print locale_path, locale_id, domain
 active_translation = support.Translations.load(locale_path, [locale_id], domain)
 if not isinstance(active_translation, support.Translations):
  active_translation = support.Translations()
 active_translation.install()
 active_translation.set_output_charset(locale.getpreferredencoding())
 install_translation_into_module()
 set_locale(locale_id)
 application_locale_path = locale_path
 return locale_id

def install_module_translation(domain=None, locale_id=None, locale_path=None, module=None):
 if locale_path is None:
  locale_path = get_locale_path(module)
 if locale_id is None:
  locale_id = get_system_locale()
 module_translation = support.Translations.load(locale_path, [locale_id], domain)
 active_translation.merge(module_translation)

def install_translation_into_module(module=__builtin__):
 def lazy_gettext(string):
  return support.LazyProxy(lambda: active_translation.ugettext(string))
 module._ = active_translation.gettext
 module.__ = lazy_gettext

mac_locales = {
 '0:0':  'en_GB.utf-8',
 '0:3':  'de_DE.utf-8',
}

def get_system_locale():
 if platform.system() == 'Windows':
  LCID = ctypes.windll.kernel32.GetUserDefaultLCID()
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

def get_locale_path(module=None):
 if not paths.is_frozen():
  return os.path.join(os.path.split(module.__file__)[0], 'locale')
 return application_locale_path

def locale_decode(s):
 encoding = locale.getlocale()[1]
 if encoding is not None:
  s = s.decode(encoding)
 return s

def set_locale(locale_id):
 try:
  try:
   current_locale = locale.setlocale(locale.LC_ALL, locale_id)
  except locale.Error:
   current_locale = locale.setlocale(locale.LC_ALL, locale_id.split('_')[0])
 except locale.Error:
  current_locale = locale.setlocale(locale.LC_ALL, '')
  logger.warning("Set to default locale %s" % current_locale)
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

