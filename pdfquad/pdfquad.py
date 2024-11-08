#! /usr/bin/env python3

"""PDF Quality Assessment for Digitisation batches

Johan van der Knijff

Copyright 2024, KB/National Library of the Netherlands

"""

import sys
import os
import shutil
import io
import time
import argparse
import csv
import logging
from lxml import isoschematron
from lxml import etree
import pymupdf
import PIL
from PIL import ImageCms
from . import jpegquality

__version__ = "0.2.a5"

# Create parser
parser = argparse.ArgumentParser(description="PDF QUality Assessment for Digitisation batches")

def errorExit(msg):
    """Write error to stderr and exit"""
    msgString = "ERROR: {}\n".format(msg)
    sys.stderr.write(msgString)
    sys.exit()


def checkFileExists(fileIn):
    """Check if file exists and exit if not"""
    if not os.path.isfile(fileIn):
        msg = "file {} does not exist".format(fileIn)
        errorExit(msg)


def checkDirExists(pathIn):
    """Check if directory exists and exit if not"""
    if not os.path.isdir(pathIn):
        msg = "directory {} does not exist".format(pathIn)
        errorExit(msg)


def parseCommandLine():
    """Parse command line"""

    # Sub-parsers for process and list commands

    subparsers = parser.add_subparsers(help='sub-command help',
                                       dest='subcommand')
    parser_process = subparsers.add_parser('process',
                                          help='process a batch')
    parser_process.add_argument('profile',
                                action="store",
                                help='validation profile name (use "pdfquad list" to list available profiles)')
    parser_process.add_argument('batchDir',
                                action="store",
                                help="batch directory")
    parser_process.add_argument('--maxpdfs', '-x',
                                action="store",
                                default=10,
                                help="maximum number of reported PDFs per output file; for larger numbers \
                                    output is split across multiple files")
    parser_process.add_argument('--prefixout', '-p',
                                action="store",
                                default='pq',
                                help="prefix of output files")
    parser_process.add_argument('--outdir', '-o',
                                action="store",
                                default=os.getcwd(),
                                help="output directory")
    parser_process.add_argument('--verbose', '-b',
                                action="store_true",
                                default=False,
                                help="report Schematron report in verbose format")
    parser_list = subparsers.add_parser('list',
                                        help='list available profiles and schemas')
    parser.add_argument('--version', '-v',
                        action="version",
                        version=__version__)

    # Parse arguments
    args = parser.parse_args()

    return args


def listProfilesSchemas(profilesDir, schemasDir):
    """List all available profiles and schemas"""
    profiles = os.listdir(profilesDir)
    print("Available profiles (directory {}):".format(profilesDir))
    for profile in profiles:
        print("  - {}".format(profile))
    schemas = os.listdir(schemasDir)
    print("Available schemas (directory {}):".format(schemasDir))
    for schema in schemas:
        print("  - {}".format(schema))
    sys.exit()


def checkProfilesSchemas(profilesDir, schemasDir):
    """Check if all profiles and schemas can be read without
    throwing parse errors"""
    profiles = os.listdir(profilesDir)
    for profile in profiles:
        try:
            readAsLXMLElt(os.path.join(profilesDir, profile))
        except Exception:
            msg = ("error parsing profile {}").format(profile)
            errorExit(msg)
    schemas = os.listdir(schemasDir)
    for schema in schemas:
        try:
            schemaElt = readAsLXMLElt(os.path.join(schemasDir, schema))
        except Exception:
            msg = ("error parsing schema {}").format(schema)
            errorExit(msg)
        try:
            isoschematron.Schematron(schemaElt)
        except etree.XSLTParseError:
            msg = ("XSLT parse error for schema {}").format(schema)
            errorExit(msg)       


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
            if mMatch not in ["is", "startswith", "endswith", "contains"]:
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


def writeXMLHeader(fileOut):
    """Write XML header"""
    xmlHead = "<?xml version='1.0' encoding='UTF-8'?>\n"
    xmlHead += "<pdfquad>\n"
    with open(fileOut,"wb") as f:
        f.write(xmlHead.encode('utf-8'))


def writeXMLFooter(fileOut):
    """Write XML footer"""
    xmlFoot = "</pdfquad>\n"
    with open(fileOut,"ab") as f:
        f.write(xmlFoot.encode('utf-8'))


