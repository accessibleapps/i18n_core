from setuptools import setup

__version__ = 0.33
__author__ = "Christopher Toth <q@q-continuum.net>"
__doc__ = """Internationalization and localization setup and support utilities."""


setup(
    name="i18n_core",
    version=str(__version__),
    description=__doc__,
    packages=["i18n_core"],
    install_requires=["babel", "platform_utils"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
    ],
)
