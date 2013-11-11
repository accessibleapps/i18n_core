from logging import getLogger
logger = getLogger('i18n_core')

try:
 import __builtin__ as builtins
except ImportError:
 import builtins

import ctypes
import gettext
import imp
import inspect
import locale
import platform
import os
import sys

from platform_utils import paths


__version__ = 0.2
__author__ = 'Christopher Toth <q@q-continuum.net>'
__doc__ = """Internationalization and localization setup and support utilities."""

DEFAULT_LOCALE = 'en_US'
application_locale = None
application_locale_path = None
installed_translations = []

def prepare_internationalization(domain, locale_path, locale_id):
 global application_locale, application_locale_path
 locale._parse_localename = _parse_localename
 logger.debug("Monkeypatched the locale module with an improved locale parser.")
 translation = find_translation(domain, locale_path, locale_id)
 if translation is None:
  translation = default_translation(domain)
  logger.debug("Falling back to default translation for domain %s" % domain)
 install_translation(translation)
 set_locale(locale_id)
 application_locale = locale_id
 application_locale_path = locale_path


def install_module_translation(module_domain, locale_path=None, locale=None, module=None):
 if module is None:
  module = get_caller_module()
 if locale_path is None:
  locale_path = get_locale_path(module)
 if locale is None:
  locale = application_locale
 translation = find_translation(module_domain, locale_path, locale)
 if translation is None:
  translation = default_translation(module_domain)
  logger.debug("Falling back to default translation for domain %s" % module_domain)
 install_translation(translation, module=module)

def get_caller_module():
 return inspect.getmodule(inspect.stack()[2][0])

def find_translation(domain, locale_path, locale_id):
 try:
  translation = gettext.translation(domain, localedir=locale_path, languages=[locale_id])
  logger.info("Initialized gettext translation for locale %s" % locale_id)
 except IOError:
  if '_' in locale_id:
   locale_id = locale_id.split('_')[0]
   try:
    translation = gettext.translation(domain, localedir=locale_path, languages=[locale_id])
    logger.info("Initialized gettext translation for locale %s" % locale_id)
   except IOError:
    translation = None
 return translation

def default_translation(domain):
 return gettext.translation(domain, fallback=True)

def install_translation(translation=None, module=builtins):
 global installed_translations
 import speaklater
 if translation is None:
  translation = gettext.translation('', fallback=True)
  logger.debug("Creating fallback translation")
 kw = {}
 if sys.version_info[0] < 3:
  kw['unicode'] = True
 translation.install(**kw)
 installed_translations.append(translation)
 def f(*args, **kwargs):
  return installed_translations[-1].ugettext(*args, **kwargs)
 lgettext = speaklater.make_lazy_gettext(lambda: f)
 lngettext = speaklater.make_lazy_gettext(lambda: translation.ungettext)
 module.lgettext = lgettext
 module.lngettext = lngettext
 module.ngettext = translation.ngettext
 module.__ = lgettext

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

def get_locale_path(module=None):
 if not paths.is_frozen():
  return os.path.join(os.path.split(module.__file__)[0], 'locale')
 return application_locale_path

def _parse_localename(localename):

 """ Parses the locale code for localename and returns the
  result as tuple (language code, encoding).

  The localename is normalized and passed through the locale
  alias engine. A ValueError is raised in case the locale name
  cannot be parsed.

  The language code corresponds to RFC 1766.  code and encoding
  can be None in case the values cannot be determined or are
  unknown to this implementation.

  This implementation fixes an issue with the implementation available in the standard library which will break on some Windows locale names which contain .
 """
 code = locale.normalize(localename)
 if '@' in code:
  # Deal with locale modifiers
  code, modifier = code.split('@')
  if modifier == 'euro' and '.' not in code:
   # Assume Latin-9 for @euro locales. This is bogus,
   # since some systems may use other encodings for these
   # locales. Also, we ignore other modifiers.
   return code, 'iso-8859-15'

 if '.' in code:
  return tuple(code.rsplit('.', 1)[:2])
 elif code == 'C':
  return None, None
 raise ValueError, 'unknown locale: %s' % localename

