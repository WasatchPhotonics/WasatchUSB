try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'USB cameras and devices from Wasatch Photonics',
    'author': 'Nathan Harrington',
    'url': 'https://github.com/nharringtonwasatch/WasatchUSB',
    'download_url': 'https://github.com/nharringtonwasatch/WasatchUSB',
    'author_email': 'nharrington@wasatchphotonics.com',
    'version': '0.1',
    'install_requires': ['phidgeter', 'pyusb', 'numpy'],
    'packages': ['wasatchusb'],
    'scripts': [],
    'name': 'WasatchUSB'
}

setup(**config)
