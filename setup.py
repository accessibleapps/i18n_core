from setuptools import setup

__version__ = 0.34
__doc__ = """Internationalization and localization setup and support utilities."""


setup(
    name="i18n_core",
    version=str(__version__),
    author="Christopher Toth",
    author_email="q@q-continuum.net",
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
