"""
``CosmosID``
------------

``cosmosid`` provides a command line client and Python library for CosmosID

"""
from setuptools import setup, find_packages

__version__ = '0.7.0'

def _get_requirements():
    with open('requirements.txt') as _file:
        requirements = _file.read().splitlines()
    requirements.append('pywin32==223;platform_system=="Windows"')
    return requirements

setup(
    name='cosmosid_cli',
    version=__version__,
    license='MIT',
    description='Command line client and Python 3 libraries for CosmosID API',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['contrib', 'docs', '*tests*']),
    python_requires='>=3.5',
    install_requires=_get_requirements(),
    package_data={
        'cosmosid': ['logger_config.yaml', ],
    },
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
