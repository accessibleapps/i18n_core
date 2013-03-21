from setuptools import setup
from i18n_core import __author__, __doc__, __version__
import os

setup(
 name = 'i18n_core',
 version = str(__version__),
 description = __doc__,
 packages = ['i18n_core'],
 install_requires = [
  'speaklater',
 ],
 classifiers = [
  'Development Status :: 3 - Alpha',
  'Intended Audience :: Developers',
  'Programming Language :: Python',
  'Topic :: Software Development :: Libraries',
 ],
)
