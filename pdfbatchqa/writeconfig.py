#! /usr/bin/env python3

"""Write configuration file
"""

import os

def writeConfigFile(configFile):
    """Create default configuration file"""

    configDir = os.path.dirname(configFile)
    fName =  os.path.basename(configFile)

    # Create configuration directory if it doesn't exist already
    if not os.path.isdir(configDir):
        os.mkdir(configDir)

    # Path to configuration file
    fConfig = os.path.join(configDir, fName)

    # Generate string with config settings.

    # Paths will need manual editing, because this is not standardized
    configString = '# settings pdfbatchqa\n'
    configString += 'profile = dbnl-fulltext.xml\n'
    configString += 'prefix = pdfbatchqa\n'

    # Write string to configuration file
    with open(fConfig,"wb") as f:
        f.write(configString.encode('utf-8'))
    