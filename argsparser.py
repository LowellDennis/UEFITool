#!/usr/bin/env python3

# Standard python modules
import os

# Local modules
from   debug         import *
import globals       as     gbl
from   uefiparser    import UEFIParser

# Class for parsing HPE Build Args files (PlatformPkgBuildArgs.txt)
class ArgsParser(UEFIParser):
    # Section Arguments            R/O        List                    Names
    ArgsEnvironmentVariables    = ('R O',    'ENVIRONMENTVARIABLES', ['variable', 'value'])
    ArgsHpbuildArgs             = (' R O O', 'HPBUILDARGS',          ['option',   'arg',  'value'])
    ArgsPythonBuildfailScripts  = ('RRO',    'PYTHONSCRIPTS',        ['pyfile',   'func', 'args'])
    ArgsPythonPrebuildScripts   = ('RRO',    'PYTHONSCRIPTS',        ['pyfile',   'func', 'args'])
    ArgsPythonPreHpbuildScripts = ('RRO',    'PYTHONSCRIPTS',        ['pyfile',   'func', 'args'])
    ArgsPythonPostbuildScripts  = ('RRO',    'PYTHONSCRIPTS',        ['pyfile',   'func', 'args'])
    #                      Section                    Debug                       regEx(s)                 Arguments
    BuildArgsSections = { 'environmentvariables':    (SHOW_ENVIRONMENTVARIABLES, 'reEnvironmentVariables', ArgsEnvironmentVariables),
                          'hpbuildargs':             (SHOW_HPBUILDARGS,          'reHpBuildArgs',          ArgsHpbuildArgs),
                          'pythonbuildfailscripts':  (SHOW_PYTHONSCRIPTS,        'rePythonScripts',        ArgsPythonBuildfailScripts),
                          'pythonprebuildscripts':   (SHOW_PYTHONSCRIPTS,        'rePythonScripts',        ArgsPythonPrebuildScripts),
                          'pythonprehpbuildscripts': (SHOW_PYTHONSCRIPTS,        'rePythonScripts',        ArgsPythonPreHpbuildScripts),
                          'pythonpostbuildscripts':  (SHOW_PYTHONSCRIPTS,        'rePythonScripts',        ArgsPythonPostbuildScripts),
    }

    # Class constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        # Initialize attributes specific to this class (capitalized attributes will be shown when class is dumped)
        self.ENVIRONMENTVARIABLES = []
        self.HPBUILDARGS          = []
        self.PYTHONSCRIPTS        = []
        # Call constructor for parent class
        super().__init__(fileName, self.BuildArgsSections, True)

    ###################
    # Private methods #
    ###################
    # None

    ##################
    # Public methods #
    ##################
    # None

    ####################
    # Special handlers #
    ####################
    # None

    ######################
    # Directive handlers #
    ######################

    # Handle the Include directive
    # line: File to be included
    # returns nothing
    def directive_include(self, line):
        def includeHandler(file):
            gbl.AddReference(file, self.fileName, self.lineNumber)     # Indicate reference to included file
            gbl.ARGs[file] = ChipsetParser(file)
        self.IncludeFile(line, includeHandler)

    ####################
    # Section handlers #
    ####################
    #None
        
    ##################
    # Match handlers #
    ##################

    # Handle a match in the [EnvironmentVariables] section
    # match: Results of regex match
    # returns nothing
    def match_reEnvironmentVariables(self, match):
        variable = match.group(1)
        value    = match.group(3) if match.group(3) != None else ''
        self.DefineMacro(variable, value.replace('\\', '/'))
        os.environ[variable] = value

    # Handle a match in the [HpBuildArgs] section
    # match: Results of regex match
    # returns nothing
    def match_reHpBuildArgs(self, match):
        # Only care about things that are being defined using the -D option
        if match.group(2) == '-D':
            macro = match.group(4)
            if not macro:
                self.ReportError(f'Unsupported -D line in HpBuildArgs section {match.group(0)}')
                return
            value = match.group(6) if match.group(6) != None else ''
            self.DefineMacro(macro, value)

    #################
    # Dump handlers #
    #################

    # Dump [EnvironmentVariables] section
    def DumpENVIRONMENTVARIABLES(self):
        if bool(self.ENVIRONMENTVARIABLES):
            print('    EnvironmentVariables:')
            for i, item in enumerate(self.ENVIRONMENTVARIABLES):
                value = '' if not 'value' in item else gbl.FixUndefined(item['value'])
                print(f"        {i}:{item['variable']}={value}")

    # Dump [HpBuildArgs] section
    def DumpHPBUILDARGS(self):
        if bool(self.HPBUILDARGS):
            print('    HpBuildArgs:')
            for i, item in enumerate(self.HPBUILDARGS):
                arg   = '' if not 'arg'   in item else  ' ' + item['arg']
                value = '' if not 'value' in item else  '=' + gbl.FixUndefined(item['value'])
                print(f"        {i}:{item['option']}{arg}{value}")

    # Dump [*PythonScripts] sections
    def DumpPYTHONSCRIPTS(self):
        if bool(self.PYTHONSCRIPTS):
            print('    PythonScripts:')
            for i, item in enumerate(self.PYTHONSCRIPTS):
                args  = '' if not 'args'  in item else  gbl.FixUndefined(item['args'])
                print(f"        {i}:{gbl.FixUndefined(item['pyfile'])}:{item['func']}({args})")

