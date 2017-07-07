Cosmos ID Metagen
=================

Command line interface (CLI) and Python client library for interacting
with the CosmosID Metagen API.

Requirements
------------

OS Packages
~~~~~~~~~~~

-  python3
-  python3-pip

Python package
~~~~~~~~~~~~~~

-  boto3
-  cliff
-  s3transfer
-  requests

Installation
============

This package provides: \* core Python client library; \* a simple CLI
for interacting with the CosmosID Metagen that uses the core library;

Basic installation
------------------

The CLI with core Python library may be installed using ``pip``.
\* simply run from console ``pip install metagen_cli``

Using the Metagen CLI
=====================

The CosmosID Metagen CLI supports authentication via Metagen API Key.
Your API key can be found on the `CosmosID Metagen profile page`_. To
automaticaly authentication via Metagen API Key you should create
credential file ``~/.metagen`` and store your API Key into it in the
following format:

.. code:: json

    {"api_key": "<your api key string>"}

You can directly use your Metagen API Key, rather than storing it in a
credential file. To use API Key authentication, pass your key as an
argument to the ``metagen`` command:

.. code:: shell

    metagen --api_key=YOUR_API_KEY <command>

Commands
--------

The Metagen CLI supports retrieving your CosmosID data and analysis and
upload your samples to CosmosID Metagen for analyzing. \* files - for
retrieving files \* analysis - for retrieving analysis results for
specified file \* upload - for aploading samples into Metagen \* reports
- for analysis report retrieving

    Note: you can get help of usage for each command and argumet of
    ``metagen`` CLI to simply run ``metagen --help`` or
    ``metagen <command> --help``

Retrieve Files
~~~~~~~~~~~~~~

To retrieve files (samples) stored in the CosmosID simply run
``metagen`` command with a ``files`` subcommand. For example:

.. code:: shell

    #to get contents of your Metagen root folder
    metagen files

    #to get contents of appropriate folder use it id as argument
    metagen files --parent <folder_id>

    #to get ordered list simly use ordering argument with field name with/without order direction
    metagen files --parent <folder_id> --order size --up

Upload files
~~~~~~~~~~~~

The Metagen CLI supports uploads sample files into CosmosID for
analysis. Metagen supports following file types: *.fastq, .fasta, .fas,
.fa, .seq, .fsa, .fq, .fna, .gz*

    Note: you can get help for usage for each commands and argumets of
    ``metagen`` CLI to simply run ``metagen --help`` or
    ``metagen <command> --help``

To upload sample file to CosmosID run ``metagen`` command with
``upload`` subcommand.

.. code:: shell

    #to upload one sample file
    metagen upload --file <path to file>

    #to upload multiple sample files
    metagen upload -f <path to file-1> -f <path to file-2>

    Note: upload of a big file takes a some time, please be patient

Having file uploaded to CosmosID the analyzing process will be
automatically started. You can check the result of analysis on the page
`CosmosID Metagen Samples`_

.. _CosmosID Metagen profile page: https://www-int.cosmosid.com/settings
.. _CosmosID Metagen Samples: https://www-int.cosmosid.com/samples

Retrieving Analysis Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To retrieve analysis results for a specified file in the CosmosID simply run
``metagen`` command with a ``analysis`` subcommand. For example:

.. code:: shell

    #to get list of analysis for a given file id
    metagen analysis --id <file ID>

    #to get ordered list of analysis for a given file id simly use ordering argument with field name with/without order direction
    metagen analysis --id <file ID> --order created --up

Generate Analysis Report Archive
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Metagen CLI support retrieving analysis reports archive from
CosmosID Metagen for a given ``File ID`` and save archive to a given
file.

To retrieve analysis report archive with CSV files run ``metagen``
command with ``reports`` subcommand.

.. code:: shell

    #to create analysis report archive and save it in current directory with name equivalent to file name in the CosmosID Metagen
    metagen reports --id <file ID>

    #to create analysis report archive and save it into given directory
    metagen reports --id <file ID> --dir ~/metagen/reports

    #to create analysis report archive and save it into given local file
    metagen reports --id <file ID> --output /tmp/analysis_report.zip