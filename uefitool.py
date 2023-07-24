#!/usr/bin/env python

# Standard python modules
import platform
import os
import re
import sys
from   random import random

# Local modules
# None

# Constants

# Determine if this is Windows OS
isWindows  = 'WINDOWS' in platform.platform().upper()

# Regular Expression for matching sections with format "item = [value]"
# Groups: 1=>item, 3->optional value
reEquate    = r'^([^=\s]+)\s*(=\s*([^$]+)?$)?'

# Regular Expression for matching sections with format "-D item = [value]"
# Groups 1=>item, 2=>optional value
reBuildArgs = r'^-D\s*([^=\s]+)\s*(=\s*([^$]+)?)?$'

# Regular expression for matching sections with format "[DEFINE]|[EDK_GLOBAL] item = [value]"
# Groups 3=>optional DEFINE, 3=>item, 4=optional value
reDefine    = r'^((DEFINE|EDK_GLOBAL)\s+)?([^=\s]+)\s*=\s*([^$]+)?$'

# Regular expression for matching sections with format "[DEFINE]|[EDK_GLOBAL] item = [value]"
# Groups 3=>optional DEFINE, 3=>item, 4=optional value
reFile      = r'^FILE\s+([^=\s]+)\s*=\s*([^\s\{]+)\s*(CHECKSUM)?\s*\{'

# Regular expression for matching sections with format "item1 [ | item2]"
# Groups 1=>library, 3=>optional path
reBar       = r'^([^\s\|$]+)\s*(\|?\s*([^$]+)?)?'

# Regular expression for matching sections with format "group.pcd[ | item1 [ | item2 [ | item3 [ | item4 [| item5]]]]]"
# Groups 1=>space, 2=>pcd, 4=>optional item1, 6=>optional item2, 8=>optional item3, 10=>optional item4, 12=?optional item5
rePcds      = r'^([^\.]+)\.\s*([^\s\|$]+)\s*(\|?\s*([^\|$]+)?)?\s*(\|?\s*([^\|$]+)?)?\s*(\|?\s*([^\|$]+)?)?\s*(\|?\s*([^\|$]+)?)?\s*(\|?\s*([^$]+)?)?'

# DEBUG Constants
# Content based skips
SHOW_COMMENT_SKIPS          = 0x8000000000    # Show lines being skipped due to being blank or comments
SHOW_SKIPPED_ARCHITECTURES  = 0x4000000000    # Show lines being skipped due to architectural limitation
SHOW_CONDITIONAL_SKIPS      = 0x2000000000       # Show lines being skipped due to conditionals
# File type skips
SHOW_SKIPPED_DSCS           = 0x0800000000    # Show DSC files skipped because they have already been processed
SHOW_SKIPPED_INFS           = 0x0400000000    # Show INF files skipped because they have already been processed
SHOW_SKIPPED_DECS           = 0x0200000000    # Show DEC files skipped because they have already been processed
SHOW_SKIPPED_FDFS           = 0x0100000000    # Show FDF files skipped because they have already been processed
# Conditional information
SHOW_CONDITIONAL_DIRECTIVES = 0x0080000000    # Show lines with conditional directives 
SHOW_CONDITIONAL_LEVEL      = 0x0040000000    # Show conditional level
SHOW_CONVERTED_CONDITIONAL  = 0x0020000000    # Show conditional after conversion to python
# Special handling
SHOW_SPECIAL_HANDLERS       = 0x0008000000    # Show special handlers
SHOW_INCLUDE_RETURN         = 0x0004000000    # Show when returing from an included files
SHOW_INCLUDE_DIRECTIVE      = 0x0002000000    # Show include directive lines
SHOW_DEFAULT_SECTION        = 0x0001000000    # Show lines handled by default section handler
# Section entry handling
SHOW_INCLUDE_ENTRIES        = 0x0000400000    # Show include definitions
SHOW_DEFINE_ENTRIES         = 0x0000200000    # Show define definitions
SHOW_SOURCES_ENTRIES        = 0x0000100000    # Show source definitions
SHOW_DEPEX_ENTRIES          = 0x0000080000    # Show depex definitions
SHOW_FV_ENTRIES             = 0x0000040000    # Show fv definitions (other than APRIORI and FILE)
SHOW_APRIORI_ENTRIES        = 0x0000020000    # Show APRIORI definitions
SHOW_FILE_ENTRIES           = 0x0000010000    # Show file defiinitions
SHOW_LIBRARIES_ENTRIES      = 0x0000008000    # Show include definitions
SHOW_INCLUDE_ENTRIES        = 0x0000004000    # Show include definitions
SHOW_PACKAGES_ENTRIES       = 0x0000002000    # Show package definitions
SHOW_COMPONENT_ENTRIES      = 0x0000001000    # Show component definitions
SHOW_INF_ENTRIES            = 0x0000000800    # Show INF definitions
SHOW_LIBRARY_CLASS_ENTRIES  = 0x0000000400    # Show LibraryClass definitions
SHOW_DEFAULT_STORE_ENTRIES  = 0x0000000200    # Show DefaultStore definitions
SHOW_PROTOCOL_ENTRIES       = 0x0000000100    # Show Protocol definitions
SHOW_PPI_ENTRIES            = 0x0000000080    # Show PPI definitions
SHOW_SKUID_ENTRIES          = 0x0000000040    # Show SkuId definitions
SHOW_GUID_ENTRIES           = 0x0000000020    # Show GUID definitions
SHOW_PCD_ENTRIES            = 0x0000000010    # Show PCD definitions
# Basic stuff
SHOW_ERROR_DIRECT1VE        = 0x0000000008    # Show lines with error directives
SHOW_MACRO_DEFINITIONS      = 0x0000000004    # Show macro definitions
SHOW_SECTION_CHANGES        = 0x0000000002    # Show changes in sections
SHOW_FILENAMES              = 0X0000000001    # Show names of files being processed

DEBUG_NONE                  = 0
DEBUG_INCLUDES              = SHOW_INCLUDE_DIRECTIVE + SHOW_INCLUDE_RETURN
DEBUG_CONDITIONALS          = SHOW_CONDITIONAL_DIRECTIVES + SHOW_CONDITIONAL_LEVEL + SHOW_CONVERTED_CONDITIONAL
DEBUG_SECTIONS              = SHOW_DEFAULT_SECTION + SHOW_PCD_ENTRIES + SHOW_GUID_ENTRIES + SHOW_SKUID_ENTRIES + SHOW_PPI_ENTRIES + SHOW_PROTOCOL_ENTRIES + \
                              SHOW_DEFAULT_STORE_ENTRIES + SHOW_LIBRARY_CLASS_ENTRIES + SHOW_INF_ENTRIES + SHOW_INCLUDE_ENTRIES + SHOW_LIBRARIES_ENTRIES + \
                              SHOW_FV_ENTRIES + SHOW_APRIORI_ENTRIES +  SHOW_FILE_ENTRIES + SHOW_DEPEX_ENTRIES + SHOW_SOURCES_ENTRIES + SHOW_DEFINE_ENTRIES + \
                              SHOW_INCLUDE_ENTRIES
DEBUG_SKIPS                 = SHOW_COMMENT_SKIPS + SHOW_CONDITIONAL_SKIPS + SHOW_SKIPPED_ARCHITECTURES
DEBUG_MINIMAL               = 0x0000000001
DEBUG_NORMAL                = 0x000000000F
DEBUG_VERBOSE               = 0x000FFFFFFF
DEBUG_ALL                   = 0xFFFFFFFFFF

