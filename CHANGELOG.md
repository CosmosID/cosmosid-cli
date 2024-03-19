# Changelog

## [2.1.11]

### Changed

* The command [workflows](README.md#workflows) shows enabled workflows
* The workflow parameter allows version specification: ex. `taxa:1.1.0`


## [2.1.9]

### Changed

* Add the ability to download 16s (ampliseq) summary comparative results.
* Added support for running Ampliseq 16s batch workflow. The command [Upload](README.md#upload-files) got mandatory Ampliseq Batch parameters: `--amplicon-preset` or `--forward-primer` with `--reverse-primer.`
* Added support for the Host Removal step for WGS samples on file upload. The command [Upload](README.md#upload-files) has the optional parameter `--host-name.`
* The command [Upload](README.md#upload-files) uses Batch Import Workflow.
* Added the possibility to download original files by file with the list of samples' IDs in command. The command [Download](README.md#download-original-samples) has parameter `--input-file`.

### Fixed

* Non-zero exit code on failures

## [2.1.8]

### Fixed

* Fixed argument `--dir` for the command `upload`

## [2.1.7]

### Changed

* The command [Comparatives](README.md#comparative-analysis) allows to view and export comparative analyses.

## [2.1.6]

### Changed

* The command [Download](README.md#download-original-samples) allows to download original samples.

### Fixed

* User bonuses balance can be used for an upload
* Indicate workflow errors during the sample import

## [2.1.5]
(skip) Technical release

## [2.1.4]

### Changed

* The command [Artifacts](README.md#retrieving-artifacts-results) shows download progress.

## [2.1.3]

### Changed

* Added new command [Artifacts](README.md#retrieving-artifacts-results) command (allows to get FastQC Zip artifacts)
* Non-functional change: Errors handling changed.
* Non-functional change: the project has been migrated to poetry.

## [2.1.2]

### Changed

1. Allowed support for python version `<4` (3.9).

## [2.1.1]

### Fixed

1. Upload to home folder
2. Wrong Api key when uploading to specific folder with `--parent` option

## [2.1.0]

### Changed

1. `folder_id` parameter default value changed to None

## [2.0.0]

### Changed

1. Workflow parameter added for file upload. See `cosmosid upload -h`
2. Mandatory `--run_id` parameter added to retrieve analysis. See `cosmosid analysis -h`
3. Redundant `--run_id` parameter removed from `cosmosid reports`.

## [1.0.9]

### Changed

1. Upgraded PyYaml dependency to 5.4

### Fixed

1. Minor: progress indicator update to 100% on task exit.

## [1.0.8]

### Changed

1. Minor: Added progress indicator for report generation

### Fixed

* The sample export got broken files (switch to v2 API).

## [1.0.7]

### Changed

1. Minor: The folder exists method optimised (don't retrieve folder content)

### Fixed

* The file list operation `cosmosid --api_key $key files --parent=$parent` limits output to 100 items.

## [1.0.6]

* only version increased (fix wrong published)

## [1.0.5]

### Changed

1. Minor: Fixed windows related issue with `pywin>=223` that allows to use Python 3.7, 3.8

## [1.0.4]

### Changed

1. Some endpoints moved to v2 in accordance with current application endpoints schema
2. Code to support new endpoints
3. Version of app moved to separate file
4. Added possibility to upload files from folder with new parameters in command
5. Fixed minor issues