# Class for parsing HPE Chipset files (HpChipsetInfo.txt)
class ChipsetParser(UEFIParser):
    # Section Arguments     R/O        List                Names
    ArgsBinaries         = ('RR',     'BINARIES',         ['binary',  'path'])
    ArgsHBbuildArgs      = (' R O O', 'HPBUILDARGS',      ['option',  'arg', 'value'])
    ArgsPlatformPackages = ('R',      'PLATFORMPACKAGES', ['package'])
    ArgsSnaps            = ('RR',     'SNAPS',            ['version', 'snap'])
    ArgsTagExceptions    = ('R',      'TAGEXCEPTIONS',    ['tag'])
    ArgsuPatches         = ('RR',     'UPATCHES',         ['patch',   'name'])
    #                    Section             Debug                   regEx(s)             Arguments
    ChipsetSections = { 'binaries':         (SHOW_BINARIES,         'reBinariesEqu',      ArgsBinaries),
                        'hpbuildargs':      (SHOW_HPBUILDARGS,      'reHpBuildArgs',      ArgsHBbuildArgs),
                        'platformpackages': (SHOW_PLATFORMPACKAGES, 'rePlatformPackages', ArgsPlatformPackages),
                        'snaps':            (SHOW_SNAPS,            'reSnaps',            ArgsSnaps),
                        'tagexceptions':    (SHOW_TAGEXCEPTIONS,    'reTagExceptions',    ArgsTagExceptions),
                        'upatches':         (SHOW_UPATCHES,         'reuPatches',         ArgsuPatches),
    }

    # Class constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        # Initialize attributes specific to this class (capitalized attributes will be shown when class is dumped)
        self.BINARIES         = []
        self.HPBUILDARGS      = []
        self.PLATFORMPACKAGES = []
        self.SNAPS            = []
        self.TAGEXCEPTIONS    = []
        self.UPATCHES         = []
        # Call constructor for parent class
        super().__init__(fileName, self.ChipsetSections)

    ###################
    # Private methods #
    ###################
    # None

    ##################
    # Public methods #
    ##################
    # None

    ####################
    # Special handlers #
    ####################
    # None

    ######################
    # Directive handlers #
    ######################
    # None

    ####################
    # Section handlers #
    ####################
    #None
        
    ##################
    # Match handlers #
    ##################

    # Handle a match in the [HpBuildArgs] section
    # match: Results of regex match
    # returns nothing
    def match_reHpBuildArgs(self, match):
        ArgsParser.match_reHpBuildArgs(self, match)

    #################
    # Dump handlers #
    #################

    # Dump [Binaries] section
    def DumpBINARIES(self):
        if bool(self.BINARIES):
            print('    Binaries:')
            for i, item in enumerate(self.BINARIES):
                print(f"        {i}:{item['binary']} {gbl.FixUndefined(item['path'])}")

    # Dump [HpBuildArgs] section
    def DumpHPBUILDARGS(self):
        ArgsParser.DumpHPBUILDARGS(self)

    # Dump [PlatformPackages] section
    def DumpPLATFORMPACKAGES(self):
        if bool(self.PLATFORMPACKAGES):
            print('    PlatformPkgs:')
            for i, item in enumerate(self.PLATFORMPACKAGES):
                print(f"        {i}:{gbl.FixUndefined(item['package'])}")

    # Dump [Snaps] section
    def DumpSNAPS(self):
        if bool(self.SNAPS):
            print('    Snaps:')
            for i, item in enumerate(self.SNAPS):
                print(f"        {i}:{item['version']}={item['snap']}")

    # Dump [TagExceptions] section
    def DumpTAGEXCEPTIONS(self):
        UEFIParser.DumpSingle(self, self.TAGEXCEPTIONS, 'TagExceptions', 'tag')

    # Dump [uPatches] section
    def DumpUPATCHES(self):
        if bool(self.UPATCHES):
            print('    uPatches:')
            for i, item in enumerate(self.UPATCHES):
                print(f"        {i}:{item['patch']} {item['name']}")
