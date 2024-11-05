#! /usr/bin/env python3

"""PDF Automated Quality Assessment Tool for KB digitisation projects

Johan van der Knijff

Requires Python 3.2 or more recent

Preconditions:

- Files that are to be analysed have a .pdf extension (all others ignored!)
- Parent directory of pdf files is called ???

Copyright 2024, KB/National Library of the Netherlands

"""

import sys
import os
import shutil
import io
import time
import argparse
import csv
from lxml import isoschematron
from lxml import etree
import pymupdf
from PIL import Image
from PIL import ImageCms
from . import jpegquality
from . import config

__version__ = "0.1.0"


def errorExit(msg):
    """Write error to stderr and exit"""
    msgString = "ERROR: {}\n".format(msg)
    sys.stderr.write(msgString)
    sys.exit()


def checkFileExists(fileIn):
    """Check if file exists and exit if not"""
    if not os.path.isfile(fileIn):
        msg = "{} does not exist".format(fileIn)
        errorExit(msg)


def checkDirExists(pathIn):
    """Check if directory exists and exit if not"""
    if not os.path.isdir(pathIn):
        msg = "{} does not exist".format(pathIn) 
        errorExit(msg)


def openFileForAppend(wFile):
    """Opens file for writing in append + binary mode"""
    try:
        f = open(wFile, "a", encoding="utf-8")
        return f

    except Exception:
        msg = "{} could not be written".format(wFile) 
        errorExit(msg)


def removeFile(fileIn):
    """Remove a file"""
    try:
        if os.path.isfile(fileIn):
            os.remove(fileIn)
    except Exception:
        msg = "Could not remove {}".format(fileIn)
        errorExit(msg)


def constructFileName(fileIn, extOut, suffixOut):
    """Construct filename by replacing path by pathOut,
    adding suffix and extension
    """

    fileInTail = os.path.split(fileIn)[1]
    baseNameIn = os.path.splitext(fileInTail)[0]
    baseNameOut = baseNameIn + suffixOut + "." + extOut
    fileOut = baseNameOut
    return fileOut


def parseCommandLine():
    """Parse command line"""

    # Create parser
    ## TODO: add config file location for Windows
    parser = argparse.ArgumentParser(description="Automated PDF Quality Assessment digitisation batches")

    parser.add_argument('profile',
                        action="store",
                        help='validation profile file')
    parser.add_argument('batchDir',
                        action="store",
                        help="batch directory")
    parser.add_argument('--prefixout',
                        action="store",
                        default='bqa',
                        help="prefix of output files")
    parser.add_argument('--verbose',
                        action="store_true",
                        default=False,
                        help="report Schematron report in verbose format")
    parser.add_argument('--version', '-v',
                        action="version",
                        version=__version__)

    # Parse arguments
    args = parser.parse_args()

    # Normalise all file paths
    args.batchDir = os.path.normpath(args.batchDir)

    return args


def listProfiles(profilesDir):
    """List all available profiles"""
    profileNames = os.listdir(profilesDir)
    print("\nAvailable profiles:\n")
    for profileName in profileNames:
        print(profileName)
    sys.exit()


def readProfile(profile, schemasDir):
    """Read a profile and returns list with for each schema
    element the corresponding type, matching method, matching
    pattern and schematronj file"""

    # Parse XML tree
    try:
        tree = etree.parse(profile)
        prof = tree.getroot()
    except Exception:
        msg = "error parsing {}".format(profile)
        errorExit(msg)

    # Output list
    listOut = []

    # Locate schema elements
    schemas = prof.findall("schema")

    for schema in schemas:
        try:
            mType = schema.attrib["type"]
            if mType not in ["fileName", "parentDirName"]:
                msg = "'{}' is not a valid 'type' value".format(mType)
                errorExit(msg)
        except KeyError:
            msg = "missing 'type' attribute in profile {}".format(profile)
            errorExit(msg)
        try:
            mMatch = schema.attrib["match"]
            if mMatch not in ["is", "startswith", "endswith"]:
                msg = "'{}' is not a valid 'match' value".format(mMatch)
                errorExit(msg)
        except KeyError:
            msg = "missing 'match' attribute in profile {}".format(profile)
            errorExit(msg)
        try:
            mPattern = schema.attrib["pattern"]
        except KeyError:
            msg = "missing 'pattern' attribute in profile {}".format(profile)
            errorExit(msg)

        schematronFile = os.path.join(schemasDir, schema.text)
        checkFileExists(schematronFile)

        listOut.append([mType, mMatch, mPattern, schematronFile])

    return listOut


