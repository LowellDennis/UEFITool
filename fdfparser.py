#!/usr/bin/env python3

# Standard python modules
import re

# Local modules
from   debug      import *
import globals    as     gbl
from   uefiparser import UEFIParser
from   dscparser  import DSCParser

# Class for an Apriori list
class Apriori:

    # Constructor
    # fileName:   Filename where the list is found
    # lineNumber: Line number where the list starts
    def __init__(self, fileName, lineNumber):
        self._fileName   = fileName
        self._lineNumber = lineNumber
        self._list       = []

    # Add an item to the apriori list
    def Append(self, item):
        self._list.append(item)

    # Getter for fileName property
    def _get_fileName(self):
        return self._fileName

    # Getter for lineNumber property
    def _get_lineNumber(self):
        return self._lineNumber

    # Getter for list property
    def _get_list(self):
        return self._list

    # Define the properties
    fileName   = property(fget = _get_fileName) 
    lineNumber = property(fget = _get_lineNumber) 
    list       = property(fget = _get_list) 

# Class for handling UEFI FDF files
class FDFParser(UEFIParser):   #debug,        regularExpression(s),                    handlerArguments
    # regExLists
    FdRegExes   = ['reDataStart', 'reDataAdd', 'reEndDesc', 'reDefine', 'reDefines', 'reSet', 'reOfsSz']
    FvRegExes   = ['reDefine', 'reSet', 'reDefines', 'reApriori', 'reInf', 'reFile', 'reSection', 'reEndDesc', 'rePath']
    RuleRegExes = ['reRule', 'reExt', 'reVer', 'reCompress', 'reGuided', 'reEndDesc']
    # Sect Args     R/O       List        Names
    ArgsCapsule = [(' RR',   'CAPSULES', ['token', 'value']),   # reSet
                   ('RR',    'CAPSULES', ['token', 'value'])]   # reCapsule
    ArgsDefines = ('RO',     'DEFINES',  ['macro', 'value'])
    ArgsFd      = [('',      None,       None),                 # reDataStart
                   ('R',     None,       None,),                # reDataAdd
                   ('',      None,       None,),                # reEndDesc (for reDataStart)
                   (' RR',   'FDS',      ['token', 'value']),   # reDefine
                   ('RR',    'FDS',      ['token', 'value']),   # reDefines
                   (' RR',   'FDS',      ['token', 'value']),   # reSet
                   ('R R',   'FDS',      ['offset', 'size'])]   # reOfsSz
    ArgsFv      = [(' RR',   'DEFINES',  ['macro', 'value']),   # reDefine
                   (' RR',   'FVS',      ['token', 'value']),   # reSet
                   ('RR',    'FVS',      ['token', 'value']),   # reDefines
                   ('R',     None,       None),                 # reApriori
                   ('O  R',  None,       None),                 # reInf
                   ('RRO',   None,       None),                 # reFile
                   ('R',     None,       None),                 # reSection
                   ('',      None,       None),                 # reEndDesc (for reApriori, reFile, and some reSection)
                   ('R',     None,       None)]                 # rePath
    ArgsRule    = [('RR',    None,       None),                 # reRule
                   ('  RR',  None,       None),                 # reExt
                   ('RR',    None,       None),                 # reVer
                   ('O',     None,       None),                 # reCompress
                   ('O',     None,       None),                 # reGuided
                   ('',      None,       None)]                 # reEndDesc
    #                Section    Debug          regEx(s)               Arguments
    FDFSections = { 'capsule': (SHOW_CAPSULE, ['reSet', 'reCapsule'], ArgsCapsule),
                    'defines': (SHOW_FD,      'reDefines',            ArgsDefines),
                    'fd':      (SHOW_FD,      FdRegExes,              ArgsFd),
                    'fv':      (SHOW_FV,      FvRegExes,              ArgsFv),
                    'rule':    (SHOW_RULE,    RuleRegExes,            ArgsRule),
    }

    # Items defiend in FV sections of an FDF file
    FDFDefines = [
        "ERASE_POLARITY",   "LOCK_CAP",     "LOCK_STATUS",        "MEMORY_MAPPED",     "READ_DISABLED_CAP",  "READ_ENABLED_CAP", "READ_STATUS",   "READ_LOCK_CAP",
        "READ_LOCK_STATUS", "STICKY_WRITE", "WRITE_DISABLED_CAP", "WRITE_ENABLED_CAP", "WRITE_LOCK_CAP",     "WRITE_LOCK_STATUS", "WRITE_STATUS",
        "BlockSize",        "NumBlocks",    "FvAlignment",        "FvNameGuid",        "FvBaseAddress",      "FvForceRebase", 
    ]

    # Class constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName, sections = [], process = True):
        # Initialize attributes specific to this class (capitalized attributes will be shown when class is dumped)
        self.APRIORI  = {}
        self.CAPSULES = []
        self.DEFINES  = []
        self.FDS      = []
        self.FVS      = []
        self.RULES    = []
        self.INFS     = []
        self.FILES    = []
        self.apriori  = None    # No apriori list          is being processed
        self.compress = None    # No compressed descriptor is being processed
        self.data     = None    # No data list             is being processed
        self.file     = None    # No file                  is being processes
        self.guided   = None    # No guided descriptor     is being processed
        self.sect     = None    # No section descriptor    is being proecessed
        # Initialize attributes specific to this class (capitalized attributes will be shown if class is dumped below)
        super().__init__(fileName, self.FDFSections, True, True, [], sections, process)

    ###################
    # Private methods #
    ###################

    # Parse an option string into a set of options
    # optionStr:    String to be parsed
    # allowSingles: Allow options without = following them
    # returns array of options and their values
    # Note: single options are returned with a value of True 
    def __getOptions__(self, optionStr, allowSingles=False):
        # Set starting conditionns
        options = []
        if optionStr != None:
            expect = 'option'
            # Loop through the options
            for token in optionStr.replace('=', ' = ').split():
                # Is an option name expected?
                if expect == 'option':
                    # Save it!
                    option = token
                    # An = is now expected
                    expect = '='
                # Is an = expected?
                elif expect == '=':
                    # Is it an equal
                    if token != '=':
                        # Are singles allowed
                        if allowSingles:
                            # Add single option
                            options.append({'option': option, 'value': True})
                            # Note this must now be the name of the next option
                            option = token
                        else:
                            self.ReportError(f'Invalid option combination encountered: {optionStr}')
                            return []
                    else:
                        expect = 'value'
                # Must be the value
                else:
                    options.append({'option': option, 'value': token})
                    expect = 'option'
            # Take care of options that were not completed
            if not expect == 'option':
                if expect == '=' and allowSingles:
                    options.append({'option': option, 'value': True})
                else:
                    self.ReportError(f'Masing value for option: {option}')
                    return []
        return options

    # Convert option list into a string
    # options:  Option list
    # returns string of options concatenated together
    def __optionStr__(self, options):
        # Set starting conditionns
        optionStr = ''
        for option in options:
            optionStr += f" {option['option']}={option['value']}"
        return optionStr

    ##################
    # Public methods #
    ##################
    # None

    ####################
    # Special handlers #
    ####################

    # For handling lines outside of a section
    # this: Self object of current file being processed
    # line: Contents of current line
    # returns nothing
    def OutsideLineHandler(self, this, line):
        # Save current lineNumber and fileName
        saved = (self.lineNumber, self.fileName)
        # Assume lineNumber and fileName object where outside line has been encounteered
        self.lineNumber, self.fileName = (this.lineNumber, this.fileName)
        # Process the outside line
        for i, regEx in enumerate([gbl.reFile, gbl.reSection, gbl.reEndDesc, gbl.rePath]): # These are all that are allowed!
            match = re.match(regEx, line, re.IGNORECASE)
            if match:
                [self.match_reFile, self.match_reSection, self.match_reEndDesc, self.match_rePath][i](match)
                break
        else:
            self.ReportError('Unsupported line outside of section')
        # Restore lineNumber and filName
        self.lineNumber, self.fileName = saved

    ######################
    # Directive handlers #
    ######################

    # Handle the Include directive
    # line: File to be included
    # returns nothing
    def directive_include(self, line):
        def includeHandler(file):
            gbl.AddReference(file, self.fileName, self.lineNumber)      # Indicate reference to included file
            if file.lower().endswith(".dsc"):
                if file in gbl.DSCs:
                    if Debug(SHOW_SKIPPED_DSCS):
                        print(f"{self.lineNumber}:Previously loaded:{file}")
                else:
                    gbl.DSCs[file] = DSCParser(file, [], True, self.OutsideLineHandler)
            else:
                if file in gbl.FDFs:
                    if Debug(SHOW_SKIPPED_FDFS):
                        print(f"{self.lineNumber}:Previously loaded:{file}")
                else:
                    gbl.FDFs[file] = FDFParser(file, self.sections, self.process)
        self.IncludeFile(line, includeHandler)

    ####################
    # Section handlers #
    ####################
    # None

    ##################
    # Match handlers #
    ##################

    # Handle a match in the [FD] section that matchs reDataStart
    # match: Results of regex match
    # returns nothing
    def match_reDataStart(self, match):
        # Previous data list must have been completed
        if not self.data == None:
            self.ReportError('Previous data list not terminated')
            return
        self.data = []
        if Debug(SHOW_FD):
            print(f'{self.lineNumber}:Entering data list')

    # Handle a match in the [FD] section that matchs reDataAdd
    # match: Results of regex match
    # returns nothing
    def match_reDataAdd(self, match):
        # reDataStart must have been already encountered
        if self.data == None:
            self.ReportError('Data list not allowed here')
            return
        data = match.group(0).replace(',', '').split()
        for datum in data:
            self.data.append(datum)
        if Debug(SHOW_FD):
            print(f'{self.lineNumber}:{match.group(0)}')

    # Handle a match in the [fv] section that matches reDefines
    # match: Results of regex match
    # returns nothing
    def match_reDefines(self, match):
        #TBD look for BLOCKS
        pass

    # Handle a match in the [fv] section that matches reApriori
    # match: Results of regex match
    # returns nothing
    def match_reApriori(self, match):
        # Previous apriori list must have been completed
        if not self.apriori == None:
            self.ReportError('Previous apriori list not terminated')
            return
        # Get APRIORI type
        self.apriori = match.group(1)
        # Start apriori list
        self.APRIORI[self.apriori] = Apriori(self.fileName, self.lineNumber)
        if Debug(SHOW_FV):
            print(f'{self.lineNumber}:Entering {self.apriori} apriori list')

    # Handle a match in the [rule] section that matches reCompress
    # match: Results of regex match
    # returns nothing
    def match_reCompress(self, match):
        # Previous compressed descriptor list must have been completed
        if not self.compress == None:
            self.ReportError('Previous compressed descriptor not terminated')
            return
        self.compress = { 'type': match.group(1)}
        if Debug(SHOW_FV):
            print(f'{self.lineNumber}:COMPRESS {"" if match.group(1) == None else match.group(1)}')
            print(f'{self.lineNumber}:Entering compressed descriptor')

    # Handle a match in the [fv] or [fd] sections that matches reEndDesc
    # match: Results of regex match
    # returns nothing
    def match_reEndDesc(self, match):
        # End apriori list (if applicable)
        if self.apriori != None:
            # Save in global variable
            gbl.Apriori[self.apriori] = self.APRIORI[self.apriori]
            # Clear Apriori list
            if Debug(SHOW_SUBELEMENT_EXIT):
                print(f'{self.lineNumber}:Exiting {self.apriori} apriori list')
            self.apriori = None
        # End guided descriptor (if applicable)
        elif self.guided != None:
            # Add guided descriptor to appropriate item
            if self.compress != None:
                self.compress['guided'] = self.guided
                if Debug(SHOW_SUBELEMENT_EXIT):
                    print(f'{self.lineNumber}:Exiting compress descriptor')
            elif self.sect != None:
                self.sect['guided']  = self.guided
                self.file['sections'].append(self.sect)
                self.sect            = None
                if Debug(SHOW_SUBELEMENT_EXIT):
                    print(f'{self.lineNumber}:Exiting guided section')
            elif self.file:
                self.file['guided']     = self.guided
                if Debug(SHOW_SUBELEMENT_EXIT):
                    print(f'{self.lineNumber}:Exiting guided descriptor')
            elif self.rule:
                self.rule['guided'] = self.guided
                if Debug(SHOW_SUBELEMENT_EXIT):
                    print(f'{self.lineNumber}:Exiting guided descriptor')
            else:
                self.ReportError('Unmatched ending brace characrter encountered: }')
            # Clear guided descriptor
            self.guided = None
        # End file descriptor (if applicable)
        elif self.file != None:
            # Add file
            self.FILES.append(self.file)
            self.file = None
            if Debug(SHOW_SUBELEMENT_EXIT):
                print(f'{self.lineNumber}:Exiting file descriptor')
        # End data list (if applicable)
        elif self.data != None:
            self.FDS.append(self.data)
            self.data = None
            if Debug(SHOW_SUBELEMENT_EXIT):
                print(f'{self.lineNumber}:Exiting data list')
        # End compressed descriptor (if applicable)
        elif self.compress != None:
            self.rule['compress'] = self.compress
            self.compress = None
            if Debug(SHOW_SUBELEMENT_EXIT):
                print(f'{self.lineNumber}:Exiting compressed descriptor')
        # End rule descriptor (if applicable)
        elif self.rule != None:
            self.RULES.append(self.rule)
            self.rule = None
            if Debug(SHOW_SUBELEMENT_EXIT):
                print(f'{self.lineNumber}:Exiting rule descriptor')
        else:
            self.ReportError('End brace found without matching start brace')

    # Handle a match in the [rules] section that matches reExt
    # match: Results of regex match
    # returns nothing
    def match_reExt(self, match):
        # reRule must have been previously encountered
        if self.rule == None:
            self.ReportError('RULE must start with FILE description')
            return
        path, ext = (match.group(3), match.group(4))
        info      = match.group(0)[0:match.span(3)[0]].split()
        kind      = info[0]
        num       = len(info)
        if num > 2:
            kind2, opts = (info[1], self.__getOptions__(' '.join(info[2:]), True))
        elif num == 2:
            if '=' in info[1] or info[1].lower() == 'optional':
                kind2, opts = ('', self.__getOptions(info[1], True))
            else:
                kind2, opts = (info[1], [])
        else:
            kind2, opts = ('', [])
        if self.guided:
            self.guided[kind] = f'{kind2}:{path}.{ext}{self.__optionStr__(opts)}'
            if Debug(SHOW_RULE):
                print(f'{self.guided[kind]}')
        elif self.compress:
            self.compress[kind] = f'{kind2}:{path}.{ext}{self.__optionStr__(opts)}'
            if Debug(SHOW_RULE):
                print(f'{self.compress[kind]}')
        else:
            self.rule[kind] = f'{kind2}:{path}.{ext}{self.__optionStr__(opts)}'
            if Debug(SHOW_RULE):
                print(f'{self.rule[kind]}')

    # Handle a match in the [fv] section that matches reFile
    # match: Results of regex match
    # returns nothing
    def match_reFile(self, match):
        def HandleOptionValue(token, msg):
            value  = token
            # Get the saves option
            token  = self.file['options'][-1]
            # Save the option and value
            self.file['options'][-1]={'option': token, 'value': value}
            if Debug(SHOW_FV):
                msg += f" {token}={value}"
            # Nothing else is expected now
            return (msg, None)
        # Previous file descriptor must have been completes
        if not self.file == None:
            self.ReportError('Previous file descriptor not terminated')
            return
        msg = ''
        kind = match.group(1)
        guid = match.group(2)
        self.file = {'type': kind, 'guid': guid, 'options': self.__getOptions__(match.group(3), True), 'sections': []}
        if Debug(SHOW_FV):
            print(f'{self.lineNumber}:FILE {kind} {guid}{msg}')
        if Debug(SHOW_SUBELEMENT_ENTER):
            print(f'{self.lineNumber}:Entering file descriptor')

    # Handle a match in the [rules] section that matches reGuided
    # match: Results of regex match
    # returns nothing
    def match_reGuided(self, match):
        # Previous guidede descriptor list must have been completed
        if not self.guided == None:
            self.ReportError('Previous guided descriptor not terminated')
            return
        self.guided = { 'guid': match.group(1)}
        if Debug(SHOW_FV):
            print(f'{self.lineNumber}:GUIDED {"" if match.group(1) == None else match.group(1)}')
            print(f'{self.lineNumber}:Entering guided descriptor')

    # Handle a match in the [fv] section that matches reInf
    # match: Results of regex match
    # returns nothing
    def match_reInf(self, match):
        # Check for Apriori
        inf = match.group(4)
        gbl.AddReference(inf, self.fileName, self.lineNumber)       # Add reference to INF file
        if self.apriori:
            self.APRIORI[self.apriori].Append(inf)
            if Debug(SHOW_FV):
                print(f'{self.lineNumber}:{inf} added to {self.apriori} list (#{len(self.APRIORI[self.apriori].list)})')
        # Normal INF entry
        else:
            # Add any detected options
            opts = self.__getOptions__(match.group(1))
            self.INFS.append((inf, opts))
            if Debug(SHOW_FV):
                print(f'{self.lineNumber}:INF {inf}{self.__optionStr__(opts)}')

    # Handle a match in the [fv] section that matches rePath
    # match: Results of regex match
    # returns nothing
    def match_rePath(self, match):
        # Can only have this when a file is being described and when one of the other descriptors is active
        if self.file == None or (self.compress != None or self.guided != None or self.sect != None):
            self.ReportError('FV path not allowed outstide of file description')
            return
        # File type must be RAW
        if not self.file['type'] == 'RAW':
            self.ReportError('FV path only allowed with RAW file types')
            return
        path = match.group(1)
        self.file['path'] = path
        if Debug(SHOW_FV):
            print(f'{self.lineNumber}:{path}')

    # Handle a match in the [rules] section that matches reRule
    # match: Results of regex match
    # returns nothing
    def match_reRule(self, match):
        kind, guid, opts = (match.group(1), match.group(2), self.__getOptions__(match.group(3), True))
        self.rule = {'type': kind, 'guid': guid, 'options': opts}
        if Debug(SHOW_RULE):
            print(f'{self.lineNumber}:{kind}={guid}{self.__optionStr__(opts)}')
        if not match.groups(4) == None:
            if Debug(SHOW_SUBELEMENT_ENTER):
                print(f'{self.lineNumber}:Entering rule descriptor')
        else:
            self.RULES.append(self.rule)
            self.rule = None
            

    # Handle a match in the [fv] section that matches reSection
    # match: Results of regex match
    # returns nothing
    def match_reSection(self, match):
        if Debug(SHOW_FV): msg = ''
        if self.file == None:
            self.ReportError('SECTION not allowed outstide of file description')
            return
        # Tokenize secion info
        items = match.group(1).split()
        # Start new section descriptor
        sect = {'options': []}
        # Determine section type
        kind = items[0].upper()
        # Handle GUIDED type (format GUIDED <guid> [options])
        if kind == 'GUIDED':
            if len(items) < 2:
                self.ReportError('SECTION GUIDED uncountered with no GUID')
                return
            value = items[1]
            sect['type'] = {'GUIDED': value}
            i = 2   # Look for options starting here!
            self.guided = {'sections': []}      # Start guided descriptor
        # Handle other types (format <type> = <value> [options])
        else:
            if len(items) < 3 or items[1] != '=':
                self.ReportError(f'Invalid SECTION {kind} uncountered')
            value = items[2]
            sect['type'] = {'type': kind, 'value': value}
            i = 3   # Look for options starting here!
        # Handle options
        while i < len(items):
            if len(items) < i + 2 or items[i+1] != '=':
                self.ReportError(f'Invalid {opt} option uncountered')
            opt = items[i]
            val = items[i+2]
            sect['options'].append({'option': opt, 'value': val})
            if Debug(SHOW_FV): msg += f'{opt}={val} '
            i += 3
        # Either add section info to current descriptor
        if kind != 'GUIDED':
            if self.guided != None:
                self.guided['sections'].append(sect)
            else:
                self.file['sections'].append(sect)
        # Or save it if it is guided
        else:
            self.sect = sect
        if Debug(SHOW_FV):
            print(f'{self.lineNumber}:SECTION {kind} {value} {msg}')
        if Debug(SHOW_SUBELEMENT_ENTER) and kind == 'GUIDED':
            print(f'{self.lineNumber}:Entering guided section')

    # Handle a match in the [rules] section that matches reVer
    # match: Results of regex match
    # returns nothing
    def match_reVer(self, match):
        # Can only have this when a rule is being described
        if self.rule == None:
            self.ReportError('RULE must start with FILE description')
            return
        kind, opts = (match.group(1), self.__getOptions__(match.group(2).strip(), True))
        if self.guided:
            self.guided[kind] = self.__optionStr__(opts)[1:]
            if Debug(SHOW_RULE):
                print(f'{self.lineNumber}:{kind}{self.guided[kind]}')
        elif self.compress:
            self.compress[kind] = self.__optionStr__(opts)[1:]
            if Debug(SHOW_RULE):
                print(f'{self.lineNumber}:{kind}{self.compress[kind]}')
        else:
            self.rule[kind] = self.__optionStr__(opts)[1:]
            if Debug(SHOW_RULE):
                print(f'{self.lineNumber}:{kind}{self.rule[kind]}')

    #################
    # Dump handlers #
    #################

    def DumpTokenValue(self, list, title):
        if bool(list):
            print(f'    {title}:')
            for i, item in enumerate(list):
                print(f"        {i}:{item['token']}={item['value']}")

    def DumpCAPSULES(self):
        self.DumpTokenValue(self.CAPSULES, 'Capsules')

    def DumpDEFINES(self):
        DSCParser.DumpDEFINES(self)

    def DumpFDS(self):
        if bool(self.FDS):
            print(f'    FDs:')
            for i, item in enumerate(self.FDS):
                if 'token' in item:
                    print(f"        {i}:{item['token']}={item['value']}")
                elif 'offset' in item:
                    print(f"        {i}:{item['offset']}:{item['size']}")
                else:
                    print(f"        {i}:{','.join(item)}")

    def DumpFVS(self):
        self.DumpTokenValue(self.FVS, 'FVs')

    def DumpRULES(self):
        def DumpItems(item, skip, indent, handler):
            result = ''
            for attr in item.keys():
                if attr in skip: continue
                value = item[attr]
                if type(value) is str: result += f"\n{indent}{attr} {gbl.FixUndefined(value)}"
                else:                  result += handler(attr, item[attr])
            return result
        def ShouldNeverGetHere(attr, item):
            self.ReportError('Error dumping rules')
            return
        def DumpLevel2(attr, item):
            first  = item['type'] if attr == 'compress' else item['guid']
            first  = '' if first == None else f' {first}'
            result = f'\n                    {attr.upper()}{first}' + DumpItems(item, ['type'], '                        ', ShouldNeverGetHere)
            return result
        def DumpLevel1(attr, item):
            first  = item['type'] if attr == 'compress' else item['guid']
            first  = '' if first == None else f' {first}'
            result = f'\n                {attr.upper()}{first}' + DumpItems(item, ['type'], '                    ', DumpLevel2)
            return result
        if bool(self.RULES):
            print(f'    RULES:')
            for item in self.RULES:
                kind = gbl.FixUndefined(item['type'])
                opts = self.__optionStr__(item['options'])
                guid = gbl.FixUndefined(item['guid'])
                msg = f"        FILE {kind}={guid}{opts}"
                msg += DumpItems(item, ['type', 'guid', 'options'], '            ', DumpLevel1)
                print(msg)

    def DumpAPRIORI(self):
        if bool(self.APRIORI):
            for name in self.APRIORI:
                print(f'    {name} Apriori:')
                for i, item in enumerate(self.APRIORI[name].list()):
                    print(f"        {i+1}:{item}")

    def DumpINFS(self):
        if bool(self.INFS):
            print('    INFs')
            for i, item in enumerate(self.INFS):
                msg = item[0]
                for opt in item[1]:
                    msg += f" {opt['option']}={opt['value']}"
                print(f'        {i}:{msg}')

    def DumpFILES(self):
        def GetOptions(opts):
            options = ''
            if bool(opts):
                for opt in opts:
                    options += f" {opt['option']}={opt['value']}"
            return options
        if bool(self.FILES):
            print('    Files')
            for i, item in enumerate(self.FILES):
                options = GetOptions(item['options'])
                if 'guided' in item:
                    pass
                print(f"        {i}:FILE {item['type']} {item['guid']}{options}")
                for j, section in enumerate(item['sections']):
                    options = GetOptions(section['options'])
                    if 'guided' in section:
                        print (f"            {j}:SECTION GUIDED {section['type']['GUIDED']}{options}")
                        for k, sect in enumerate(section['guided']['sections']):
                            sect = sect['type']
                            print (f"                {k}:SECTION {sect['type']} {sect['value']}")
                        continue
                    section = section['type']
                    print (f"            {j}:SECTION {section['type']} {section['value']}{options}")
