# Jprofile


## What is *jprofile*?

*Jprofile* is a simple tool for automated profiling of large batches of *JP2* (JPEG 2000 part 1) images. Internally it wraps around [*jpylyzer*](http://jpylyzer.openpreservation.org/), which is used for validating each image and for extracting its properties. The *jpylyzer* output is then validated against a set of [*Schematron*](http://en.wikipedia.org/wiki/Schematron) schemas that contain the required characteristics for master, access and target images, respectively.


## Installation

The easiest method to install *Jprofile* is to use the [*pip* package manager](https://en.wikipedia.org/wiki/Pip_(package_manager)). <strike>Alternatively, Windows users can also use stand-alone binaries that don't require Python at all (see below).</strike> Windows binaries are discontinued from jprofile 0.9.0 onward, use pip installation instead!

## Installation with pip (single user)

This will work on any platform for which Python is available. You need a recent version of *pip* (version 9.0 or more recent). To install *Jprofile* for a single user, use the following command:

    pip install jprofile --user

## Installation with pip (all users)

To install *Jprofile* for *all* users, use the following command:

    pip install jprofile

You need local admin (Windows) / superuser (Linux) privilige to do this. On Windows, you can do this by running the above command in a Command Prompt window that was opened as Administrator. On Linux, use this:

    sudo pip install jprofile



## Command-line syntax

```
usage: jprofile batchDir prefixOut -p PROFILE
```

## Positional arguments

**batchDir**: root directory of batch

**prefixOut**: prefix that is used for writing output files

**PROFILE**: name of profile that defines schemas for master, access and target images

To list all available profiles, use a value of *l* or *list* for *PROFILE*.


## Batch structure

*Jprofile* was designed for processing digitisation batches that are delivered to the KB by external suppliers. These batches typically contain (losslessly compressed) *master* JP2s, (lossily compressed) *access* JP2s and (sometimes) also *technical target* JP2s. These are located in a folder structure that contains (sub) directories named *master*, *access* and *targets-jp2*, respectively. Below is an example:

	./testbatch
	├── access
	│   ├── IMAGE000060.jp2
	│   ├── IMAGE000061.jp2
	│   ├── IMAGE000062.jp2
	│   ├── ::
	│   ├── IMAGE000080.jp2
	│   └── IMAGE000081.jp2
	├── master
	│   ├── IMAGE000060.jp2
	│   ├── IMAGE000061.jp2
	│   ├── IMAGE000062.jp2
	│   ├── ::
	│   ├── IMAGE000080.jp2
	│   └── IMAGE000081.jp2
	└── targets-jp2


As long as a batch follows this basic structure, *Jprofile* can handle it. Note that:

* *master*, *access* and *targets-jp2* directories may occur at different nesting levels. This is no problem, since *jprofile* recursively traverses all subdirectories in a batch.

* if either a *master*, *access* or *targets-jp2* directory is missing, *jprofile* will simply ignore it (i.e. it's perfectly OK if your batch only contains *master* images).

* Batches may contain other folders. These are ignored by *jprofile*.

## Profiles

A *profile* is an *XML*-formatted file that simply defines which schemas are used to validate *jpylyzer*'s output for master, access and target images, respectively. Here's an example:

    <profile>
    
    <!-- Sample profile -->
       
    <schemaMaster>master300Gray_2014.sch</schemaMaster>
    <schemaAccess>access300Colour_2014.sch</schemaAccess>
    <schemaTarget>master300Colour_2014.sch</schemaTarget>
    
    </profile>

Note that each entry only contains the *name* of a profile, not its full path! All profiles are located in the *profiles* directory in the installation folder.

## Available profiles

The following profiles are included by default:

| Name|Description|
| :------| :-----|
|kb_generic_2014.xml|Generic profile for KB digitisation streams (doesn't include any checks on resolution or colour spaces!)|
|kb_300Colour_2014.xml|As generic profile, but with additional requirements on resolution (must be equal to 300 ppi) and colour space (must be Adobe RGB 1998)|
|kb_300Gray_2014.xml|As generic profile, but with additional requirements on resolution (must be equal to 300 ppi) and colour space (must be Gray Gamma 2.2)|
|kb_600Colour_2014.xml|As generic profile, but with additional requirements on resolution (must be equal to 600 ppi) and colour space (must be Adobe RGB 1998)|
|kb_600Gray_2014.xml|As generic profile, but with additional requirements on resolution (must be equal to 600 ppi) and colour space (must be Gray Gamma 2.2)|

It is possible to create custom-made profiles. Just add them to the *profiles* directory in the installation folder.

## Schemas

The quality assessment is based on a number of rules/tests that are defined a set of *Schematron* schemas. These are located in the *schemas* folder in the installation directory. In principle *any* property that is reported by *jpylyzer* can be used here, and new tests can be added by editing the schemas. More details on this can be found in [this blog post](https://www.bitsgalore.org/2012/09/04/automated-assessment-jp2-against-technical-profile).
 
## Available schemas

| Name|Description|
|:------| :-----|
|kbMaster_2014.sch|Generic schema for losslessly-compressed master images according to 2014 specifications|
|master600Colour_2014.sch|Schema for losslessly-compressed master images, 600 ppi, Adobe RGB (1998) colour space|
|master600Gray_2014.sch|Schema for losslessly-compressed master images, 600 ppi, Gray Gamma 2.2 colour space|
|master300Colour_2014.sch|Schema for losslessly-compressed master images, 300 ppi, Adobe RGB (1998) colour space|
|master300Gray_2014.sch|Schema for losslessly-compressed master images, 300 ppi, Gray Gamma 2.2 colour space|
|kbAccess_2014.sch|Generic schema for lossily-compressed access images according to 2014 specifications|
|access600Colour_2014.sch|Schema for lossily-compressed access images, 600 ppi, Adobe RGB (1998) colour space|
|access600Gray_2014.sch|Schema for lossily-compressed access images, 600 ppi, Gray Gamma 2.2 colour space|
|access300Colour_2014.sch|Schema for lossily-compressed access images, 300 ppi, Adobe RGB (1998) colour space|
|access300Gray_2014.sch|Schema for lossily-compressed access images, 300 ppi, Gray Gamma 2.2 colour space|

It is possible to create custom-made schemas. Just add them to the *schemas* directory in the installation folder.

## Overview of 2014 schemas

The following tables give a general overview of the technical profiles that the generic master- and access schemas are representing:

### Master

|Parameter|Value|
|:---|:---|
|File format|JP2 (JPEG 2000 Part 1)|
|Compression type|Reversible 5-3 wavelet filter|
|Colour transform|Yes (only for colour images)|
|Number of decomposition levels|5|
|Progression order |RPCL|
|Tile size |1024 x 1024|
|Code block size|64 x 64 (2<sup>6</sup> x 2<sup>6</sup>)|
|Precinct size	|256 x 256 (2<sup>8</sup>) for 2 highest resolution levels; 128 x 128 (2<sup>7</sup>) for remaining resolution levels|
|Number of quality layers|11|
|Target compression ratio layers|2560:1 [1] ; 1280:1 [2] ;  640:1 [3] ; 320:1 [4] ; 160:1 [5] ; 80:1 [6] ; 40:1 [7] ; 20:1 [8] ; 10:1 [9] ; 5:1 [10] ; - [11]|
|Error resilience|Start-of-packet headers; end-of-packet headers; segmentation symbols|
|Sampling rate|Stored in "Capture Resolution" fields|
|Capture metadata|Embedded as XMP metadata in XML box|


### Access

|Parameter|Value|
|:---|:---|
|File format|JP2 (JPEG 2000 Part 1)|
|Compression type|Irreversible 7-9 wavelet filter|
|Colour transform|Yes (only for colour images)|
|Number of decomposition levels|5|
|Progression order |RPCL|
|Tile size |1024 x 1024|
|Code block size|64 x 64 (2<sup>6</sup> x 2<sup>6</sup>)|
|Precinct size	|256 x 256 (2<sup>8</sup>) for 2 highest resolution levels; 128 x 128 (2<sup>7</sup>) for remaining resolution levels|
|Number of quality layers|8|
|Target compression ratio layers|2560:1 [1] ; 1280:1 [2] ;  640:1 [3] ; 320:1 [4] ; 160:1 [5] ; 80:1 [6] ; 40:1 [7] ; 20:1 [8]|
|Error resilience|	Start-of-packet headers; end-of-packet headers; segmentation symbols|
|Sampling rate|Stored in "Capture Resolution" fields|
|Capture metadata|Embedded as XMP metadata in XML box|

Note that jpylyzer is unable to establish the compression ratio of individual layers, so the access schema only checks for the overall compression ratio (i.e. 20:1). The more specific schemas (300Colour, 600Gray, etc.) contain additional checks for resolution values, the number of colour components and embedded ICC profiles.

## Usage examples

### List available profiles

    jprofile d:\myBatch mybatch -p list

This results in a list of all available profiles (these are stored in the installation folder's *profiles* directory):

    Available profiles:

    kb_600Gray_2014.xml
    kb_300Gray_2014.xml
    kb_300Colour_2014.xml
    kb_600Colour_2014.xml
    kb_generic_2014.xml


### Analyse batch

    jprofile d:\myBatch mybatch -p kb_300Colour_2014.xml

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

## Known limitations

- Images that have names containing square brackets ("[" and "]" are ignored (limitation of *Python*'s *glob* module, will be solved in the future).

## Licensing

*Jprofile* is released under the [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html).

## Useful links

- [*jpylyzer*](http://jpylyzer.openpreservation.org/)
- [*Schematron*](http://en.wikipedia.org/wiki/Schematron)
- [Automated assesment of JP2 against a technical profile using jpylyzer and Schematron](http://openpreservation.org/blog/2012/09/04/automated-assessment-jp2-against-technical-profile/)


