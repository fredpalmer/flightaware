try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

PACKAGE = "flightaware"
NAME = "flightaware"
DESCRIPTION = "A python REST interface for flightaware data"
AUTHOR = "Fred Palmer"
AUTHOR_EMAIL = "fred.palmer@gmail.com"
URL = "https://github.com/fredpalmer/flightaware"

config = {
    "description": DESCRIPTION,
    "author": AUTHOR,
    "url": URL,
    "author_email": AUTHOR_EMAIL,
    "version": "0.1",
    "install_requires": [
        "requests>=2.0.0",
    ],
    "keywords": "travel flightaware airline flight flight-tracking flight-data",
    "classifiers": [
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
    ],
    "packages": [PACKAGE, ],
    "scripts": [],
    "name": NAME,
    "license": "MIT",
}

setup(**config)