# Global Variables
BasePath                = None
Paths                   = []
MacroVer                = 0
Macros                  = {}
PCDs                    = {}
Files                   = {}
LibraryClasses          = {}
GUIDs                   = {}
SkuIds                  = {}
DefaultStores           = {}
DSCs                    = {}
Files                   = {}
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
    return f'v{MacroVer}:{macro} = {value}' 

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
    global BasePath, Paths
    # First try path as-is
    if os.path.exists(partial.replace('/', "\\")): return partial
    # Try partial appended to each path in Paths
    for p in Paths:
        file = JoinPath(p, partial)
        if os.path.exists(file): return os.path.relpath(file, BasePath).replace('\\', '/')
    return None

# Add an entry to the database
# db:    Database to which to add entry
# name:  Name under which to add the entry
# entry: Entry to be added
# returns nothing
def Add2DB(db, name, entry):
    if name in db:
        for item in db[name]:
            if item.fileName == entry.fileName:
                if item.lineNumber == entry.lineNumber:
                    return
        db[name].append(entry)
    else:
        db[name] = [entry]

# Get section string
# object: Item from which to get the section string
# returns section[.arch[.extra]]
def GetSection(section):
    value  = f"[{section[0]}"
    length = len(section)
    if length > 1:
        value += f".{section[1]}"
        if length > 2:
            value += f".{section[2]}"
    return value + ']'

