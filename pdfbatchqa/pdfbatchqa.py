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
import io
import time
import configargparse
from lxml import isoschematron
from lxml import etree
import pymupdf
from PIL import Image
from PIL import ImageCms
from . import writeconfig
from . import config

__version__ = "0.1.0"


def errorExit(msg):
    """Write error to stderr and exit"""
    msgString = ("ERROR: " + msg + "\n")
    sys.stderr.write(msgString)
    sys.exit()


def checkFileExists(fileIn):
    """Check if file exists and exit if not"""
    if not os.path.isfile(fileIn):
        msg = fileIn + " does not exist!"
        errorExit(msg)


def checkDirExists(pathIn):
    """Check if directory exists and exit if not"""
    if not os.path.isdir(pathIn):
        msg = pathIn + " does not exist!"
        errorExit(msg)


def openFileForAppend(wFile):
    """Opens file for writing in append + binary mode"""
    try:
        f = open(wFile, "a", encoding="utf-8")
        return f

    except Exception:
        msg = wFile + " could not be written"
        errorExit(msg)


def removeFile(fileIn):
    """Remove a file"""
    try:
        if os.path.isfile(fileIn):
            os.remove(fileIn)
    except Exception:
        msg = "Could not remove " + fileIn
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
    parser = configargparse.ArgumentParser(description="Automated PDF Quality Assessment digitisation batches",
                                           default_config_files=[config.configfile])

    parser.add_argument('batchDir',
                        action="store",
                        help="batch directory")
    parser.add_argument('--prefixout',
                        action="store",
                        help="prefix of output files")
    parser.add_argument('--profile',
                        action="store",
                        help='name of profile that defines validation schemas.\
                              Type "l" or "list" to view all available profiles')
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
    """Read a profile and return dictionary with all associated schemas"""

    # Parse XML tree
    try:
        tree = etree.parse(profile)
        prof = tree.getroot()
    except Exception:
        msg = "error parsing " + profile
        errorExit(msg)

    # Locate schema elements
    schemaLowQualityElement = prof.find("schemaLowQuality")
    schemaHighQualityElement = prof.find("schemaHighQuality")

    # Get corresponding text values
    schemaLowQuality = os.path.join(schemasDir, schemaLowQualityElement.text)
    schemaHighQuality = os.path.join(schemasDir, schemaHighQualityElement.text)
 
    # Check if all files exist, and exit if not
    checkFileExists(schemaLowQuality)
    checkFileExists(schemaHighQuality)

    # Add schemas to a dictionary
    schemas = {"schemaLowQuality": schemaLowQuality,
               "schemaHighQuality": schemaHighQuality}

    return schemas


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


def extractSchematron(report):
    """Parse output of Schematron validation and extract interesting bits"""

    outString=""

    for elem in report.iter():
        if elem.tag == "{http://purl.oclc.org/dsdl/svrl}failed-assert":

            config.status = "fail"

            # Extract test definition
            test = elem.get('test')
            outString += 'Test "' + test + '" failed ('

            # Extract text description from text element
            for subelem in elem.iter():
                if subelem.tag == "{http://purl.oclc.org/dsdl/svrl}text":
                    description = (subelem.text)
                    outString += description + ")" + config.lineSep
    return outString


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


def getCompressionRatio(noBytes, bpc, components, width, height):
    """Compute compression ratio.
    """
    # Total bytes per pixel
    bytesPerPixel = (bpc * components)/8

    # Uncompressed image size
    sizeUncompressed = bytesPerPixel * width * height

    # Compression ratio
    if noBytes != 0:
        compressionRatio = sizeUncompressed / noBytes
    else:
        # Obviously something going wrong here ...
        compressionRatio = -9999

    compressionRatio = round(compressionRatio, 2)

    return compressionRatio


