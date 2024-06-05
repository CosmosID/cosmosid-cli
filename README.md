# CosmosID-HUB Microbiome CLI

Command line interface (CLI) and Python 3 client library for interacting with the CosmosID-HUB API. Only works with
Python [3.6,3.7,3.8,3.9,3.10].

## Requirements

### OS Packages

* python3
* python3-pip

### Python package

* poetry

# Installation

This package provides:

* core Python 3 client library;
* a simple CLI for interacting with the CosmosID-HUB API;

## Basic installation

The CLI with the core Python library can be installed using `pip3`.

* simply run from console `sudo pip3 install cosmosid_cli`

> Note: pip3 and setuptools should be upgraded to latest version. Please update those packages on you workstation
> regarding to your OS update process before setup CosmosID-HUB CLI.
>
> ```shell
> E.g. for Ubuntu 14.04 perform following steps:
> $ sudo apt-get update
> $ sudo apt-get upgrade
> $ sudo -H pip3 install -U pip setuptools
>```
>
> If you had have previously installed CosmosID-HUB CLI just upgrade CLI
> to latest version.
>
> ```shell
> $ sudo -H pip3 install --upgrade cosmosid_cli
> ```

To install package locally from folder with source files do the following:

* install `poetry` check the [doc](https://python-poetry.org/docs/#osx--linux--bashonwindows-install-instructions)
* `cd cosmosid-cli/package/`
* `poetry install`

## Installation from package management service Anaconda.org
Assure that you have Conda already installed or install it based on your system requirements - [link](https://docs.anaconda.com/anaconda/install/ )

Follow the [cosmosid project page](https://anaconda.org/cosmosid/cosmosid-cli) to check the last version of cosmosid-cli available on Anaconda.org

The CLI with Conda can be installed by the following command:
```shell
conda install -c cosmosid -c conda-forge cosmosid-cli
```

Verify the CLI version installed
```shell
cosmosid --version
```

## Using the CosmosID-HUB CLI

The CosmosID-HUB CLI supports authentication via CosmosID-HUB API Key.
Your API key can be found on the [CosmosID-HUB profile page](https://app.cosmosid.com/settings).
To automatically authenticate via CosmosID-HUB API Key you should create
credential file `~/.cosmosid` and store your API Key into it in
the following format:

```json
{
  "api_key": "<your api key string>"
}
```

You can directly use your CosmosID-HUB API Key, rather than storing it in a credential file. To use API Key authentication,
pass your key as an argument to the `cosmosid` command:

```shell
cosmosid --api_key=YOUR_API_KEY <command>
```

CLI supports files of following extensions: 'fasta', 'fna', 'fasta.gz', 'fastq', 'fq', 'fastq.gz', 'bam', 'sra'

## Commands

There are several types of commands supported by the CosmosID-HUB CLI

1. Commands for retrieving data to terminal (output) from CosmosID cloud - files, runs, analysis.
2. Commands for uploading metagenomics or amplicon samples to
   CosmosID cloud for analysis - uploads.
3. Commands for retrieving the reports archive from CosmosID cloud - reports

> Note: Each command has options. To get usage information for each CosmosID-HUB CLI command, the user can simply
> run `cosmosid <command> --help`

### Make Directory

The command to make a new directory or sub-directory. See --help for options:

```
usage: cosmosid mkdir [-h] [--parent PARENT] [--name NAME]

Make a new directory in a given directory.

options:
  -h, --help            show this help message and exit
  --parent PARENT, -p PARENT
                        ID of the parent directory. Default: Root
  --name NAME, -n NAME
                        Name of the new directory
```
Example to create a `New` in some parent (`41dad2d0-dcf2-429c-8e06-1ebea192985d`):
```shell
cosmosid --api_key=your-key mkdir -n New -p 41dad2d0-dcf2-429c-8e06-1ebea192985d
```

### Retrieve Files

The commands for retrieving data have options for output format. The user can get data into the terminal (or another
output) in a different format - csv, json, table, value, yaml (table is default), and specify the column(s) to show. In
additional there are CSV format options, user can quote
or unquote or partly quote output values - all, minimal, none, non-numeric (by default only non-numeric values are
quoted)

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
  --order {type,name,id,status,reads,created}, -o {type,name,id,status,size,created}
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
                        Maximum display width, 1 to disable. You can also use
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
cosmosid files --parent=<folder_id>

#to get ordered list simply use the ordering argument with field name with/without order direction
cosmosid files --parent=<folder_id> --order size --up
```

### Retrieve Sample Runs

An each file (sample) stored in CosmosID has one or more Sample Run(s) associated with it.

Example of output for the --help options for the <runs> command:

```shell
$ cosmosid runs --help

usage: cosmosid runs [-h] [-f {csv,json,table,value,yaml}] [-c COLUMN] [--quote {all,minimal,none,nonnumeric}] [--noindent] [--max-width <integer>]
                     [--fit-width] [--print-empty] [--sort-column SORT_COLUMN] [--sort-ascending | --sort-descending] --id ID [--order {id,status,created}] [--up]

Show List Of Runs for a given File.

optional arguments:
  -h, --help            show this help message and exit
  --id ID, -i ID
                        ID of the sample
  --order {id,status,created}, -o {id,status,created}
                        field for ordering
  --up                  order direction

output formatters:
  output formatter options

  -f {csv,json,table,value,yaml}, --format {csv,json,table,value,yaml}
                        the output format, defaults to table
  -c COLUMN, --column COLUMN
                        specify the column(s) to include, can be repeated to show multiple columns
  --sort-column SORT_COLUMN
                        specify the column(s) to sort the data (columns specified first have a priority, non-existing columns are ignored), can be repeated
  --sort-ascending      sort the column(s) in ascending order
  --sort-descending     sort the column(s) in descending order

CSV Formatter:
  --quote {all,minimal,none,nonnumeric}
                        when to include quotes, defaults to nonnumeric

json formatter:
  --noindent            whether to disable indenting the JSON

table formatter:
  --max-width <integer>
                        Maximum display width, <1 to disable. You can also use the CLIFF_MAX_TERM_WIDTH environment variable, but the parameter takes precedence.
  --fit-width           Fit the table to the display width. Implied if --max-width greater than 0. Set the environment variable CLIFF_FIT_WIDTH=1 to always enable
  --print-empty         Print empty table if there is no data to show.
```


For example:
To retrieve sample run(s) associated with a file simply run the `cosmosid` command with `runs` subcommand. 

```shell
#to get runs associated with a speciffic file (sample)
cosmosid runs --id=<file_id>

#command output:

Runs list for file example_2.fastq.gz (id: 5020a209-30b8-4fb3-bd78-b9fa1cd9f3ae)

+--------------------------------------+---------------------+---------------+------------------+---------+--------------------------------------+
| id                                   | created             | workflow_name | workflow_version | status  | artifact_types                       |
+--------------------------------------+---------------------+---------------+------------------+---------+--------------------------------------+
| a3dfe717-15d0-5053-a5b7-5c24597b73b4 | 2022-05-16 17:41:13 | ura           | 1.0.0            | Success | ura                                  |
| d722bfcb-a3e7-4617-9141-20f5168e8c2f | 2022-05-16 17:40:15 | amr_vir       | 1.0.0            | Success | functional-pathway,functional-goterm |
+--------------------------------------+---------------------+---------------+------------------+---------+--------------------------------------+
```

### Upload files

The CosmosID-HUB CLI supports uploading sample files into CosmosID for analysis.
CosmosID supports the following file formats and extension names:
.fasta, .fna, .fasta.gz, .fastq, .fq, .fastq.gz, bam, bam.gz, sra, sra.gz. (SRA files can be uploaded without extension)

CosmosID supports the following types of analysis:

* Metagenomics
* Amplicon - 16S or ITS (only 16S and ITS supported for now)

> Note: you can get usage help for each command and arguments of CosmosID-HUB CLI by simply runnig `cosmosid --help`
> or `cosmosid <command> --help`

```shell
# cosmosid upload --help
usage: cosmosid upload [-h] [--file FILE] [--parent PARENT] --type {metagenomics,amplicon-16s,amplicon-its}
                       [-wf WORKFLOW] [--forward-primer FORWARD_PRIMER] [--reverse-primer REVERSE_PRIMER]
                       [--amplicon-preset {v1_v3,v3_v4,v4}]
                       [--host-name {human:2.0.0,human:1.0.0,dog:2.0.0,domestic_cat:2.0.0,cow:1.0.0,chicken:2.0.0,mouse:2.0.0,monkey:2.0.0,cattle:2.0.0,pig:2.0.0}]
                       [--dir DIR]

Upload files to cosmosid.

optional arguments:
  -h, --help            show this help message and exit
  --file FILE, -f FILE
                        file(s) for upload. Supported file types: fasta, fna, fasta.gz, fastq, fq, fastq.gz, bam, sra e.g. cosmosid upload
                        -f /path/file1.fasta -f /path/file2.fn
  --parent PARENT, -p PARENT
                        cosmosid parent folder ID for upload
  --type {metagenomics,amplicon-16s,amplicon-its}, -t {metagenomics,amplicon-16s,amplicon-its}
                        Type of analysis for a file
  -wf WORKFLOW, --workflow WORKFLOW
                        To specify multiple workflows, define them coma separated without any additional symbols.For example: 
                        -wf amr_vir,taxa
                        To specify workflow verions, define it by ':'. For example:
                        -wf taxa:1.1.0,amr_vir

  --forward-primer FORWARD_PRIMER
                        Only for 'ampliseq' workflow
  --reverse-primer REVERSE_PRIMER
                        Only for 'ampliseq' workflow
  --amplicon-preset {v1_v3,v3_v4,v4}
                        Only for 'ampliseq' workflowv1_v3:
                        - forward_primer: AGAGTTTGATCCTGGCTCAG
                        - reverse_primer: ATTACCGCGGCTGCTGG
                        v3_v4:
                        - forward_primer: CCTACGGGRSGCAGCA
                        - reverse_primer: GACTACHVGGGTATCTAATCC
                        v4:
                        - forward_primer: GTGYCAGCMGCCGCGGTAA
                        - reverse_primer: GGACTACHVGGGTWTCTAAT
  --host-name {human:2.0.0,human:1.0.0,dog:2.0.0,domestic_cat:2.0.0,cow:1.0.0,chicken:2.0.0,mouse:2.0.0,monkey:2.0.0,cattle:2.0.0,pig:2.0.0}
                        Name for host removal.
                        *Available only for type `metagenomics`
                        human:2.0.0 - Human 2.0.0 (GCF_009914755.1_T2T-CHM13v2.0)
                        human:1.0.0 - Human 1.0.0 (GRCh38_p6)
                        dog:2.0.0 - Dog (GCF_014441545.1_ROS_Cfam_1.0)
                        domestic_cat:2.0.0 - Domestic Cat (GCF_018350175.1_F.catus_Fca126_mat1.0)
                        cow:1.0.0 - Cow (GCF_002263795l_1_ARS-UCD1_2)
                        chicken:2.0.0 - Chicken (GCF_016699485.2_bGalGal1.mat.broiler.GRCg7b)
                        mouse:2.0.0 - Mouse (GCF_000001635.27_GRCm39)
                        monkey:2.0.0 - Monkey (GCF_003339765.1_Mmul_10)
                        cattle:2.0.0 - Cattle (GCF002263795.2 - ARS-UCD1.3)
                        pig:2.0.0 - Pig (GCF_000003025.6_Sscrofa11.1)
  --dir DIR, -d DIR
                        directory with files for upload e.g. cosmosid upload -d /path/my_dir

```

To upload sample file to CosmosID run `cosmosid` command with `upload` subcommand. By default samples will be uploaded
into root folder. To upload sample into specific *existing* folder you must use id of the folder as parameter.
The CosmosID-HUB CLI supports uploading multiple Single-Read and Paired-End samples. For Paired-End samples, the CLI
automatically parse and merge samples in pairs if the samples follow the naming conventions like: xxx_R1.fastq and
xxx_R2.fastq OR xxx_R1_001.fastq and xxx_R2_001.fastq. Note: Paired-End samples require "fastq" format

To upload all samples from folder run `cosmosid upload` command with path to folder specified by --dir/-d parameter
> Note: _This command respects Paired-End samples grouping with the same rules as for regular upload_

> Note: _The default workflow is `taxa`_, that is not allowed for amplicon samples, and should be overriden by `--workflow` argument.

> Note: _You can view all possible workflows by `workflow` command

Running example:

`cosmosid upload --type metagenomics -f /pathtofile/test1_R1.fastq` -f /pathtofile/test1_R2.fastq -f
/pathtofile/test2.fasta

```shell
#to upload one sample file for Metagenomics analysis
cosmosid upload --file <path to file> --type metagenomics

#to upload sample file into specific folder for Amplicon 16s analysis
cosmosid upload --file <path to file-1> --parent <folder id> --type amplicon-16s

#to upload all files from folder
cosmosid upload -d /home/user/samples/ --type metagenomics

#to upload with host-removal
cosmosid upload --file <path to file> --type metagenomics --host-name <host name>

#to upload ampliseq-batch
cosmosid upload --file <path to file> --type amplicon-16s --workflow ampliseq --amplicon-preset <preset>
cosmosid upload --file <path to file> --type amplicon-16s --workflow ampliseq --forward-primer <forward primer> --reverse-primer <reverse primer>

```

> Note: uploading of a big file takes time, please be patient
> Available host names: human:2.0.0, human:1.0.0, dog:2.0.0, domestic_cat:2.0.0, cow:1.0.0, chicken:2.0.0, mouse:2.0.0, monkey:2.0.0, cattle:2.0.0, pig:2.0.0

Once file has been uploaded to CosmosID the analyzing process will automatically begin.
You can check the status of metagenomics analysis on the page [CosmosID Samples](https://app.cosmosid.com/samples).
Amplicon analysis results available only from CosmosID-HUB CLI for now.

### Get enabled workflows

To view workflows, that can be used for `upload` command, you can use `workflows` command:

```shell
cosmosid workflows
```

Result:
```
Using base URL: https://app.cosmosid.com
+---------------+---------+----------------------------+---------------------------------------------------------------------------------------------------------------+
| Name          | Version | Sample Type                | Description                                                                                                   |
+---------------+---------+----------------------------+---------------------------------------------------------------------------------------------------------------+
| amplicon_its  | 1.0.0   | Amplicon ITS               | Amplicon ITS workflow allows you to characterize the fungi in a microbial community based on ITS              |
|               |         |                            | (internal transcribed spacer) region with a genus to species taxonomic resolution of fungi.                   |
| ampliseq      | 1.0.0   | Amplicon 16S               | Amplicon 16S workflow allows you to characterize the bacteria in a microbial community based on 16S           |
|               |         |                            | rRNA marker gene with a genus to species taxonomic resolution of bacteria.                                    |
|               |         |                            |                                                                                                               |
|               |         |                            | Please be advised, we recommend running Amplicon 16S workflow with a batch of sequencing data that has        |
|               |         |                            | been generated from the same sequencing run. Running the Amplicon 16S workflow in a group of samples          |
|               |         |                            | from the same sequencing run allows for more accurate error correction and denoising because it takes         |
|               |         |                            | advantage of the technical variability present within the sequencing run. This variability can be used        |
|               |         |                            | to identify and correct errors that are specific to the sequencing run, rather than errors that are           |
|               |         |                            | specific to individual samples. That&#39;s why running Amplicon 16S with only 1 sample may not yield          |
|               |         |                            | successful results.                                                                                           |
| amr_vir       | 1.0.0   | Shotgun metagenomics (WGS) | The AMR and Virulence Marker workflow allows you to characterize the antimicrobial and virulence genes        |
|               |         |                            | in the microbiome community.                                                                                  |
| amr_vir       | 1.1.0   | Shotgun metagenomics (WGS) | None                                                                                                          |
| bacteria_beta | 1.0.0   | Shotgun metagenomics (WGS) | The Bacteria Beta 2.1.0 workflow allows you to characterize the composition of the bacterial community        |
|               |         |                            | in your sample with our new Bacterial Beta Database 2.1.0.                                                    |
| functional    | 1.0.0   | Shotgun metagenomics (WGS) | The Functional workflow allows you to leverage the power of the MetaCyc Pathway and Gene Ontology             |
|               |         |                            | databases to characterize and predict the functional potential of the underlying microbiome community.        |
|               |         |                            |                                                                                                               |
|               |         |                            | If you are planning to run Functional 1.0 workflow for your data, please consider running Functional          |
|               |         |                            | 2.0 since Functional 1.0 will be phased out and will be unavailable on the HUB in 6 months time.              |
| kepler        | 1.0.0   | Shotgun metagenomics (WGS) | We are delighted to present the newest edition of our Taxa Workflow, "Taxa-Kepler". The taxa                  |
|               |         |                            |       workflow has been upgraded to effectively merge the sensitivity and precision of our k-mer methodology  |
|               |         |                            |       with our novel Probabilistic Smith-Waterman read-alignment approach. The resulting integration not only |
|               |         |                            |       augments the ability to estimate taxa abundance but also enhances the classification accuracy and       |
|               |         |                            |       precision. Experience accurate microbiome community characterization with "Taxa-Kepler"                 |
| kepler        | 1.1.0   | Shotgun metagenomics (WGS) | None                                                                                                          |
| kepler_domain | 1.1.0   | Shotgun metagenomics (WGS) | None                                                                                                          |
| taxa          | 1.1.0   | Shotgun metagenomics (WGS) | The Taxa workflow allows you to leverage the power of the CosmosID taxonomic databases to characterize        |
|               |         |                            | the microbiome community with strain level resolution across multiple kingdoms.                               |
| taxa          | 1.2.0   | Shotgun metagenomics (WGS) | The Taxa workflow allows you to leverage the power of the CosmosID taxonomic databases to characterize        |
|               |         |                            | the microbiome community with strain level resolution across multiple kingdoms.                               |
+---------------+---------+----------------------------+---------------------------------------------------------------------------------------------------------------+

```

### Retrieving Analysis Results

Analysis results can be retrieved from CosmosID by useing run id or file id. The latest run analysis results will be
retrieved when file id used.
To retrieve analysis results for a specified run in CosmosID simply run `cosmosid` command with `analysis` subcommand.

```shell
$ cosmosid analysis --help
usage: cosmosid analysis [-h] [-f {csv,json,table,value,yaml}] [-c COLUMN] [--quote {all,minimal,none,nonnumeric}] [--noindent] [--max-width <integer>]
                         [--fit-width] [--print-empty] [--sort-column SORT_COLUMN] [--sort-ascending | --sort-descending] [--id ID] [--run_id RUN_ID]
                         [--order {database,id,strains,strains_filtered,status}] [--up]

Show Analysis for a given file.

optional arguments:
  -h, --help            show this help message and exit
  --id ID, -i ID
                        ID of a file
  --run_id RUN_ID, -r RUN_ID
                        ID of a sample run
  --order {database,id,strains,strains_filtered,status}, -o {database,id,strains,strains_filtered,status}
                        field for ordering
  --up                  order direction

output formatters:
  output formatter options

  -f {csv,json,table,value,yaml}, --format {csv,json,table,value,yaml}
                        the output format, defaults to table
  -c COLUMN, --column COLUMN
                        specify the column(s) to include, can be repeated to show multiple columns
  --sort-column SORT_COLUMN
                        specify the column(s) to sort the data (columns specified first have a priority, non-existing columns are ignored), can be repeated
  --sort-ascending      sort the column(s) in ascending order
  --sort-descending     sort the column(s) in descending order

CSV Formatter:
  --quote {all,minimal,none,nonnumeric}
                        when to include quotes, defaults to nonnumeric

json formatter:
  --noindent            whether to disable indenting the JSON

table formatter:
  --max-width <integer>
                        Maximum display width, <1 to disable. You can also use the CLIFF_MAX_TERM_WIDTH environment variable, but the parameter takes precedence.
  --fit-width           Fit the table to the display width. Implied if --max-width greater than 0. Set the environment variable CLIFF_FIT_WIDTH=1 to always enable
  --print-empty         Print empty table if there is no data to show.
```


For example:

```shell
#to get list of analysis for the latest run of file
cosmosid analysis --id=<file ID>

#to get list of analysis for a given run id
cosmosid analysis --run_id=<run ID>

#to get ordered list of analysis for a given file id simply use ordering argument with field name with/without order direction
cosmosid analysis --id=<file ID> --order created --up
```

> Note: There is no analysis results for Amplicon 16S and Amplicon ITS sample. Use report generation instead of getting
> list of analysis for Amplicon 16S and Amplicon ITS.

### Generate Analysis Report Archive

The CosmosID-HUB CLI supports retrieving the archive of analysis reports from CosmosID for a given `File ID` with a
given `Run ID` and saving the archive to a given file.

To retrieve an analysis report archive with TSV files run the `cosmosid` command with `reports` subcommand.

```shell
$ cosmosid reports --help
usage: cosmosid reports [-h] --id ID [--timeout TIMEOUT]
                        [--output OUTPUT | --dir DIR]

Get analysis reports TSV

optional arguments:
  -h, --help            show this help message and exit
  --id ID, -i ID
                        ID of cosmosid sample.
  --timeout TIMEOUT, -t TIMEOUT
                        The timeout in seconds. Default: 5 minutes.
  --output OUTPUT, -o OUTPUT
                        output file name. Must have .zip extension. Default: is equivalent to cosmosid file name.
  --dir DIR, -d DIR
                        Output directory for a file. Default: is current directory.
```

For example:

```shell
# to create analysis report archive for the latest run of sample and save it in
# a current directory with a name equivalent to file name in CosmosID
cosmosid reports --id=<file ID>

# to create analysis report archive for the given run of sample and save it in
# a current directory with a name equivalent to file name in CosmosID
cosmosid reports --id=<file ID> --run_id=<run ID>

# to create analysis report archive for the given run of sample and save it
# in a given directory
cosmosid reports --id=<file ID> --run_id=<run ID> --dir ~/cosmosid/reports

# to create analysis report archive for the given run of sample and save it
# into a given local file
cosmosid reports --id=<file ID> --output /tmp/analysis_report.zip
```

### Retrieving Artifacts Results

Artifacts results can be retrieved from CosmosID by using run id.
To retrieve artifacts results for a specified run in CosmosID simply run `cosmosid` command with `artifacts` subcommand.
```shell
$ cosmosid artifacts --help
usage: cosmosid artifacts [-h] [-f {csv,json,table,value,yaml}] [-c COLUMN] [--quote {all,minimal,none,nonnumeric}] [--noindent] [--max-width <integer>]
                          [--fit-width] [--print-empty] [--sort-column SORT_COLUMN] [--sort-ascending | --sort-descending] --run_id RUN_ID [--type {fastqc-zip}]
                          [--url] [--output OUTPUT] [--dir DIR]

Show Artifacts for a given file.

optional arguments:
  -h, --help            show this help message and exit
  --run_id RUN_ID, -r RUN_ID
                        ID of a sample run
  --type {fastqc-zip}, -t {fastqc-zip}
                        Artifact type to download
  --url                 show download url
  --output OUTPUT, -o OUTPUT
                        output file name. Must have .zip extension. Default: is equivalent to cosmosid file name.
  --dir DIR, -d DIR
                        Output directory for a file. Default: is current directory.

output formatters:
  output formatter options

  -f {csv,json,table,value,yaml}, --format {csv,json,table,value,yaml}
                        the output format, defaults to table
  -c COLUMN, --column COLUMN
                        specify the column(s) to include, can be repeated to show multiple columns
  --sort-column SORT_COLUMN
                        specify the column(s) to sort the data (columns specified first have a priority, non-existing columns are ignored), can be repeated
  --sort-ascending      sort the column(s) in ascending order
  --sort-descending     sort the column(s) in descending order

CSV Formatter:
  --quote {all,minimal,none,nonnumeric}
                        when to include quotes, defaults to nonnumeric

json formatter:
  --noindent            whether to disable indenting the JSON

table formatter:
  --max-width <integer>
                        Maximum display width, <1 to disable. You can also use the CLIFF_MAX_TERM_WIDTH environment variable, but the parameter takes precedence.
  --fit-width           Fit the table to the display width. Implied if --max-width greater than 0. Set the environment variable CLIFF_FIT_WIDTH=1 to always enable
  --print-empty         Print empty table if there is no data to show.
```


For example:

```shell

#to get list of artifacts for a given run id
cosmosid artifacts --run_id=<run ID>

##to create artifacts archive for the given run id of sample and store it to given path
cosmosid artifacts --run_id=<run ID> --type=fastqc-zip --dir /home/user


##to create artifacts archive for the given run id of sample and store it with given name in current dir
cosmosid artifacts --run_id=<run ID> --type=fastqc-zip --output artifacts_report.zip

##to create artifacts archive for the given run id of sample and store it with given name and given dir
cosmosid artifacts --run_id=<run ID> --type=fastqc-zip --dir /home/user --output artifacts_report.zip

#to get url to download the archive
cosmosid artifacts --run_id=<run ID> --type=fastqc-zip --url
```

### Download Original Samples

Original samples can be downloaded from CosmosID by using samples_ids.
To download samples for a specified samples_id in CosmosID simply run `cosmosids` command with `download` subcommand.

> Note: We recommend installing pycurl for the best experience with a sample download,
> see: http://pycurl.io/docs/latest/index.html#installation

```shell
$ cosmosid download --help
usage: cosmosid download [-h] [-f {csv,json,table,value,yaml}] [-c COLUMN] [--quote {all,minimal,none,nonnumeric}] [--noindent] [--max-width <integer>]
                         [--fit-width] [--print-empty] [--sort-column SORT_COLUMN] [--sort-ascending | --sort-descending] [--samples_ids SAMPLES_IDS]
                         [--input-file INPUT_FILE] [--dir DIR] [--no-display] [--concurrent-downloads CONCURRENT_DOWNLOADS]

Download Samples for a given samples ids.

optional arguments:
  -h, --help            show this help message and exit
  --samples_ids SAMPLES_IDS, -s SAMPLES_IDS
                        Comma separated list of samples uuids
  --input-file INPUT_FILE
                        Path to file with samples' ids
  --dir DIR, -d DIR
                        Output directory for a file. Default: is current directory.
  --no-display          Disable displaying loading process
  --concurrent-downloads CONCURRENT_DOWNLOADS
                        Limit concurrent files downloads

output formatters:
  output formatter options

  -f {csv,json,table,value,yaml}, --format {csv,json,table,value,yaml}
                        the output format, defaults to table
  -c COLUMN, --column COLUMN
                        specify the column(s) to include, can be repeated to show multiple columns
  --sort-column SORT_COLUMN
                        specify the column(s) to sort the data (columns specified first have a priority, non-existing columns are ignored), can be repeated
  --sort-ascending      sort the column(s) in ascending order
  --sort-descending     sort the column(s) in descending order

CSV Formatter:
  --quote {all,minimal,none,nonnumeric}
                        when to include quotes, defaults to nonnumeric

json formatter:
  --noindent            whether to disable indenting the JSON

table formatter:
  --max-width <integer>
                        Maximum display width, <1 to disable. You can also use the CLIFF_MAX_TERM_WIDTH environment variable, but the parameter takes precedence.
  --fit-width           Fit the table to the display width. Implied if --max-width greater than 0. Set the environment variable CLIFF_FIT_WIDTH=1 to always enable
  --print-empty         Print empty table if there is no data to show.
```


For example:

```shell

#to download the original samples and save them in the current dir
cosmosid download --samples_ids=<sample_id>

#to download the originals samples and save them in the current dir
cosmosid download --samples_ids=<sample_id>,<sample_id> #separated by comma ","

#to download the originals samples and store them in the given path
cosmosid download --samples_ids=<sample_id>,<sample_id> --dir=<path_to_directory>

#to download the originals samples without displaying download progress
cosmosid download --samples_ids=<samples_id>,<sample_id> --no-display

#to download the original samples with specified quantity of concurrent files downloads
cosmosid download --samples_ids=<sample_id>,<sample_id> --concurrent-downloads=<quantity>

#to download the original samples using file with their ids
cosmosid download --input-file=<path-to-file>

```

> Note: You can specify chunk size by CHUNK_SIZE environment variable

### Comparative analysis

It's possible to view list of comparative analyses and download them.

#### List commands

```shell
#print list of comparatives generated using metadata & cohorts menu
cosmosid comparatives --help

usage: cosmosid comparatives [-h] [-f {csv,json,table,value,yaml}] [-c COLUMN] [--quote {all,minimal,none,nonnumeric}] [--noindent] [--max-width <integer>]
                             [--fit-width] [--print-empty] [--sort-column SORT_COLUMN] [--sort-ascending | --sort-descending]

List of comparatives

optional arguments:
  -h, --help            show this help message and exit

output formatters:
  output formatter options

  -f {csv,json,table,value,yaml}, --format {csv,json,table,value,yaml}
                        the output format, defaults to table
  -c COLUMN, --column COLUMN
                        specify the column(s) to include, can be repeated to show multiple columns
  --sort-column SORT_COLUMN
                        specify the column(s) to sort the data (columns specified first have a priority, non-existing columns are ignored), can be repeated
  --sort-ascending      sort the column(s) in ascending order
  --sort-descending     sort the column(s) in descending order

CSV Formatter:
  --quote {all,minimal,none,nonnumeric}
                        when to include quotes, defaults to nonnumeric

json formatter:
  --noindent            whether to disable indenting the JSON

table formatter:
  --max-width <integer>
                        Maximum display width, <1 to disable. You can also use the CLIFF_MAX_TERM_WIDTH environment variable, but the parameter takes precedence.
  --fit-width           Fit the table to the display width. Implied if --max-width greater than 0. Set the environment variable CLIFF_FIT_WIDTH=1 to always enable
  --print-empty         Print empty table if there is no data to show.
```

Print list of comparatives generated using the comparative analysis menu:

```shell
$ cosmosid comparative analyses --help
usage: cosmosid comparative analyses [-h] [-f {csv,json,table,value,yaml}] [-c COLUMN] [--quote {all,minimal,none,nonnumeric}] [--noindent]
                                     [--max-width <integer>] [--fit-width] [--print-empty] [--sort-column SORT_COLUMN] [--sort-ascending | --sort-descending]
                                     [--comparative-id COMPARATIVE_ID]

List of all comparative analyses outside comparatives (if there are no any comparative ids)

optional arguments:
  -h, --help            show this help message and exit
  --comparative-id COMPARATIVE_ID
                        Comparatives' ids

output formatters:
  output formatter options

  -f {csv,json,table,value,yaml}, --format {csv,json,table,value,yaml}
                        the output format, defaults to table
  -c COLUMN, --column COLUMN
                        specify the column(s) to include, can be repeated to show multiple columns
  --sort-column SORT_COLUMN
                        specify the column(s) to sort the data (columns specified first have a priority, non-existing columns are ignored), can be repeated
  --sort-ascending      sort the column(s) in ascending order
  --sort-descending     sort the column(s) in descending order

CSV Formatter:
  --quote {all,minimal,none,nonnumeric}
                        when to include quotes, defaults to nonnumeric

json formatter:
  --noindent            whether to disable indenting the JSON

table formatter:
  --max-width <integer>
                        Maximum display width, <1 to disable. You can also use the CLIFF_MAX_TERM_WIDTH environment variable, but the parameter takes precedence.
  --fit-width           Fit the table to the display width. Implied if --max-width greater than 0. Set the environment variable CLIFF_FIT_WIDTH=1 to always enable
  --print-empty         Print empty table if there is no data to show.
```

Example: print list of child comparatives generated under a parent comparative using metadata & cohorts menu

```shell
$ cosmosid comparative analyses --comparative-id=<comparative_id>
```

#### Export commands

Export comparative analyses without log scale

```shell
$ cosmosid comparative analyses export --help
usage: cosmosid comparative analyses export [-h] --id ID [--tax-level {kingdom,order,phylum,class,family,genus,species,strain}] [--log-scale]
                                            [--concurrent-downloads CONCURRENT_DOWNLOADS] [--dir DIR]

Download results of comparative analyses

optional arguments:
  -h, --help            show this help message and exit
  --id ID       IDs of comparative analyses
  --tax-level {kingdom,order,phylum,class,family,genus,species,strain}
                        Taxonomy
  --log-scale           Includes results with logscale
  --concurrent-downloads CONCURRENT_DOWNLOADS
                        Limit concurrent files downloads
  --dir DIR, -d DIR
                        Output directory for a file. Default: is current directory.
```

Example export comparative analyses with specified taxonomy level ('species' by default):

```shell
$ cosmosid comparative analyses export --id=<analysis_id> --tax-level=class --tax-level=genus
```