# Class for a database entries
class DB:
    ###################
    # Private methods #
    ###################

    # Class constructor
    # object:   Object in which database entry is found
    # names:    List of attribute names  for this object
    # values:   List of attribute values for this object (same order/size as)
    # key:      Name of attribute that is to be the key value
    # db:       Database into which the entry is to be placed
    # debug:    Debug setting to check for output purposes
    # returns nothing
    def __init__(self, object, names, values, key, db, debug):
        # Init secion and file info
        self.section    = object.section
        # Initialize file data
        self.fileName   = object.fileName
        self.lineNumber = object.lineNumber
        # Copy map to class
        if Debug(debug): msg = f"{object.lineNumber}:{object.sectionStr}"
        for i, name in enumerate(names):
            value = values[i]
            setattr(self, name, value)
            if Debug(debug):
                if value == None or type(value) is str and value == '': continue
                msg = msg + f"{name}={value} "
        # Add entry to the database
        key = getattr(self, key)
        Add2DB(db, key, self)
        # Show info if debug is enabled
        if Debug(debug): print(msg.rstrip())

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
    # sectionsInfo:         Dictionary of allowed section names indicating their formats and support for subsections
    # allowIncludes:        True if !include directive is supported
    # allowConditionals:    True if conditional directives (!if, !ifdef, !ifndef, !else, !elseif, !endif) are supported
    # additionalDirectives: List of allowed directives other than include and conditionals (default is [] for None)
    # sections:             Starting sections (default is [] for None)
    #                       An array is used because multiple sections can be defined at a time
    # process:              Starting processing state (default is True)
    # returns nothing
    #
    # NOTES on handlers in child class!
    #    Child class MAY  provide a handler for "section_<name>"    for each name in sectionsInfo.
    #    "DefaultSection" is used for any section that  does not have a handler in the child class.
    #    Child class MUST provide a handler for "directive_<name>"  for each name in additionalDirectives.
    #    If no handler is found an error will be generated.
    #    Child class MUST provide a hanlder for "directive_include" if allowIncludes is se to True.
    #    If no handler is found an error will be generated.
    #    Child class MAY  provide "onentry_<name>" handler to be called when section "name" is entered.
    #    Child class MAY  provide "onexit_<name>"  handler to be called when section "name" is exited.
    #    Child class MAY  provide "macro_<name>"   handler to be called when macro "name" is set.
    #    This class provides handlers for all conditional directives.

    def __init__(self, fileName, sectionsInfo, allowIncludes = False, allowConditionals = False, additionalDirectives = [], sections = [], process = True):
        global MacroVer
        # Save given information
        self.fileName             = fileName
        self.sectionsInfo         = sectionsInfo
        self.allowIncludes        = allowIncludes
        self.allowConditionals    = allowConditionals
        self.additionalDirectives = additionalDirectives
        self.sections             = sections
        self.process              = process
        # Initialize other needed items
        self.processGuided        = None                       # Indicates that no guided descriptor is being processed
        self.processFile          = None                       # Indicates that no file descriptor is being processed
        self.processApriori       = None                       # Indicates that no apriori is being processed
        self.inSubsection         = False                      # Indicates that no is being processed
        self.subsections          = None                       # Subsections being processed
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
        pattern = """[ \t]\#.*|("(?:\\[\S\s]|[^"\\])*"|'(?:\\[\S\s]|[^'\\])*'|[\S\s][^"'#]*))"""
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
        # Check for unended subsection
        if self.inSubsection and bool(self.sections):
            self.ReportError(f"{self.section[0]} section missing closing brace")
            #print(f"{self.lineNumber}:{self.fileName} Setting insubsection to FALSE!")
            self.inSubsection = False
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
            if name in self.sectionsInfo:
                # Make sure architecture is supported
                if self.__sectionSupported__(items):
                    sectionStr = GetSection(items)
                    if Debug(SHOW_SECTION_CHANGES): print(f"{self.lineNumber}:{sectionStr}")
                    # Call onentry section handler (if any)
                    handler = getattr(self, f"onentry_{name}", None)
                    if handler and callable(handler): handler()
                # Else taken care of in __sectionSupported method!
                # No need to look for handler here because some section may use the default handler
            else: self.ReportError(f"Unknown section: {section}")
        return True

    # Call the section handler or the default section handler for the indicated section and line
    # section: Section which is to be handled
    # line:    Line    which is to be handled
    # returns nothing
    def __dispatchSectionHandler__(self, section, line):
        # Get the named handler
        handler = getattr(self, f"section_{section}", None)
        if handler and callable(handler):
            # Process the regular expression
            regex = self.sectionsInfo[section][1]
            match = match = re.match(regex, line) if regex else None
            # Call the named handler
            handler(line, match)
        # No named handler was available or callable: used default handler
        else: self.DefaultSection(line, section)

    # Handle subsection process (not call unless section supports subsections)
    # line: Line which is to be handled
    def __handleSubsection__(self, line):
        global SHOW_COMMENT_SKIPS
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        # Handle casse where a subsection is already being processed
        if self.inSubsection:
            # Look for end of subsection block
            if line.endswith("}") and self.inSubsection:
                # Signal end of subsection block and subsection
                #print(f"{self.lineNumber}:{self.fileName} Setting insubsection to FALSE!")
                self.inSubsection = False
                self.subsections  = None
                if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
                return
            # Look for subsection entry
            elif "<" in line:
                # Convert to normal section format
                line              = line.lower().replace("<", "[").replace(">", "]")
                # Save current section informarion
                sections          = self.sections
                # Don't call exit section handlers
                self.sections     = []
                # Handle subsection entry
                self.__handleNewSection__(line)
                # Save subsection information
                self.subsections  = self.sections
                # Restore the original section info
                self.sections     = sections
                return
            # Handle case where a subsection was alredy entered
            elif self.subsections:
                # Save current section info
                sections          = self.sections
                # Set subsection info
                self.sections     = self.subsections
                # Process the section line
                self.__handleIndividualLine__(line)
                # Restore the original section info
                self.sections     = sections
                return
        # Look for entry into a subsection block
        token = line.split(maxsplit=1)[0].upper()
        if line.endswith("{") and not token in ['APRIORI', 'FILE']:
            # Remove subsection block marker
            line                  = line[:-1].strip()
            # Indicate inside of subsection block
            #print(f"{self.lineNumber}:{self.fileName} Setting insubsection to TRUE! {token}")
            self.inSubsection     = True
            # No subsection started yet
            self.subsections      = None
        # Handle line within the section
        self.__dispatchSectionHandler__(self.section[0], line)

    # Handles items in an apriori list
    # line: Line to handle
    # returns nothing
    def __handleAprioriList__(self, line):
        global SHOW_COMMENT_SKIPS
        # Look for end of list
        if line == '}':
            # Indicate that list is done
            self.processApriori = None
            if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
        else:
            # Otherwise process it normally
            self.__dispatchSectionHandler__(self.section[0], line)

    # Handles items within a guided descriptor
    # line: Line to handle
    # returns nothing
    def __handleGuidedDescriptor__(self, line):
        global SHOW_COMMENT_SKIPS, SHOW_FILE_ENTRIES
        # Look for end of guided descriptor
        if line == '}':
            # Add guided information to file info
            guid = self.processGuided['GUIDED']
            self.processFile[guid] = self.processGuided
            # Indicate that guided decriptor is done
            self.processGuided = None
            if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
        else:
            # Otherwise add information on line to guided info
            items = line.split(maxsplit=1)
            kind  = items[0].upper()
            value = '' if len(items) == 1 else ' '.join(items[1].split())
            self.processGuided[kind] = value
            if Debug(SHOW_FILE_ENTRIES): print(f"{self.lineNumber}:{kind}{'' if not value else ' = '+ value}")

    # Handles items within a guided descriptor
    # line: Line to handle
    # returns nothing
    def __handleFileDescriptor__(self, line):
        global Files, SHOW_COMMENT_SKIPS, SHOW_FILE_ENTRIES
        # Look for end of file descriptor
        if line == '}':
            # Get file descriptor
            guid = self.processFile['GUID']
            # See if it is already in the Files list
            if guid in Files:
                # Get the current file decscriptor
                file = Files[guid]
                # Update it with now information
                for item in self.processFile:
                    file[item] = self.processFile[item]
            # Otherwise add now file descriptor
            else: Files[guid] = self.processFile
            # Indicate file descriptor processing is done
            self.processFile = None
            if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
        else:
            # See what kind of line this is
            items = line.split(maxsplit=1)
            kind  = items[0].upper()
            # Look for GUIDED SECTION
            if kind == 'SECTION' and 'GUIDED' in line:
                # Make sure it is properly formatted
                if len(items) == 1 or not items[1].endswith('{'):
                    self.ReportError(f"Unsupported guided section format: {line}")
                    return
                # Remove trailing '{' and GUIDED from rest of line
                items[1] = items[1][:-1].replace('GUIDED', '')
                # Tokenize rest of line
                items = items[1].split()
                guided = { "GUIDED": items[0] }
                # See if we have any attributes
                if len(items) > 1:
                    # Make sure attributes are properly paired
                    if (len(items) - 1) % 3 != 0:
                        self.ReportError(f'Bad format for guided section linee: {line}')
                        return
                    # Make sure attributes are properly formatted
                    for idx in range(2, len(items), 3):
                        if items[idx] != '=':
                            self.ReportError(f'Bad format for guided section linee: {line}')
                            return
                    # Add attributes to inf
                    if Debug(SHOW_FILE_ENTRIES): msg = ''
                    for idx in range(1, len(items), 3):
                        guided[items[idx]] = items[idx+2]
                        if Debug(SHOW_FILE_ENTRIES): msg += f'{items[idx]} = {items[idx+2]}'
                # Indicate need to process guided descriptor
                self.processGuided = guided
                if Debug(SHOW_FILE_ENTRIES): print(f'{self.lineNumber}: SECTION GUIDED {msg}')
                return
            # Look for COMPRESS lines
            elif kind == 'COMPRESS':
                return
            # Look for GUIDED lines
            elif kind == 'GUIDED':
                # Make sure it is properly formatted
                if len(items) == 1 or not items[1].endswith('{'):
                    self.ReportError(f"Unsupported guidded section format: {line}")
                    return
                # Indicate need to process guided descriptor
                self.processGuided = { "GUID": items[1].split('{')[0] }
                return
            # Handle all other kinds of lines
            self.processFile[kind] = '' if len(items) == 1 else ' '.join(items[1].split())
            if Debug(SHOW_FILE_ENTRIES): print(f'{self.lineNumber}:{kind} {items[1] if len(items)> 1 else ""}')

    # Handles an individual line that is not a directive or section header
    # line: line to be handled
    # returns nothing
    def __handleIndividualLine__(self, line):
        global reDefine, reFile
        # See if a apriori  is being processed
        if self.processApriori:
            self.__handleAprioriList__(line)
        # See if a guidded descriptor is being processed
        elif self.processGuided:
            self.__handleGuidedDescriptor__(line)
        # See if a file descriptor is being processed
        elif self.processFile:
            self.__handleFileDescriptor__(line)
        # Lines outside of a section are not allowed
        elif bool(self.sections):
            # Process line inside of each of the current sections
            for self.section in self.sections:
                # Make sure architecture is supported
                if self.__sectionSupported__(self.section):
                    self.sectionStr = GetSection(self.section)
                    # Get base section name
                    section = self.section[0]
                    # Are subsections supported by current section
                    if self.sectionsInfo[section][0]:
                        # Handle possible subsection
                        self.__handleSubsection__(line)
                        return
                    self.__dispatchSectionHandler__(self.section[0], line)
                # Else taken care of in __sectionSupported__ method!
        else:
            # Allow DEFINE equates outside of sections
            match = re.match(reDefine, line)
            if match:
                # Make sure it is a DEFINE
                if match.group(2) != 'DEFINE':
                    self.ReportError(f"Unsupported line discovered outside of a section")
                    return
                # Process definiiton
                self.DefineMacro(match.group(3), match.group(4))
                return
            # Allow FILE definitions outside of sections
            match = re.match(reFile, line)
            if not match:
                self.ReportError(f"Unsupported line discovered outside of a section")
                return
            # Indicate need to process file cescriptor
            self.processFile = { "TYPE": match.group(1), "GUID": match.group(2)}
            if Debug(SHOW_FILE_ENTRIES): print(f'{self.lineNumber}: FILE {match.group(1)}, {match.group(2)}')

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
        try:
            with open(self.fileName, 'r') as file:
                content = file.readlines()
            # Go through the content one at a time
            self.lineNumber = 0
            for line in content:
                self.lineNumber += 1
                if (self.lineNumber, self.fileName) == (34, 'Intel/EagleStreamFDBin/EagleStreamRpPkg/Include/Fdf/FvOpRomPath.dsc'):
                    pass
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
        except PermissionError:
            self.ReportError(f"Unexpected error occured attempting to open file: {self.fileName}")

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
            pass            # OK to do notfing here (means result can't be evaluated "as is")
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
                    pass    # Ok to do nothing here (means result can't be evaluated any furhter)
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
    def DefineMacro(self, macro, value):
        global SHOW_MACRO_DEFINITIONS, Macros
        try:
            # See if value can be interpreted
            value = eval(value)
        except Exception:
            value = '"' + value + '"'
        # Save result
        if not value: macrovalue = '""'
        result = SetMacro(macro, value)
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{self.lineNumber}:{result}')
        # Call handler for this macro (if found)
        handler = getattr(self, f"macro_{macro}", None)
        if handler and callable(handler): handler(value)

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
        global SHOW_INCLUDE_DIRECTIVE, SHOW_INCLUDE_RETURN, SHOW_CONDITIONAL_SKIPS
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
        else:
            if Debug(SHOW_CONDITIONAL_SKIPS): print(f"{self.lineNumber}:SKIPPED - Conditionally")


    # Check results of regular expression match
    # match:   Regular expression result
    # usage:   Group usage string (character at each index indicates how that group is to be used)
    #          ' ' - Skip group(index+1)
    #          'R' - group(index+1) is required (cannot be empty string or None
    #          'O" - group(index+1) is optional (may be empty and will be set to empty if None)
    #          'X' - group(index+1) is forbidden (must be empty or None)
    # last:    The last item in the list (this is for checking for C style comments)
    # line:    Line being processed (for error message)
    # returns a tuple of a True if there were no error or false if there were errors
    #                 followed by a the list values of each of the groups listed in items (some may be '')
    def CheckGroups(self, match, usage, last, line):
        noError = False
        values  = []
        # Handle case where match is no good
        if not match: self.ReportError(f'Invalid {self.section[0]} format: {line}')
        else:
            # Loop through groups to check
            for g, u in enumerate(usage):
                if u == ' ': continue   # Skip unused groups
                g += 1                  # Adjust group index
                # Get value (take care of case where value was not given and where value is the last one)
                value = "" if match.group(g) == None or match.group(g).startswith('//') else (match.group(last).split(' //')[0].strip() if g == last else match.group(g))
                # Make sure require groups are present and forbidden groups are not
                if (u == 'R' and not value) or (u == 'X' and value):
                    self.ReportError(f'Invalid {self.section[0]} format: {line}')
                    break
                # Append the value
                values.append(value)
            else:
                # We got through all of the groups without and error
                noError = True
        # Return the results
        return (noError, values)

