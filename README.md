# Cosmos ID

 Command line interface (CLI) and Python 3 client library for interacting with the CosmosID API. Only works with Python 3, Python 2.7 is not supported yet.

## Requirements

### OS Packages
* python3
* python3-pip

### Python package
* boto3
* cliff
* s3transfer
* requests

# Installation

This package provides:
* core Python 3 client library;
* a simple CLI for interacting with the CosmosID that uses the core library;

## Basic installation
The CLI with the core Python library can be installed using `pip3`.
* simply run from console `sudo pip3 install cosmosid_cli`

> Note: pip3 and setuptools should be upgraded to latest version. Please update those packages on you workstation regarding to your OS update process before setup cosmosid cli.
> ```shell
> E.g. for Ubuntu 14.04 perform following steps:
> $ sudo apt-get update
> $ sudo apt-get upgrade
> $ sudo -H pip3 install -U pip setuptools 
>```
> If you had have previously installed CosmosID CLI just upgrade CLI  
> to latest version.
> ```shell
> $ sudo -H pip3 install --upgrade cosmosid_cli
> ```


# Using the CosmosID CLI

The CosmosID CLI supports authentication via CosmosID API Key.
Your API key can be found on the [CosmosID profile page](https://app.cosmosid.com/settings).
To automatically authenticate via CosmosID API Key you should create  
credential file `~/.cosmosid` and store your API Key into it in  
the following format:
```json
{"api_key": "<your api key string>"}
```
You can directly use your CosmosID API Key, rather than storing it in a credential file. To use API Key authentication, pass your key as an argument to the `cosmosid` command:
```shell
cosmosid --api_key=YOUR_API_KEY <command>
```

## Commands

There are several types of commands supported by the CosmosID CLI
1. Commands for retrieving data to terminal (output) from CosmosID cloud - files, analysis.
2. Commands for uploading metagenomics or amplicon samples to 
   CosmosID cloud for analysis - uploads.
3. Commands for retrieving the reports archive from CosmosID cloud - reports

> Note: Each command has options. To get usage information for each CosmosID CLI command, the user can simply run `cosmosid <command> --help`

### Retrieve Files
The commands for retrieving data have options for output format. The user can get data into the terminal (or another output) in a different format - csv, json, table, value, yaml (table is default), and specify the column(s) to show. In additional there are CSV format options, user can quote
or unquote or partly quote output values - all, minimal, none, non-numeric (by default only non-numeric values are quoted)

Example of output for the --help options for the <files> command:
```shell
$ cosmosid files --help
usage: cosmosid files [-h] [-f {csv,json,table,value,yaml}] [-c COLUMN]
                      [--noindent] [--max-width <integer>] [--fit-width]
                      [--print-empty] [--quote {all,minimal,none,nonnumeric}]
                      [--parent PARENT]
                      [--order {type,name,id,status,size,created}] [--up]

Show files in a given directory.

optional arguments:
  -h, --help            show this help message and exit
  --parent PARENT, -p PARENT
                        ID of the parent directory. Default: Root
  --order {type,name,id,status,size,created}, -o {type,name,id,status,size,created}
                        field for ordering
  --up                  order direction

output formatters:
  output formatter options

  -f {csv,json,table,value,yaml}, --format {csv,json,table,value,yaml}
                        the output format, defaults to table
  -c COLUMN, --column COLUMN
                        specify the column(s) to include, can be repeated

json formatter:
  --noindent            whether to disable indenting the JSON

table formatter:
  --max-width <integer>
                        Maximum display width, <1 to disable. You can also use
                        the CLIFF_MAX_TERM_WIDTH environment variable, but the
                        parameter takes precedence.

  --fit-width       Fit the table to the display width. Implied if --max-
                        width greater than 0. Set the environment variable
                        CLIFF_FIT_WIDTH=1 to always enable

 --print-empty     Print empty table if there is no data to show.

CSV Formatter:
  --quote {all,minimal,none,nonnumeric} when to include quotes, defaults to nonnumeric
```

To retrieve files (samples) stored in CosmosID simply run the `cosmosid` command with a `files` subcommand. For example:
```shell
#to get contents of your CosmosID root folder
cosmosid files

#to get contents of appropriate folder use its id as argument
cosmosid files --parent <folder_id>

#to get ordered list simply use the ordering argument with field name with/without order direction
cosmosid files --parent <folder_id> --order size --up
```
### Upload files
The CosmosID CLI supports uploading sample files into CosmosID for analysis. CosmosID supports the following file types:
*.fastq, .fasta, .fas, .fa, .seq, .fsa, .fq, .fna, .gz*

CosmosID supports the following types of analysis:
* Metagenomics
* Amplicon - 16S or ITS (only 16S and ITS supported for now)

> Note: you can get usage help for each command and arguments of CosmosID CLI by simply runnig `cosmosid --help` or `cosmosid <command> --help`

To upload sample file to CosmosID run `cosmosid` command with `upload` subcommand. By default samples will be uploaded into root folder. To upload sample into specific *existing* folder you must use id of the folder as parameter.
```shell
#to upload one sample file for Metagenomics analysis
cosmosid upload --file <path to file> --type metagenomics

#to upload sample file into specific folder for Amplicon 16s analysis
cosmosid upload --file <path to file-1> --parent <folder id> --type amplicon-16s
```

> Note: uploading of a big file takes time, please be patient

Once file has been uploaded to CosmosID the analyzing process will automatically begin.
You can check the status of metagenomics analysis on the page [CosmosID Samples](https://app.cosmosid.com/samples).  
Amplicon analysis results available only from CosmosID CLI for now.

### Retrieving Analysis Results

To retrieve analysis results for a specified file in CosmosID simply run `cosmosid` command with `analysis` subcommand. For example:
```shell
#to get list of analysis for a given file id
cosmosid analysis --id <file ID>

#to get ordered list of analysis for a given file id simly use ordering  
argument with field name with/without order direction
cosmosid analysis --id <file ID> --order created --up
```

> Note: There is no analysis results for Amplicon 16S and Amplicon ITS sample. Use report generation instead of getting list of analysis for Amplicon 16S and Amplicon ITS.

### Generate Analysis Report Archive
The CosmosID CLI supports retrieving the archive of analysis reports from CosmosID for a given `File ID` and saving the archive to a given file.

To retrieve an analysis report archive with TSV files run the `cosmosid` command with `reports` subcommand.
```shell
#to create analysis report archive and save it in a current directory with  
a name equivalent to file name in CosmosID
cosmosid reports --id <file ID>

#to create analysis report archive and save it into given directory
cosmosid reports --id <file ID> --dir ~/cosmosid/reports

#to create analysis report archive and save it into a given local file
cosmosid reports --id <file ID> --output /tmp/analysis_report.zip
```