def findSchema(PDF, schemas):
    """Find schema based on match with name or parent directory"""

    # Initial value of flag that indicates schema match
    schemaMatchFlag = False
    # Initial value of schema reference
    schemaMatch = "undefined"

    fPath, fName = os.path.split(PDF)
    parentDir = os.path.basename(fPath)

    for schema in schemas:
        mType = schema[0]
        mMatch = schema[1]
        mPattern = schema[2]
        mSchema = schema[3]
        if mType == "parentDirName" and mMatch == "is":
            if parentDir == mPattern:
                schemaMatch = mSchema
                schemaMatchFlag = True
        elif mType == "parentDirName" and mMatch == "startswith":
            if parentDir.startswith(mPattern):
                schemaMatch = mSchema
                schemaMatchFlag = True
        elif mType == "parentDirName" and mMatch == "endswith":
            if parentDir.endswith(mPattern):
                schemaMatch = mSchema
                schemaMatchFlag = True
        elif mType == "parentDirName" and mMatch == "contains":
            if mPattern in parentDir:
                schemaMatch = mSchema
                schemaMatchFlag = True
        if mType == "fileName" and mMatch == "is":
            if fName == mPattern:
                schemaMatch = mSchema
                schemaMatchFlag = True
        elif mType == "fileName" and mMatch == "startswith":
            if fName.startswith(mPattern):
                schemaMatch = mSchema
                schemaMatchFlag = True
        elif mType == "fileName" and mMatch == "endswith":
            if fName.endswith(mPattern):
                schemaMatch = mSchema
                schemaMatchFlag = True
        elif mType == "fileName" and mMatch == "contains":
            if mPattern in fName:
                schemaMatch = mSchema
                schemaMatchFlag = True

    return schemaMatchFlag, schemaMatch


def getProperties(PDF):
    """Extract properties and return result as Element object"""

    # Create element object to store all properties
    propertiesElt = etree.Element("properties")

    # Element to store exceptions at file level
    exceptionsFileElt = etree.Element("exceptions")

    # Create and fill descriptive elements
    fPathElt = etree.Element("filePath")
    fPathElt.text = PDF
    fSizeElt = etree.Element("fileSize")
    fSizeElt.text = str(os.path.getsize(PDF))

    # Add to properies element
    propertiesElt.append(fPathElt)
    propertiesElt.append(fSizeElt)

    # Parse PDF and check for open password
    openPasswordElt = etree.Element("openPassword")
    try:
        doc = pymupdf.open(PDF)
        rc = doc.authenticate("whatever")
        if rc == 0:
            openPasswordElt.text = str(True)
            propertiesElt.append(openPasswordElt)
            logging.warning("PDF has open password")
            return propertiesElt
        else:
            openPasswordElt.text = str(False)
            propertiesElt.append(openPasswordElt)
    except Exception  as e:
        ex = etree.SubElement(exceptionsFileElt,'exception')
        ex.text = str(e)
        propertiesElt.append(exceptionsFileElt)
        logging.warning(("while opening PDF: {}").format(str(e)))
        return propertiesElt

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

    pageNo = 1
    for page in doc:
        pageElt = etree.Element("page")
        pageElt.attrib["number"] = str(pageNo)
        pageNo += 1
        images = page.get_images(full=False)
        for image in images:
            imageElt = etree.Element("image")
            exceptionsStreamElt = etree.Element("exceptions")
            # Store properties at PDF object dictionary level to a dictionary
            propsDict = {}
            propsDict['xref'] = image[0]
            #propsDict['smask'] = image[1]
            propsDict['width'] = image[2]
            propsDict['height'] = image[3]
            propsDict['bpc'] = image[4]
            propsDict['colorspace'] = image[5]
            propsDict['altcolorspace'] = image[6]
            #propsDict['name'] = image[7]
            propsDict['filter'] = image[8]

            # Read raw image stream data from xref id
            xref = propsDict['xref']
            imageReadSuccess = False
            propsStream = {}
            stream = doc.xref_stream_raw(xref)
            try:
                im = PIL.Image.open(io.BytesIO(stream))
                im.load()
                imageReadSuccess = True
            except Exception as e:
                ex = etree.SubElement(exceptionsStreamElt,'exception')
                ex.text = str(e)
                logging.warning(("page {} while reading image stream: {}").format(str(pageNo), str(e)))

            if imageReadSuccess:
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

                if im.format == "JPEG":
                    try:
                        # Estimate JPEG quality using least squares matching
                        # against standard quantization tables
                        quality, rmsError, nse = jpegquality.computeJPEGQuality(im)
                        propsStream['JPEGQuality'] = quality
                        propsStream['NSE_JPEGQuality'] = nse
                    except Exception as e:
                        ex = etree.SubElement(exceptionsStreamElt,'exception')
                        ex.text = str(e)
                        logging.warning(("page {} while estimating JPEG quality from image stream: {}").format(str(pageNo), str(e)))

                for key, value in im.info.items():
                    if isinstance(value, bytes):
                        propsStream[key] = 'bytestream'
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
                except Exception as e:
                    ex = etree.SubElement(exceptionsStreamElt,'exception')
                    ex.text = str(e)
                    logging.warning(("page {} while extracting ICC profile properties from image stream: {}").format(str(pageNo), str(e)))

            # Dictionaries to element objects
            propsDictElt = dictionaryToElt('dict', propsDict)
            propsStreamElt = dictionaryToElt('stream', propsStream)
            propsStreamElt.append(exceptionsStreamElt)
            # Add properties to image element
            imageElt.append(propsDictElt)
            imageElt.append(propsStreamElt)

            # Add image element to page element
            pageElt.append(imageElt)

        # Add page element to pages element
        pagesElt.append(pageElt)

    # Add all remaining elements to properties element
    propertiesElt.append(metadataElt)
    propertiesElt.append(pageModeElt)
    propertiesElt.append(signatureFlagElt)
    noPagesElt = etree.Element("noPages")
    noPagesElt.text = str(pages)
    propertiesElt.append(noPagesElt)
    propertiesElt.append(pagesElt)
    propertiesElt.append(exceptionsFileElt)

    return propertiesElt