# Class for parsing HPE Build Args files (PlatformPkgBuildArgs.txt)
class ArgsParser(UEFIParser):                      #  subsections?, regularExpression
    BuildArgsSections = { 'environmentvariables':    (False,         reEquate),
                          'hpbuildargs':             (False,         reBuildArgs),
                          'pythonbuildfailscripts':  (False,         None),
                          'pythonprebuildscripts':   (False,         None),
                          'pythonprehpbuildscripts': (False,         None),
                          'pythonpostbuildscripts':  (False,         None),
    }

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

    # Handle a line in the [EnvironmentVariables] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_environmentvariables(self, line, match):
        # Handle match results: groups 1 required, 3 optional
        good, items = self.CheckGroups( match, "R O", 3, line)
        if good:
          self.DefineMacro(items[1], items[2])

    # Handle a line in the [HpBuildArgs] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_hpbuildargs(self, line, match):
        # Handle match results: groups 1 required, 3 optional
        good, items = self.CheckGroups(match, "R O", 3, line)
        if good:
          self.DefineMacro(items[0], items[1])

    # The following sections are handled by the defaut handler:
    #     pythonbuildfailscripts
    #     pythonprebuildscripts
    #     pythonprehpbuildscripts
    #     pythonpostbuildscripts

# Class for parsing HPE Chipset files (HpChipsetInfo.txt)
class ChipsetParser(UEFIParser):          #  subsections?, regularExpression
    ChipsetSections = { 'binaries':         (False,        None),
                        'hpbuildargs':      (False,        reBuildArgs),
                        'platformpackages': (False,        None),
                        'snaps':            (False,        None),
                        'tagexceptions':    (False,        None),
                        'upatches':         (False,        None),
    }

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
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_hpbuildargs(self, line, match):
        # Handle match results: groups 1 required, 3 optional
        good, items = self.CheckGroups(match, "R O", 3, line)
        if good:
          self.DefineMacro(items[0], items[1])

    # The following sections are handled by the defaut handler:
    #    binaries
    #    platformpackages
    #    snaps
    #    tagexceptions
    #    upatches

