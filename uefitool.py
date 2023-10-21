#!/usr/bin/env python3

# Standard python modules
import os

# Local modules
import globals      as gbl
from   commandline  import ProcessCommandLine
from   platforminfo import PlatformInfo

################
# Main Program #
################
ProcessCommandLine()
platform = os.getcwd() if not gbl.CommandLineResults.path else gbl.CommandLineResults.path
print(f'HPE Platform Directory: {platform}')
PlatformInfo(platform.replace('\\', '/'))

###########
### TBD ###
###########
# - Cross-reference items to make sure things are consistent
# - Right now assumes build with DEBUG ... need non-DEBUG option as well.
# - Generate list of addresses.
# - Fully check syntax of files ... right now syntax is assumed to be OK.
# - Generate dependency list/chains for each inf.
# - Fix macro definitions and evaluation (needs to be section, then file, then global)
# - What other useful output could be generated?

# Other ideas
# - Tool that interfaces with data generated here that processes log files and converts GUIDs to actual human readable names.
# - Tool that can compare two log files ignoring differences where drivers or resources are loaded at different addresses.