def validate(schema, propertiesElt, verboseFlag):
    """Validate extracted properties against schema"""

    # Initial value of validation outcome
    validationOutcome = "Pass"

    # Initial value of flag that indicates whether validation ran
    validationSuccess = False

    # Element used to store validation report
    reportElt = etree.Element("schematronReport")
    # Get schema as lxml.etree element
    mySchemaElt = readAsLXMLElt(schema)
    # Start Schematron magic ...
    schematron = isoschematron.Schematron(mySchemaElt,
                                          store_report=True)

    try:
        # Validate properties element against schema
        validationResult = schematron.validate(propertiesElt)
        # Set status to "Fail" if properties didn't pass validation
        if not validationResult:
            validationOutcome = "Fail"
        report = schematron.validation_report
        validationSuccess = True

    except Exception:
        validationOutcome = "Fail"
        logging.error(("Schematron validation failed for {}").format(schema))

    try:
        # Re-parse Schematron report
        report = etree.fromstring(str(report))
        # Make report less verbose
        if not verboseFlag:
            report = summariseSchematron(report)
        # Add to report element
        reportElt.append(report)
    except Exception:
        # No report available because Schematron validation failed
        pass

    return validationSuccess, validationOutcome, reportElt


def processPDF(PDF, verboseFlag, schemas):
    """Process one PDF"""

    # Create output element for this PDF
    pdfElt = etree.Element("file")

    # Initial value of flag that indicates whether PDF passes or fails quality checks
    validationOutcome = "Pass"
    # Initial value of flag that indicates whether validation was successful
    validationSuccess = False

    # Select schema based on directory or file name pattern defined in profile
    schemaMatchFlag, mySchema = findSchema(PDF, schemas)
    
    # Extract properties
    propertiesElt = getProperties(PDF)

    # Validate extracted properties against schema
    if schemaMatchFlag:
        validationSuccess, validationOutcome, reportElt = validate(mySchema, propertiesElt, verboseFlag)
    else:
        # No schema match
        validationOutcome = "Fail"
        logging.warning("no schema match")

    if not validationSuccess:
        logging.warning("Schematron validation was not successful")

    # Create schema and status elements
    schemaElt = etree.Element("schema")
    schemaElt.text = mySchema
    validationSuccessElt = etree.Element("validationSuccess")
    validationSuccessElt.text = str(validationSuccess)
    validationOutcomeElt = etree.Element("validationOutcome")
    validationOutcomeElt.text = validationOutcome
    # Add all child elements to PDF element
    pdfElt.append(propertiesElt)
    pdfElt.append(schemaElt)
    pdfElt.append(validationSuccessElt)
    pdfElt.append(validationOutcomeElt)
    if schemaMatchFlag:
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
    "pdfquad")

     # Create config directory if it doesn't exist already
    if not os.path.isdir(configpath):
        os.mkdir(configpath)
   
    # Locate package directory
    packageDir = os.path.dirname(os.path.abspath(__file__))

    # Profile and schema locations in installed package and config folder
    profilesDirPackage = os.path.join(packageDir, "profiles")
    schemasDirPackage = os.path.join(packageDir, "schemas")
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

    # Check if all profiles and schemas can be parsed
    checkProfilesSchemas(profilesDir, schemasDir)

    # Get input from command line
    args = parseCommandLine()
    action = args.subcommand

    if action == "process":
        profile = os.path.basename(args.profile)
        batchDir = os.path.normpath(args.batchDir)
        prefixOut = args.prefixout
        outDir = os.path.normpath(args.outdir)
        maxPDFs = int(args.maxpdfs)
        verboseFlag = args.verbose
    elif action == "list":
        listProfilesSchemas(profilesDir, schemasDir)
    elif action is None:
        print('')
        parser.print_help()
        sys.exit()
    
    # Add profilesDir to profile definition
    profile = os.path.join(profilesDir, profile)

    # Check if files / directories exist
    checkFileExists(profile)
    checkDirExists(batchDir)
    checkDirExists(outDir)

    # Check if outDir is writable
    if not os.access(outDir, os.W_OK):
        msg = ("directory {} is not writable".format(outDir))
        errorExit(msg)

    # Batch dir name
    batchDirName = os.path.basename(batchDir)
    # Construct output prefix for this batch
    prefixBatch = ("{}_{}").format(prefixOut, batchDirName)
    
    # Set up logging
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Get schema patterns and locations from profile
    schemas = readProfile(profile, schemasDir)

    # Summary file with quality check status (pass/fail) and no of pages
    summaryFile = os.path.normpath(("{}_summary.csv").format(prefixBatch))
    summaryFile = os.path.join(outDir, summaryFile)
    with open(summaryFile, 'w', newline='', encoding='utf-8') as fSum:
        writer = csv.writer(fSum)
        writer.writerow(["file", "validationSuccess", "validationOutcome", "noPages", "fileOut"])

    listPDFs = getFilesFromTree(batchDir, "pdf")

    # start clock for statistics
    start = time.time()
    print("pdfquad started: " + time.asctime())

    # Iterate over all PDFs
    pdfCount = 1
    outFileCount = 1
    fileOut = ("{}_{}.xml").format(prefixBatch, str(outFileCount).zfill(3))
    fileOut = os.path.join(outDir, fileOut)
    writeXMLHeader(fileOut)

    for myPDF in listPDFs:
        logging.info(("file: {}").format(myPDF))
        if pdfCount > maxPDFs:
            writeXMLFooter(fileOut)
            outFileCount += 1
            fileOut = ("{}_{}.xml").format(prefixBatch, str(outFileCount).zfill(3))
            fileOut = os.path.join(outDir, fileOut)
            writeXMLHeader(fileOut)
            pdfCount = 1
        myPDF = os.path.abspath(myPDF)
        pdfResult = processPDF(myPDF, verboseFlag, schemas)
        if len(pdfResult) != 0:
            try:
                noPages = pdfResult.find('properties/noPages').text
            except AttributeError:
                noPages = "na"
            try:
                validationSuccess = pdfResult.find('validationSuccess').text
            except AttributeError:
                validationSuccess = "na"
            try:
                validationOutcome = pdfResult.find('validationOutcome').text
            except AttributeError:
                validationOutcome = "na"
            with open(summaryFile, 'a', newline='', encoding='utf-8') as fSum:
                writer = csv.writer(fSum)
                writer.writerow([myPDF, validationSuccess, validationOutcome, noPages, fileOut])
            # Convert output to XML and add to output file
            outXML = etree.tostring(pdfResult,
                                    method='xml',
                                    encoding='utf-8',
                                    xml_declaration=False,
                                    pretty_print=True)

            with open(fileOut,"ab") as f:
                f.write(outXML)

            pdfCount += 1

    writeXMLFooter(fileOut)

    # Timing output
    end = time.time()

    print("pdfquad ended: " + time.asctime())

    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = round((timeElapsed / 60), 2)

    print("Elapsed time: {} minutes".format(timeInMinutes))


if __name__ == "__main__":
    main()
