#! /usr/bin/env python3
"""wrapper functions for poppler"""

import subprocess as sub
from lxml import etree
from . import config

def getReadErrors(rescueLine):
    """parse ddrescue output line for values of readErrors"""
    lineItems = rescueLine.split(",")

    for item in lineItems:
        # Note that 'errors' item was renamed to 'read errors' between ddrescue 1.19 and 1.22
        # This should work in either case
        if "errors:" in item:
            reEntry = item.split(":")
            readErrors = int(reEntry[1].strip())

    return readErrors


def pdfimages(args):
    """pdfimages wapper function"""

    success = False
    # Create Element object to hold pdfimages output
    pdfImagesElt = etree.Element("pdfimages")

    try:
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE,
                      shell=False, bufsize=1, universal_newlines=True)
        stdout, stderr = p.communicate()
        exitStatus = p.returncode
        success = True

    except Exception:
        # I don't even want to to start thinking how one might end up here ...
        exitStatus = -99
        stdout = ""
        stderr = ""

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
