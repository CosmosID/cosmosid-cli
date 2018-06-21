#!/usr/bin/env python
"""
``CosmosID``
------------

``cosmosid`` provides a command line client and Python library for CosmosID

"""

import sys

from setuptools import setup, find_packages

__version__ = '0.3.0'

setup(
    name='cosmosid_cli',
    version=__version__,
    license='MIT',
    description='Command line client and Python 3 libraries for CosmosID API',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['contrib', 'docs', '*tests*']),
    python_requires='~=3.5',
    install_requires=['requests>=2.17', 'cliff==2.8.0', 'PyYAML==3.12',
                      'six', 'boto3>=1.4.2', 'concurrent-log-handler==0.9.9',
                      's3transfer>=0.1.10', 'tzlocal==1.4'] + \
                     ['pywin32==223'] if sys.platform.startswith("win") else [],
    include_package_data=True,
    dependency_links=[],
    author='CosmosID',
    author_email='support@cosmosid.com',
    keywords='API Client for CosmosID',
    url='https://www.cosmosid.com/',
    classifiers=[
        'Environment :: Console',
    ],
    entry_points={
        'console_scripts': ['cosmosid = cosmosid.cli:main'],
        'cosmosid': [
            'files = cosmosid.command:Files',
            'runs = cosmosid.command:Runs',
            'analysis = cosmosid.command:Analysis',
            'upload = cosmosid.command:Upload',
            'reports = cosmosid.command:Reports',
        ],

    },
    test_suite=''
)