def processPDF(PDF):
    """Process one PDF"""

    # Initialise status (pass/fail)
    config.status = "pass"
    schemaMatch = True

    # Initialise empty text string for error log output
    ptOutString = ""

    # Create output element for this PDF
    pdfElt = etree.Element("file")

    # Create list that contains all file path components (dir names)
    pathComponents, fName = getPathComponentsAsList(PDF)

    # Select schema based on whether this is a PDF with 50% or 85%
    # JPEG quality (from path name pattern in batch)
    if "300ppi-50" in pathComponents:
        mySchema = config.schemaLowQualityLXMLElt
        schemaMatch = True
    elif "300ppi-85" in pathComponents:
        mySchema = config.schemaHighQualityLXMLElt
        schemaMatch = True
    else:
        schemaMatch = False
        config.status = "fail"
        description = "Name of parent directory does not match any schema"
        ptOutString += description + config.lineSep

    if schemaMatch:
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
                noBytesStream = len(stream)
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
                propsStream['compressionRatio'] = getCompressionRatio(noBytesStream,
                                                                      bitsPerComponent,
                                                                      noComponents,
                                                                      width,
                                                                      height)

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
        noPagesElt = etree.Element("noPages")
        noPagesElt.text = str(pages)
        propertiesElt.append(noPagesElt)
        propertiesElt.append(pagesElt)

        try:
            # Start Schematron magic ...
            schematron = isoschematron.Schematron(mySchema,
                                                  store_report=True)

            # Validate tools output against schema
            schemaValidationResult = schematron.validate(propertiesElt)
            report = schematron.validation_report

        except Exception:
            config.status = "fail"
            description = "Schematron validation resulted in an error"
            ptOutString += description + config.lineSep

        # Re-parse Schematron report and add to report element
        report = etree.fromstring(str(report))
        reportElt.append(report)
        # Add all child elements to PDF element
        pdfElt.append(propertiesElt)
        pdfElt.append(reportElt)

        # Parse output of Schematron validation and extract
        # interesting bits
        try:
            schOutString = extractSchematron(report)
            ptOutString += schOutString
        except Exception:
            config.status = "fail"
            description = "Error processing Schematron output"
            ptOutString += description + config.lineSep

    if config.status == "fail":

        config.fFailed.write(PDF + config.lineSep)
        config.fFailed.write("*** Schema validation errors:" + config.lineSep)
        config.fFailed.write(ptOutString)
        config.fFailed.write("####" + config.lineSep)

    statusLine = PDF + "," + config.status + config.lineSep
    config.fStatus.write(statusLine)

    return pdfElt


def main():
    """Main function"""

    # Path to configuration file (from https://stackoverflow.com/a/53222876/1209004
    # and https://stackoverflow.com/a/13184486/1209004).
    # TODO on Windows this should return the AppData/Local folder, does this work??
    configpath = os.path.join(
    os.environ.get('LOCALAPPDATA') or
    os.environ.get('XDG_CONFIG_HOME') or
    os.path.join(os.environ['HOME'], '.config'),
    "pdfbatchqa")

    config.configfile = os.path.join(configpath, 'pdfbatchqa.conf')

    # Create config directory + file if it doesn't exist already
    if not os.path.isfile(config.configfile):
        writeconfig.writeConfigFile(config.configfile)
   
    # Locate package directory
    packageDir = os.path.dirname(os.path.abspath(__file__))

    # Profiles and schemas dirs.
    profilesDir = os.path.join(packageDir, "profiles")
    schemasDir = os.path.join(packageDir, "schemas")

    # Check if profiles dir exists and exit if not
    checkDirExists(profilesDir)

    # Get input from command line
    args = parseCommandLine()

    batchDir = args.batchDir
    prefixOut = args.prefixout
    fileOut = prefixOut + ".xml"

    profile = args.profile
    if profile in["l", "list"]:
        listProfiles(profilesDir)
    elif profile is None:
        msg = "profile is undefined"
        errorExit(msg)
    else:
        profile = os.path.join(profilesDir, profile)
        checkFileExists(profile)
    
    # Get schema locations from profile
    schemas = readProfile(profile, schemasDir)

    schemaLowQuality = schemas["schemaLowQuality"]
    schemaHighQuality = schemas["schemaHighQuality"]
 
    # Get schemas as lxml.etree elements
    config.schemaLowQualityLXMLElt = readAsLXMLElt(schemaLowQuality)
    config.schemaHighQualityLXMLElt = readAsLXMLElt(schemaHighQuality)
 
    # Set line separator for output/ log files to OS default
    config.lineSep = "\n"

    # Open log files for writing (append)

    # File with summary of quality check status (pass/fail) for each image
    statusLog = os.path.normpath(prefixOut + "_status.csv")
    removeFile(statusLog)
    config.fStatus = openFileForAppend(statusLog)

    # File that contains detailed results for all images that failed
    # quality check
    failedLog = os.path.normpath(prefixOut + "_failed.txt")
    removeFile(failedLog)
    config.fFailed = openFileForAppend(failedLog)

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
        pdfResult = processPDF(myPDF)
        if len(pdfResult) != 0:
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

    # Close output files
    config.fStatus.close()
    config.fFailed.close()

    # Timing output
    end = time.time()

    print("pdfbatchqa ended: " + time.asctime())

    # Elapsed time (seconds)
    timeElapsed = end - start
    timeInMinutes = round((timeElapsed / 60), 2)

    print("Elapsed time: " + str(timeInMinutes) + " minutes")


if __name__ == "__main__":
    main()
