#!/usr/bin/env python3

# Standard python modules
import argparse

# Local modules
from   debug   import *
import globals as     gbl

# Handles command line errors
class CommandLineParser(argparse.ArgumentParser):

  def __init__(self):
        global ProgramVersion
        super().__init__(prefix_chars='-/' if gbl.isWindows else '-', description=f'HPE EDKII UEFI DSC/INF/DEC/FDF Processing Tool: V{gbl.ProgramVersion}')

  def error(self, msg):
      message = self.format_usage() + self.prog + ': error: ' + msg
      gbl.Error(message)
      exit(1)

# This will allow user to input debug level
# as decimal or hexadecimal (with leading 0x)
def auto_int(x):
  ret = int(x, 0)

# Process the command line
#   Initializes command line flags
#   Initializes DebugLevel
# returns nothing
def ProcessCommandLine():
    CommandLine = CommandLineParser()
    # Add ability to get help
    CommandLine.add_argument('-?',
                    action = 'help',
                    help=argparse.SUPPRESS)
    # Add ability to control macro listing
    CommandLine.add_argument('-m', '--macros',
                    action = 'store_true',
                    dest='macros',
                    help='do not generate macro list (macros.lst)')
    # Add ability to control source files listing
    CommandLine.add_argument('-s', '--source',
                    action = 'store_true',
                    dest='sources',
                    help='do not generate source file and references list (source.lst, references.lst)')
    # Add ability to control PCD listing
    CommandLine.add_argument('-p', '--pcds',
                    action = 'store_true',
                    dest='pcds',
                    help='do not generate pcd list (pcd.lst)')
    # Add ability to control apriori listing
    CommandLine.add_argument('-a', '--apriori',
                    action = 'store_true',
                    dest='apriori',
                    help='do not generate apiriori list (apriori.lst)')
    # Add ability to control protocol listing
    CommandLine.add_argument('-i', '--ppis',
                    action = 'store_true',
                    dest='ppis',
                    help='do not generate ppi list (ppis.lst)')
    # Add ability to control protocol listing
    CommandLine.add_argument('-r', '--protocols',
                    action = 'store_true',
                    dest='protocols',
                    help='do not generate protocol list (protocol.lst)')
    # Add ability to control protocol listing
    CommandLine.add_argument('-g', '--guids',
                    action = 'store_true',
                    dest='guids',
                    help='do not generate guid list (guid.lst)')
    # Add ability to control protocol listing
    CommandLine.add_argument('-l', '--libraries',
                    action = 'store_true',
                    dest='libraries',
                    help='do not generate libraries list (libraries.lst)')
    # Add ability to control dump listing
    CommandLine.add_argument('--dump',
                    action = 'store_true',
                    dest='dump',
                    help='dump all file results to screen')
    # Add ability to control debug output
    group = CommandLine.add_mutually_exclusive_group()
    group.add_argument('-n', '--nominal',
                    action = 'store_true',
                    dest='nominal',
                    help='turn on nominal debug output')
    group.add_argument('-t', '--typical',
                    action = 'store_true',
                    dest='typical',
                    help='turn on typical debug output')
    group.add_argument('-v', '--verbose',
                    action = 'store_true',
                    dest='verbose',
                    help='turn on verbose debug output')
    group.add_argument('-f', '--full',
                    action = 'store_true',
                    dest='full',
                    help='turn on full debug output')
    group.add_argument('-d', '--debug',
                    dest='debug',
                    metavar='type',
                    type=auto_int,
                    nargs='*',
                    default=0,
                    help='turn on debug to a specific level (64-bit integer, use 0x prefix to specify in hex)')
    # Add path to platform directory
    CommandLine.add_argument('path',
                    metavar='path',
                    type=str,
                    help='path to platform directory (default is current directory')
    # Parse the command line
    gbl.CommandLineResults = CommandLine.parse_args()
    # Show header
    print(CommandLine.description)
    # Handle results of command line parsing
    if gbl.CommandLineResults.nominal:
        SetDebug(DEBUG_MINIMUM)
    elif gbl.CommandLineResults.typical:
        SetDebug(DEBUG_TYPICAL)
    elif gbl.CommandLineResults.verbose:
        SetDebug(DEBUG_VERBOSE)
    elif gbl.CommandLineResults.full:
        SetDebug(DEBUG_ALL)
    else:
        SetDebug(gbl.CommandLineResults.debug)
