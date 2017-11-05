import re
import codecs
from setuptools import setup


# https://packaging.python.org/en/latest/distributing/

with codecs.open('quantdom/__init__.py', mode='r', encoding='utf-8') as f:
    INFO = dict(re.findall(r"__(\w+)__ = '([^']+)'", f.read(), re.MULTILINE))

with codecs.open('README.rst', mode='r', encoding='utf-8') as f:
    INFO['long_description'] = f.read()

with codecs.open('requirements.txt', mode='r', encoding='utf-8') as f:
    REQUIRES = f.read().split()

SETUP_REQUIRES = ['pytest-runner']
TEST_REQUIRES = ['pytest>=3.2.1', 'pytest-qt>=2.2.1']
PACKAGES = ['quantdom', ]
PACKAGE_DATA = {'': ['LICENSE']}


setup(
    name=INFO['package'],
    version=INFO['version'],
    description=INFO['short_description'],
    long_description=INFO['long_description'],
    author=INFO['author'],
    author_email=INFO['author_email'],
    license=INFO['license'],
    url=INFO['url'],
    install_requires=REQUIRES,
    setup_requires=SETUP_REQUIRES,
    tests_require=TEST_REQUIRES,
    packages=PACKAGES,
    package_data=PACKAGE_DATA,
    platforms='any',
    entry_points={
        'console_scripts': [
            'quantdom = quantdom.cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Science/Research',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment',
        'License :: OSI Approved :: Apache Software License',
    ],
    keywords='quant trading',
    zip_safe=False,
    test_suite='tests',
)
