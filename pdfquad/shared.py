#! /usr/bin/env python3

"""PDF Quality Assessment for Digitisation batches

Johan van der Knijff

Copyright 2024, KB/National Library of the Netherlands

Module with shared functions

"""

import sys
import os

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
