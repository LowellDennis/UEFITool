#!/usr/bin/env python

# Standard python modules
# None

# Local modules
from   debug      import *
import globals    as     gbl
from   uefiparser import UEFIParser

# Class for handling UEFI DSC files
class DSCParser(UEFIParser):
    # Section Arguments         R/O              List              Names
    ArgsBuildOptions          = (' ORO',         'BUILDOPTIONS',   ['tag', 'option', 'value'])
    ArgsComponents            = ('R',            'COMPONENTS',     ['inf'])
    ArgsDefaultStores         = ('R R',          'DEFAULTSTORES',  ['value', 'name'])
    ArgsDefines               = [('RO',          'DEFINES',        ['macro', 'value']),     # reDefines
                                 ('ORO',         'DEFINES',        ['macro', 'value'])]     # reEdkGlobals
    ArgsLibraryClasses        = ('R R',          'LIBRARYCLASSES', ['name', 'path'])
    ArgsPcdsDynamic           = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsDynamicDefault    = ('RR R O X X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsDynamicEx         = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsDynamicExDefault  = ('RR O O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsDynamicExHii      = ('RR R R R O O', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'variablename', 'variableguid', 'variableoffset', 'hiidefaultvalue', 'hiiattribute'])
    ArgsPcdsDynamicExVpd      = ('RR R O O X X', 'PCDS',           gbl.GetVpdOptionNames)
    ArgsPcdsDynamicHii        = ('RR R R R O O', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'variablename', 'variableguid', 'variableoffset', 'hiidefaultvalue'])
    ArgsPcdsDynamicVpd        = ('RR R O O X X', 'PCDS',           gbl.GetVpdOptionNames)
    ArgsPcdsFeatureFlag       = ('RR O X X X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value'])
    ArgsPcdsFixedatBuild      = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdsPatchableInModule = ('RR R O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsSkuIds                = ('RRO',          'SKUIDS',         ['value', 'skuid', 'parent'])
    ArgsUserExtensions        = ('R',            'USEREXTENSIONS', ['ext'])
    #                Section                  Debug                 regEx(s)                      Arguments
    DSCSections = { 'buildoptions':          (SHOW_BUILDOPTIONS,   'reBuildOptions',              ArgsBuildOptions),
                    'components':            (SHOW_COMPONENTS,     'reComponents',                ArgsComponents),
                    'defaultstores':         (SHOW_DEFAULTSTORES,  'reDefaultStores',             ArgsDefaultStores),
                    'defines':               (SHOW_DEFINES,        ['reDefines', 'reEdkGlobals'], ArgsDefines),
                    'libraryclasses':        (SHOW_LIBRARYCLASSES, 'reLibraryClasses',            ArgsLibraryClasses),
                    'pcdsdynamic':           (SHOW_PCDS,           'rePcds',                      ArgsPcdsDynamic),
                    'pcdsdynamicdefault':    (SHOW_PCDS,           'rePcds',                      ArgsPcdsDynamicDefault),
                    'pcdsdynamicex':         (SHOW_PCDS,           'rePcds',                      ArgsPcdsDynamicEx),
                    'pcdsdynamicexdefault':  (SHOW_PCDS,           'rePcds',                      ArgsPcdsDynamicExDefault),
                    'pcdsdynamicexhii':      (SHOW_PCDS,           'rePcds',                      ArgsPcdsDynamicExHii),
                    'pcdsdynamicexvpd':      (SHOW_PCDS,           'rePcds',                      ArgsPcdsDynamicExVpd),
                    'pcdsdynamichii':        (SHOW_PCDS,           'rePcds',                      ArgsPcdsDynamicHii),
                    'pcdsdynamicvpd':        (SHOW_PCDS,           'rePcds',                      ArgsPcdsDynamicVpd),
                    'pcdsfeatureflag':       (SHOW_PCDS,           'rePcds',                      ArgsPcdsFeatureFlag),
                    'pcdsfixedatbuild':      (SHOW_PCDS,           'rePcds',                      ArgsPcdsFixedatBuild),
                    'pcdspatchableinmodule': (SHOW_PCDS,           'rePcds',                      ArgsPcdsPatchableInModule),
                    'skuids':                (SHOW_SKUIDS,         'reSkuIds',                    ArgsSkuIds),
                    'userextensions':        (SHOW_USEREXTENSIONS, 'reUserExtensions',            ArgsUserExtensions),
    }

    # Constructor
    # sections: Starting sections (default is [] for None)
    # process:  Starting conditional processing state (default is True)
    # outside:  Function for handling lines outside of sections (default is None)
    # returns nothing
    def __init__(self, fileName, sections = [], process = True, outside = None):
        # Initialize attributes specific to this class (capitalized attributes will be shown when class is dumped)
        self.BUILDOPTIONS   = []
        self.COMPONENTS     = []
        self.DEFAULTSTORES  = []
        self.DEFINES        = []
        self.LIBRARYCLASSES = []
        self.PCDS           = []
        self.SKUIDS         = []
        self.USEREXTENSIONS = []
        # Call constructor for parent class
        super().__init__(fileName, self.DSCSections, True, True, ['error'], sections, process, outside)

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

    def macro_SUPPORTED_ARCHITECTURES(self, value):
        SupportedArchitectures = value.upper().replace('"', '').split("|")
        if Debug(SHOW_SPECIAL_HANDLERS):
            print(f"{self.lineNumber}: Limiting architectires to {','.join(SupportedArchitectures)}")

    ######################
    # Directive handlers #
    ######################

    # Handle the Error directive
    # message: Error message
    # returns nothing
    def directive_error(self, message):
        # Display error message (if currently processsing)
        if Debug(SHOW_ERROR_DIRECT1VE):
            print(f"{self.lineNumber}:error {message}")
        if self.process:
            self.ReportError(f"error({message})")

    # Handle the Include directive
    # includeFile: File to be included
    # returns nothing
    def directive_include(self, includeFile):
        def includeDSCFile(file):
            gbl.AddReference(file, self.fileName, self.lineNumber)      # Indicate reference to included file
            if file in gbl.DSCs and gbl.DSCs[file].macroVer == gbl.MacroVer:
                    if Debug(SHOW_SKIPPED_DSCS):
                        print(f"{self.lineNumber}:Previously loaded:{file}")
            else:
                gbl.DSCs[file] = DSCParser(file, self.sections, self.process)
        self.IncludeFile(includeFile, includeDSCFile)

    ####################
    # Section handlers #
    ####################
    # None

    ##################
    # Match handlers #
    ##################

    # Handle a match in the [BuildOptions] section
    # match: Results of regex match
    # returns nothing
    def match_reBuildOptions(self, match):
        # Look for line continuation character
        if match.group(5):
            self.lineContinuation = True

    # Handle a match in the [Components] section
    # match: Results of regex match
    # returns nothing
    def match_reComponents(self, match):
        # Look for sub-element entry
        if match.group(3) and match.group(3) == '{':
            self.EnterSubElement()  # Defaults are fine

    # Handle a match in the [Defines] section for reDefines
    # match: Results of regex match
    # returns nothing
    def match_reDefines(self, match):
        macro, value = (match.group(1), match.group(2))
        self.DefineMacro(macro, value if value != None else '')

    # Handle a match in the [Defines] section for reEdkGlobal
    # match: Results of regex match
    # returns nothing
    def match_reEdkGlobal(self, match):
        macro, value = (match.group(2), match.group(3))
        self.DefineMacro(macro, value if value != None else '')

    # Handle a match in the [libraryclasses] section for reLibraryClasses
    # match: Results of regex match
    # returns nothing
    def match_reLibraryClasses(self, match):
        file = match.group(3).replace('"', '')
        gbl.AddReference(file, self.fileName, self.lineNumber)      # Indicate reference to INF file
        gbl.INFs.append(file)

    # Handle a match in one of the PCD sections
    # match: Results of regex match
    # returns nothing
    def match_rePcds(self, match):
        # Only process below if this matches a PCD default override
        for i in range(1,13):
            if (i < 5 and match.group(i) == None) or (i > 8 and not match.group(i) == None):
                return
        gbl.Pcds['dsc'][match.group(1)+'.'+match.group(2)] = (match.group(4), match.group(6), match.group(8))

    #################
    # Dump handlers #
    #################

    # Dump [BuildOptions] section
    def DumpBUILDOPTIONS(self):
        if bool(self.BUILDOPTIONS):
            print('    BuildOptions:')
            for i, item in enumerate(self.BUILDOPTIONS):
                tag   = '' if not 'tag'   in item else item['tag'] + ':'
                value = '' if not 'value' in item else '=' + gbl.FixUndefined(item['value'])
                print(f"        {i}:{tag}{item['option']}{value}")

    # Dump [Components] section
    def DumpCOMPONENTS(self):
        UEFIParser.DumpSingle(self, self.COMPONENTS, 'Components', 'inf', True)

    # Dump [DefaultStores] section
    def DumpDEFAULTSTORES(self):
        if bool(self.DEFAULTSTORES):
            print('    DefaultStores:')
            for i, item in enumerate(self.DEFAULTSTORES):
                print(f"        {i}:{item['value']}|{item['name']}")

    # Dump [Defines] section
    def DumpDEFINES(self):
        if bool(self.DEFINES):
            print('    Defines:')
            for i, item in enumerate(self.DEFINES):
                value = '' if item['value'] == None else gbl.FixUndefined(item['value'])
                print(f"        {i}:{item['macro']}={value}")

    # Dump [LibraryClasses] section
    def DumpLIBRARYCLASSES(self):
        if bool(self.LIBRARYCLASSES):
            print('    LibraryClasses:')
            for i, item in enumerate(self.LIBRARYCLASSES):
                print(f"        {i}:{item['name']}|{gbl.FixUndefined(item['path'])}")

    # Dump [Pcds*] sections
    def DumpPCDS(self):
        if bool(self.PCDS):
            print('    Pcds:')
            for i, item in enumerate(self.PCDS):
                # There are a couple of possibilities here
                values = []
                if 'value' in item:
                    for field in ['value', 'datumtype', 'maximumdatumsize']:
                        values.append(eval("'' if not '{field}' in item else '|' + item['{field}']"))
                    print(f"        {i}:{item['pcdtokenspaceguidname']}.{item['pcdname']}{values[0]}{values[1]}{values[2]}")
                else:
                    for field in ['variableName', 'variableGuid', 'variableOffset', 'hiiDefaultValue', 'hiiAttribute']:
                        values.append(eval("'' if not '{field}' in item else '|' + item['{field}']"))
                    print(f"        {i}:{item['pcdtokenspaceguidname']}.{item['pcdname']}{values[0]}{values[1]}{values[2]}{values[3]}{values[4]}")

    # Dump [SkuIds] section
    def DumpSKUIDS(self):
        if bool(self.SKUIDS):
            print('    SkuIds:')
            for i, item in enumerate(self.SKUIDS):
                parent = '' if not 'parent' in item else '|' + item['parent']
                print(f"        {i}:{item['value']}|{item['skuid']}{parent}")

    # Dump [UserExtensions] section
    def DumpUSEREXTENSIONS(self):
        UEFIParser.DumpSingle(self, self.USEREXTENSIONS, 'UserExtensions', 'ext')