class FDFParser(UEFIParser): #  subsections?, regularExpression
    FDFSections = { 'capsule': (False,        None),
                    'defines': (False,        reDefine),
                    'fd':      (False,        None),
                    'fv':      (True,         None),
                    'rule':    (False,        None),
    }

    # Items defiend in FV sections of an FDF file
    FDFDefines = [
        "ERASE_POLARITY",   "LOCK_CAP",     "LOCK_STATUS",        "MEMORY_MAPPED",     "READ_DISABLED_CAP",  "READ_ENABLED_CAP", "READ_STATUS",   "READ_LOCK_CAP",
        "READ_LOCK_STATUS", "STICKY_WRITE", "WRITE_DISABLED_CAP", "WRITE_ENABLED_CAP", "WRITE_LOCK_CAP",     "WRITE_LOCK_STATUS", "WRITE_STATUS",
        "BlockSize",        "NumBlocks",    "FvAlignment",        "FvNameGuid",        "FvBaseAddress",      "FvForceRebase", 
    ]

    ###################
    # Private methods #
    ###################

    # Class constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        # Initialize attributes specific to this class (capitalized attributes will be shown if class is dumped below)
        self.DEFINES = {}
        self.INFS    = []
        self.APRIORI = {}
        # Call cunstructor for parent class
        for item in self.FDFDefines: self.DEFINES[item] = None
        super().__init__(fileName, self.FDFSections, True, True)

    ######################
    # Directive handlers #
    ######################

    # Handle the Include directive
    # line: File to be included
    # returns nothing
    def directive_include(self, line):
        global DSCs, MacroVer, FDFs, SHOW_SKIPPED_DSCS, SHOW_SKIPPED_FDFS
        def includeHandler(file):
            if file.lower().endswith(".dsc"):
                if file in DSCs and DSCs[file].macroVer == MacroVer:
                    if Debug(SHOW_SKIPPED_DSCS): print(f"{self.lineNumber}:Previously loaded:{file}")
                else: DSCs[file] = DSCParser(file, [], True)
            else:
                if file in FDFs and FDFs[file].macroVer == MacroVer:
                    if Debug(SHOW_SKIPPED_FDFS): print(f"{self.lineNumber}:Previously loaded:{file}")
                else: FDFs.append(FDFParser(file))
        self.IncludeFile(line, includeHandler)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Defines] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_defines(self, line, match):
        # Handle match results: groups 3 required, 4 optional
        good, items = self.CheckGroups(match, "  RO", 4, line)
        if good:
            self.DefineMacro(items[0], items[1])

    # Handle a line in the [Defines] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_fv(self, line, match):
        global reEquate, reFile, SHOW_INF_ENTRIES, SHOW_APRIORI_ENTRIES, SHOW_FILE_ENTRIES
        def HandleINF():
            temp = line.replace('INF', '').lstrip()
            if temp == '': return False
            # Split line into tokens
            items = temp.split()
            # Path to INF file is always the last token
            inf = { 'FILE': items[-1] }
            # See if we have any attributes
            if len(items) > 1:
                # Make sure attributes are properly paired
                if (len(items) - 1) % 3 != 0: return False
                # Make sure attributes are properly formatted
                for idx in range(1, len(items) - 1, 3):
                    if items[idx] != '=': return False
                # Add attributes to inf
                for idx in range(0, len(items) - 1, 3):
                    inf[items[idx]] = items[idx+2]
            if self.processApriori == None: self.INFS.append(inf)
            else: self.APRIORI[self.processApriori].append(inf)
            if Debug(SHOW_INF_ENTRIES): print(f'{self.lineNumber}:INF {inf["FILE"]}')
            return True
        # Get first token on the line
        define = False
        items = line.split(maxsplit=1)
        kind  = items[0].upper()
        # Handle INF lines
        # Format: INF [attr1 = value1 [attr2 = value2 [...]]] path
        if kind == "INF":
            if not HandleINF():
                self.ReportError(f'Bad format for INF line: {line}')
            return
        # Handle FILE lines
        elif kind == "FILE":
            match = re.match(reFile, line)
            if not match:
                self.ReportError(f"Bad format for FILE line: {line}")
            else:
                self.processFile = { "TYPE": match.group(1), "GUID": match.group(2)}
                if Debug(SHOW_FILE_ENTRIES): msg = f'FILE {match.group(1)}, {match.group(2)}'
                if match.group(3) != None:
                    if match.group(3) == 'CHECKSUM':
                        self.processFile['CHECKSUM'] = 'TRUE'
                        if Debug(SHOW_FILE_ENTRIES): msg += f', CHECKSUM'
                    elif match.group(3) != '':
                        pass        # OK to do nothing here (means match.group(3) was not matched to anything useful)
                    else:
                        pass        # TBD (Not sure what else match.group(3) could be!!!)
                if Debug(SHOW_FILE_ENTRIES): print(f'{self.lineNumber}:{msg}')
            return
        # Handle APRIORI lines
        elif kind == "APRIORI":
            if len(items) != 2:
                self.ReportError(f"Bad format for APRIORI line: {line}")
                return
            self.processApriori               = items[1].upper()
            self.APRIORI[self.processApriori] = []
            if Debug(SHOW_APRIORI_ENTRIES): print(f'{self.lineNumber}:APRIORI {items[1].replace("{", "").rstrip()}')
            return
        # Handle DEFINE lines
        elif kind == "DEFINE":
            define = True
            line = line.replace('DEFINE', '').lstrip()
            # This is intended to fall through
        # Should be an equate!
        match = re.match(reEquate, line)
        good, items = self.CheckGroups(match, "RR", 2, line)
        if good:
            if define:
                self.DefineMacro(items[0], items[1])
            else:
                if not items[0] in self.FDFDefines:
                    self.ReportError(f'Unsupported FV define: {items[0]}')
                self.DEFINES[items[0]] = items[1]
                if Debug(SHOW_MACRO_DEFINITIONS): print(f'{self.lineNumber}:{items[0]} = {items[1]}')
            return
        # else handled in CheckGroups

    # The following sections are handled by the defaut handler:
    #    fd
    #    fv
    #    rule

