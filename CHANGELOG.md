# Changelog

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