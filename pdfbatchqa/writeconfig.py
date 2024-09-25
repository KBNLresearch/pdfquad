#! /usr/bin/env python3

"""Write configuration file
"""

import os
import platform

def writeConfigFile(configFile):
    """Create default configuration file"""

    configDir = os.path.dirname(configFile)
    fName =  os.path.basename(configFile)

    # Create configuration directory if it doesn't exist already
    if not os.path.isdir(configDir):
        os.mkdir(configDir)

    # Path to configuration file
    fConfig = os.path.join(configDir, fName)

    # Generate string with config settings. This is platform-dependent,
    # so first get the platform
    myPlatform = platform.system()

    if myPlatform == "Windows":
        # Paths will need manual editing, because this is not standardized
        configString = '# settings pdfbatchqa\n'
        configString += 'profile = dbnl-fulltext.xml\n'
        configString += 'prefix = pdfbatchqa\n'
        configString += 'pdfimages = C:\\poppler-24.07.0\\Library\\bin\\pdfimages.exe # pdfimages executable # pdfimages executable\n'
        configString += 'pdfinfo = C:\\poppler-24.07.0\\Library\\bin\\pdfinfo.exe # pdfinfo executable\n'
        configString += 'exiftool = C:\\exiftool\\exiftool.exe # exiftool executable\n'
    else:
        # This works on Linux, and probably MacOS as well
        configString = '# settings pdfbatchqa\n'
        configString += 'profile = dbnl-fulltext.xml\n'
        configString += 'prefix = pdfbatchqa\n'
        configString += 'pdfimages = pdfimages # pdfimages executable\n'
        configString += 'pdfinfo = pdfinfo # pdfinfo executable\n'
        configString += 'exiftool = exiftool # exiftool executable\n'

    # Write string to configuration file
    with open(fConfig,"wb") as f:
        f.write(configString.encode('utf-8'))
    