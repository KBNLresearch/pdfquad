#! /usr/bin/env python3

"""PDF Quality Assessment for Digitisation batches

Johan van der Knijff

Copyright 2024, KB/National Library of the Netherlands

Module with code related to schematron, schemas and profiles

"""

import sys
import os
import logging
from lxml import isoschematron
from lxml import etree
from . import shared


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
            shared.errorExit(msg)
    schemas = os.listdir(schemasDir)
    for schema in schemas:
        try:
            schemaElt = readAsLXMLElt(os.path.join(schemasDir, schema))
        except Exception:
            msg = ("error parsing schema {}").format(schema)
            shared.errorExit(msg)
        try:
            isoschematron.Schematron(schemaElt)
        except etree.XSLTParseError:
            msg = ("XSLT parse error for schema {}").format(schema)
            shared.errorExit(msg)       


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
        shared.errorExit(msg)

    # Output list
    listOut = []

    # Locate schema elements
    schemas = prof.findall("schema")

    for schema in schemas:
        try:
            mType = schema.attrib["type"]
            if mType not in ["fileName", "parentDirName"]:
                msg = "'{}' is not a valid 'type' value".format(mType)
                shared.errorExit(msg)
        except KeyError:
            msg = "missing 'type' attribute in profile {}".format(profile)
            shared.errorExit(msg)
        try:
            mMatch = schema.attrib["match"]
            if mMatch not in ["is", "startswith", "endswith", "contains"]:
                msg = "'{}' is not a valid 'match' value".format(mMatch)
                shared.errorExit(msg)
        except KeyError:
            msg = "missing 'match' attribute in profile {}".format(profile)
            shared.errorExit(msg)
        try:
            mPattern = schema.attrib["pattern"]
        except KeyError:
            msg = "missing 'pattern' attribute in profile {}".format(profile)
            shared.errorExit(msg)

        schematronFile = os.path.join(schemasDir, schema.text)
        shared.checkFileExists(schematronFile)

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


def summariseSchematron(report):
    """Return summarized version of Schematron report with only output of
    failed tests"""

    for elem in report.iter():
        if elem.tag == "{http://purl.oclc.org/dsdl/svrl}fired-rule":
            elem.getparent().remove(elem)

    return report


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
