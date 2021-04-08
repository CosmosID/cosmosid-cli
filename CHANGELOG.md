# Changelog

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