#!/usr/bin/env python

# Standard python modules
import os
import re
import sys

# Local modules
# None

# Constants

# Items defined in the [Defines] section of an INF file
INFDefines = [
    "BASE_NAME",     "CONSTRUCTOR",              "DESTRUCTOR",  "EDK_RELEASE_VERSION",       "EFI_SPECIFICATION_VERSION",
    "ENTRY_POINT",   "FILE_GUID",                "INF_VERSION", "LIBRARY_CLASS",             "MODULE_UNI_FILE",
    "PCD_IS_DRIVER", "PI_SPECIFICATION_VERSION", "MODULE_TYPE", "UEFI_HII_RESOURCE_SECTION", "UEFI_SPECIFICATION_VERSION",
    "UNLOAD_IMAGE",  "VERSION_STRING",
]

# DEBUG Constants
SHOW_COMMENT_SKIPS          = 0x80000000    # Show lines being skipped due to being blank or comments
SHOW_SKIPPED_ARCHITECTURES  = 0x40000000    # Show lines being skipped due to architectural limitation
SHOW_SKIPPED_DECS           = 0x20000000    # Show DEC files being skipped because they were previously loaded
SHOW_SKIPPED_INFS           = 0x1000000     # Show INF files being skipped because they were previously loaded
SHOW_ERROR_DIRECT1VE        = 0x02000000    # Show lines with error directives
SHOW_SPECIAL_HANDLERS       = 0x01000000    # Show special handlers
#
SHOW_CONDITIONAL_SKIPS      = 0x00800000    # Show lines being skipped due to conditionals
SHOW_CONVERTED_CONDITIONAL  = 0x00400000    # Show conditional after conversion to python
SHOW_CONDITIONAL_LEVEL      = 0x00200000    # Show conditional level
SHOW_CONDITIONAL_DIRECTIVES = 0x00100000    # Show lines with conditional directives 
#
SHOW_DEFAULT_SECTION        = 0x00080000    # Show lines handled by default section handler
SHOW_PACKAGES_ENTRIES       = 0x00020000    # Show package definitions
SHOW_COMPONENT_ENTRIES      = 0x00010000    # Show component definitions
SHOW_INF_ENTRIES            = 0x00008000    # Show INF definitions
SHOW_LIBRARY_CLASS_ENTRIES  = 0x00004000    # Show LibraryClass definitions
SHOW_DEFAULT_STORE_ENTRIES  = 0x00002000    # Show DefaultStore definitions
SHOW_PROTOCOL_ENTRIES       = 0x00001000    # Show Protocol definitions
SHOW_PPI_ENTRIES            = 0x00000800    # Show PPI definitions
SHOW_SKUID_ENTRIES          = 0x00000400    # Show SkuId definitions
SHOW_GUID_ENTRIES           = 0x00000200    # Show GUID definitions
SHOW_PCD_ENTRIES            = 0x00000100    # Show PCD definitions
#
SHOW_INCLUDE_RETURN         = 0x00000020    # Show when returing from an included files
SHOW_INCLUDE_DIRECTIVE      = 0x00000010    # Show include directive lines
#
SHOW_MACRO_DEFINITIONS      = 0x00000004    # Show macro definitions
SHOW_SECTION_CHANGES        = 0x00000002    # Show changes in sections
SHOW_FILENAMES              = 0X00000001    # Show names of files being processed

DEBUG_NONE                  = 0
DEBUG_INCLUDES              = SHOW_INCLUDE_DIRECTIVE + SHOW_INCLUDE_RETURN
DEBUG_CONDITIONALS          = SHOW_CONDITIONAL_DIRECTIVES + SHOW_CONDITIONAL_LEVEL + SHOW_CONVERTED_CONDITIONAL
DEBUG_SECTIONS              = SHOW_DEFAULT_SECTION + SHOW_PCD_ENTRIES + SHOW_GUID_ENTRIES + SHOW_SKUID_ENTRIES + SHOW_PPI_ENTRIES + SHOW_PROTOCOL_ENTRIES + SHOW_DEFAULT_STORE_ENTRIES + SHOW_LIBRARY_CLASS_ENTRIES + SHOW_INF_ENTRIES
DEBUG_SKIPS                 = SHOW_COMMENT_SKIPS + SHOW_CONDITIONAL_SKIPS + SHOW_SKIPPED_ARCHITECTURES
DEBUG_MINIMAL               = 0x00000001
DEBUG_NORMAL                = 0x0000000F
DEBUG_VERBOSE               = 0x001FFFFF
DEBUG_ALL                   = 0xFFFFFFFF

# Global Variables
BasePath                = None
Paths                   = []
MacroVer                = 0
Macros                  = {}
PCDs                    = {}
LibraryClasses          = {}
GUIDs                   = {}
SkuIds                  = {}
DefaultStores           = {}
DSCs                    = {}
DECs                    = []
INFs                    = []
FDFs                    = []
SupportedArchitectures  = []
DebugLevel              = DEBUG_ALL

# Debug output checker
# check: Debug item to check
# retuns True if item is enabled, False otherwise
def Debug(check):
    global DebugLevel
    result = DebugLevel & check
    return result != 0

# Output an error message to STDERR
# message: Message to display
# returns nothing
def Error(message):
    global DebugLevel
    out = sys.stdout if DebugLevel > 0 else sys.stderr
    out.write(f"\n*** ERROR *** {message}\n")
    out.flush()

# Set the value of a macro and update the macro version
# macro: Name of macro to set
# value: Value to be given to the macro
# returns nothing
def SetMacro(macro, value):
    global MacroVer, Macros
    if macro in Macros and str(Macros[macro]) == str(value): return
    Macros[macro] = value
    MacroVer      += 1
    if Debug(SHOW_MACRO_DEFINITIONS): print(f'v{MacroVer}:{macro} = {value}')

# Join two paths together and make sure slashes are consistent
# path1: First path to join
# path2: Second path to join
# returns conjoined path
def JoinPath(path1, path2):
    return os.path.join(path1, path2).replace('\\', '/')

# Looks for a macro definition in a DSC file
# dsc:   DSC file in which to search
# macro: Macro for which to search
# returns value associated with macro or None if not found
def GetMacroValue(dsc, macro):
    # Regular expression patter to match [DEFINE] <macro>=<value>
    pattern = rf"^\s*(?:DEFINE\s+)?{macro}\s*=\s*(.*)$"
    # Search the file line by line for the macro
    with open(dsc, "r") as file:
        for line in file:
            match = re.match(pattern, line)
            if match:
                # Found it: return it's value!
                return match.group(1).strip()
    # Could not find it: return None
    return None

# Determine full path from partial path
# partial: partial path for whcihc to search
# returns full path or None if full path could not be found
def FindPath(partial):
    global Paths
    # First try path as-is
    if os.path.exists(partial): return partial
    # Try partial appended to each path in Paths
    for p in Paths:
        file = JoinPath(p, partial)
        if os.path.exists(file): return file
    return None

# Fill in section information for object
# self:    Object reference
# section: Section information
# object:  Referring object
# returns nothing
def SetSectionAndFileInfo(self, section, object):
    # Initialize section data
    self.section = section[0]
    length       = len(section)
    self.arch    = None if length < 2 else section[1]
    self.extra   = None if length < 3 else section[2]
    # Initialize file data
    self.file    = object.fileName
    self.line    = object.lineNumber

# Add an entry to the database
# db:    Database to which to add entry
# name:  Name under which to add the entry
# entry: Entry to be added
# returns nothing
def Add2DB(db, name, entry):
    if name in db:
        for item in db[name]:
            if item.file == entry.file:
                if item.line == entry.line:
                    return
        db[name].append(entry)
    else:
        db[name] = [entry]