# Class for handling UEFI DEC files
class DECParser(UEFIParser):               #  subsections, regularExpression
    DECSections = { 'defines':               (False,       reDefine),
                    'guids':                 (False,       reEquate),
                    'includes':              (False,       None),
                    'libraryclasses':        (False,       reBar),
                    'pcdsdynamic':           (True,        rePcds),
                    'pcdsdynamicex':         (True,        rePcds),
                    'pcdsfeatureflag':       (True,        rePcds),
                    'pcdsfixedatbuild':      (True,        rePcds),
                    'pcdspatchableinmodule': (True,        rePcds),
                    'ppis':                  (False,       None),
                    'protocols':             (False,       None),
                    'userextensions':        (False,       None),
                    # Below are specail section handlers that can only occur when processing a subsection!
                    'packages':              (False,       None),
                    'headerfiles':           (False,       None),
    }

    ###################
    # Private methods #
    ###################

    # Constructor
    # filename: File to parse
    # returns nothing
    def __init__(self, fileName):
        # Initialize attributes specific to this class (capitalized attributes will be shown if class is dumped below)
        self.INCLUDES       = []
        self.LIBRARYCLASSES = []
        self.PACKAGES       = []    # Only used with subsections
        self.HEADERFILES    = []    # Only used with subsections
        # Call cunstructor for parent class
        super().__init__(fileName, self.DECSections)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Defines] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_defines(self, line, match):
        # Handle match results: groups 3 required, 4 optional
        good, items = self.CheckGroups(match, "  RO", 4, line)
        if good:
          self.DefineMacro(items[0], items[1])

    # Handle a line in the [Guids] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_guids(self, line, match):
        global SHOW_GUID_ENTRIES
        # Handle match results: groups 1 required, 3 optional
        good, items = self.CheckGroups(match, "R R", 3, line)
        if good:
            DB(self, ['guid', 'value'], items, 'guid', GUIDs, SHOW_GUID_ENTRIES)

    # Handle a line in the [Includes] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_includes(self, line, match):
        global SHOW_INCLUDE_ENTRIES
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split("//")[0].strip()
        self.INCLUDES.append(line)
        if Debug(SHOW_INCLUDE_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [LibraryClasses] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_libraryclasses(self, line, match):
        global SHOW_LIBRARY_CLASS_ENTRIES
        # Handle match results: groups 1 required, 2 required)
        good, items = self.CheckGroups(match, "RR", 3, line)
        if good:
            self.LIBRARYCLASSES.append(( items[0], items[1] ))
            if Debug(SHOW_LIBRARY_CLASS_ENTRIES): print(f"{self.lineNumber}:{items[0]}|{items[1]}")

    # Handle a line in the [PcdsDynamic] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamic(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 4 optional, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR R R R X X", 2, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue', 'datumtype', 'token'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)
 
    # Handle a line in the [PcdsDynamicEx] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamicex(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 4 optional, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR R 0 0 X X", 5, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue', 'datumtype', 'token'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsFeatureFlag] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsfeatureflag(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 4 optional, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR R R R X X", 2, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue', 'datumtype', 'token'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsFixedAtBuild] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsfixedatbuild(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 4 optional, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR R R R X X", 2, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue', 'datumtype', 'token'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsPatchableInModule] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdspatchableinmodule(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 4 optional, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR R R R X X", 2, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue', 'datumtype', 'token'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [Ppis] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_ppis(self, line, match):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        super().DefaultSection(line, "ppis")

    # Handle a line in the [Protocols] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_protocols(self, line, match):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        super().DefaultSection(line, "protocols")

    #############################################
    # Section handlers (only when inSubsection) #
    #############################################

    # Handle a line in the [Protocols] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_packages(self, line, match):
        global DECs, SHOW_PACKAGES_ENTRIES
        # Only allow this section handle if in a subsection
        if not self.inSubsection:
            self.ReportError('section packages cannot be used outside of braces')
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        DECs.append((self.fileName, self.lineNumber, line))
        self.PACKAGES.append(line)
        if Debug(SHOW_PACKAGES_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [Protocols] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_headerfiles(self, line, match):
        # Only allow this section handle if in a subsection
        if not self.inSubsection:
            self.ReportError('section packages cannot be used outside of braces')
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.HEADERFILES.append(line)
        super().DefaultSection(line, "headerfiles")

    # The following sections are handled by the defaut handler:
    #    userextensions

# Class for handling UEFI DEC files
class INFParser(UEFIParser):          # subsections, regularExpression 
    INFSections = { 'binaries':        (False,       None),
                    'buildoptions':    (False,       None),
                    'defines':         (False,       reDefine),
                    'depex':           (False,       None),
                    'featurepcd':      (False,       rePcds),
                    'fixedpcd':        (False,       rePcds),
                    'guids':           (False,       reEquate),
                    'includes':        (False,       None),
                    'libraryclasses':  (False,       reBar),
                    'packages':        (False,       None),
                    'patchpcd':        (False,       rePcds),
                    'pcd':             (False,       rePcds),
                    'pcdex':           (False,       rePcds),
                    'ppis':            (False,       None),
                    'protocols':       (False,       None),
                    'sources':         (False,       None),
                    'userextensions':  (False,       None),
    }

    # Items defined in the [Defines] section of an INF file (because these are all caps they will show up in dump)
    INFDefines = [
        "BASE_NAME",     "CONSTRUCTOR",              "DESTRUCTOR",  "EDK_RELEASE_VERSION",       "EFI_SPECIFICATION_VERSION",
        "ENTRY_POINT",   "FILE_GUID",                "INF_VERSION", "LIBRARY_CLASS",             "MODULE_UNI_FILE",
        "PCD_IS_DRIVER", "PI_SPECIFICATION_VERSION", "MODULE_TYPE", "UEFI_HII_RESOURCE_SECTION", "UEFI_SPECIFICATION_VERSION",
        "UNLOAD_IMAGE",  "VERSION_STRING",
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
        # Initialize attributes specific to this class (capitalized attributes will be shown if class is dumped below)
        self.reference      = [(referenceName, referenceLine)]  # This attribute is handled in a special case
        self.DEFINES        = {}
        self.DEPEX          = ""
        self.INCLUDES       = []
        self.SOURCES        = []
        self.PPIS           = []
        self.PROTOCOLS      = []
        self.PACKAGES       = []
        self.LIBRARYCLASSES = []
        for attr in self.INFDefines: setattr(self, attr, None)
        # Call cunstructor for parent class
        super().__init__(fileName, self.INFSections)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Defines] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_defines(self, line, match):
        global SHOW_DEFINE_ENTRIES
        # Handle match results: groups 3 required, 4 optional
        good, items = self.CheckGroups(match, "  RO", 4, line)
        if good:
            # Is it a DEFINE case
            if match.group(2) == 'DEFINE':
                self.DEFINES[items[0]] = items[1]
            # Make sure it is a supported attribute
            else:
                if not items[0] in self.INFDefines:
                    self.ReportError(f"Unsupported INF define: {items[0]}")
                    return
                setattr(self, items[0], items[1])
            if Debug(SHOW_DEFINE_ENTRIES): print(f"{self.lineNumber}:{items[0]}={items[1]}")

    # Handle a line in the [Depex] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_depex(self, line, match):
        self.DEPEX += " " + re.sub("[ \t]+", " ", line)
        if Debug(SHOW_DEPEX_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [FeaturePcd] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_featurepcd(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR O X X X X", 2, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [FixedPcd] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_fixedpcd(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR O X X X X", 2, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [Guids] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_guids(self, line, match):
        global GUIDs, SHOW_GUID_ENTRIES
        # Handle match results: groups 1 required, 3 forbidden
        good, items = self.CheckGroups(match, "R X", 1, line)
        if good:
            DB(self, ['guid', 'value'], items, 'guid', GUIDs, SHOW_GUID_ENTRIES)

    # Handle a line in the [Includes] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_includes(self, line, match):
        global SHOW_INCLUDE_ENTRIES
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.INCLUDES.append(line)
        if Debug(SHOW_INCLUDE_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [LibraryClasses] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_libraryclasses(self, line, match):
        global SHOW_LIBRARY_CLASS_ENTRIES
        # Handle match results: groups 1 required, 3forbidden
        good, items = self.CheckGroups(match, "R X", 3, line)
        if good:
            self.LIBRARYCLASSES.append(items[0])
            if Debug(SHOW_LIBRARY_CLASS_ENTRIES): print(f"{self.lineNumber}:{items[0]}")

    # Handle a line in the [Packages] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_packages(self, line, match):
        global DECs, SHOW_PACKAGES_ENTRIES
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        DECs.append((self.fileName, self.lineNumber, line))
        self.PACKAGES.append(line)
        if Debug(SHOW_PACKAGES_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [PatchPcd] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_patchpcd(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR O X X X X", 2, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)


    # Handle a line in the [Pcd] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcd(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 4,6,8 optional, 10,12 forbidden
        good, items = self.CheckGroups(match, "RR O O O X X", 8, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue', 'datumtype', 'token'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)


    # Handle a line in the [PcdEx] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdex(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 4 optional, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR O X X X X", 2, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'defaultvalue'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [Ppis] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_ppis(self, line, match):
        global SHOW_PPI_ENTRIES
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.PPIS.append(line)
        if Debug(SHOW_PPI_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [Protocols] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_protocols(self, line, match):
        global SHOW_PROTOCOL_ENTRIES
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.PROTOCOLS.append(line)
        if Debug(SHOW_PROTOCOL_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [Sources] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_sources(self, line, match):
        global SHOW_SOURCES_ENTRIES
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.SOURCES.append(line)
        if Debug(SHOW_SOURCES_ENTRIES): print(f"{self.lineNumber}:{line}")

    # The following sections are handled by the defaut handler:
    #    binaries
    #    buildoptions
    #    userextensions

# Class for handling UEFI DSC files
class DSCParser(UEFIParser):                # subsections, regularExpression 
    DSCSections = { 'buildoptions':          (False,       None),
                    'components':            (True,        None),
                    'defaultstores':         (False,       reBar),
                    'defines':               (False,       reDefine),
                    'libraries':             (False,       None),
                    'libraryclasses':        (False,       reBar),
                    'pcdsdynamic':           (False,       rePcds),
                    'pcdsdynamicdefault':    (False,       rePcds),
                    'pcdsdynamicex':         (False,       rePcds),
                    'pcdsdynamicexdefault':  (False,       rePcds),
                    'pcdsdynamicexhii':      (False,       rePcds),
                    'pcdsdynamicexvpd':      (False,       rePcds),
                    'pcdsdynamichii':        (False,       rePcds),
                    'pcdsdynamicvpd':        (False,       rePcds),
                    'pcdsfeatureflag':       (False,       rePcds),
                    'pcdsfixedatbuild':      (False,       rePcds),
                    'pcdspatchableinmodule': (False,       rePcds),
                    'skuids':                (False,       reBar),
                    'userextensions':        (False,       None),
    }

    ###################
    # Private methods #
    ###################

    # Constructor
    # sections: Starting sections (default is [] for None)
    # process:  Starting conditional processing state (default is True)
    # returns nothing
    def __init__(self, fileName, sections = [], process = True):
        # Initialize attributes specific to this class (capitalized attributes will be shown if class is dumped below)
        self.LIBRARIES        = []
        # Call constructor for parent class
        super().__init__(fileName, self.DSCSections, True, True, ['error'], sections, process)

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
        global DSCs, MacroVer, SHOW_SKIPPED_DSCS
        def includeDSCFile(file):
            if file in DSCs and  DSCs[file].macroVer == MacroVer:
                    if Debug(SHOW_SKIPPED_DSCS): print(f"{self.lineNumber}:Previously loaded:{file}")
            else: DSCs[file] = DSCParser(file, self.sections, self.process)
        self.IncludeFile(includeFile, includeDSCFile)

    ####################
    # Special handlers #
    ####################

    def macro_SUPPORTED_ARCHITECTURES(self, value):
        global SupportedArchitectures
        SupportedArchitectures = value.upper().replace('"', '').split("|")
        if Debug(SHOW_SPECIAL_HANDLERS): print(f"{self.lineNumber}: Limiting architectires to {','.join(SupportedArchitectures)}")

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Components] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_components(self, line, match):
        global INFs, SHOW_COMPONENT_ENTRIES
        # Include the file
        line = line.replace('"', '')
        INFs.append((self.fileName, self.lineNumber, line))
        if Debug(SHOW_COMPONENT_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [DefaultStores] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_defaultstores(self, line, match):
        global DefaultStores, SHOW_DEFAULT_STORE_ENTRIES
        # Handle match results: groups 1, 3 required)
        good, items = self.CheckGroups(match, "R R", 3, line)
        if good:
            DB(self, ['name', 'value'], items, 'name', DefaultStores, SHOW_DEFAULT_STORE_ENTRIES)


    # Handle a line in the [Defines] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_defines(self, line, match):
        # Handle match results: groups 3 required, 4 optional
        good, items = self.CheckGroups(match, "  RO", 4, line)
        if good:
          self.DefineMacro(items[0], items[1])

    # Handle a line in the [PcdsFeatureFlag] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsfeatureflag(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2 required, 4 optional, 6,8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR O X X X X", 4, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'value'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsFixedAtBuild] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsfixedatbuild(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4 required, 4,8 optional, 10,12 forbidden
        good, items = self.CheckGroups(match, "RR R O O X X", 8, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsPatchableInModule] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdspatchableinmodule(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4 required, 6,8 optional, 10,12 forbidden
        good, items = self.CheckGroups(match, "RR R O O X X", 8, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsDynamic] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamic(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4 required, 6,8 optional, 10,12 forbidden
        good, items = self.CheckGroups(match, "RR R O O X X", 8, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsDynamicEx] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamicex(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4 required, 6,8 optional, 10,12 forbidden
        good, items = self.CheckGroups(match, "RR R O O X X", 8, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsDynamicDefault] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamicdefault(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4 required, 6 optional, 8,10,12 forbidden
        good, items = self.CheckGroups(match, "RR R O X X X", 6, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsDynamicHII] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamichii(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4,6,8 required, 10,12 optional
        good, items = self.CheckGroups(match, "RR R R R O O", 12, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'variablename', 'variableguid', 'variableoffset', 'hiidefaultvalue', 'hiiattribute'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsDynamicHII] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamicvpd(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4 required, 6,8 optional, 10,12 forbidden
        good, items = self.CheckGroups(match, "RR R O O X X", 8, line)
        if good:
            if items[4]:
                DB(self, ['pcdtokenspaceguidname', 'pcdname', 'vpdoffset', 'maximumdatumsize', 'value'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)
            else:
                DB(self, ['pcdtokenspaceguidname', 'pcdname', 'vpdoffset', 'value'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsDynamicExDefault] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamicexdefault(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4 required, 6,8 optional, 10,12 forbidden
        good, items = self.CheckGroups(match, "RR O O O X X", 8, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsDynamicExHii] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamicexhii(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4,6,8 required, 10 optional, 12 forbidden
        good, items = self.CheckGroups(match, "RR R R R O O", 12, line)
        if good:
            DB(self, ['pcdtokenspaceguidname', 'pcdname', 'variablename', 'variableguid', 'variableoffset', 'hiidefaultvalue'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [PcdsDynamicExVpd] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_pcdsdynamicexvpd(self, line, match):
        global PCDs, SHOW_PCD_ENTRIES
        # Handle match results: groups 1,2,4 required, 6,8 optional, 10,12 forbidden
        good, items = self.CheckGroups(match, "RR R O O X X", 8, line)
        if good:
            if items[4]:
                DB(self, ['pcdtokenspaceguidname', 'pcdname', 'vpdoffset', 'maximumdatumsize', 'value'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)
            else:
                DB(self, ['pcdtokenspaceguidname', 'pcdname', 'vpdoffset', 'value'], items, 'pcdname', PCDs, SHOW_PCD_ENTRIES)

    # Handle a line in the [SkuIds] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_skuids(self, line, match):
        global SkuIds, SHOW_SKUID_ENTRIES
        # Handle match results: groups 1, 3
        good, items = self.CheckGroups(match, "R R", 3, line)
        if good:
            DB(self, ['value', 'skuid'], items, 'skuid', SkuIds, SHOW_SKUID_ENTRIES)

    # Handle a line in the [Libraries] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_libraries(self, line, match):
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        self.LIBRARIES.append(line)
        if Debug(SHOW_LIBRARIES_ENTRIES): print(f"{self.lineNumber}:{line}")

    # Handle a line in the [LibraryClasses] section
    # line:  Contents of line
    # match: Results of regex match
    # returns nothing
    def section_libraryclasses(self, line, match):
        global LibraryClasses, SHOW_LIBRARY_CLASS_ENTRIES, INFs
        # Handle match results: groups 1, 3 required)
        good, items = self.CheckGroups(match, "R R", 3, line)
        if good:
            DB(self, ['name', 'path'], items, 'name', LibraryClasses, SHOW_LIBRARY_CLASS_ENTRIES)
            INFs.append( (self.fileName, self.lineNumber, items[1].replace('"', '')) )

    # The following sections are handled by the defaut handler:
    #    buildoptions
    #    userextensions

class PlatformInfo:
    ###################
    # Private methods #
    ###################
    content = []

    # Class constructor
    # platform: Platform directory
    # returns nothing
    def __init__(self, platform):
        global BasePath
        self.platform  = platform
        self.__findBase__()
        savedDir = os.getcwd()
        os.chdir(BasePath)
        self.platform  = os.path.relpath(platform, BasePath).replace('\\', '/')
        self.argsFile  = JoinPath(self.platform, "PlatformPkgBuildArgs.txt")
        self.dscFile   = JoinPath(self.platform, "PlatformPkg.dsc")
        self.decFile   = JoinPath(self.platform, "PlatformPkg.dec")
        self.fdfFile   = JoinPath(self.platform, "PlatformPkg.fdf")
        platform = self.platform[-6:-3]
        build_dir = os.path.join(BasePath, 'Build')
        self.__setEnvironment__('PLATFORM', platform)
        self.__setEnvironment__('TARGET', 'DEBUG')
        self.__setEnvironment__('BUILD_DIR', build_dir)
        self.__setEnvironment__('WORKSPACE', BasePath)
        self.__getWorkspace__()
        self.__getPaths__()
        self.__getHpPlatformPkg__()
        self.__processPlatform__()
        os.chdir(savedDir)

    # Set environment variable and also save in Macros
    def __setEnvironment__(self, variable, value):
        global isWindows
        result = SetMacro(variable, value.replace('\\', '/'))
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')
        if isWindows: value = value.replace('/', '\\')
        os.environ[variable] = value

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
        # Get PATH from the environment
        result = SetMacro('PATH', os.environ['PATH'].replace('\\', '/'))
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')

    # Utility form finding a particular line in the argsFile
    # lookFor: Partial contents of line being sought
    # returns Line split by ';'
    # EXITS WITH ERROR IF NOT FOUND OR LINE DOES NOT SPLIT
    def __findLine__(self, lookFor):
        # Read in arguments file
        if not bool(self.content):
            with open(self.argsFile, 'r') as file:
                self.content = file.readlines()
        for line in self.content:
            if lookFor in line:
                items = line.strip().split(';', maxsplit=1)
                if len(items) < 2:
                    Error('Invaid format in {lookFor} line ... exiting!')
                    sys.exit(3)
                return items
        Error(f'Unable to locate {lookFor} in {self.argsFile}')
        sys.exit(2)

    def __getWorkspace__(self):
        global BasePath
        # Get workpace and prebuild lines from args file
        workspaceItems = self.__findLine__(';set_platform_workspace')
        # HpCommon is expected to be in this path!
        if not 'HpCommon' in workspaceItems[0]:
            Error(f'Unable to detect path to HpCommon')
            sys.exit(3)
        index = workspaceItems[0].index('HpCommon')
        self.hppython = os.path.abspath(os.path.join(BasePath, workspaceItems[0][0:index]))
        sys.path.insert(0,self.hppython)
        # Make workspace path absolute        
        workspaceArg = os.path.abspath(os.path.join(BasePath, workspaceItems[1].replace("set_platform_workspace", "")[2:-2]))
        from HpCommon import HpSetPlatformWorkspace
        HpSetPlatformWorkspace.set_platform_workspace(JoinPath(BasePath, workspaceArg))

    # Determines value for PACKAGES_PATH environment variable
    # returns nothing
    def __getPaths__(self):
        global Paths
        paths = os.environ["PACKAGES_PATH"].replace("\\", "/")
        Paths = paths.split(";")
        result = SetMacro("PACKAGE_PATH", Paths)
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')

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
            result = SetMacro("COMMON_FAMILY", commonFamily)
            if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')
            file = FindPath(JoinPath(commonFamily, "PlatformPkgConfigCommon.dsc"))
            if not file:
                Error('Unable to locate common family file ... exiting!')
                sys.exit(3)
            hpPlatformPkg = GetMacroValue(file, "HP_PLATFORM_PKG")
            if not hpPlatformPkg:
                Error('Unable to determine value for HP_PLATFORM_PKG ... exiting!')
                sys.exit(4)
        result = SetMacro("HP_PLATFORM_PKG", hpPlatformPkg)
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')
    
    def sortedKeys(self, dict):
        keys = list(dict.keys())
        keys.sort()
        return keys

    def dump(self, object, indent, skip = []):
        kind = type(object)
        if   kind is object: items = dir(object)
        elif kind is list:   items = object
        elif kind is dict:   items = self.sortedKeys(object)
        else:
            return    # What else can be done here
        for item in items:
            if item.startswith('__'):              continue
            if item == 'section' and not 'section' in skip:             # Special handling for section
                print(f"{indent}section: {GetSection(object.section)}")
                continue
            if item != item.upper():               continue             # Only dump attributes in all caps
            value = getattr(object, item) if kind is object else object[item]
            if value == None:                      continue
            if type(value) is str and not value:   continue
            if type(value) is list:
                 if bool(value):
                    print(f"{indent}{item}: {value[0]}")
                    spaces = ' ' * (len(item) + 2)
                    for lst in value[1:]:
                        print(f"{indent}{spaces}{lst}")
            elif type(value) is dict:
                 if bool(value):
                    keys = self.sortedKeys(value)
                    print(f"{indent}{item}: {keys[0]}: {value[keys[0]]}")
                    spaces = ' ' * (len(item) + 2)
                    for key in keys[1:]:
                        print(f"{indent}{spaces}{key}: {value[key]}")
            else:
                print(f"{indent}{item}: {value}")

    # Process a platform and output the results
    # returns nothing
    def __processPlatform__(self):
        global DSCs, DECs, INFs, BasePath, Macros, PCDs, SHOW_SKIPPED_INFS, SHOW_SKIPPED_DECS
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
                if Debug(SHOW_SKIPPED_INFS): print(f"{number}:{name}:Previously loaded:{file}")
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
                if Debug(SHOW_SKIPPED_DECS): print(f"{number}:{name}:Previously loaded:{file}")
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
        for macro in self.sortedKeys(Macros): print(f"{macro}={Macros[macro]}")
        print(f"List of LibraryClasses:")
        print(f"-----------------------")
        for lcs in self.sortedKeys(LibraryClasses):
            print(f"{lcs}:")
            for lc in LibraryClasses[lcs]:
                print(f"    {lc.lineNumber}:{lc.fileName}")
                self.dump(lc, '        ')
        print(f"List of GUIDS:")
        print(f"--------------")
        for guids in self.sortedKeys(GUIDs):
            print(f"{guids}:")
            for guid in GUIDs[guids]:
                print(f"    {guid.lineNumber}:{guid.fileName}")
                self.dump(guid, '        ')
        print(f"List of SkuIds:")
        print(f"---------------")
        for skuids in self.sortedKeys(SkuIds):
            print(f"{skuids}:")
            for skuid in SkuIds[skuids]:
                print(f"    {skuid.lineNumber}:{skuid.fileName}")
                self.dump(skuid, '        ')
        print(f"List of DefaultStores:")
        print(f"---------------------")
        for dfs in self.sortedKeys(DefaultStores):
            print(f"{dfs}:")
            for df in DefaultStores[dfs]:
                print(f"    {df.lineNumber}:{df.fileName}")
                self.dump(df, '        ')
        print(f"List of PCDs:")
        print(f"-------------")
        for pcds in self.sortedKeys(PCDs):
            print(f"{pcds}:")
            for pcd in PCDs[pcds]:
                print(f"    {pcd.lineNumber}:{pcd.fileName}")
                print(f"        section: {GetSection(pcd.section)}")
                self.dump(pcd, '            ', ['section'])
        print(f"List of INFs:")
        print(f"-------------")
        for inf in infs:
            print(f"{inf}:")
            inf = infs[inf]
            for i in range(0, len(inf.reference)):
              print(f"    Reference: {inf.reference[i][1]}:{inf.reference[i][0]}")
            self.dump(inf, '    ', ['reference'])
        print(f"List of Files:")
        print(f"--------------")
        for file in Files:
            print(f"{file}")
            self.dump(Files[file], '    ')
            
# Indicate platform to be processed
#platform = "D:/ROMS/G11/a55/HpeProductLine/Volume/HpPlatforms/A55Pkg"
platform = "D:/ROMS/G11/u54/HpeProductLine/Volume/HpPlatforms/U54Pkg"
PlatformInfo(platform)

###########
### TBD ###
###########
# - Still need to add support for COMPRESS files to FDF FV sections
# - Add processing of all sections so that all syntax and information is checked
# - Allow platform directory to be passed in instead of hard coded
# - Convert other file lists to dictionaries and used MacroVer like it is used for DSC?
# - Cross-reference items to make sure things are consistent?
# - Generate files instead of output to the screen so it can be used by other utilites
