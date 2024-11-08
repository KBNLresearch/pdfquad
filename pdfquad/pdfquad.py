#! /usr/bin/env python3

"""PDF Quality Assessment for Digitisation batches

Johan van der Knijff

Copyright 2024, KB/National Library of the Netherlands

"""

import sys
import os
import shutil
import time
import argparse
import csv
import logging
from lxml import etree
from . import properties
from . import schematron
from . import shared

__version__ = "0.2.a6"

# Create parser
parser = argparse.ArgumentParser(description="PDF QUality Assessment for Digitisation batches")


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


def processPDF(PDF, verboseFlag, schemas):
    """Process one PDF"""

    # Create output element for this PDF
    pdfElt = etree.Element("file")

    # Initial value of flag that indicates whether PDF passes or fails quality checks
    validationOutcome = "Pass"
    # Initial value of flag that indicates whether validation was successful
    validationSuccess = False

    # Select schema based on directory or file name pattern defined in profile
    schemaMatchFlag, mySchema = schematron.findSchema(PDF, schemas)
    
    # Extract properties
    propertiesElt = properties.getProperties(PDF)

    # Validate extracted properties against schema
    if schemaMatchFlag:
        validationSuccess, validationOutcome, reportElt = schematron.validate(mySchema,
                                                                              propertiesElt,
                                                                              verboseFlag)
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
    shared.checkDirExists(profilesDirPackage)
    shared.checkDirExists(schemasDirPackage)

    # Copy profiles and schemas to respective dirs in config dir
    if not os.path.isdir(profilesDir):
        shutil.copytree(profilesDirPackage, profilesDir)
    if not os.path.isdir(schemasDir):
        shutil.copytree(schemasDirPackage, schemasDir)

    # Check if all profiles and schemas can be parsed
    schematron.checkProfilesSchemas(profilesDir, schemasDir)

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
        schematron.listProfilesSchemas(profilesDir, schemasDir)
    elif action is None:
        print('')
        parser.print_help()
        sys.exit()
    
    # Add profilesDir to profile definition
    profile = os.path.join(profilesDir, profile)

    # Check if files / directories exist
    shared.checkFileExists(profile)
    shared.checkDirExists(batchDir)
    shared.checkDirExists(outDir)

    # Check if outDir is writable
    if not os.access(outDir, os.W_OK):
        msg = ("directory {} is not writable".format(outDir))
        shared.errorExit(msg)

    # Batch dir name
    batchDirName = os.path.basename(batchDir)
    # Construct output prefix for this batch
    prefixBatch = ("{}_{}").format(prefixOut, batchDirName)
    
    # Set up logging
    logging.basicConfig(handlers=[logging.StreamHandler(sys.stdout)],
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Get schema patterns and locations from profile
    schemas = schematron.readProfile(profile, schemasDir)

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
