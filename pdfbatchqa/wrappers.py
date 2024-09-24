#! /usr/bin/env python3
"""wrapper functions for poppler"""

import os
import subprocess as sub
from lxml import etree
from . import config

def pdfimagesList(PDF):
    """pdfimages list wrapper function"""

    success = False
    # Create Element object to hold pdfimages output
    pdfImagesElt = etree.Element("pdfimages")

    # TODO:
    # - check if pdimages exists
    # - add wrapping of Windows executable at user-defined location (defined in config file)

    args = [config.pdfimages]
    args.append('-list')
    args.append(PDF)

    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                      shell=False, bufsize=1, universal_newlines=True)
        stdout, stderr = p.communicate()
        exitStatus = p.returncode
        if exitStatus == 0:
            success = True

    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99
        stdout = ""

    if success:
        # Split pdfimages output at lines
        outList = stdout.splitlines()
        noLines = len(outList)

        # Split header items to list
        headersList = outList[0].split()
        noCols = len(headersList)

        # List for values
        valuesList = []
        
        # Split remaining items and add to valuesList (skip line 2, which only contains dashes)
        for i in range(2, noLines):
            values = outList[i].split()
            valuesList.append(values)

        for line in valuesList:
            imageElt = etree.Element("image")
            for col in range(0,noCols):
                thisProperty = headersList[col]
                thisValue = line[col]
                thisElt = etree.Element(thisProperty)
                thisElt.text = thisValue
                imageElt.append(thisElt)
            
            pdfImagesElt.append(imageElt)

    return pdfImagesElt


def pdfimagesExtract(PDF, outDir):
    """pdfimages extract wrapper function"""

    success = False

    args = [config.pdfimages]
    args.append('-all')
    args.append(PDF)
    args.append(os.path.join(outDir, 'crap'))

    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                      shell=False, bufsize=1, universal_newlines=True)
        stdout, stderr = p.communicate()
        exitStatus = p.returncode
        if exitStatus == 0:
            success = True

    except Exception:
        pass

    return success


def pdfinfo(PDF):
    """pdfinfo wrapper function"""

    success = False
    # Create Element object to hold pdfinfo output
    pdfInfoElt = etree.Element("pdfinfo")

    # TODO:
    # - check if pdinfo exists
    # - add wrapping of Windows executable at user-defined location (defined in config file)

    args = [config.pdfinfo]
    args.append(PDF)

    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                      shell=False, bufsize=1, universal_newlines=True)
        stdout, stderr = p.communicate()
        exitStatus = p.returncode
        if exitStatus == 0:
            success = True

    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99
        stdout = ""

    if success:
        # Split pdfinfo output at lines
        outList = stdout.splitlines()

        for line in outList:
            items = line.split(":")
            thisProperty = items[0].strip().replace(" ", "_")
            thisValue = items[1].strip()
            thisElt = etree.Element(thisProperty)
            thisElt.text = thisValue
            pdfInfoElt.append(thisElt)

    return pdfInfoElt


def exiftool(imagefile):
    """exiftool wrapper function"""

    success = False

    args = [config.exiftool]
    args.append('-X')
    args.append(imagefile)

    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                      shell=False, bufsize=1, universal_newlines=True)
        stdout, stderr = p.communicate()
        exitStatus = p.returncode
        if exitStatus == 0:
            success = True

    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99
        stdout = ""

    return stdout
