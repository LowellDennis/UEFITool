#!/usr/bin/env python

# Standard python modules
# None

# Local modules
from   debug      import *
import globals    as     gbl
from   uefiparser import UEFIParser
from   dscparser  import DSCParser

# Class for handling UEFI DEC files
class DECParser(UEFIParser):
    # Section Arguments          R/O             List              Names
    ArgsDefines               = ('RO',           'DEFINES',        ['macro', 'value'])
    ArgsGuids                 = ('R R',          'GUIDS',          ['guid'])
    ArgsIncludes              = ('R',            'INCLUDES',       ['include'])
    ArgsLibraryClasses        = ('R R',          'LIBRARYCLASSES', ['name', 'path'])
    ArgsPcdsDynamic           = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsDynamicEx         = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsFeatureFlag       = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsFixedatBuild      = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsPatchableInModule = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPpis                  = ('R R',          'PPIS',           ['ppi'])
    ArgsProtocols             = ('R R',          'PROTOCOLS',      ['protocol'])
    ArgsUserExtensions        = ('R',            'USEREXTENSIONS', ['ext'])
    ArgsPackages              = ('R',            'PACKAGES',       ['path'])
    ArgsHeaderFiles           = ('R',            'HEADERFILES',    ['path'])
    #                Section                  Debug                 regEx(s)               Arguments
    DECSections = { 'defines':               (SHOW_DEFINES,        'reDefines',            ArgsDefines),
                    'guids':                 (SHOW_GUIDS,          'reGuids',              ArgsGuids),
                    'includes':              (SHOW_INCLUDES,       'reIncludes',           ArgsIncludes),
                    'libraryclasses':        (SHOW_LIBRARYCLASSES, 'reLibraryClasses',     ArgsLibraryClasses),
                    'pcdsdynamic':           (SHOW_PCDS,           'rePcds',               ArgsPcdsDynamic),
                    'pcdsdynamicex':         (SHOW_PCDS,           'rePcds',               ArgsPcdsDynamicEx),
                    'pcdsfeatureflag':       (SHOW_PCDS,           'rePcds',               ArgsPcdsFeatureFlag),
                    'pcdsfixedatbuild':      (SHOW_PCDS,           'rePcds',               ArgsPcdsFixedatBuild),
                    'pcdspatchableinmodule': (SHOW_PCDS,           'rePcds',               ArgsPcdsPatchableInModule),
                    'ppis':                  (SHOW_PPIS,           'rePpis',               ArgsPpis),
                    'protocols':             (SHOW_PROTOCOLS,      'reProtocolsEqu',       ArgsProtocols),
                    'userextensions':        (SHOW_USEREXTENSIONS, 'reUserExtensions',     ArgsUserExtensions),
                    # Below are special section handlers that can only occur when processing a sub-element!
                    'packages':              (SHOW_PACKAGES,       'rePackages',           ArgsPackages),
                    'headerfiles':           (SHOW_HEADERFILES,    'reHeaderFiles',        ArgsHeaderFiles),
    }

    # Constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        # Initialize attributes specific to this class (capitalized attributes will be shown when class is dumped)
        self.DEFINES        = []
        self.GUIDS          = []
        self.INCLUDES       = []
        self.LIBRARYCLASSES = []
        self.PCDS           = []
        self.PPIS           = []
        self.PROTOCOLS      = []
        self.USEREXTENSIONS = []
        self.PACKAGES       = []
        self.HEADERFILES    = []
        # Call constructor for parent class
        super().__init__(fileName, self.DECSections)

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

    # Handle a match in the [Defines] section for reDefines
    # match: Results of regex match
    # returns nothing
    def match_reDefines(self, match):
        DSCParser.match_reDefines(self, match)

    # Handle a match in the [Guids] section
    # match: Results of regex match
    # returns nothing
    def match_reGuids(self, match):
        name = match.group(1)
        guid = match.group(3)
        gbl.Guids[name] = guid              # Overrite OK

    # Handle a match in any of the PCD sections for rePcd
    # match: Results of regex match
    # returns nothing
    def match_rePcds(self, match):
        # See if we need to enter a sub-element
        if match.group(13) and match.group(13) == '{':
            self.EnterSubElement()  # Defaults are fine
        # Only process below if this matches a PCD definition
        for i in range(1,13):
            if (i < 9 and match.group(i) == None) or (i > 8 and not match.group(i) == None):
                return
        gbl.Pcds['dec'][match.group(1)+'.'+match.group(2)] = (match.group(4), match.group(6), match.group(8))

    # Handle a match in the [Ppis] section
    # match: Results of regex match
    # returns nothing
    def match_rePpis(self, match):
        ppi  = match.group(1)
        guid = match.group(3)
        gbl.Ppis[ppi] = guid                # Overrite OK

    # Handle a match in the [Protocols] section
    # match: Results of regex match
    # returns nothing
    def match_reProtocolsEqu(self, match):
        protocol = match.group(1)
        guid     = match.group(3)
        gbl.Protocols[protocol] = guid      # Overrite OK

    ###########################################
    # Match handlers (only when inSubsection) #
    ###########################################

    # Handle a match in the <Packages> sub-element
    # match: Results of regex match
    # returns nothing
    def match_rePackages(self, match):
        # Only allow this section handler if in a sub-element
        if not self.inSubsection:
            self.ReportError('section packages cannot be used outside of braces')
            return
        DSCParser.match_rePackages(self.match)

    # Handle a match in the <HeaderFiles> sub-element
    # match: Results of regex match
    # returns nothing
    def match_reHeaderFiles(self, match):
        # Only allow this section handler if in a sub-element
        if not self.inSubsection:
            self.ReportError('section headerfiles cannot be used outside of braces')

    #################
    # Dump handlers #
    #################

    # Dump [Defines] section
    def DumpDEFINES(self):
        DSCParser.DumpDEFINES(self)

    # Dump [Guids] section
    def DumpGUIDS(self):
        UEFIParser.DumpSingle(self, self.GUIDS, 'GUIDs', 'guid')

    # Dump [Includes] section
    def DumpINCLUDES(self):
        UEFIParser.DumpSingle(self, self.INCLUDES, 'Includes', 'include', True)

    # Dump [LibraryClasses] section
    def DumpLIBRARYCLASSES(self):
        DSCParser.DumpLIBRARYCLASSES(self)

    # Dump [Ppis] section
    def DumpPPIS(self):
        UEFIParser.DumpSingle(self, self.PPIS, 'PPIs', 'ppi')

    # Dump [Pcd*] sections
    def DumpPCDS(self):
        DSCParser.DumpPCDS(self)

    # Dump [Protocols] section
    def DumpPROTOCOLS(self):
        UEFIParser.DumpSingle(self, self.PROTOCOLS, 'Protocols', 'protocol')

    # Dump [UserExTensions] section
    def DumpUSEREXTENSIONS(self):
        DSCParser.DumpUSEREXTENSIONS(self)

    # Dump <Packeges> sub-element
    def DumpPACKAGES(self):
        UEFIParser.DumpSingle(self, self.PACKAGES, 'Packages', 'path', True)

    # Dump <HeaderFiles> sub-element
    def DumpHEADERFILES(self):
        UEFIParser.DumpSingle(self, self.HEADERFILES, 'HeaderFiles', 'path', True)
