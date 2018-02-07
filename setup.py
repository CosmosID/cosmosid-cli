#!/usr/bin/env python
"""
``CosmosID``
------------

``cosmosid`` provides a command line client and Python library for CosmosID

"""

from setuptools import setup, find_packages

__version__ = '0.1.0'

setup(
    name='cosmosid_cli',
    version=__version__,
    license='MIT',
    description='Command line client and Python 3 libraries for CosmosID API',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['contrib', 'docs', '*tests*']),
    python_requires='~=3.2',
    install_requires=['requests==2.17', 'cliff==2.8.0',
                      'six', 'boto3==1.4.2',
                      's3transfer==0.1.10', 'tzlocal==1.4'],
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
            'upload = cosmosid.command:Upload',
            'analysis = cosmosid.command:Analysis',
            'reports = cosmosid.command:Reports',
        ],

    },
    test_suite=''
)

