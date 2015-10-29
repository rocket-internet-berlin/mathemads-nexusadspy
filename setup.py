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
    author='Daniel Olel, Georg Waltherg',
    author_email='daniel.olel@rocket-internet.com, '
                 'georg.waltherg@rocket-internet.com',
    url='https://github.com/rocket-om/open_nexusadspy',
    packages=['nexusadspy'],
    package_dir={'nexusadspy': 'nexusadspy'},
    package_data={},
    include_package_data=False,
    zip_safe=False,
    keywords='nexuadspy appnexus api python',
    classifiers=[
        'Development Status :: In Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ]
)
