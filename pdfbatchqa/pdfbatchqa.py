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
import time
import argparse
import xml.etree.ElementTree as ET
from lxml import isoschematron
from lxml import etree
from . import wrappers
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
    parser = argparse.ArgumentParser(description="JP2 profiler for KB")

    parser.add_argument('batchDir',
                        action="store",
                        help="batch directory")

    parser.add_argument('prefixOut',
                        action="store",
                        help="prefix of output files")
    parser.add_argument('-p', '--profile',
                        action="store",
                        default="list",
                        help='name of profile that defines schemas for master,\
                               access and target images. Type "l" or "list" \
                              to view all available profiles')
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


def readProfile(profile, profilesDir, schemasDir):
    """Read a profile and return dictionary with all associated schemas"""

    profile = os.path.join(profilesDir, profile)

    # Check if profile exists and exit if not
    checkFileExists(profile)

    # Parse XML tree
    try:
        tree = ET.parse(profile)
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
            if extensionString in thisExtension:
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


def processPDF(PDF):
    """Process one PDF"""

    # Initialise status (pass/fail)
    config.status = "pass"
    schemaMatch = True

    # Initialise empty text string for error log output
    ptOutString = ""

    # Create list that contains all file path components (dir names)
    pathComponents, fName = getPathComponentsAsList(PDF)

    # Create output element for this PDF
    pdfElt = etree.Element("file")
    fPathElt = etree.Element("filePath")
    fPathElt.text = PDF
    fSizeElt = etree.Element("fileSize")
    fSizeElt.text = str(os.path.getsize(PDF))

    # Create elements to store properties and Schematron report
    propertiesElt = etree.Element("properties")
    reportElt = etree.Element("schematronReport")

    # TODO Select schema based on whether this is a PDF with 50% or 85%
    # JPEG quality (from file name or path name pattern in batch?)

    """
    if "master" in pathComponents:
        mySchema = config.schemaMasterLXMLElt
    elif "access" in pathComponents:
        mySchema = config.schemaAccessLXMLElt
    elif "targets-jp2_access" in pathComponents:
        if "_MTF_GRAY_" in fName:
            mySchema = config.schemaTargetAccessGrayLXMLElt
        else:
            mySchema = config.schemaTargetAccessRGBLXMLElt
    elif "targets-jp2" in pathComponents:
        if "_MTF_GRAY_" in fName:
            mySchema = config.schemaTargetGrayLXMLElt
        else:
            mySchema = config.schemaTargetRGBLXMLElt
    else:
        schemaMatch = False
        config.status = "fail"
        description = "Name of parent directory does not match any schema"
        ptOutString += description + config.lineSep
    """

    # For now we just use this schema
    mySchema = config.schemaLowQualityLXMLElt
    schemaMatch = True

    if schemaMatch:

        # Run Poppler tools on image and write result to text file
        try:
            args = ['pdfimages']
            args.append('-list')
            args.append(PDF)
            resultPDFImages = wrappers.pdfimages(args)
        except Exception:
            config.status = "fail"
            description = "Error running pdfimages"
            ptOutString += description + config.lineSep

        # Add tool-specific elements to properties element
        propertiesElt.append(resultPDFImages)

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
        pdfElt.append(fPathElt)
        pdfElt.append(fSizeElt)
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
    prefixOut = args.prefixOut

    profile = args.profile
    if profile in["l", "list"]:
        listProfiles(profilesDir)

    # Get schema locations from profile
    schemas = readProfile(profile, profilesDir, schemasDir)

    schemaLowQuality = schemas["schemaLowQuality"]
    schemaHighQuality = schemas["schemaHighQuality"]
 
    # Get schemas as lxml.etree elements
    config.schemaLowQualityLXMLElt = readAsLXMLElt(schemaLowQuality)
    config.schemaHighQualityLXMLElt = readAsLXMLElt(schemaHighQuality)
 
    # Set line separator for output/ log files to OS default
    config.lineSep = "\n"

    # Root element to which we will add output for all PDFs
    rootElt = etree.Element("pdfbatchqa")

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

    # Iterate over all PDFs
    for myPDF in listPDFs:
        myPDF = os.path.abspath(myPDF)
        pdfResult = processPDF(myPDF)
        rootElt.append(pdfResult)

    # Convert output to XML
    outXML = etree.tostring(rootElt, 
                                    method='xml',
                                    encoding='utf-8',
                                    xml_declaration=True,
                                    pretty_print=True)

    # Write XML to file
    ## TODO: implement incremental updates (see Jpylyzer) to avoid memory
    # problems or data loss in case of unexpected crashes!
    with open(prefixOut + ".xml","wb") as f:
        f.write(outXML)

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