# Class for a database entries
class DB:
    ###################
    # Private methods #
    ###################

    # Class constructor
    # sections: Section in which database entry is found (format [name[, arch, [extra]]])
    # info:     Information associated with database entry (value|ID)
    # object:   Object in which database entry is found
    # key:      Name of database key attribute
    # db:       Database into which the entry is to be placed
    # items:    Info items to show when debug is enabled
    # debug:    Debug setting to check
    # returns nothing
    def __init__(self, section, info, object, key, db, items, debug):
        # Init secion and file info
        SetSectionAndFileInfo(self, section, object)
        # Parse the info
        if not self.parseInfo(info): return
        # Add entry to the database
        Add2DB(db, getattr(self, key), self)
        # Show info if debug is enabled
        if Debug(debug):
            msg = f"{object.lineNumber}:{object.sectionStr}"
            for item in items:
                msg = msg + f"{item}={getattr(self, item)} "
            print(msg.rstrip())

# Class for a DefaultStores entries
class DefaultStore(DB):
    ###################
    # Private methods #
    ###################

    # Class constructor
    # sections: Section in which DefaultStores entry is found (format [name[, arch, [extra]]])
    # info:     Information associated with DefaultStore entry (value|ID)
    # object:   Object in which DefaultStore entry is found
    # returns nothing
    def __init__(self, section, info, object):
        global DefaultStores, SHOW_DEFAULT_STORE_ENTRIES
        super().__init__(section, info, object, "id", DefaultStores, ["id", "value"], SHOW_DEFAULT_STORE_ENTRIES)

    # Parse DefaultStore info line (format "value|id")
    # info: line of info to parse
    # returns True if info parsed without error, False otherwise   
    def parseInfo(self, info):
        # Get value
        items        = info.split("|", maxsplit=1)
        self.value   = items[0].strip()
        # Get ID (if it is there)
        if len(items) < 2:
            object.reportError("DefaultStore info not valid: {info}")
            return False
        self.id      = items[1].strip().replace('"', '')
        return True

# Class for a SkuId entry
class SkuId(DB):
    ###################
    # Private methods #
    ###################

    # Class constructor
    # sections: Section in which SkuId entry is found (format [name[, arch, [extra]]])
    # info:     Information associated with SKuId entry (value|ID)
    # object:   Object in which SkuId entry is found
    # returns nothing
    def __init__(self, section, info, object):
        global SkuIds, SHOW_SKUID_ENTRIES
        super().__init__(section, info, object, "id", SkuIds, ["id", "value"], SHOW_SKUID_ENTRIES)

    # Parse SkuId info line (format "value|id")
    # info: line of info to parse
    # returns True if info parsed without error, False otherwise   
    def parseInfo(self, info):
        # Get value
        items        = info.split("|", maxsplit=1)
        self.value   = items[0].strip()
        # Get ID (if it is there)
        if len(items) < 2:
            object.reportError("SkuID info not valid: {info}")
            return False
        self.id      = items[1].strip().replace('"', '')
        return True

# Class for a LibraryClass entry
class LibraryClass(DB):
    ###################
    # Private methods #
    ###################

    # Class constructor
    # sections: Section in which LibraryClass entry is found (format [name[, arch, [extra]]])
    # info:     Information associated with LibraryClass (name|infPath)
    # object:   Object in which LibraryClass is found
    # returns nothing
    def __init__(self, section, info, object):
        global LibraryClasses, SHOW_LIBRARY_CLASS_ENTRIES
        super().__init__(section, info, object, "name", LibraryClasses, ["name", "path"], SHOW_LIBRARY_CLASS_ENTRIES)

    # Parse LibraryClass info line (format "name[|path]")
    # info: line of info to parse
    # returns True if info parsed without error, False otherwise   
    def parseInfo(self, info):
        # Init name
        items        = info.split("|", maxsplit=1)
        self.name    = items[0].strip()
        # Get path (if it is there)
        self.path    = None if len(items) < 2 else items[1].strip().replace('"', '')
        return True

# Class for a PCD entry
class PCD(DB):
    ###################
    # Private methods #
    ###################

    # Class constructor
    # sections: Section in which PCD is found (format [name[, arch, [extra]]])
    # info:     Information associated with PCD (format guid.name[|value[|kind[|token]]])
    # object:   Object in which PCD is found
    # returns nothing
    def __init__(self, section, info, object):
        global PCDs, SHOW_PCD_ENTRIES
        super().__init__(section, info, object, "name", PCDs, ["guid", "name", "value", "kind", "token"], SHOW_PCD_ENTRIES)

    # Parse PCD info line (format "name|path")
    # info: line of info to parse (format name or guid.name[|value[|type[|token]]])
    # returns True if info parsed without error, False otherwise   
    def parseInfo(self, info):
        # Init items that may not be specified
        self.guid      = self.value = self.kind = self.token = None
        # Split into GUID and name (if appropriate, might be just name)
        items          = info.split(".", maxsplit=1)
        if len(items) > 1:
            # Format is guid.name[|value[|type[|token]]]
            # Get GUID
            self.guid  = items[0].strip()
            # Look for value, type, token
            items      = items[1].strip().split("|")
            # Get name
            self.name  = items[0]
            length     = len(items)
            # Get remaining items (if any)
            if length > 1:
                self.value = items[1].strip()
                if length > 2:
                    self.kind  = items[2].strip()
                    if length > 3:
                        self.token = items[3].strip()
        else:
            # Format name
            # Get name
            self.name  = items[0].strip()
        return True

# Class for a GUID entry
class GUID(DB):
    ###################
    # Private methods #
    ###################

    # Class constructor
    # sections: Section in which GUID definition or reference is found (format name[, arch, [extra]])
    # info:     Reference or definition associated with GUID (format name[={UINT32, UINT16, UINT16, {UINT08, UINT08, UINT08, UINT08, UINT08, UINT08, UINT08, UINT08}]}
    # object:   Object in which GUID reference or definition is found
    # returns nothing
    def __init__(self, section, info, object):
        global GUIDs, SHOW_GUID_ENTRIES
        super().__init__(section, info, object, "name", GUIDs, ["name", "value"], SHOW_GUID_ENTRIES)

    # Parse GUID info line (format "name|path")
    # info: line of info to parse (format name[=guid])
    # returns True if info parsed without error, False otherwise   
    def parseInfo(self, info):
        # Split into name and GUID (if appropriate
        items        = info.split("=", maxsplit=1)
        # Get name
        self.name    = items[0].strip()
        # Get GUID (if preseent)
        self.value   = None if len(items) < 2 else items[1].strip()
        return True
    
