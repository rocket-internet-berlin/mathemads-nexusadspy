# !/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='nexusadspy',
    version='0.1.0',
    description='Thin wrapper around AppNexus API',
    author='Daniel Olel, Georg Walther',
    author_email='daniel.olel@rocket-internet.com, '
                 'georg.walther@rocket-internet.com',
    url='https://github.com/mathemads/nexusadspy',
    download_url='https://github.com/mathemads/nexusadspy/tarball/master',
    packages=['nexusadspy'],
    package_dir={'nexusadspy': 'nexusadspy'},
    package_data={},
    include_package_data=False,
    zip_safe=False,
    keywords='nexuadspy appnexus api python',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ]
)