def readAsLXMLElt(xmlFile):
    """Parse XML file with lxml and return result as element object
    (not the same as Elementtree object!)
    """

    f = open(xmlFile, 'r', encoding="utf-8")
    # Note we're using lxml.etree here rather than elementtree
    resultAsLXMLElt = etree.parse(f)
    f.close()

    return resultAsLXMLElt


def getFilesFromTree(rootDir, extensionString):
    """Walk down whole directory tree (including all subdirectories) and
    return list of those files whose extension contains user defined string
    NOTE: directory names are disabled here!!
    implementation is case insensitive (all search items converted to
    upper case internally!
    """

    extensionString = extensionString.upper()

    filesList = []

    for dirname, dirnames, filenames in os.walk(rootDir):
        # Suppress directory names
        for subdirname in dirnames:
            thisDirectory = os.path.join(dirname, subdirname)

        for filename in filenames:
            thisFile = os.path.join(dirname, filename)
            thisExtension = os.path.splitext(thisFile)[1]
            thisExtension = thisExtension.upper()
            if extensionString.strip() == '*' or extensionString in thisExtension:
                filesList.append(thisFile)
    return filesList


def getPathComponentsAsList(path):
    """Returns a list that contains all path components (dir names) in path
    Adapted from:
    http://stackoverflow.com/questions/3167154/how-to-split-a-dos-path-into-its-components-in-python
    """

    drive, path_and_file = os.path.splitdrive(path)
    pathComponent, fileComponent = os.path.split(path_and_file)

    folders = []
    while 1:
        pathComponent, folder = os.path.split(pathComponent)

        if folder != "":
            folders.append(folder)
        else:
            if pathComponent != "":
                folders.append(pathComponent)

            break

    folders.reverse()
    return(folders, fileComponent)


def summariseSchematron(report):
    """Return summarized version of Schematron report with only output of
    failed tests"""

    for elem in report.iter():
        if elem.tag == "{http://purl.oclc.org/dsdl/svrl}fired-rule":
            elem.getparent().remove(elem)

    return report


def dictionaryToElt(name, dictionary):
    """Create Element object from dictionary"""
    elt = etree.Element(name)
    for key, value in dictionary.items():
        child = etree.Element(key)
        child.text = str(value)
        elt.append(child)
    return elt


def getBPC(image):
    """Return Bits per Component as a function of mode and components values"""
    mode_to_bpp = {"1": 1,
                   "L": 8,
                   "P": 8,
                   "RGB": 24,
                   "RGBA": 32,
                   "CMYK": 32,
                   "YCbCr": 24,
                   "LAB": 24,
                   "HSV": 24,
                   "I": 32,
                   "F": 32}

    bitsPerPixel = mode_to_bpp[image.mode]
    noComponents = len(image.getbands())

    if noComponents != 0  and isinstance(bitsPerPixel, int):
        bpc = int(bitsPerPixel/noComponents)
    else:
        bpc = -9999

    return bpc