# Base class for all UEFI file types
class UEFIParser:
    ConditionalDirectives = ['if', 'ifdef', 'ifndef', 'elseif', 'else', 'endif']
    AllArchitectures      = ['AARCH32', 'AARCH64', 'IA32', 'RISCV64', 'X64']

    ConversionMap = {
        'FALSE':    'False',         # Boolean False
        'TRUE':     'True',          # Boolean True
        'sizeof':   'len',           # Length
        '&&':       'and',           # Logical AND
        '||':       'or',            # Logical OR
        '<>':       '!=',            # Inequality
        '=>':       '>=',            # Greater than or equal to
        '=<':       '<=',            # Less than or equal to
        '!':        'not',           # Logical NOT
    }

    ###################
    # Private methods #
    ###################

    # Class constructor
    # fileName:             File to be parsed
    # allowedSections:      List of allowed section names
    # allowIncludes:        True if !include directive is supported
    # allowConditionals:    True if conditional directives (!if, !ifdef, !ifndef, !else, !elseif, !endif) are supported
    # additionalDirectives: List of allowed directives other than include and conditionals (default is [] for None)
    # sections:             Starting sections (default is [] for None)
    #                       An array is used because multiple sections can be defined at a time
    # process:              Starting processing state (default is True)
    # returns nothing
    #
    # NOTES on handlers in child class!
    #    Child class MAY  provide a handler for "section_<name>"    for each name in allowedSections.
    #    "DefaultSection" is used for any section that  does not have a handler in the child class.
    #    Child class MUST provide a handler for "directive_<name>"  for each name in additionalDirectives.
    #    If no handler is found an error will be generated.
    #    Child class MUST provide a hanlder for "directive_include" if allowIncludes is se to True.
    #    If no handler is found an error will be generated.
    #    Child class MAY  provide "onentry_<name>" handler to be called when section "name" is entered.
    #    Child class MAY  provide "onexit_<name>"  handler to be called when section "name" is exited.
    #    Child class MAY  provide "macro_<name>"   handler to be called when macro "name" is set.
    #    This class provides handlers for all conditional directives.

    def __init__(self, fileName, allowedSections, allowIncludes = False, allowConditionals = False, additionalDirectives = [], sections = [], process = True):
        global MacroVer
        # Save given information
        self.fileName             = fileName
        self.allowedSections      = allowedSections
        self.allowIncludes        = allowIncludes
        self.allowConditionals    = allowConditionals
        self.additionalDirectives = additionalDirectives
        self.sections             = sections
        self.process              = process
        # Initialize other needed items
        self.hasDirectives        = bool(additionalDirectives) # Indicates if the file supports any directives other than include and conditionals
        self.lineNumber           = 0                          # Current line being processed
        self.commentBlock         = False                      # Indicates if currently processing a comment block
        self.section              = None                       # Indicates the current section being processed (one of self.sections)
        self.sectionStr           = ""                         # String representing current section (for messaging)
        self.macroVer             = MacroVer                   # Version of macros when this file was first loaded
        # Setup conditional processiong
        self.conditionHandled     = False                      # Indicates if current conditional has been handled
        self.conditionalStack     = []                         # For nesting of conditionals
        self.allowedConditionals  = []                         # Note If, Ifdef, and Ifndef are always allowed
        self.__parse__()
    
    # Looks for and removes any comments
    # line: line on which to look for potential comments
    # returns Line with comments removed or None if entire line was a comment
    def __removeComment__(self, line):
        global SHOW_COMMENT_SKIPS
        line = line.strip()
        if self.commentBlock:
            if line.endswith("*/"): self.commentBlock = False
            if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
            return None               
        else:
            if not line or (line.startswith('#') or line.startswith(';') or line.startswith("/*")):
                if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
                if line.startswith("/*"): self.commentBlock = True
                return None
        # Remove any trailing comments
        pattern = """ \#.*|("(?:\\[\S\s]|[^"\\])*"|'(?:\\[\S\s]|[^'\\])*'|[\S\s][^"'#]*))"""
        line = re.sub(pattern, "", line)
        line = re.sub(pattern.replace('#',';'), "", line)
        return line.strip()

    # Looks for and handles directives
    # line: line on which to look for potential directive
    # returns True if line was a directive and processed, False otherwise
    def __handleDirective__(self, line):
        # Get out if this file does not support directives
        if not self.allowIncludes and not self.allowConditionals and not self.hasDirectives: return False
        # Get out if line is not a directive
        if not line.startswith('!'): return False
        # Isolate directive
        items = line.split(maxsplit=1)
        directive = items[0][1:].lower()
        # Make sure directive is allowed
        if (self.allowIncludes and directive == 'include') or (self.allowConditionals and directive in self.ConditionalDirectives) or (directive in self.allowedDirectives):
            # Make sure directive has a handler
            handler = getattr(self, f"directive_{directive}", None)
            if handler and callable(handler): handler(items[1].strip() if len(items) > 1 else None)
            else: self.ReportError(f"Handler for directive not found: {directive}")
        else: self.ReportError(f"Unknown directive: {directive}")
        return True

    # Indicates if a particular section is a supported architecture
    # section: section to check
    # returns True if supported, False otherwise
    def __sectionSupported__(self, section):
        global SupportedArchitectures, SHOW_SKIPPED_ARCHITECTURES
        # Sections that do not stipulate architecture are always supported
        if len(section) < 2:                  return True
        arch = section[1].upper()
        # Patchup arch
        if   arch == 'peim': arch = 'IA32'
        elif arch == 'arm':  arch = 'AARCH64'
        elif arch == 'ipf':  arch = 'X64'
        if not arch in self.AllArchitectures: return True
        if arch in SupportedArchitectures:    return True
        if Debug(SHOW_SKIPPED_ARCHITECTURES): print(f"{self.lineNumber}:SKIPPED - unsupported architecture")
        return False

    # Looks for and handles section headers
    # line: line on which to look for potential section header
    # returns True if line was a setion header and processed, False otherwise
    def __handleNewSection__(self, line):
        global SHOW_SECTION_CHANGES
        # Look for section header (format "[<sections>]")
        match = re.match(r'\[([^\[\]]+)\]', line)
        if not match: return False
        # Call onexit section handlers (if any)
        if bool(self.sections):
            for section in self.sections:
                # Make sure section is supported archtecture
                if self.__sectionSupported__(section):
                    handler = getattr(self, f"onexit_{section[0].lower()}", None)
                    if handler and callable(handler): handler()
                # else handled by __sectionSupported__ method
            # Clear old sections
            self.sections.clear()
        # Get sections (format <section1>[, <designator2>[, ... <designatorn>]])
        sections = match.group(1).split(',')
        # Loop through sections
        for section in sections:
            # Get section info (format <name>[.<tag1>[.<tag2>]])
            items    = section.lower().strip().split('.')
            # Add to current sections
            self.sections.append(items)
            # Get name
            name     = items[0].lower()
            # Make sure it is an allowed section name
            if name in self.allowedSections:
                # Make sure architecture is supported
                if self.__sectionSupported__(items):
                    sectionStr = '[' + '.'.join(items) + ']'
                    if Debug(SHOW_SECTION_CHANGES): print(f"{self.lineNumber}:{sectionStr}")
                    # Call onentry section handler (if any)
                    handler = getattr(self, f"onentry_{name}", None)
                    if handler and callable(handler): handler()
                # Else taken care of in __sectionSupported method!
                # No need to look for handler here because some section may use the default handler
            else: self.ReportError(f"Unknown section: {section}")
        return True

    # Handles an individual line that is not a directive or section header
    # line: line to be handled
    # returns nothing
    def __handleIndividualLine__(self, line):
        # Lines outside of a section are not allowed
        if bool(self.sections):
            # Process line inside of each of the current sections
            for self.section in self.sections:
                # Make sure architecture is supported
                if self.__sectionSupported__(self.section):
                    self.sectionStr = '[' + '.'.join(self.section) + ']'
                    handler = getattr(self, f"section_{self.section[0]}", None)
                    if handler and callable(handler): handler(line)
                    else:                             self.DefaultSection(line, self.section[0])
                # Else taken care of in __sectionSupported__ method!
        else: self.ReportError(f"Line discovered outside of a section")

    # Expandes all macros within a line
    # line: line in which macros are to be expanded
    # returns line with macros expanded
    def __expandMacros__(self, line):
        global Macros
        # Look for all macros in the line (format "$(<macroName>)")
        matches = re.findall(r'\$\(([^\)]+)\)', line)
        # Loop through all ocurrances
        for match in matches:
            # Replace the macro with its value (or __<macroName>__UNDEFINED__ if it is not defined)
            line = line.replace(f"$({match})", str(Macros[match]) if match in Macros else F"__{match}__UNDEFINED__")
        # Return expanded line
        return line

    # Method for parsing a file file line by line
    # filePath:  file to be parsed
    def __parse__(self):
        global SHOW_FILENAMES, SHOW_CONDITIONAL_SKIPS
        if Debug(SHOW_FILENAMES): print(f"Processing {self.fileName}")
        # Read in the file
        with open(self.fileName, 'r') as file:
            content = file.readlines()
        # Go through the content one at a time
        self.lineNumber = 0
        for line in content:
            self.lineNumber += 1
            line = self.__removeComment__(line)
            if not line: continue
            # Expand macros before parsing
            line = self.__expandMacros__(line)
            # Handle directives (if any)
            if self.__handleDirective__(line):  continue
            # Conditional processing may indicate to ignore
            if not self.process:
                if Debug(SHOW_CONDITIONAL_SKIPS): print(f"{self.lineNumber}:SKIPPED - Conditionally")
                continue
            # Look for section change
            if self.__handleNewSection__(line): continue
            # Must by a regular line
            self.__handleIndividualLine__(line)

    # Handle a new conditional
    # returns nothing
    def __newConditional__(self):
        # Save current conditional settings
        self.conditionalStack.append((self.process, self.conditionHandled, self.allowedConditionals))
        # Allowed conditionals are all of the ifs, elses and endif
        # Inherits self.process!
        self.conditionHandled           = False
        self.allowedConditionals = ['Elseif', 'Else', 'Endif']

    # Convert a DSC style expression to one that Python can interpret
    # expression: Expression to be converted
    # returns converted expression
    def __convertExpression__(self, expression):
        # Match string literals (format "<string>") and replace them with a placeholder (format __STRING_LITERAL<#>))
        # This is so nothing inside of string literals is changed by this routine
        placeholders = []
        def replaceStringLiterals(match):
            # Replace "FALSE" and "TRUE" with their boolean values
            if match.group(0).upper() == '"FALSE"': return 'False'
            if match.group(0).upper() == '"TRUE"':  return 'True'
            # Replace string literal with a placeholder
            placeholders.append(match.group(0))
            return f'__STRING_LITERAL_{len(placeholders)-1}__'
        # Look for string literals in the expression
        expression = re.sub(r'".*?"', replaceStringLiterals, expression)
        # Add spaces between operators and other items in the expression
        pattern = r'(\b\w+\b|\+\+|--|->|<<=|>>=|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|\?|:|~|!|<|>|=|\+|\-|\*|/|%|&|\||\^|\(|\)|\[|\]|{|}|;|,|\.)'
        expression = re.sub(pattern, r' \1 ', expression)
        # Tokenize the expression
        tokens = expression.split()
        # Rebuild expressio while looping through tokens
        expression = []
        for token in tokens:
            # Substitute items in conversion map (if any)
            if token in self.ConversionMap: token = self.ConversionMap[token]
            # Substitute items with the macro values (if appropriate)
            elif token in Macros: token = Macros[token]
            expression.append(token)
        # Rebuild the expression
        expression = " ".join(expression)
        # Fixup auto-increment and auto-decrement operations (if any)
        expression = re.sub(r'(\w+)\+\+', r'\g<1> += 1', expression)
        expression = re.sub(r'(\w+)--', r'\g<1> -= 1', expression)
        # Restore the string literals that were replaced with place holders
        for i, placeholder in enumerate(placeholders):
            expression = expression.replace(f'__STRING_LITERAL_{i}__', placeholder)
        # Return converted expression
        return expression

    # Evaluata a condition
    # kind:      Type of condition to evaluate (one of "if", "ifdef", or "ifndef")
    # condition: Condition to evaluate
    def __evaluateCondition__(self, kind, condition):
        # Convert the expression to a Python expression
        result = self.__convertExpression__(condition)
        if Debug(SHOW_CONVERTED_CONDITIONAL): print(f"{self.lineNumber}:ConvertedCondition: {result}")
        try:
            # Try to interpret it
            result = eval(result)
        except Exception:
            pass
        # Handle if condition
        if kind == 'If':
            try:
                # Handle an integer result
                # NOTE: Boolean True converts to 1 and False to 0
                result = int(result)
                return result != 0
            except Exception:
                # Integer result not possible, must be a boolean
                # Replace undefined macros with ""
                macro_pattern = r'(__[^ \t]+_UNDEFINED__)'
                while re.search(macro_pattern, result):
                     match = re.search(macro_pattern, result)
                     undefinedMacro = match.group(1)
                     result = result.replace(f"{undefinedMacro}", '""')
                try:
                    # Try to interpret it
                    result = eval(result)
                except:
                    pass
                # Return result
                return result if type(result) is bool else result.upper() == "TRUE"
        # Handle ifdef condition
        elif kind == 'Ifdef':
            if type(result) == bool: return True    # In this case the eval worked so an __UNDEFINED__ macro could have existed otherwise eval would have failed
            return '__UNDEFINED__' not in result    # Eval must have failed ... was it because of __UNDEFINED__ macro?
        # Handle ifndef condition
        else:
            if type(result) == bool: return False   # In this case the eval worked so an __UNDEFINED__ macro could have existed otherwise eval would have failed
            return '_UNDEFINED__' in result         # Eval must have failed ... was it because of __UNDEFINED__ macro?

    ######################
    # Directive handlers #
    ######################

    # Handle the If directive
    # condition: If condition
    # returns nothing
    def directive_if(self, condition):
        global SHOW_CONDITIONAL_DIRECTIVES, SHOW_CONDITIONAL_LEVEL
        # if is always allowed
        if Debug(SHOW_CONDITIONAL_DIRECTIVES): print(f"{self.lineNumber}:if {condition}")
        self.__newConditional__()
        if self.process:
            # Set processing flag appropriately
            self.process = self.conditionHandled = self.__evaluateCondition__('If', condition)
        if Debug(SHOW_CONDITIONAL_LEVEL):
            print(f"{self.lineNumber}:ConditionalLevel:{len(self.conditionalStack)}, Process: {self.process}, allowedConditionals: if, idef, indef, {', '.join(self.allowedConditionals)}")

    # Handle the If directive
    # condition: Ifdef condition
    # returns nothing
    def directive_ifdef(self, condition):
        global SHOW_CONDITIONAL_DIRECTIVES, SHOW_CONDITIONAL_LEVEL
        # ifdef is always allowed
        if Debug(SHOW_CONDITIONAL_DIRECTIVES): print(f"{self.lineNumber}:ifdef {condition}")
        self.__newConditional__()
        if self.process:
            # Set processing flag appropriately
            self.process = self.conditionHandled = self.__evaluateCondition__('Ifdef', condition)
        if Debug(SHOW_CONDITIONAL_LEVEL):
            print(f"{self.lineNumber}:ConditionalLevel:{len(self.conditionalStack)}, Process: {self.process}, allowedConditionals: if, idef, indef, {', '.join(self.allowedConditionals)}")

    # Handle the If directive
    # condition: Ifndef condition
    # returns nothing
    def directive_ifndef(self, condition):
        global SHOW_CONDITIONAL_DIRECTIVES, SHOW_CONDITIONAL_LEVEL
        # ifndef is always allowed
        if Debug(SHOW_CONDITIONAL_DIRECTIVES): print(f"{self.lineNumber}:ifndef {condition}")
        self.__newConditional__()
        if self.process:
            # Set processing flag appropriately
            self.process = self.conditionHandled = self.__evaluateCondition__('Ifndef', condition)
        if Debug(SHOW_CONDITIONAL_LEVEL):
            print(f"{self.lineNumber}:ConditionalLevel:{len(self.conditionalStack)}, Process: {self.process}, allowedConditionals: if, idef, indef, {', '.join(self.allowedConditionals)}")

    # Handle the Else directive
    # condition: Should be empty
    # returns nothing
    def directive_else(self, condition):
        global SHOW_CONDITIONAL_DIRECTIVES, SHOW_CONDITIONAL_LEVEL
        # Make sure else is allowed at this time
        if Debug(SHOW_CONDITIONAL_DIRECTIVES): print(f"{self.lineNumber}:else")
        if not "Else" in self.allowedConditionals:
            self.ReportError("Unexpected else directive encountered.")
        # Now that else have been encountered only ifs and endif are allowed
        self.allowedConditionals = ['Endif']
        # Set processing flag apprpriately
        self.process = False    # Assume no processing
        if bool(self.conditionalStack):
            if self.conditionalStack[-1][0]:
                self.process = not self.conditionHandled 
            # else already taken care of by setting it to False above
        else:
            self.process = not self.conditionHandled
        if Debug(SHOW_CONDITIONAL_LEVEL):
            print(f"{self.lineNumber}:ConditionalLevel:{len(self.conditionalStack)}, Process: {self.process}, allowedConditionals: if, idef, indef, {', '.join(self.allowedConditionals)}")

    # Handle the ElseIf directive
    # condition: If condition
    # returns nothing
    def directive_elseif(self, condition):
        global SHOW_CONDITIONAL_DIRECTIVES, SHOW_CONDITIONAL_LEVEL
        # Make sure elseif is allowed at this time
        if Debug(SHOW_CONDITIONAL_DIRECTIVES): print(f"{self.lineNumber}:elseif {condition}")
        if not "Elseif" in self.allowedConditionals:
            self.ReportError("Unexpected elseif directive encountered.")
        # There is no change in allowed conditionals!
        # Set processing flag apprpriately
        self.process = False    # Assume no processing
        if bool(self.conditionalStack):
            if self.conditionalStack[-1][0]:
                if not self.conditionHandled:
                    self.process = self.conditionHandled = self.__evaluateCondition__('If', condition)
                # else already taken care of by setting it to False above
            # else already taken care of by setting it to False above
        else:
            self.process = self.conditionHandled = self.__evaluateCondition__('If', condition)
        if Debug(SHOW_CONDITIONAL_LEVEL):
            print(f"{self.lineNumber}:ConditionalLevel:{len(self.conditionalStack)}, Process: {self.process}, allowedConditionals: if, idef, indef, {', '.join(self.allowedConditionals)}")

    # Handle the Endif directive
    # condition: Should be empty
    # returns nothing
    def directive_endif(self, condition):
        global SHOW_CONDITIONAL_DIRECTIVES, SHOW_CONDITIONAL_LEVEL
        # Make sure elseif is allowed at this time
        if Debug(SHOW_CONDITIONAL_DIRECTIVES): print(f"{self.lineNumber}:endif")
        if not "Endif" in self.allowedConditionals:
            self.ReportError("Unexpected endif directive encountered.")
        # Set processing flag and allows Conditional to what they were for previous if level
        self.process, self.conditionHandled, self.allowedConditionals = self.conditionalStack.pop()
        if Debug(SHOW_CONDITIONAL_LEVEL):
            print(f"{self.lineNumber}:ConditionalLevel:{len(self.conditionalStack)}, Process: {self.process}, allowedConditionals: if, idef, indef, {', '.join(self.allowedConditionals)}")

    ##################
    # Public methods #
    ##################

    # Default section handler
    # name: List attribute name in which to save information (None means do not save)
    # line: section line
    # returns nothing
    def DefaultSection(self, line, name = None):
        global SHOW_DEFAULT_SECTION
        if name:
            attr = getattr(self, name, None)
            if not attr: setattr(self, name, [line])
            else:        attr.append(line)
        if Debug(SHOW_DEFAULT_SECTION): print(f"{self.lineNumber}:{self.sectionStr}: {line}")

    # Defines a new macro
    # line: line containing the macro
    # returns nothing
    def DefineMacro(self, line):
        global SHOW_MACRO_DEFINITIONS, Macros
        # Get the macroName and macroValue (format <macroName>=<macroValue>)
        macroName, macroValue = line.split('=', 1)
        macroName         = macroName.strip()
        macroValue        = macroValue.strip()
        try:
            # See if value can be interpreted
            macroValue = eval(macroValue)
        except Exception:
            macroValue = '"' + macroValue + '"'
        # Save result
        if not macroValue: macrovalue = '""'
        SetMacro(macroName, macroValue)
        # Call handler for this macro (if found)
        handler = getattr(self, f"macro_{macroName}", None)
        if handler and callable(handler): handler(macroValue)

    # Handles error repoting
    # message: error message
    # returns nothing
    def ReportError(self, message):
        # Display error message with file name and line number where error is encountered to stderr
        Error(f"{self.fileName}, line: {self.lineNumber}\n              {message}\n")

    # Determine full path to a file
    # path: partial path of file being searched for
    # returns full path to file or None if file could not be found
    def FindFile(self, path):
        global Paths, Macros
        # Make sure there are no undefined macros in the file path'
        if '_UNDEFINED__' in path:
            items = path.split("__")
            #if items[1] == "FSP_PKG" and "COMMON_FAMILY" in Macros:
            #    path = path.replace("__FSP_PKG__UNDEFINED__", Macros["COMMON_FAMILY"].replace('"',"").split('/')[-1].replace("Intel", "") + "FspPkg")
            #else:
            self.ReportError(f"Unable to locate file due to undefined macro: {path}")
            return None
        # Remove quotes that were added by macro expansion
        path = path.replace('"', '')
        file = FindPath(path)
        if not file: self.ReportError(f"Unable to locate file {path}")
        return file

    # Include a file
    # partial: Partial path of file being included
    # handler: Routine to handle the inclusion
    # returns full path to file or None if file could not be found
    def IncludeFile(self, partial, handler):
        global SHOW_INCLUDE_DIRECTIVE, SHOW_INCLUDE_RETURN 
        if self.process:
            # Get full path to file to be incuded
            file = self.FindFile(partial)
            # Make sure full path was found
            if file:
               # Include the file!
                if Debug(SHOW_INCLUDE_DIRECTIVE): print(f"{self.lineNumber}:Including {file}")
                handler(file)
                if Debug(SHOW_INCLUDE_RETURN): print(f"{self.lineNumber}:Returning to {self.fileName}")
            # Note else error handled in self.FindFile!

