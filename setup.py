from setuptools import setup

__version__ = "0.3.9"
__doc__ = """Internationalization and localization setup and support utilities."""

with open('README.md', 'rt') as f:
    readme = f.read()

setup(
    name="i18n_core",
    version=str(__version__),
    author="Christopher Toth",
    author_email="q@q-continuum.net",
    description=__doc__,
    long_description = readme,
    long_description_content_type = "text/markdown",
    packages=["i18n_core"],
    install_requires=["babel", "platform_utils"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries",
    ],
)
