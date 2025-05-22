# PDF QUality Assessment for Digitisation batches

## What is pdfquad?

Pdfquad is a simple tool for automated quality assessment of PDF documents in digitisation batches against a user-defined technical profile. It uses [PyMuPDF](https://pymupdf.readthedocs.io/) to parse the PDF file structure and extract some relevant properties. Properties of embedded images are extracted using [Pillow](https://pillow.readthedocs.io/).

These properties are serialized to a simple XML structure, which is then evaluated against [Schematron rules](http://en.wikipedia.org/wiki/Schematron) that define the expected/required technical characteristics.

## Installation

Install the software with the [pip package manager](https://en.wikipedia.org/wiki/Pip_(package_manager)):

```
pip install pdfquad
```

Then run pdfquad once:

```
pdfquad
```

Depending on your system, pdfquad will create a folder named *pdfquad* in one of the following locations: 

- For Linux, it will use the location defined by environment variable *$XDG_CONFIG_HOME*. If this variable is not set, it will use the *.config* directory in the user's home folder (e.g. `/home/johan/.config/pdfquad`). Note that the *.config* directory is hidden by default.
- For Windows, it will use the *AppData\Local* folder (e.g. `C:\Users\johan\AppData\Local\pdfquad`).

The folder contains two subdirectories named *profiles* and *schemas*, which are explained in the "Profiles" and "Schemas" sections below.

## Command-line syntax

The general syntax of pdfquad is:

```
usage: pdfquad [-h] [--version] {process,list,copyps} ...
```

Pdfquad has three sub-commands:

|Command|Description|
|:-----|:--|
|process|Process a batch.|
|list|List available profiles and schemas.|
|copyps|Copy default profiles and schemas to user directory.|

### process command

Run pdfquad with the *process* command to process a batch. The syntax is:

```
usage: pdfquad process [-h] [--maxpdfs MAXPDFS] [--prefixout PREFIXOUT]
                       [--outdir OUTDIR] [--verbose]
                       profile batchDir
```

The *process* command expects the following positional arguments: 

|Argument|Description|
|:-----|:--|
|profile|This defines the validation profile. Note that any file paths entered here will be ignored, as Pdfquad only accepts  profiles from the profiles directory. You can just enter the file name without the path. Use the *list* command to list all available profiles.|
|batchDir|This defines the batch directory that will be analyzed.|

In addition, the following optional arguments are available:

|Argument|Description|
|:-----|:--|
|--maxpdfs, -x|This defines the maximum number of PDFs that are reported in each output XML file (default: 10).|
|--prefixout, -p|This defines a text prefix on which the names of the output files are based (default: "pq").|
|--outdir, -o|This defines the directory where output is written (default: current working directory from which pdfquad is launched).|
|--verbose, -b|This tells pdfquad to report Schematron output in verbose format.|

In the simplest case, we can call pdfquad with the profile and the batch directory as the only arguments:

```
pdfquad process dbnl-fulltext.xml ./mybatch
```

Pdfquad will now recursively traverse all directories and files inside the "mybatch" directory, and analyse all PDF files (based on a file extension match).

### list command

Run pdfquad with the *list* command to get a list of the available profiles and schemas, as well as their locations. For example:

```
pdfquad list
```

Results in:

```
Available profiles (directory /home/johan/.config/pdfquad/profiles):
  - dbnl-fulltext.xml
Available schemas (directory /home/johan/.config/pdfquad/schemas):
  - pdf-dbnl-85.sch
  - pdf-dbnl-50.sch
```

### copyps command

If you run pdfquad with the *copyps* command, it will copy the default profiles and schemas that are included in the installation over to your user directory.

**Warning:** any changes you made to the default profiles or schemas will be lost after this operation, so proceed with caution! If you want to keep any of these files, just make a copy and save them under a different name before running the *copyps* command.

## Profiles

A profile is an XML file that defines how a digitisation batch is evaluated. It is made up of one or more *schema* elements, that each link a file or directory naming pattern to a Schematron file. Here's an example:

```xml
<?xml version="1.0"?>

<profile>

<schema type="parentDirName" match="endswith" pattern="pi-85">pdf-dbnl-85.sch</schema>
<schema type="parentDirName" match="endswith" pattern="pi-50">pdf-dbnl-50.sch</schema>

</profile>
```

Here we see two *schema* elements. Each element refers to a Schematron file (explained in the next section). The values of the *type*, *match* and *pattern* attributes define how this file is linked to file or directory names inside the batch:

- If **type** is "fileName", the matching is based on the naming of a PDF. In case of "parentDirName" the matching uses the naming of the direct parent directory of a PDF.
- The **match** attribute defines whether the matching pattern with the file or directory name is exact ("is") or partial ("startswith", "endswith", "contains".)
- The **pattern** attribute defines a text string that is used for the match.

In the example above, the profile says that if a PDF has a direct parent directory whose name ends with "pi-85", pdfquad should use Schematron file "pdf-dbnl-85.sch". If the directory name ends with "pi-50", it should use "pdf-dbnl-50.sch".

### Available profiles

Currently the following profiles are included:

|Profile|Description|
|:--|:--|
|dbnl-fulltext.xml|Profile for DBNL full-text digitisation batches.|
|kbr.xml|Profile for KBR digitisation batches.|

## Schemas

Schemas contain the Schematron rules on which the quality assessment is based. Some background information about this type of rule-based validation can be found in [this blog post](https://www.bitsgalore.org/2012/09/04/automated-assessment-jp2-against-technical-profile). Currently the following schemas are included:

### pdf-dbnl-85.sch

This is a schema for production master PDFs with images in JPEG format that are compressed at 85% quality. It includes the following checks:

|Check|Value|
|:---|:---|
|Thumbnails|Document does not open with thumbnails|
|File attachments|Document does not contain file attachments|
|Digital signatures|Document does not contain digital signatures|
|JavaScript|Document does not contain JavaScript|
|Open password|Document is not protected with open password|
|Exceptions, PDF|Parsing at PDF level did not result in any exceptions|
|PDF version|1.7|
|Encryption|Document does not use encryption|
|Annotations|Document does not contain WaterMark, Screen, Movie, 3D, Sound, FileAttachment, Link, Ink, Popup, Widget, Polygon, Text, FreeText or SVG annotations|
|Optional Content|Document does not contain any optional content layers|
|Images per page|Each page contains exactly 1 image|
|Watermarks|Document does not contain watermarks|
|ICC profile|Each image contains an ICC profile, which is either defined as a PDF object, or embedded in the image stream|
|Width, height|Image XObject dictionary values and image stream values are identical|
|Bits per component|Image XObject dictionary values and image stream values are identical|
|Filter value of Image XObject dictionary|DCTDecode|
|Image stream format|JPEG|
|Image stream resolution (ppi)|Within range \[299, 301\]|
|Image stream color components|3|
|Image stream JPEG Quality|Within range \[83, 87\]|
|Exceptions, stream|Parsing of the image streams did not result in any exceptions|

### pdf-dbnl-50.sch

This is a schema for small access PDFs with images in JPEG format that are compressed at 50% quality. It includes the following checks:

|Check|Value|
|:---|:---|
|Thumbnails|Document does not open with thumbnails|
|File attachments|Document does not contain file attachments|
|Digital signatures|Document does not contain digital signatures|
|JavaScript|Document does not contain JavaScript|
|Open password|Document is not protected with open password|
|Exceptions, PDF|Parsing at PDF level did not result in any exceptions|
|PDF version|1.7|
|Encryption|Document does not use encryption|
|Annotations|Document does not contain WaterMark, Screen, Movie, 3D, Sound, FileAttachment, Link, Ink, Popup, Widget, Polygon, Text, FreeText or SVG annotations|
|Optional Content|Document does not contain any optional content groups|
|Images per page|Each page contains exactly 1 image|
|Watermarks|Document does not contain watermarks|
|ICC profile|Each image contains an ICC profile, which is either defined as a PDF object, or embedded in the image stream|
|Width, height|Image XObject dictionary values and image stream values are identical|
|Bits per component|Image XObject dictionary values and image stream values are identical|
|Filter value of Image XObject dictionary|DCTDecode|
|Image stream format|JPEG|
|Image stream resolution (ppi)|Within range \[299, 301\]|
|Image stream color components|3|
|Image stream JPEG Quality|Within range \[48, 52\]|
|Exceptions, stream|Parsing of the image streams did not result in any exceptions|

### pdf-kbr-85.sch

As pdf-dbnl-85.sch, but without checks on ICC profile and filter value of image dictionary.

### pdf-kbr-50.sch

As pdf-dbnl-50.sch, but without checks on ICC profile and filter value of image dictionary.

## Output

Pdfquad reports the following output:

### Comprehensive output file (XML)

Pdfquad generates one or more comprehensive output files in XML format. For each PDF, these contain all extracted properties, as well a the Schematron report and the assessment status. [Here's an example file](./examples/pq_batchtest_001.xml).

Since these files can get really large, Pdfquad splits the results across multiple output files, using the following naming convention:

- pq_mybatch_001.xml
- pq_mybatch_002.xml
- etcetera

By default Pdfquad limits the number of reported PDFs for each output file to 10, after which it creates a new file. This behaviour can be changed by using the *--maxpdfs* (alias *-x*) option. For example, the command below will limit the number of PDFs per output file to 1 (so each PDF will have its dedicated output file):

```
pdfquad process dbnl-fulltext.xml ./mybatch -x 1
```

### Summary file (CSV)

This is a comma-delimited text file with, for each PDF, the following columns:

|Column|Description|
|:-----|:--|
|file|Full path to the PDF file.|
|validationSuccess|Flag with value *True* if Schematron validation was succesful, and *False* if not. A value *False* indicates that the file could not be validated (e.g. because no matching schema was found, or the validation resulted in an unexpected exception)|
|validationOutcome|The outcome of the Schematron validation/assessment. Value is *Pass* if file passed all tests, and *Fail* otherwise. Note that it is automatically set to *Fail* if the Schematron validation was unsuccessful (i.e. "validationSuccess" is *False*)|
|noPages|The number of pages in the document.|
|fileOut|Corresponding comprehensive output file with full output for this PDF.|

Here's an example:

``` csv
file,validationSuccess,validationOutcome,noPages,fileOut
/home/johan/pdfquad-test/mybatch/20241106/anbe001lexi02/300dpi-85/anbe001lexi02_01.pdf,True,Pass,1528,/home/johan/pdfquad-test/pq_mybatch_001.xml
/home/johan/pdfquad-test/mybatch/20241106/anbe001lexi02/300dpi-50/anbe001lexi02_01.pdf,True,Fail,1528,/home/johan/pdfquad-test/pq_mybatch_001.xml
/home/johan/pdfquad-test/mybatch/20241106/brin003196603/300dpi-85/brin003196603_01.pdf,True,Fail,1260,/home/johan/pdfquad-test/pq_mybatch_001.xml
/home/johan/pdfquad-test/mybatch/20241106/brin003196603/300dpi-50/brin003196603_01.pdf,True,Fail,1260,/home/johan/pdfquad-test/pq_mybatch_001.xml
/home/johan/pdfquad-test/mybatch/20241105/_deu002201201/300dpi-85/_deu002201201_01.pdf,True,Fail,297,/home/johan/pdfquad-test/pq_mybatch_001.xml
/home/johan/pdfquad-test/mybatch/20241105/_deu002201201/300dpi-50/_deu002201201_01.pdf,True,Fail,297,/home/johan/pdfquad-test/pq_mybatch_001.xml
/home/johan/pdfquad-test/mybatch/20241105/_boe012192401/300dpi-85/_boe012192401_01.pdf,True,Pass,346,/home/johan/pdfquad-test/pq_mybatch_001.xml
/home/johan/pdfquad-test/mybatch/20241105/_boe012192401/300dpi-50/_boe012192401_01.pdf,True,Fail,346,/home/johan/pdfquad-test/pq_mybatch_001.xml
```

## Licensing

Pdfquad is released under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0).

## Useful links

- [Schematron](http://en.wikipedia.org/wiki/Schematron)