# Class for parsing HPE Build Args files (PlatformPkgBuildArgs.txt)
class ArgsParser(UEFIParser):
    BuildArgsSections =   [ 'hpbuildargs', 'environmentvariables', 'pythonprehpbuildscripts', 'pythonprebuildscripts', 'pythonpostbuildscripts', 'pythonbuildfailscripts' ]

    ###################
    # Private methods #
    ###################

    # Class constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        # Call cunstructor for parent class
        super().__init__(fileName, self.BuildArgsSections, True)

    ######################
    # Directive handlers #
    ######################

    # Handle the Include directive
    # line: File to be included
    # returns nothing
    def directive_include(self, line):
        def includeHandler(file):
            parser = ChipsetParser(file)            
        self.IncludeFile(line, includeHandler)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [HpBuildArgs] section
    # line:    Line to handle
    # returns nothing
    def section_hpbuildargs(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        # Look for definition (format "-D <macroName=macroValue")
        if line.startswith('-D'):
            _, line = line.split(maxsplit=1)
            self.DefineMacro(line)

    # Handle a line in the [EnvironmentVariables] section
    # line:    Line to handle
    # returns nothing
    def section_environmentvariables(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        # Look for definition (format "-D <macroName=macroValue")
        if line.startswith('-D'):
            _, line = line.split(maxsplit=1)
            self.DefineMacro(line)
        else:
            super().DefaultSection(line, "environementvariables")

    # The following sections are handled by the defaut handler:
    #     pythonprebuildscripts
    #     pythonpostbuildscripts
    #     pythonbuildfailscripts

# Class for parsing HPE Chipset files (HpChipsetInfo.txt)
class ChipsetParser(UEFIParser):
    ChipsetSections =   [ "platformpackages",  "hpbuildargs", "binaries", "upatches", "snaps", "tagexceptions" ]

    ###################
    # Private methods #
    ###################

    # Class constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        # Call cunstructor for parent class
        super().__init__(fileName, self.ChipsetSections)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [HpBuildArgs] section
    # line:    Line to handle
    # returns nothing
    def section_hpbuildargs(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        # Look for definition (format "-D <macroName=macroValue")
        if line.startswith('-D'):
            _, line = line.split(maxsplit=1)
            self.DefineMacro(line)

    # The following sections are handled by the defaut handler:
    #    platformpackages
    #    binaries
    #    upatches
    #    snaps
    #    tagexceptions

class FDFParser(UEFIParser):
    FDFSections =   [ 'defines', 'fd', 'fv', 'rule' ]

    ###################
    # Private methods #
    ###################

    # Class constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        # Call cunstructor for parent class
        super().__init__(fileName, self.FDFSections, True, True)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Defines] section
    # line:    Line to handle
    # returns nothing
    def section_defines(self,  line):
        # Remove "DEFINE" (if found)
        if line.startswith('DEFINE '):
            _, line = line.split('DEFINE', maxsplit=1)
        # Define macro!
        self.DefineMacro(line)

    ######################
    # Directive handlers #
    ######################

    # Handle the Include directive
    # line: File to be included
    # returns nothing
    def directive_include(self, line):
        def includeHandler(file):
            if file.lower().endswith(".dsc"):
                dsc = DSCParser(file)
            else:    
                fdf = FDFParser(file)
        self.IncludeFile(line, includeHandler)

# Class for handling UEFI DEC files
class DECParser(UEFIParser):
    DECSections = [
        'defines',         'guids',            'includes',              'libraryclasses', 'pcdsdynamic', 'pcdsdynamicex',
        'pcdsfeatureflag', 'pcdsfixedatbuild', 'pcdspatchableinmodule', 'ppis',           'protocols',   'userextensions',
    ]

    ###################
    # Private methods #
    ###################

    # Constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        super().__init__(fileName, self.DECSections)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Defines] section
    # line:    Line to handle
    # returns nothing
    def section_defines(self,  line):
        # Remove "DEFINE" (if found)
        if line.startswith('DEFINE '):
            _, line = line.split('DEFINE', maxsplit=1)
        # Define macro!
        self.DefineMacro(line)

    # Handle a line in the [Guids] section
    # line:    Line to handle
    # returns nothing
    def section_guids(self,  line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        guid = GUID(self.section, line, self)

    # Handle a line in the [Includes] section
    # line:    Line to handle
    # returns nothing
    def section_includes(self,  line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        super().DefaultSection(line, "includes")

    # Handle a line in the [LibraryClasses] section
    # line:    Line to handle
    # returns nothing
    def section_libraryclasses(self,  line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        # Just in case there is some training gunk on the line!
        line = line.split()[0]
        libraryclass = LibraryClass(self.section, line, self)

    # Handle a line in the [PcdsDynamic] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamic(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)
 
    # Handle a line in the [PcdsDynamicEx] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamicex(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsFeatureFlag] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsfeatureflag(self,  line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsFixedAtBuild] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsfixedatbuild(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsPatchableInModule] section
    # line:    Line to handle
    # returns nothing
    def section_pcdspatchableinmodule(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [Ppis] section
    # line:    Line to handle
    # returns nothing
    def section_ppis(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        super().DefaultSection(line, "ppis")

    # Handle a line in the [Protocols] section
    # line:    Line to handle
    # returns nothing
    def section_protocols(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        super().DefaultSection(line, "protocols")

    # The following sections are handled by the defaut handler:
    #    userextensions

# Class for handling UEFI DEC files
class INFParser(UEFIParser):
    INFSections = [
        'binaries', 'buildoptions', 'defines', 'depex', 'featurepcd', 'fixedpcd',  'guids',   'includes',      'libraryclasses',
        'packages', 'patchpcd',     'pcd',     'pcdex', 'ppis',       'protocols', 'sources', 'userextensions',
    ]

    ###################
    # Private methods #
    ###################

    # Constructor
    # fileName:         File to parse
    # referenceName:    Name of file referencing the INF
    # referenceLine:    Line of file referencing the INF
    # returns nothing
    def __init__(self, fileName, referenceName, referenceLine):
        global INFDefines
        self.reference = [(referenceName, referenceLine)]
        self.defines   = {}
        self.depex     = ""
        self.includes  = []
        self.sources   = []
        self.ppis      = []
        self.protocols = []
        self.packages  = []
        for attr in INFDefines: setattr(self, attr, None)
        super().__init__(fileName, self.INFSections)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Defines] section
    # line:    Line to handle
    # returns nothing
    def section_defines(self, line):
        global INFDefines
        items = line.split("=", maxsplit = 1)
        if len(items) < 2:
            self.ReportError("Invalid INF define: {line}")
            return
        attr  = items[0].strip()
        value = items[1].strip()
        if attr.startswith("DEFINE"):
            attr = attr.replace("DEFINE","").lstrip()
            self.defines[attr] = value
        else:
            if not attr in INFDefines:
                self.ReportError(f"Unsupported INF define: {attr}")
                return
            setattr(self, attr, value)
        if Debug(SHOW_INF_ENTRIES): print(f"{self.lineNumber}:{attr}={value}")

    # Handle a line in the [Depex] section
    # line:    Line to handle
    # returns nothing
    def section_depex(self, line):
        self.depex += " " + re.sub("[ \t]+", " ", line)
        if Debug(SHOW_INF_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [FeaturePcd] section
    # line:    Line to handle
    # returns nothing
    def section_featurepcd(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [FixedPcd] section
    # line:    Line to handle
    # returns nothing
    def section_fixedpcd(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [Guids] section
    # line:    Line to handle
    # returns nothing
    def section_guids(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        guid = GUID(self.section, line, self)

    # Handle a line in the [Includes] section
    # line:    Line to handle
    # returns nothing
    def section_includes(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.includes.append(line)
        if Debug(SHOW_INF_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [LibraryClasses] section
    # line:    Line to handle
    # returns nothing
    def section_libraryclasses(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        libraryclass = LibraryClass(self.section, line, self)

    # Handle a line in the [Packages] section
    # line:    Line to handle
    # returns nothing
    def section_packages(self, line):
        global DECs
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        DECs.append((self.fileName, self.lineNumber, line))
        self.packages.append(line)
        if Debug(SHOW_PACKAGES_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [PatchPcd] section
    # line:    Line to handle
    # returns nothing
    def section_patchpcd(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [Pcd] section
    # line:    Line to handle
    # returns nothing
    def section_pcd(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdEx] section
    # line:    Line to handle
    # returns nothing
    def section_pcdex(self,  line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [Ppis] section
    # line:    Line to handle
    # returns nothing
    def section_ppis(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.ppis.append(line)
        if Debug(SHOW_INF_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [Protocols] section
    # line:    Line to handle
    # returns nothing
    def section_protocols(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.protocols.append(line)
        if Debug(SHOW_INF_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [Sources] section
    # line:    Line to handle
    # returns nothing
    def section_sources(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.sources.append(line)
        if Debug(SHOW_INF_ENTRIES): print(f"{self.lineNumber}:{line}")

    # The following sections are handled by the defaut handler:
    #    binaries
    #    buildoptions
    #    userextensions

# Class for handling UEFI DSC files
class DSCParser(UEFIParser):
    DSCSections =   [ 'buildoptions',          'components',           'defaultstores',    'defines',
                      'libraries',             'libraryclasses',       'pcdsdynamic',      'pcdsdynamicdefault',
                      'pcdsdynamicex',         'pcdsdynamicexdefault', 'pcdsdynamicexhii', 'pcdsdynamicexvpd',
                      'pcdsdynamichii',        'pcdsdynamicvpd',       'pcdsfeatureflag',  'pcdsfixedatbuild',
                      'pcdspatchableinmodule', 'skuids',               'userextensions',    ]

    DSCDirectives = [ 'error']

    ###################
    # Private methods #
    ###################

    # Constructor
    # sections: Starting sections (default is [] for None)
    # process:  Starting conditional processing state (default is True)
    # returns nothing
    def __init__(self, fileName, sections = [], process = True):
        self.allowSubsections    = False
        # Call cunstructor for parent class
        super().__init__(fileName, self.DSCSections, True, True, self.DSCDirectives, sections, process)

    ######################
    # Directive handlers #
    ######################

    # Handle the Error directive
    # message: Error message
    # returns nothing
    def directiveError(self, message):
        # Display error message (if currently processsing)
        if Debug(SHOW_ERROR_DIRECT1VE): print(f"{self.lineNumber}:error {message}")
        if self.process: self.ReportError(f"error({message})")

    # Handle the Include directive
    # includeFile: File to be included
    # returns nothing
    def directive_include(self, includeFile):
        def includeDSCFile(file):
            global DSCs, MacroVer
            if file in DSCs:
                if DSCs[file].macroVer == MacroVer:
                    if Debug(SHOW_INCLUDE_DIRECTIVE): print(f"{self.lineNumber}:Previously loaded:{file}")
                    return DSCs[file]
            DSCs[file] = DSCParser(file, self.sections, self.process)
        self.IncludeFile(includeFile, includeDSCFile)

    ####################
    # Section handlers #
    ####################

    # [Components] on entry handler
    # returns nothing
    def onentry_components(self):
        # Components section can have subsections within but they must be enclosed in curly braces "{}"
        self.allowSubsections = False
        if Debug(SHOW_SPECIAL_HANDLERS): print(f"{self.lineNumber}: component section entry detected")

    # [Components] on exit handler
    # returns nothing
    def onexit_components(self):
        # Make sure curly braces have been closed
        if self.allowSubsections:
            self.ReportError("Component section missing closing brace (})")
        if Debug(SHOW_SPECIAL_HANDLERS): print(f"{self.lineNumber}: component section exit detected")

    # Handle a line in the [Components] section
    # line:    Line to handle
    # returns nothing
    def section_components(self,  line):
        global INFs
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        if self.allowSubsections:
            if line.endswith("}"):
                self.allowSubsections = False
                line                  = line[-1].rstrip()
                if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
                return
            elif "<" in line:
                line             = line.replace("<", "[").replace(">", "]")
                sections         = self.sections
                self.sections    = []
                self.__handleNewSection__(line)
                self.subsections = self.sections
                self.sections    = sections
                return
            elif self.subsections:
                sections        = self.sections
                self.sections   = self.subsections
                self.__handleIndividualLine__(line)
                self.sections   = sections
                return
        if line.endswith("{"):
            line                  = line[:-1].strip()
            self.allowSubsections = True
            self.subsections      = None
        # Include the file
        line = line.replace('"', '')
        INFs.append((self.fileName, self.lineNumber, line))
        if Debug(SHOW_COMPONENT_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [DefaultStores] section
    # line:    Line to handle
    # returns nothing
    def section_defaultstores(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        store = DefaultStore(self.section, line, self)

    # Handle a line in the [Defines] section
    # line:    Line to handle
    # returns nothing
    def section_defines(self, line):
        # Remove "DEFINE" (if found)
        if line.startswith('DEFINE '):
            _, line = line.split('DEFINE', maxsplit=1)
        # Define macro!
        self.DefineMacro(line)

    # Handle a line in the [PcdsFeatureFlag] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsfeatureflag(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsFixedAtBuild] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsfixedatbuild(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsPatchableInModule] section
    # line:    Line to handle
    # returns nothing
    def section_pcdspatchableinmodule(self,  line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsDynamic] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamic(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsDynamicEx] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamicex(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsDynamicDefault] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamicdefault(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsDynamicHII] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamichii(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsDynamicHII] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamicvpd(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsDynamicExDefault] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamicexdefault(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsDynamicExHii] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamicexhii(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [PcdsDynamicExVpd] section
    # line:    Line to handle
    # returns nothing
    def section_pcdsdynamicexvpd(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        pcd = PCD(self.section, line, self)

    # Handle a line in the [SkuIds] section
    # line:    Line to handle
    # returns nothing
    def section_skuids(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        sku = SkuId(self.section, line, self)

    # Handle a line in the [Libraries] section
    # line:    Line to handle
    # returns nothing
    def section_libraries(self, line):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        super().DefaultSection(line, "libraries")

    # Handle a line in the [LibraryClasses] section
    # line:    Line to handle
    # returns nothing
    def section_libraryclasses(self, line):
        global INFs
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        libraryclass = LibraryClass(self.section, line, self)
        INFs.append((self.fileName, self.lineNumber, libraryclass.path.replace('"', '')))

    # The following sections are handled by the defaut handler:
    #    buildoptions
    #    userextensions

    ##################
    # Macro handlers #
    ##################
    def macro_SUPPORTED_ARCHITECTURES(self, value):
        global SupportedArchitectures
        SupportedArchitectures = value.upper().replace('"', '').split("|")
        if Debug(SHOW_SPECIAL_HANDLERS): print(f"{self.lineNumber}: Limiting architectires to {','.join(SupportedArchitectures)}")

class PlatformInfo:
    ###################
    # Private methods #
    ###################

    # Class constructor
    # platform: Platform directory
    # returns nothing
    def __init__(self, platform):
        self.platform  = platform
        self.argsFile  = JoinPath(platform, "PlatformPkgBuildArgs.txt")
        self.dscFile   = JoinPath(platform, "PlatformPkg.dsc")
        self.decFile   = JoinPath(platform, "PlatformPkg.dec")
        self.fdfFile   = JoinPath(platform, "PlatformPkg.fdf")
        self.__findBase__()
        self.__getPaths__()
        self.__getHpPlatformPkg__()
        self.__processPlatform__()

    # Finds the base directory of the platform tree
    # returns nothing
    # EXITS WIT?H ERROR MESSAGE AND DOES NOT RETURN IF NOT FOUND
    def __findBase__(self):
        global BasePath
        BasePath = self.platform
        while True:
            # Look for Edk2 in current directory
            if os.path.isdir(os.path.join(BasePath, 'Edk2')): break
            # If not base move up one directory level
            old = BasePath
            BasePath = os.path.dirname(BasePath)
            # Get out if not found and no more levels to explore
            if BasePath == old:
                Error('Unable to locate base of UEFI platform tree ... exiting!')
                sys.exit(1)

        os.environ["WORKSPACE"] = BasePath

    # Determines value for PACKAGES_PATH environment variable
    # returns nothing
    def __getPaths__(self):
        global BasePath, Paths
        def findWorkspace():
            # Read in arguments file
            with open(self.argsFile, 'r') as file:
                content = file.readlines()
            for line in content:
                if "set_platform_workspace" in line:
                    return line.strip()
            Error('Unable to locate workspace settings ... exiting!')
            sys.exit(2)
        line  = findWorkspace()
        items = line.split(';', maxsplit=1)
        pyFile = JoinPath(BasePath, items[0])
        if len(items) < 2:
            Error('Invaid format in workspace settings ... exiting!')
            sys.exit(3)
        pyArg = items[1].replace("set_platform_workspace", "")[2:-2]
        sys.path.insert(0, os.path.dirname(pyFile))
        from HpSetPlatformWorkspace import set_platform_workspace
        set_platform_workspace(JoinPath(BasePath, pyArg))
        paths = os.environ["PACKAGES_PATH"].replace("\\", "/")
        Paths = paths.split(";")
        SetMacro("PACKAGE_PATH", Paths)

    # Finds the chipset DSC file
    # returns the chipset file
    # EXITS WIT?H ERROR MESSAGE AND DOES NOT RETURN IF NOT FOUND
    def __getHpPlatformPkg__(self):
        global Macros
        hpPlatformPkg = GetMacroValue(self.dscFile, "HP_PLATFORM_PKG")
        if not hpPlatformPkg:
            commonFamily = GetMacroValue(self.dscFile, "COMMON_FAMILY")
            if not commonFamily:
                Error('Unable to determine value for COMMON_FAMILY ... exiting!')
                sys.exit(2)
            SetMacro("COMMON_FAMILY", commonFamily)
            file = FindPath(JoinPath(commonFamily, "PlatformPkgConfigCommon.dsc"))
            if not file:
                Error('Unable to locate common family file ... exiting!')
                sys.exit(3)
            hpPlatformPkg = GetMacroValue(file, "HP_PLATFORM_PKG")
            if not hpPlatformPkg:
                Error('Unable to determine value for HP_PLATFORM_PKG ... exiting!')
                sys.exit(4)
        SetMacro("HP_PLATFORM_PKG", hpPlatformPkg)

    # Process a platform and output the results
    # returns nothing
    def __processPlatform__(self):
        global DSCs, DECs, INFs, BasePath, Macros, PCDs
        # Parse the args file
        print(f"Parsing Args files:")
        print(f"-------------------")
        args = ArgsParser(self.argsFile)

        # Parse the DSC files
        # This will generate a list of DEC and INF files to parse
        print(f"Parsing DSC files:")
        print(f"------------------")
        DSCs[self.dscFile] = DSCParser(self.dscFile)

        # Parse the INF files
        print(f"Parsing INF files:")
        print(f"------------------")
        infs = {}
        for name, number, path in INFs:
            file               = FindPath(path)
            if not file:
                Error(f"{name}, line: {number}\n              Unable to locate file {path}\n")
                continue
            if file in infs:
                if Debug(SHOW_SKIPPED_INFS): print(f"INF @{number} in {name} skipped because it was previosly parsed")
                inf = infs[file]
                # Only add reference if it is not already there
                if not (name, number) in inf.reference:
                    inf.reference.append((name, number))
            else:
                infs[file] = INFParser(file, name, number)

        # Parse the DEC files
        print(f"Parsing DEC files:")
        print(f"------------------")
        decs = {}
        for name, number, path in DECs:
            file               = FindPath(path)
            if not file:
                Error(f"{name}, line: {number}\n              Unable to locate file {path}\n")
                continue
            if file in decs:
                if Debug(SHOW_SKIPPED_DECS): print(f"DEC @{number} in {name} skipped because it was previosly parsed")
            else:
                decs[file] = DECParser(file)

        # Parse the DSC files
        # This will generate a list of DEC and INF files to parse
        print(f"Parsing FDF files:")
        print(f"------------------")
        fdfFile = FDFParser(self.fdfFile)

        # Show results
        print(f"RESULTS:")
        print(f"--------")
        print(f"Base Directory:          {BasePath}")
        print(f"Platform ARGS:           {self.argsFile}")
        print(f"Platform DSC:            {self.dscFile}")
        print(f"Platform DEC:            {self.decFile}")
        print(f"Platform FDF:            {self.fdfFile}")
        print(f"Supported Architectures: {','.join(SupportedArchitectures)}")
        print(f"List of Macros:")
        print(f"---------------")
        for macro in Macros: print(f"{macro}={Macros[macro]}")
        print(f"List of PCDs:")
        print(f"-------------")
        for pcds in PCDs:
            print(f"{pcds}:")
            for pcd in PCDs[pcds]:
                print(f"    {pcd.line}:{pcd.file}")
                print(f"        Section: [{pcd.section}.{pcd.arch}.{pcd.extra}]")
                print(f"        Value: {pcd.value}\n        Kind: {pcd.kind}\n        Token: {pcd.token}")
        print(f"List of LibraryClasses:")
        print(f"-----------------------")
        for lcs in LibraryClasses:
            print(f"{lcs}:")
            for lc in LibraryClasses[lcs]:
                print(f"    {lc.line}:{lc.file}")
                print(f"        Section: [{lc.section}.{lc.arch}.{lc.extra}]")
                print(f"        Path: {lc.path}")
        print(f"List of GUIDS:")
        print(f"--------------")
        for guids in GUIDs:
            print(f"{guids}:")
            for guid in GUIDs[guids]:
                print(f"    {guid.line}:{guid.file}")
                print(f"        Section: [{guid.section}.{guid.arch}.{guid.extra}]")
                print(f"        Value: {guid.value}")
        print(f"List of SkuIds:")
        print(f"---------------")
        for skuids in SkuIds:
            print(f"{skuids}:")
            for skuid in SkuIds[skuids]:
                print(f"    {skuid.line}:{skuid.file}")
                print(f"        Section: [{skuid.section}.{skuid.arch}.{skuid.extra}]")
                print(f"        Value: {skuid.value}")
        print(f"List of DefaultStores:")
        print(f"---------------------")
        for dfs in DefaultStores:
            print(f"{dfs}:")
            for df in DefaultStores[dfs]:
                print(f"    {df.line}:{df.file}")
                print(f"        Section: [{df.section}.{df.arch}.{df.extra}]")
                print(f"        Value: {df.value}")
        print(f"List of INFs:")
        print(f"-------------")
        for inf in infs:
            print(f"{inf}:")
            inf = infs[inf]
            for i in range(0, len(inf.reference)):
              print(f"    Reference: {inf.reference[i][1]}:{inf.reference[i][0]}")
            print(f"    Defines:")
            for attr in INFDefines:
                value = getattr(inf, attr, None)
                if value: print(f"        {attr}: {value}")
            for define in inf.defines:
                print(f"        {define}: {inf.defines[define]}")
            if bool(inf.includes):
                print(f"    Includes:")
                for include in inf.includes:
                    print(f"        {include}")
            if bool(inf.sources):
                print(f"    Sources:")
                for source in inf.sources:
                    print(f"        {source}")
            if bool(inf.ppis):
                print(f"    PPIs:")
                for ppi in inf.ppis:
                    print(f"        {ppi}")
            if bool(inf.protocols):
                print(f"    Protocols:")
                for protocol in inf.protocols:
                    print(f"        {protocol}")
            if bool(inf.depex): print(f"    DepEx: {inf.depex}")

# Indicate platform to be processed
platform = "D:/ROMS/G11/u54/HpeProductLine/Volume/HpPlatforms/U54Pkg"
PlatformInfo(platform)
