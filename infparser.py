#!/usr/bin/env python3

# Standard python modules
import os

# Local modules
from   debug      import *
import globals    as     gbl
from   dscparser  import DSCParser
from   uefiparser import UEFIParser

# Class for handling UEFI INF files
class INFParser(UEFIParser):
    # Section Arguments    R/O             List              Names
    Argsbinaries       = ('RR O O O O',   'BINARIES',       ['kind', 'path', 'tag1', 'tag2', 'tag3', 'tag4'])
    ArgsBuildOptions   = (' ORO',         'BUILDOPTIONS',   ['tag', 'option', 'value'])
    ArgsDefines        = ('RO',           'DEFINES',        ['macro', 'value'])
    ArgsDepEx          = ('R',            'DEPEX',          ['depex'])
    ArgsFeaturePcd     = ('RR O O',       'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'featureflagexpression'])
    ArgsFixedPcd       = ('RR O O',       'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'featureflagexpression'])
    ArgsGuids          = ('R X',          'GUIDS',          ['guid'])
    ArgsIncludes       = ('R',            'INCLUDES',       ['include'])
    ArgsLibraryClasses = ('R O',          'LIBRARYCLASSES', ['name', 'path'])
    ArgsPackages       = ('R',            'PACKAGES',       ['path'])
    ArgsPatchPcd       = ('RR O O',       'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'featureflagexpression'])
    ArgsPcd            = ('RR O O',       'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'featureflagexpression'])
    ArgsPcdEx          = ('RR O O',       'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'featureflagexpression'])
    ArgsPpis           = ('R X',          'PPIS',           ['ppi'])
    ArgsProtocols      = ('R   OOO',      'PROTOCOLS',      ['protocol', 'not', 'pcdtokenspaceguidname', 'pcdname'])
    ArgsSources        = ('ROOOOOOO',     'SOURCES',        ['source', 'source2', 'source3', 'source4', 'source5', 'source6', 'source7', 'source8'])
    ArgsUserExtensions = ('R',            'USEREXTENSIONS', ['ext'])
    #                Section                  Debug                 regEx(s)               Arguments
    INFSections = { 'binaries':              (SHOW_BINARIES,       'reBinariesBar',        Argsbinaries),
                    'buildoptions':          (SHOW_BUILDOPTIONS,   'reBuildOptions',       ArgsBuildOptions),
                    'defines':               (SHOW_DEFINES,        'reDefines',            ArgsDefines),
                    'depex':                 (SHOW_DEPEX,          'reDepex',              ArgsDepEx),
                    'featurepcd':            (SHOW_PCDS,           'rePcdOvr',             ArgsFeaturePcd),
                    'fixedpcd':              (SHOW_PCDS,           'rePcdOvr',             ArgsFixedPcd),
                    'guids':                 (SHOW_GUIDS,          'reGuids',              ArgsGuids),
                    'includes':              (SHOW_INCLUDES,       'reIncludes',           ArgsIncludes),
                    'libraryclasses':        (SHOW_LIBRARYCLASSES, 'reLibraryClasses',     ArgsLibraryClasses),
                    'packages':              (SHOW_PACKAGES,       'rePackages',           ArgsPackages),
                    'patchpcd':              (SHOW_PCDS,           'rePcdOvr',             ArgsPatchPcd),
                    'pcd':                   (SHOW_PCDS,           'rePcdOvr',             ArgsPcd),
                    'pcdex':                 (SHOW_PCDS,           'rePcdOvr',             ArgsPcdEx),
                    'ppis':                  (SHOW_PPIS,           'rePpis',               ArgsPpis),
                    'protocols':             (SHOW_PROTOCOLS,      'reProtocolsBar',       ArgsProtocols),
                    'sources':               (SHOW_SOURCES,        'reSources',            ArgsSources),
                    'userextensions':        (SHOW_USEREXTENSIONS, 'reUserExtensions',     ArgsUserExtensions),
    }

    # Items defined in the [Defines] section of an INF file (because these are all caps they will show up in dump)
    INFDefines = [
        "BASE_NAME",     "CONSTRUCTOR",              "DESTRUCTOR",  "EDK_RELEASE_VERSION",       "EFI_SPECIFICATION_VERSION",
        "ENTRY_POINT",   "FILE_GUID",                "INF_VERSION", "LIBRARY_CLASS",             "MODULE_UNI_FILE",
        "PCD_IS_DRIVER", "PI_SPECIFICATION_VERSION", "MODULE_TYPE", "UEFI_HII_RESOURCE_SECTION", "UEFI_SPECIFICATION_VERSION",
        "UNLOAD_IMAGE",  "VERSION_STRING",
    ]

    # Constructor
    # fileName:         File to parse
    # referenceName:    Name of file referencing the INF
    # referenceLine:    Line of file referencing the INF
    # returns nothing
    def __init__(self, fileName):
        # Initialize attributes specific to this class (capitalized attributes will be shown when class is dumped)
        self.BINARIES       = []
        self.BUILDOPTIONS   = []
        self.DEFINES        = []
        self.DEPEX          = []
        self.PCDS           = []
        self.GUIDS          = []
        self.INCLUDES       = []
        self.LIBRARYCLASSES = []
        self.PACKAGES       = []
        self.PPIS           = []
        self.PROTOCOLS      = []
        self.SOURCES        = []
        self.USEREXTENSIONS = []
        # Call constructor for parent class
        super().__init__(fileName, self.INFSections)

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
    # None

    ##################
    # Match handlers #
    ##################

    # Handle a match in the [Ppis] section for rePpis
    # match: Results of regex match
    # returns nothing
    def match_reGuids(self, match):
        guid = match.group(1)
        gbl.ReferenceGuid(guid, gbl.Guids, self.fileName, self.lineNumber)

    # Handle a match in the [Pcds] section for rePcdOvr
    # match: Results of regex match
    # returns nothing
    def match_rePcdOvr(self, match):
        gbl.ReferencePCD(match.group(1), match.group(2), self.fileName, self.lineNumber)

    # Handle a match in the [Packages] section for rePackages
    # match: Results of regex match
    # returns nothing
    def match_rePackages(self, match):
        DSCParser.match_rePackages(self, match)

    # Handle a match in the [Ppis] section for rePpis
    # match: Results of regex match
    # returns nothing
    def match_rePpis(self, match):
        ppi = match.group(1)
        gbl.ReferenceGuid(ppi, gbl.Ppis, self.fileName, self.lineNumber)

    # Handle a match in the [Ppis] section for rePpis
    # match: Results of regex match
    # returns nothing
    def match_reProtocolsBar(self, match):
        protocol = match.group(1)
        gbl.ReferenceGuid(protocol, gbl.Protocols, self.fileName, self.lineNumber)

    # Handle a match in the [Sources] section for rePackages
    # match: Results of regex match
    # returns nothing
    def match_reSources(self, match):
        def AddSource(file):
            path = os.path.join(os.path.dirname(self.fileName), file).replace('\\', '/')
            gbl.ReferenceSource(path, self.fileName, self.lineNumber)
        files = match.group(1)
        if '|' in files:
            AddSource(files.split('|')[0].lstrip())
        else:
            for file in files.split(' '):
                AddSource(file)

    #################
    # Dump handlers #
    #################

    # Dump [Binaries] section
    def DumpBINARIES(self):
        if bool(self.BINARIES):
            print('    Binaries:')
            for i, item in enumerate(self.BINARIES):
                values = []
                for field in ['tag1', 'tag2', 'tag3', 'tag4']:
                    values.append(eval("'' if not '{field}' in item else '|' + item['{field}']"))
                print(f"        {i}:{item['type']}.{gbl.FixUndefined(item['path'])}{values[0]}{values[1]}{values[2]}{values[3]}")

    # Dump [BuildOptions] section
    def DumpBUILDOPTIONS(self):
        DSCParser.DumpBUILDOPTIONS(self)

    # Dump [Defines] section
    def DumpDEFINES(self):
        DSCParser.DumpDEFINES(self)

    # Dump [DepEx] section
    def DumpDEPEX(self):
        if bool(self.DEPEX):
            depex = ''
            for i, item in enumerate(self.DEPEX):
                items = item['depex'].split()
                depex += ' '.join(items) + ' '
            print(f"    DepEx: {depex.rstrip()}")

    # Dump [Guids] section
    def DumpGUIDS(self):
        UEFIParser.DumpSingle(self, self.GUIDS, 'GUIDs', 'guid')

    # Dump [Includes] section
    def DumpINCLUDES(self):
        UEFIParser.DumpSingle(self, self.INCLUDES, 'Includes', 'include', True)

    # Dump [LibraryClasses] section
    def DumpLIBRARYCLASSES(self):
        DSCParser.DumpLIBRARYCLASSES(self)

    # Dump [Packages] section
    def DumpPACKAGES(self):
        UEFIParser.DumpSingle(self, self.PACKAGES, 'Packages', 'path', True)

    # Dump [*Pcd*] sections
    def DumpPCDS(self):
        DSCParser.DumpPCDS(self)

    # Dump [Ppis] section
    def DumpPPIS(self):
        UEFIParser.DumpSingle(self, self.PPIS, 'PPIs', 'ppi')

    # Dump [Protocols] section
    def DumpPROTOCOLS(self):
        if bool(self.PROTOCOLS):
            print('    Protocols:')
            for i, item in enumerate(self.PROTOCOLS):
                inv     = '' if not 'not'                   in item else ' not'
                space   = '' if not 'pcdtokenspaceguidname' in item else ' ' + item['pcdtokenspaceguidname']
                pcdname = '' if not 'pcdname'               in item else '.' + item['pcdname']
                print(f"        {i}:{item['protocol']}{inv}{space}{pcdname}")

    # Dump [Sources] section
    def DumpSOURCES(self):
        if bool(self.SOURCES):
            print('    Sources:')
            for i, item in enumerate(self.SOURCES):
                values = []
                for field in ['source2', 'source3', 'source4', 'source5', 'source6', 'source7', 'source8']:
                    values.append(eval("'' if not '{field}' in item else '|' + item['{field}']"))
                print(f"        {i}:{item['source']}{values[0]}{values[1]}{values[2]}{values[3]}{values[4]}{values[5]}{values[6]}")

    # Dump [UserExtensions] section
    def DumpUSEREXTENSIONS(self):
        DSCParser.DumpUSEREXTENSIONS(self)