def processPDF(PDF, verboseFlag, schemas):
    """Process one PDF"""

    # Create output element for this PDF
    pdfElt = etree.Element("file")

    # Create list that contains all file path components (dir names)
    pathComponents, fName = getPathComponentsAsList(PDF)
    # Direct parent dir name
    parentDir = pathComponents[-1]

    # Flag that indicates whether PDF matches with a schema
    schemaMatch = False

    # Select schema based on directory or file name pattern defined in profile
    for schema in schemas:
        mType = schema[0]
        mMatch = schema[1]
        mPattern = schema[2]
        mSchema = schema[3]
        if mType == "parentDirName" and mMatch == "is":
            if parentDir == mPattern:
                mySchema = mSchema
                schemaMatch = True
        elif mType == "parentDirName" and mMatch == "startswith":
            if parentDir.startswith(mPattern):
                mySchema = mSchema
                schemaMatch = True
        elif mType == "parentDirName" and mMatch == "endswith":
            if parentDir.endswith(mPattern):
                mySchema = mSchema
                schemaMatch = True
        if mType == "fileName" and mMatch == "is":
            if fName == mPattern:
                mySchema = mSchema
                schemaMatch = True
        elif mType == "fileName" and mMatch == "startswith":
            if fName.startswith(mPattern):
                mySchema = mSchema
                schemaMatch = True
        elif mType == "fileName" and mMatch == "endswith":
            if fName.endswith(mPattern):
                mySchema = mSchema
                schemaMatch = True

    if not schemaMatch:
        # TODO: should we quietly ignore this, or report it somewhere?
        # TODO: use logging for this instead!
        pass


    if schemaMatch:
        # Get schema as lxml.etree element
        mySchemaElt = readAsLXMLElt(mySchema)
    
        # Create and fill descriptive elements
        fPathElt = etree.Element("filePath")
        fPathElt.text = PDF
        fSizeElt = etree.Element("fileSize")
        fSizeElt.text = str(os.path.getsize(PDF))

        # Create elements to store properties and Schematron report
        propertiesElt = etree.Element("properties")
        reportElt = etree.Element("schematronReport")

        # Parse PDF
        doc = pymupdf.open(PDF)

        # Page count
        pages = doc.page_count
        # Document metadata
        metadata = doc.metadata
        metadataElt = dictionaryToElt('meta', metadata)

        # Read pageMode from document catalog (if it exists)
        # pageMode is needed for the thumbnail check
        catXref = doc.pdf_catalog()
        pageMode = doc.xref_get_key(catXref, "PageMode")
        pageModeElt = etree.Element("PageMode")
        if pageMode[0] == 'null':
            pageModeElt.text = "undefined"
        else:
            pageModeElt.text = pageMode[1]

        # Check for digital signatures
        signatureFlag = doc.get_sigflags()
        signatureFlagElt = etree.Element("signatureFlag")
        signatureFlagElt.text = str(signatureFlag)

        # Wrapper element for pages output
        pagesElt = etree.Element("pages")

        for page in doc:
            pageElt = etree.Element("page")
            images = page.get_images(full=False)
            for image in images:
                imageElt = etree.Element("image")
                # Store PDF object level properties to dictionary
                propsPDF = {}
                propsPDF['xref'] = image[0]
                #propsPDF['smask'] = image[1]
                propsPDF['width'] = image[2]
                propsPDF['height'] = image[3]
                propsPDF['bpc'] = image[4]
                propsPDF['colorspace'] = image[5]
                propsPDF['altcolorspace'] = image[6]
                #propsPDF['name'] = image[7]
                propsPDF['filter'] = image[8]

                # Read raw image stream data from xref id
                xref = propsPDF['xref']
                stream = doc.xref_stream_raw(xref)
                im = Image.open(io.BytesIO(stream))
                im.load()
                propsStream = {}
                propsStream['format'] = im.format
                width = im.size[0]
                height = im.size[1]
                propsStream['width'] = width
                propsStream['height'] = height
                propsStream['mode'] = im.mode
                noComponents = len(im.getbands())
                propsStream['components']= noComponents
                bitsPerComponent = getBPC(im)
                propsStream['bpc'] = bitsPerComponent

                try:
                    # Estimate JPEG quality using least squares matching against
                    # standard quantization tables
                    quality, rmsError, nse = jpegquality.computeJPEGQuality(im)
                    propsStream['JPEGQuality'] = quality
                    propsStream['NSE_JPEGQuality'] = nse
                except Exception:
                    pass

                for key, value in im.info.items():
                    if isinstance(value, bytes):
                        propsStream[key] = 'bytes'
                    elif key == 'dpi' and isinstance(value, tuple):
                        propsStream['ppi_x'] = value[0]
                        propsStream['ppi_y'] = value[1]
                    elif key == 'jfif_density' and isinstance(value, tuple):
                        propsStream['jfif_density_x'] = value[0]
                        propsStream['jfif_density_y'] = value[1]
                    elif isinstance(value, tuple):
                        # Skip any other properties that return tuples
                        pass
                    else:
                        propsStream[key] = value

                try:
                    # ICC profile name and description
                    icc = im.info['icc_profile']
                    iccProfile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
                    propsStream['icc_profile_name'] = ImageCms.getProfileName(iccProfile).strip()
                    propsStream['icc_profile_description'] = ImageCms.getProfileDescription(iccProfile).strip()
                except KeyError:
                    pass
                
                # Dictionaries to element objects
                propsPDFElt = dictionaryToElt('pdf', propsPDF)
                propsStreamElt = dictionaryToElt('stream', propsStream)
                # Add properties to image element
                imageElt.append(propsPDFElt)
                imageElt.append(propsStreamElt)

                # Add image element to page element
                pageElt.append(imageElt)

            # Add page element to pages element
            pagesElt.append(pageElt)

        # Add all child elements to properties element
        propertiesElt.append(fPathElt)
        propertiesElt.append(fSizeElt)
        propertiesElt.append(metadataElt)
        propertiesElt.append(pageModeElt)
        propertiesElt.append(signatureFlagElt)
        noPagesElt = etree.Element("noPages")
        noPagesElt.text = str(pages)
        propertiesElt.append(noPagesElt)
        propertiesElt.append(pagesElt)

        try:
            # Start Schematron magic ...
            schematron = isoschematron.Schematron(mySchemaElt,
                                                  store_report=True)

            # Validate tools output against schema
            schemaValidationResult = schematron.validate(propertiesElt)
            report = schematron.validation_report

        except Exception:
            # TODO: use logging for this instead!
            config.status = "fail"
            description = "Schematron validation resulted in an error"

        # Re-parse Schematron report
        report = etree.fromstring(str(report))
        # Make report less verbose
        if not verboseFlag:
            report = summariseSchematron(report)
        # Add to report element
        reportElt.append(report)
        # Quality check status
        status = "pass"
        for elem in report.iter():
            if elem.tag == "{http://purl.oclc.org/dsdl/svrl}failed-assert":
                status = "fail"
                break
        # Create element for this
        statusElt = etree.Element("status")
        statusElt.text = status
        # Add all child elements to PDF element
        pdfElt.append(propertiesElt)
        pdfElt.append(statusElt)
        pdfElt.append(reportElt)

    return pdfElt


