# Pdfbatchqa

## What is *pdfbatchqa*?

*Pdfbatchqa* is a simple tool for automated checking of digitisation batches of *PDF* files against a user-defined technical profile. Internally it wraps around the *pdfimages* tool from the [*Poppler*](https://en.wikipedia.org/wiki/Poppler_(software)) library, which is used to extract the image-related properties for each PDF. The *pdfimages* output is then validated against a set of [*Schematron*](http://en.wikipedia.org/wiki/Schematron) schemas that define the required technical characteristics.


## Installation

The easiest method to install *pdfbatchqa* is to use the [*pip* package manager](https://en.wikipedia.org/wiki/Pip_(package_manager)).


## Installation with pip (single user)

This will work on any platform for which Python is available. You need a recent version of *pip* (version 9.0 or more recent). To install *pdfbatchqa* for a single user, use the following command:

```
pip install pdfbatchqa --user
```

## Installation with pip (all users)

To install *pdfbatchqa* for *all* users, use the following command:

```
pip install jprofile
```

You need local admin (Windows) / superuser (Linux) privilige to do this. On Windows, you can do this by running the above command in a Command Prompt window that was opened as Administrator. On Linux, use this:

```
sudo pip install jprofile
```

## Command-line syntax

```
usage: pdfbatchqa batchDir prefixOut -p PROFILE
```

## Positional arguments

**batchDir**: root directory of batch

**prefixOut**: prefix that is used for writing output files

**PROFILE**: name of profile that defines the validation schemas

To list all available profiles, use a value of *l* or *list* for *PROFILE*.


## Batch structure

*Pdfbatchqa* was designed for processing digitisation batches that are delivered to the KB by external suppliers as part of the DBNL stream. For each digitised publication, these batches typically contain two PDF files:

1. A high quality PDF with images in JPEG format that are enoded at 85% JPEG quality
2. A lower quality PDF with images in JPEG format that are enoded at 50% JPEG quality

TODO: describe how we can distinguish between 1. and 2. (folder name, file name?).

## Profiles

A *profile* is an *XML*-formatted file that simply defines which schemas are used to validate the extracted properties of the high and low quality PDFs, respectively. Here's an example:

``` xml
<?xml version="1.0"?>

<profile>

<!-- Profile for DBNL full-text digitisation batches -->

<schemaLowQuality>pdf-dbnl-generic.sch</schemaLowQuality>
<schemaHighQuality>pdf-dbnl-generic.sch</schemaHighQuality>

</profile>
```

Note that each entry only contains the *name* of a schema, not its full path! All schemas are located in the *schemass* directory in the installation folder.

Also note that in the above example, the same schema is used for both low and high quality PDFs!

## Available profiles

The following profiles are included by default:

| Name|Description|
| :------| :-----|
|dbnl-fulltext.xml|Profile for DBNL full-text digitisation batches|

It is possible to create custom-made profiles. Just add them to the *profiles* directory in the installation folder.

## Schemas

The quality assessment is based on a number of rules/tests that are defined a set of *Schematron* schemas. These are located in the *schemas* folder in the installation directory. In principle *any* property that is reported by *pdfimages* can be used here, and new tests can be added by editing the schemas.
 
## Available schemas

| Name|Description|
|:------| :-----|
|pdf-dbnl-generic.sch|Generic schema for DBNL full-text digitisation batches|

It is possible to create custom-made schemas. Just add them to the *schemas* directory in the installation folder.

## Overview schemas

The following tables give a general overview of the technical profiles that the current schemas are representing:

### pdf-dbnl-generic

|Parameter|Value|
|:---|:---|
|Image format|JPEG|
|Image resolution|(295, 305)|
|Number of color components|3|

## Usage examples

### List available profiles

```
pdfbatchqa d:\myBatch mybatch -p list
```

This results in a list of all available profiles (these are stored in the installation folder's *profiles* directory):

```
Available profiles:

dbnl-fulltext.xml
```

### Analyse batch

```
pdfbatchqa -p dbnl-fulltext.xml d:\myBatch mybatch
```

TODO: update remaining documentation.

<!--
This will result in the creation of 2 output files:

- `mybatch_status.csv` (status output file)
- `mybatch_failed.txt` (detailed output on images that failed quality asessment)

## Status output file

This is a comma-separated file with the assessment status of each analysed image. The assessment status is either *pass* (passed all tests) or *fail* (failed one or more tests). Here's an example:

    F:\test\access\MMKB03_000004896_00015_access.jp2,pass
    F:\test\access\MMKB03_000004896_00115_access.jp2,pass
    F:\test\access\MMKB03_000004896_00215_access.jp2,pass
    F:\test\targets-jp2\MMKB03_MTF_RGB_20120626_02_01.jp2,fail
    F:\test\master\MMKB03_000004896_00015_master.jp2,pass

## Failure output file

Any image that failed one or more tests are reported in the failure output file. For each failed image, it contains a full reference to the file path, followed by the specific errors. An example:

    F:\test\targets-jp2\MMKB03_MTF_RGB_20120626_02_01.jp2
    *** Schema validation errors:
    Test "layers = '11'" failed (wrong number of layers)
    Test "transformation = '5-3 reversible'" failed (wrong transformation)
    Test "comment = 'KB_MASTER_LOSSLESS_01/01/2015'" failed (wrong codestream comment string)
    ####

Entries in this file are separated by a sequence of 4 '#' characters. Note that each line here corresponds to a failed test in the schema. For images that are identified as not-valid JP2 some additional information from *jpylyzer*'s output is included as well. For example:


    F:\test\master\MMUBL07_MTF_GRAY_20121213_01_05.jp2
    *** Schema validation errors:
    Test "isValidJP2 = 'True'" failed (no valid JP2)
    *** Jpylyzer JP2 validation errors:
    Test methIsValid failed
    Test precIsValid failed
    Test approxIsValid failed
    Test foundNextTilePartOrEOC failed
    Test foundEOCMarker failed
    ####


Here, the outcome of test *isValidJP2* means that the image does not conform to the *JP2* specification. The lines following 'Jpylyzer JP2 validation errors' lists the specific errors that were reported by *jpylyzer*. The meaning of these errors can be found in the [*jpylyzer* User Manual](http://jpylyzer.openpreservation.org//userManual.html).

## Preconditions

- All images that are to be analysed have a .jp2 extension (all others are ignored!)
- *Master* images are located in a (subdirectory of a) directory called '*master*'
- *Access* images are located in a (subdirectory of a) directory called '*access*'
- *Target* images are located in a (subdirectory of a) directory called '*targets-jp2*'.
- Either of the above directories may be missing.

Other than that, the organisation of images may follow any arbitrary directory structure (*jprofile* does a recursive scan of whole directory tree of a batch).

-->

## Known limitations

- PDFs that have names containing square brackets ("[" and "]" are ignored (limitation of *Python*'s *glob* module, will be solved in the future).

## Licensing

*Pdfbatchqa* is released under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Useful links

- [Poppler](https://poppler.freedesktop.org/)
- [Schematron](http://en.wikipedia.org/wiki/Schematron)