def main():
    """Main function"""

    # Path to configuration dir (from https://stackoverflow.com/a/53222876/1209004
    # and https://stackoverflow.com/a/13184486/1209004).
    # TODO on Windows this should return the AppData/Local folder, does this work??
    configpath = os.path.join(
    os.environ.get('LOCALAPPDATA') or
    os.environ.get('XDG_CONFIG_HOME') or
    os.path.join(os.environ['HOME'], '.config'),
    "pdfbatchqa")

     # Create config directory if it doesn't exist already
    if not os.path.isdir(configpath):
        os.mkdir(configpath)
   
    # Locate package directory
    packageDir = os.path.dirname(os.path.abspath(__file__))

    # Profile and schema locations in installed package and config folder
    profilesDirPackage = os.path.join(packageDir, "profiles")
    schemasDirPackage = schemasDir = os.path.join(packageDir, "schemas")
    profilesDir = os.path.join(configpath, "profiles")
    schemasDir = os.path.join(configpath, "schemas")

    # Check if package profiles and schemas dirs exist
    checkDirExists(profilesDirPackage)
    checkDirExists(schemasDirPackage)

    # Copy profiles and schemas to respective dirs in config dir
    if not os.path.isdir(profilesDir):
        shutil.copytree(profilesDirPackage, profilesDir)
    if not os.path.isdir(schemasDir):
        shutil.copytree(schemasDirPackage, schemasDir)

    # Get input from command line
    args = parseCommandLine()

    batchDir = args.batchDir
    prefixOut = args.prefixout

    # Batch dir name
    batchDirName = os.path.basename(batchDir)

    # Construct output prefix for this batch
    prefixBatch = ("{}_{}").format(prefixOut, batchDirName)

    fileOut = ("{}.xml").format(prefixBatch)

    profile = args.profile
    profile = os.path.join(profilesDir, profile)
    checkFileExists(profile)

    verboseFlag = args.verbose

    # Get schema patterns and locations from profile
    schemas = readProfile(profile, schemasDir)

    # Summary file with quality check status (pass/fail) and no of pages
    summaryFile = os.path.normpath(("{}_summary.csv").format(prefixBatch))
    with open(summaryFile, 'w', newline='', encoding='utf-8') as fSum:
        writer = csv.writer(fSum)
        writer.writerow(["file", "status", "noPages"])

    listPDFs = getFilesFromTree(batchDir, "pdf")

    # start clock for statistics
    start = time.time()
    print("pdfbatchqa started: " + time.asctime())

    # Write XML header
    xmlHead = "<?xml version='1.0' encoding='UTF-8'?>\n"
    xmlHead += "<pdfbatchqa>\n"

    with open(fileOut,"wb") as f:
        f.write(xmlHead.encode('utf-8'))

    # Iterate over all PDFs
    for myPDF in listPDFs:
        myPDF = os.path.abspath(myPDF)
        pdfResult = processPDF(myPDF, verboseFlag, schemas)
        if len(pdfResult) != 0:
            noPages = pdfResult.find('properties/noPages').text
            status = pdfResult.find('status').text
            with open(summaryFile, 'a', newline='', encoding='utf-8') as fSum:
                writer = csv.writer(fSum)
                writer.writerow([myPDF, status, noPages])
            # Convert output to XML and add to output file
            outXML = etree.tostring(pdfResult,
                                    method='xml',
                                    encoding='utf-8',
                                    xml_declaration=False,
                                    pretty_print=True)

            with open(fileOut,"ab") as f:
                f.write(outXML)

    # Write XML footer
    xmlFoot = "</pdfbatchqa>\n"

    with open(fileOut,"ab") as f:
        f.write(xmlFoot.encode('utf-8'))

    # Timing output
    end = time.time()

    print("pdfbatchqa ended: " + time.asctime())

    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = round((timeElapsed / 60), 2)

    print("Elapsed time: {} minutes".format(timeInMinutes))


if __name__ == "__main__":
    main()
