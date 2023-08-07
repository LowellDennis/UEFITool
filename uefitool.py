#!/usr/bin/env python

# Standard python modules
import platform
import os
import re
import sys
from   random import random

# Local modules
# None

###################
# DEBUG Constants #
###################

# Content based skips
SHOW_COMMENT_SKIPS           = 0x8000000000000000    # Show lines being skipped due to being blank or comments
SHOW_SKIPPED_ARCHITECTURES   = 0x4000000000000000    # Show lines being skipped due to architectural limitation
SHOW_CONDITIONAL_SKIPS       = 0x2000000000000000       # Show lines being skipped due to conditionals
# File type skips
SHOW_SKIPPED_DSCS            = 0x0800000000000000    # Show DSC files skipped because they have already been processed
SHOW_SKIPPED_INFS            = 0x0400000000000000    # Show INF files skipped because they have already been processed
SHOW_SKIPPED_DECS            = 0x0200000000000000    # Show DEC files skipped because they have already been processed
SHOW_SKIPPED_FDFS            = 0x0100000000000000    # Show FDF files skipped because they have already been processed
# Conditional information
SHOW_CONDITIONAL_DIRECTIVES  = 0x0080000000000000    # Show lines with conditional directives
SHOW_CONDITIONAL_LEVEL       = 0x0040000000000000    # Show conditional level
SHOW_CONVERTED_CONDITIONAL   = 0x0020000000000000    # Show conditional after conversion to python
# Special handling
SHOW_SPECIAL_HANDLERS        = 0x0008000000000000    # Show special handlers
SHOW_INCLUDE_RETURN          = 0x0004000000000000    # Show when returing from an included files
SHOW_INCLUDE_DIRECTIVE       = 0x0002000000000000    # Show include directive lines
SHOW_DEFAULT_SECTION         = 0x0001000000000000    # Show lines handled by default section handler
SHOW_SUBSECTION_ENTER        = 0x0000800000000000    # Show entry into subsections
SHOW_SUBSSECTION_EXIT        = 0x0000400000000000    # Show exit  from subsections
# Section entry handling
SHOW_USEREXTENSIONS          = 0x0000001000000000    # Show lines in UserExtensions         sections
SHOW_TAGEXCEPTIONS           = 0x0000000800000000    # Show lines in TagException           sections
SHOW_SOURCES                 = 0x0000000400000000    # Show lines in Sources                sections
SHOW_SNAPS                   = 0x0000000200000000    # Show lines in Snaps                  sections
SHOW_SKUIDS                  = 0x0000000100000000    # Show lines in SkuIds                 sections
SHOW_RULE                    = 0x0000000080000000    # Show lines in Rule                   sections
SHOW_PYTHONPREHPBUILDSCRIPTS = 0x0000000040000000    # Show lines in PythonHpPreBuildScripts sections
SHOW_PYTHONPREBUILDSCRIPTS   = 0x0000000020000000    # Show lines in PythonPreBuildScripts   sections
SHOW_PYTHONPOSTBUILDSCRIPTS  = 0x0000000010000000    # Show lines in PythonPostBuildScripts  sections
SHOW_PYTHONBUILDFAILSCRIPTS  = 0x0000000008000000    # Show lines in PythoBuildFailScripts   sections
SHOW_PROTOCOLS               = 0x0000000004000000    # Show lines in Protocols              sections
SHOW_PPIS                    = 0x0000000002000000    # Show lines in PPIs                   sections
SHOW_PLATFORMPACKAGES        = 0x0000000001000000    # Show lines in PlatformPackages       sections
SHOW_PCDS                    = 0x0000000000800000    # Show lines in PCDs                   sections
SHOW_UPATCHES                = 0x0000000000400000    # Show lines in uPatches               sections
SHOW_PACKAGES                = 0x0000000000200000    # Show lines in Packages               sections
SHOW_LIBRARYCLASSES          = 0x0000000000100000    # Show lines in LibraryClasses         sections
SHOW_INCLUDES                = 0x0000000000080000    # Show lines in Includes               sections
SHOW_HPBUILDARGS             = 0x0000000000040000    # Show lines in HpBuildArgs             sections
SHOW_HEADERFILES             = 0x0000000000020000    # Show lines in HeaderFiles            sections
SHOW_GUIDS                   = 0x0000000000010000    # Show lines in GUIDs                  sections
SHOW_FV                      = 0x0000000000008000    # Show lines in FV                     sections
SHOW_FMPPAYLOAD              = 0x0000000000004000    # Show lines in PmpPayload             sections
SHOW_FD                      = 0x0000000000001000    # Show lines in FD                     sections
SHOW_ENVIRONMENTVARIABLES    = 0x0000000000000800    # Show lines in EnvironmentVariable     sections
SHOW_DEPEX                   = 0x0000000000000400    # Show lines in Depex                  sections
SHOW_DEFINES                 = 0x0000000000000200    # Show lines in Defines                sections
SHOW_DEFAULTSTORES           = 0x0000000000000100    # Show lines in DefaultStores          sections
SHOW_COMPONENTS              = 0x0000000000000080    # Show lines in Components             sections
SHOW_CAPSULE                 = 0x0000000000000040    # Show lines in Capsule                sections
SHOW_BUILDOPTIONS            = 0x0000000000000020    # Show lines in BuildOptions           sections
SHOW_BINARIES                = 0x0000000000000010    # Show lines in Binaries               sections
# Basic stuff
SHOW_ERROR_DIRECT1VE         = 0x0000000000000008    # Show lines with error directives
SHOW_MACRO_DEFINITIONS       = 0x0000000000000004    # Show macro definitions
SHOW_SECTION_CHANGES         = 0x0000000000000002    # Show changes in sections
SHOW_FILENAMES               = 0X0000000000000001    # Show names of files being processed

# All in one setting values
DEBUG_NONE                   = 0x0000000000000000
DEBUG_MINIMAL                = 0x0000000000000001
DEBUG_NORMAL                 = 0x000000000000000F
DEBUG_VERBOSE                = 0x00FFFFFFFFFFFFFF
DEBUG_ALL                    = 0xFFFFFFFFFFFFFFFF

# Set the debug level
DebugLevel                   = DEBUG_MINIMAL

################################
# Regular expression constants #
################################

# Notes on regular expressions
# Beginning of line                                 ^
# End of line                                       $
# Capture into a group                              (<capture>)
# Until non-space character                         [^\s]+
# Until equal or non-space character                [^=\s]+
# Until non-space or end of line                    [^\s]+$
# Until the end of line                             [^.]+$
# Skip over optional spaces                         \s*
# Skip over at least one mandatory space            \s+
# This or that                                      this|that

### Partial regular expressions for use below

# Regular Expression for matching the next item
# Groups: 1=>item
reNext                = r'(.+)'

# Regular Expression for matching lines with format "item"<eol>
# Groups: 1=>item
reToEOL               = reNext + r'$'

# Regular Expression for matching lines with format "item [= [value]]"
# Groups: 1=>item, 3->optional value (Note = only required if value is specified)
reSoftEquate          = r'([^=\s]+)\s*(=\s*(.+))?$'

# Regular Expression for matching lines with format "item = [value]"
# Groups: 1=>item, 2->optional value (Note = is always required!)
reFirmEquate          = r'([^=\s]+)\s*=\s*(.+)?$'

# Regular Expression for matching lines with format "item = value"
# Groups: 1=>item, 2->value (Note = is aways required)
reHardEquate          = r'([^=\s]+)\s*=\s*' + reToEOL

# Regular Expression for matching lines with format "item1 [| item2]
# Groups: 1=>item1, 3->optional item2
re1Bar                = r'([^\s\|]+)(\s*\|\s*' + reNext + ')?$'

# Regular Expression for matching lines with format "item1 | items2 [ | items3]
# Groups: 1=>item1, 2->item2, 4=>optional item 3 (Note third bar required for item3)
re1or2Bars           = r'([^\s\|]+)\s*\|\s*([^\s\|]+)(\s*|\s*(.+))?$'

# Regular Expression for matching lines with format "item1 | items2 [| items3 [| item4 [| item5 [| item6]]]]
# Groups: 1=>item1, 2->item2, 4=>optional item3, 6=>optional item4, 8=>optional item5, 10=>optional item6
re1to5Bars            = r'([^\s\|]+)\s*\|\s* ([^\s\|]+) (\s*\|\s*([^\s\|]+))? (\s*\|\s*([^\s\|]+))? (\s*\|\s*([^\s\|]+))? (\s*\|\s*([^\s\|]+))?'

# Regular Expression for matching lines with format "item1 [ items2 [ items3 [ item4 [ item5 [ item6 [ item7 [ item8 ]]]]]]
# Groups: 1=>item1, 2->optional item2, 3=>optional item3, 4=>optional item4, 5=>optional item5, 6=>optional item6, 7=>optional item7, 8=>optional item8
re1to8Items           = r'^([^\s]+)\s*([^\s]+)?\s*([^\s]+)?\s*([^\s]+)?\s*([^\s]+)?\s*([^\s]+)?\s*([^\s]+)?\s*([^\s]+)?$'

### Regular expressions for use in any UEFI file
################################################

# Regular expression for matching lines with format "DEFINE item = [value]"
# Groups 1=>DEFINE, 2=>item, 3=optional value (Note DEFINE and = are required)
reDefine              = r'^(DEFINE)\s+' + reFirmEquate

### Regular expressions for BuildArgs.txt files
###############################################

# Regular Expression for matching lines with format "-D variable [= [value]]"
# Groups 1=>variable, 3=>optional value (Note = is always required)
reEnvironmentVariables = r'^' + reFirmEquate

# Regular Expression for matching lines with format "-<char>|--<word> [arg [= [value]]]"
# Groups 2=>-<char> or --<word>, 4=>optional arg, 6=>optional value (Note = is only required if value is specified)
reHpBuildArgs          = r'^((-[a-zA-Z]|--[a-zA-Z0-9_]+)\s+)(' + reSoftEquate[0:-1] + r')?$'

# Regular Expression for matching lines with format "pyfile:function(arguments)"
# Groups 1=>pyfile, 2=>function, 3=>arguments
rePythonScripts        = r'^([^;]+);([^\(]+)\(([^\)]*)\)'

### Regular expressions for ChipsetInfo.txt files
#################################################

# Regular Expression for matching lines with format "binary = path"
# Groups 1=>binary, 2=path
reBinariesEqu          = r'^' + reFirmEquate

# Regular Expression for matching lines with format "-D arg [= [value]]"
# Groups 1=>arg, 3=>optional value
# reHpBuildArgs same as above

# Regular Expression for matching lines with format "package"
# Groups 1=>package
rePlatformPackages     = r'^' + reToEOL

# Regular Expression for matching lines with format "version = snap"
# Groups 1=>version, 2=snap
reSnaps                = r'^' + reHardEquate

# Regular Expression for matching lines with format "tag"
# Groups 1=>tag
reTagExceptions        = r'^' + reToEOL

# Regular Expression for matching lines with format "patch = name"
# Groups 1=>patch, 2=name
reuPatches             = r'^' + reHardEquate

### Regular expressions for DSC files
#####################################

# Regular Expression for matching lines with format "[[tag]:] option = value [\]"
# Groups 2=>optional tag, 3=>option, 4=>optional value, 5=>optional \ (line continuation indicator)
reBuildOptions         = r'^(([^:]+):)?\s*([^\s=]+)\s*=\s*([^\\]+)?(\\)?$'

# Regular expression for matching lines with format "inf [{]"
# Groups 1=>inf, 3=>optional { (subsection start indicator)
reComponents           = r'^([^\s\{]+)(\s*(\{)?)?$'

# Regular expression for matching lines with format "value | name"
# Groups 1=>value, 3=>name.
reDefaultStores        = r'^' + re1Bar

# Regular expression for matching lines with format "value = name"
# Groups 1=>value, 2=>name
reDefines              = r'^' + reFirmEquate 

# Regular expression for matching lines with format "EDK_GLOBAL item = [value]"
# Groups 1=>EDK_GLOBAL, 2=>item, 3=optional value (Note the = is always required)
reEdkGlobals           = reDefine.replace('DEFINE', 'EDK_GLOBAL')

# Regular expression for matching lines with format "name | path"
# Groups 1=>name, 3=>optional path
reLibraryClasses       = r'^' + re1Bar

# Regular expression for matching lines with format "group.pcd[ | item1 [ | item2 [ | item3 [ | item4 [| item5]]]]]"
# Groups 1=>space, 2=>pcd, 4=>optional item1, 6=>optional item2, 8=>optional item3, 10=>optional item4, 12=>optional item5, 13=>optional subsection marker
reItem                 = r'\s*\|\s*(L?\"[^\"]+\"|\{[^\}]+\}|[^\s\|\{}]+)'
rePcds                 = fr'^([^\.]+)\.([^\s\|]+)({reItem}({reItem}({reItem}({reItem}({reItem}?)?)?)?)?)?' + r'\s*(\{)?$'

# Regular expression for matching lines with format "value | skuid [ | [parent]]"
# Groups 1=>value, 2=>skuid, 4=>optional parent
reSkuIds               = r'^' + re1or2Bars

# Regular expression for matching lines with format "extension"
# Groups 1=>extension
reUserExtensions       = r'^' + reToEOL

### Regular expressions for INF files
#####################################

# Regular expression for matching lines with format "kind | path [| tag1 [| tag2 [| tag3 [| tag4]]]]"
# Groups 1=>kind, 2=>path, 4=>optional tag1 6=>optional tag2 8=>optional tag3 10=>optional tag4
reBinariesBar          = r'^' + re1to5Bars

# Regular Expression for matching lines with format "[[tag]:] option = value [\]"
# Groups 2=>optional tag, 3=>option, 4=>value, 5=>optional \ (line continuation indicator)
# reBuildOptions same as above

# Regular expression for matching lines with format "value = name"
# Groups 1=>value, 2=>name
# reDefines same as above

# Regular expression for matching lines with format "dependency"
# Groups 1=>dependency
reDepex                = r'^' + reToEOL

# Regular expression for matching lines with format "group.pcd[ | item1 [ | item2 [ | item3 [ | item4 [| item5]]]]]"
# Groups 1=>space, 2=>pcd, 4=>optional item1, 6=>optional item2, 8=>optional item3, 10=>optional item4, 12=?optional item5
# rePcds same as above

# Regular expression for matching lines with format "guid = value"
# Groups 1=>guid, 3=>optional value
reGuids                = r'^([^=\s]+)\s*(=\s*(' + reNext + r'))?$'

# Regular expression for matching lines with format "include"
# Groups 1=>include
reIncludes             = r'^' + reToEOL

# Regular expression for matching lines with format "include"
# Groups 1=>include
rePackages             = r'^' + reToEOL

# Regular expression for matching lines with format "ppi [ = value ]"
# Groups 1=>ppi 2=>optional value (Note: = only required when optional value is given)
rePpis                 = r'^([^=\s]+)\s*(=\s*(' + reNext + r'))?$'

# Regular expression for matching lines with format "protocol [ | [not] space.pcd ]"
# Groups 1=>protocol, 4=>optional not, 6=>optional space, 7=>optional pcd (Note: | only required when optional pcd is given)
reProtocolsBar         = r'^([^\s\|]+)(\s*\|\s*((NOT)\s+)?(([^\.]+)\.)?(.+))?$'

# Regular expression for matching lines with format "path'
# Groups 1=>path
reSources              = r'^' + re1to8Items

# Regular expression for matching lines with format "extension"
# Groups 1=>extension
# reUserExtensions same as above

### Regular expressions for DEC files
#####################################

# Regular expression for matching lines with format "value = name"
# Groups 1=>value, 2=>name
# reDefines same as above

# Regular expression for matching lines with format "guid = value"
# Groups 1=>guid, 3=>optional value
# reGuids same as above

# Regular expression for matching lines with format "include"
# Groups 1=>include
# reIncludes same as above

# Regular expression for matching lines with format "name | path"
# Groups 1=>name, 3=>optional path
# reLibraryClasses same as above

# Regular expression for matching lines with format "group.pcd[ | item1 [ | item2 [ | item3 [ | item4 [| item5]]]]]"
# Groups 1=>space, 2=>pcd, 4=>optional item1, 6=>optional item2, 8=>optional item3, 10=>optional item4, 12=>optional item5, 13=>optional subsection marker
# rePcds same as above

# Regular expression for matching lines with format "ppi = value"
# Groups 1=>ppi, 3=>optional value
# rePpis same as above

# Regular expression for matching lines with format "protocol = value"
# Groups 1=>protocol, 3=>value
reProtocolsEqu         = r'^([^=\s]+)\s*(=\s*(' + reNext + r'))$'

# Regular expression for matching lines with format "extension"
# Groups 1=>extension
# reUserExtensions same as above

# Regular expression for matching lines with format "include"
# Groups 1=>include
# rePackages same as above

# Regular expression for matching lines with format "path"
# Groups 1=>path
reHeaderFiles          = r'^' + reToEOL

### Regular expressions for FDF files
#####################################

# Regular expression for matching lines with format "token = value"
# Groups 1=>DXE|PEI, 2=>subsection marker
reApriori              = r'^APRIORI\s+(PEI|DXE)\s*(\{)$'

# Regular expression for matching lines with format "token = value"
# Groups 1=>token, 2=>value
reCapsule              = r'^' + reFirmEquate

# Regular expression for matching lines with format "value = name"
# Groups 1=>value, 2=>name
# reDefines same as above

# Regular expression for matching lines with format "0x??, 0x?? ..."
# Groups 1=>optional options, 2=>inf
reHexNumber            = r'0x[0-9A-F][0-9A-F]?'
reData                 = r'^((' + reHexNumber + r'\s*,\s*)+(' + reHexNumber + ')?)$'

# Regular expression for matching lines with format "DATA = {"
# Groups 1=>optional options, 2=>inf
reDataStart            = r'^DATA\s+=\s+{$'

# Regular expression for matching lines with format "}"
# Groups None
reEndBrace             = r'^\}'

# Regular expression for matching lines with format "FILE type = guid [options]"
# Groups 1=>type, 2=>quid, 3=optional options
#reFile                 = r'^FILE\s+([^=\s]+)\s*=\s*([^\s\{]+)\s*([^\s\{]+)*\s*\{'
reFile                 = r'^FILE\s*([^=\s]+)\s*=\s*([^\s\{]+)\s*([^\{]+)?\{$'

# Regular expression for matching lines with format "INF [options] inf"
# Groups 1=>optional options, 2=>inf
reInf                  = r'^INF\s+(([^\s=]+)\s*=\s*(\"[^\"]+\"|[^\s]+)\s+)*' + reToEOL

# Regular expression for matching lines with format "offset | size"
# Groups 1=>offset, 2=>size
reOfsSz                = r'^' + re1Bar

# Regular expression for matching lines with format "value = name"
# Groups 1=>value, 2=>name
reRule                 = r'^' + reToEOL

# Regular expression for matching lines with format FILE type = guid [CHECKSUM]"
# Groups 1=>type, 2=>quid, 3=optional CHECKSUM
reSection              = r'^SECTION\s+([^\{]+)(\{)?$'

# Regular expression for matching lines with format "value = name"
# Groups 1=>set, 2=>pcd, 2=>value
reSet                 = r'^(set)\s+' + reFirmEquate

# Regular expression for matching lines with format "path"
# Groups 1=>path, 2=>options descriptor continuaton character, {
rePath                = r'^([^\{]+)(\{)?$'

# Global Variables
BasePath                = None
Paths                   = []

# Macro definitions used in expansion
MacroVer                = 0
Macros                  = {}

# For keeping track of the files
ARGs                    = {}
DSCs                    = {}
INFs                    = []
DECs                    = []
FDFs                    = {}

# For limiting the architectures
SupportedArchitectures  = []

# Determine if this is Windows OS
isWindows  = 'WINDOWS' in platform.platform().upper()

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
    if not macro in Macros or str(Macros[macro]) != str(value):
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
# Get section string
# returns section[.arch[.extra]]
def GetSection(section):
    value  = '['
    sep    = ''
    for sect in section:
        value += sep + sect
        sep   = '.'
    return value + ']'

# PcdsDynamicExVpd and PcdsDynamicVpd can have two possible option name sets
# this:   object to which the PCD line belongs
# match:  result of the regular expressuion match
# line:   entire PCD line
# returns correct option names for the PCD line in question
def GetVpdOptionNames(this, match, line):
    if match.group(4): return ['pcdtokenspaceguidname', 'pcdname', 'vpdoffset', 'maximumdatumsize', 'value']
    return                    ['pcdtokenspaceguidname', 'pcdname', 'vpdoffset', 'value']

def FixUndefined(string):
        # Look for all macros in the line (format "$(<macroName>)")
        matches = re.findall(r'__([a-zA-Z0-9_]+)__UNDEFINED__', string)
        # Loop through all ocurrances
        for match in matches:
            # Replace __macroName__UNDEFINED__ with $(macroName)
            string = string.replace(f'__{match}__UNDEFINED__', f'$({match})')
        # Return expanded line
        return string

# Base class for all UEFI file types
class UEFIParser:
    ConditionalDirectives = ['if', 'ifdef', 'ifndef', 'elseif', 'else', 'endif']
    AllArchitectures      = ['AARCH32', 'AARCH64', 'IA32', 'RISCV64', 'X64']
    AllTooling            = ['EDK', 'EDKII']
    ConversionMap         = {
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

    # Class constructor
    # fileName:             File to be parsed
    # sectionsInfo:         Dictionary of allowed section names indicating how to handle them
    # allowIncludes:        True if !include directive is supported
    # allowConditionals:    True if conditional directives (!if, !ifdef, !ifndef, !else, !elseif, !endif) are supported
    # additionalDirectives: List of allowed directives other than include and conditionals (default is [] for None)
    # sections:             Starting sections (default is [] for None)
    #                       An array is used because multiple sections can be defined at a time
    # process:              Starting processing state (default is True)
    # outside:              Function for handling lines outside of sections (default is None)
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

    def __init__(self, fileName, sectionsInfo, allowIncludes = False, allowConditionals = False, additionalDirectives = [], sections = [], process = True, outside = None):
        global MacroVer
        # Save given information
        self.fileName             = fileName
        self.sectionsInfo         = sectionsInfo
        self.allowIncludes        = allowIncludes
        self.allowConditionals    = allowConditionals
        self.additionalDirectives = additionalDirectives
        self.sections             = sections
        self.process              = process
        self.outside              = outside
        # Initialize other needed items
        self.lineContinuation     = None                       # Indicates that previous line did not end with a line continuation character
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

    ###################
    # Private methods #
    ###################

    # Looks for and removes any comments
    # line: line on which to look for potential comments
    # returns Line with comments removed or None if entire line was a comment
    def __removeComments__(self, line):
        global SHOW_COMMENT_SKIPS
        placeholders = []
        def replaceString(match):
            # Replace string literal with a placeholder
            placeholders.append(match.group(0))
            return f'__STRING_LITERAL_{len(placeholders)-1}__'
        line = line.strip()
        # Handle case where currently in a comment block
        if self.commentBlock:
            # Look for exit from comment block
            if line.endswith("*/"): self.commentBlock = False
            if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
            return None
        else:
            # Look for comment lines 
            if not line or (line.startswith('#') or line.startswith(';') or line.startswith("/*")):
                if Debug(SHOW_COMMENT_SKIPS): print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
                # Look for entry into comment block
                if line.startswith("/*"): self.commentBlock = True
                return None
        # Replace strings with placeholders
        line    = re.sub(r'".*?"', replaceString, line)
        line    = re.sub(r"'.*?'", replaceString, line)
        # Remove any trailing comments
        #pattern = """[ \t]\#.*|("(?:\\[\S\s]|[^"\\])*"|'(?:\\[\S\s]|[^'\\])*'|[\S\s][^"'#]*))"""
        line    = line.split('#')[0]
        line    = re.sub(r'[ \t]+;.+$', '', line)
        line    = re.sub(r'//[a-zA-Z0-9\*_ \t]+$', '', line)
        # Restore strings from placeholders
        for i, placeholder in enumerate(placeholders):
            line = line.replace(f'__STRING_LITERAL_{i}__', placeholder)
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

    # Indicates if a particular section is a supported architecture and tooling
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
        # Eliminate sections that do not conform to the architecture convention
        if not arch in self.AllArchitectures: return True
        if arch in SupportedArchitectures:
            # Eliminate sections that do not have a tooling portion
            if len(section) < 3:              return True
            third = section[2].upper
            # Eliminate sections that do not conform to tooling convention
            if not third in self.AllTooling:  return True
            if third == 'EDKII':              return True
        if Debug(SHOW_SKIPPED_ARCHITECTURES): print(f"{self.lineNumber}:SKIPPED - unsupported section {GetSection(section)}")
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

    # Check results of regular expression match
    # match:   Regular expression result
    # usage:   Group usage string (character at each index indicates how that group is to be used)
    #          ' ' - Skip group(index+1)
    #          'R' - group(index+1) is required (cannot be empty string or None
    #          'O" - group(inde*x+1) is optional (may be empty and will be set to empty if None)
    #          'X' - group(index+1) is forbidden (must be empty or None)
    # line:    Line being processed (for error message)
    # returns a tuple of a True if there were no error or false if there were errors
    #                 followed by a the list values of each of the groups listed in items (some may be '')
    def __handleMatch__(self, match, usage, line):
        noError = False
        values  = []
        # Handle case where match is no good
        if not match: self.ReportError(f'Invalid {self.section[0]} format: {line}')
        else:
            # Loop through groups to check
            for g, u in enumerate(usage):
                if u == ' ': continue   # Skip unused groups
                g += 1                  # Adjust group index
                # Get value (take care of case where value was not given)
                value = "" if match.group(g) == None else match.group(g)
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
    
    # Add an entry into a database if entries
    # this:   Object in which database entry is comes
    # names:  List of attribute names  for this entry
    # values: List of attribute values for this entry (same order/size as names)
    # key:    Name of attribute that is to be the key value
    # db:     Database into which the entry is to be placed
    # debug:  Debug setting to check for output purposes
    # returns nothing
    def __updateAttribute__(self, names, values, attribute, debug):
        attribute = getattr(self, attribute)
        entry = {}
        # Init secion and file info
        entry['section']    = self.section
        # Initialize file data
        entry['fileName']   = self.fileName
        entry['lineNumber'] = self.lineNumber
        # Copy map to class
        if Debug(debug): msg = f"{self.lineNumber}:{self.sectionStr}"
        for i, name in enumerate(names):
            value = values[i]
            entry[name] = value
            if Debug(debug):
                if value == None or type(value) is str and value == '': continue
                msg = msg + f"{name}={value} "
        # Add entry to the attribute
        attribute.append(entry)
        # Show info if debug is enabled
        if Debug(debug): print(msg.rstrip())

    # Call the section handler or the default section handler for the indicated section and line
    # section: Section which is to be handled
    # line:    Line    which is to be handled
    # returns nothing
    def __dispatchSectionHandler__(self, section, line):
        # Get section info
        info = self.sectionsInfo[section]
        # Match to appropriate regular expressions
        regExes = info[1]
        if type(regExes) is list:
            for idx, regEx in enumerate(regExes):
                match = re.match(regEx, line, re.IGNORECASE)
                if match: break
        else:
            idx   = None
            match = re.match(regExes, line, re.IGNORECASE)
        # Get appropriate handler arguments
        args = info[2] if idx == None else info[2][idx]
        # Call the handler
        good, items = self.__handleMatch__(match, args[0], line)
        if good:
            # Update attribute (if any)
            attribute = args[1]
            if attribute:
                # Get names (might need to be called)
                names = args[2]
                if callable(names): names = names(self, match, line)
                self.__updateAttribute__(names, items, attribute, info[0])
            # Call the named handler if present and callable
            handler = getattr(self, f"section_{section}", None)
            if handler and callable(handler):
                handler(idx, match)
        # else taken care of in __handleMatch__

    # Handle subsection process (not call unless section supports subsections)
    # line: Line which is to be handled
    def __handleSubsection__(self, line):
        global SHOW_SUBSSECTION_EXIT
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        # Look for end of subsection block
        if line.endswith("}") and self.inSubsection:
            # Signal end of subsection block and subsection
            self.inSubsection = False
            self.subsections  = None
            if Debug(SHOW_SUBSSECTION_EXIT): print(f"{self.lineNumber}:Exiting subsection")
            return
        # Look for subsection marker
        if "<" in line:
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
        # Handle case where a subsection was already marked
        elif self.subsections:
            # Save current section info
            sections          = self.sections
            # Set subsection info
            self.sections     = self.subsections
            # Process the section line (ignoring subsections)
            self.__handleIndividualLine__(line, True)
            # Restore the original section info
            self.sections     = sections
            return
        self.__dispatchSectionHandler__(self.section[0], line)

    # Handles line continuations
    # line: Line to handle
    # returns nothing
    def __handleLineContinuation__(self, line):
        print(f'{self.lineNumber}:Line continuation handling is TBD')

    # Handles an individual line that is not a directive or section header
    # line:             Line to be handled
    # ignoreSubsection: When True will ignore the inSubsection setting
    # returns nothing
    def __handleIndividualLine__(self, line, ignoreSubsection = False):
        # See if a line continuation is being processed
        if self.lineContinuation:
            self.__handleLineContinuation__(line)
        # See if subsection is being processed
        elif not ignoreSubsection and self.inSubsection:
            self.__handleSubsection__(line)
        # Must be in a section
        elif bool(self.sections):
            # Process line inside of each of the current sections
            for self.section in self.sections:
                # Make sure architecture is supported
                if self.__sectionSupported__(self.section):
                    self.sectionStr = GetSection(self.section)
                    self.__dispatchSectionHandler__(self.section[0], line)
                # Else taken care of in __sectionSupported__ method!
        # Lines outside of a section are usually not allowed
        else:
            # See if outside line handler is installed
            if self.outside:
                self.outside(self, line)
            else:
                self.ReportError(f"Unsupported line discovered outside of a section")

    # Expandes all macros within a line
    # line: line in which macros are to be expanded
    # returns line with macros expanded
    # Note: Undefined macros will appear as __<marco>__UNDEFINED__
    def __expandMacros__(self, line):
        global Macros
        # Look for all macros in the line (format "$(<macroName>)")
        matches = re.findall(r'\$\(([^\)]+)\)', line)
        # Loop through all ocurrances
        for match in matches:
            # Replace the macro with its value (or __<macroName>__UNDEFINED__ if it is not defined)
            value = str(Macros[match]).replace('"', '') if match in Macros else F"__{match}__UNDEFINED__"
            line = line.replace(f"$({match})", '""' if not value else value)
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
                line = self.__removeComments__(line)
                if not line: continue
                # Expand macros before parsing
                line = self.__expandMacros__(line)
                # Handle directives (if any)
                if self.__handleDirective__(line):  continue
                # Conditional processing may indicate to ignore
                if not self.process:
                    if Debug(SHOW_CONDITIONAL_SKIPS): print(f"{self.lineNumber}:SKIPPED - Conditionally")
                    continue
                # Handle DEFINE lines anywhere
                match = re.match(reDefine, line, re.IGNORECASE)
                if match:
                    value = match.group(3)
                    self.DefineMacro(match.group(2), value if value != None else '')
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
        pattern = r'(\+\+|--|->|<<=|>>=|<=|>=|==|!=|&&|\|\||\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|\?|:|~|!|<|>|=|\+|\-|\*|/|%|&|\||\^|\(|\)|\[|\]|{|}|;|,)'
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
    # TBD ... Need to add evaulation of GUIDS
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
                     result = result.replace(f"{undefinedMacro}", 'None')
                try:
                    # Try to interpret it
                    result = eval(result)
                except:
                    # Surround any un evalueated values with quotes and try one more time
                    items = result.split()
                    for i, item in enumerate(items):
                        if item[0] == '"':               continue
                        if item[0] in '+-*/%=&|^><!':    continue
                        if item in ['and', 'or', 'not']: continue
                        items[i] = '"' + items[i] + '"'
                    result = ' '.join(items)
                    try:
                        result = eval(result)
                    except:
                        pass        # What else can be done here!
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

    # Defines a new macro
    # line: line containing the macro
    # returns nothing
    def DefineMacro(self, macro, value):
        global Macros, SHOW_MACRO_DEFINITIONS
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

    # Used to mark entry into a subsection
    def EnterSubsection(self):
        # This only needs to happen for first section in sections that are grouped together
        if self.sections.index(self.section) == 0:
            # Make sure previous subsection is done
            if self.inSubsection:
                self.ReportError('Unable to enter subsection because already in subsection')
                return
            self.inSubsection = True
            if Debug(SHOW_SUBSECTION_ENTER): print(f'{self.lineNumber}:Entering subsection')

# Class for parsing HPE Build Args files (PlatformPkgBuildArgs.txt)
class ArgsParser(UEFIParser):                        #debug,                        regularExpression(s),   arguments
    BuildArgsSections = { 'environmentvariables':    (SHOW_ENVIRONMENTVARIABLES,    reEnvironmentVariables, ('R O',    'ENVIRONMENTVARIABLES', ['variable', 'value'])),
                          'hpbuildargs':             (SHOW_HPBUILDARGS,             reHpBuildArgs,          (' R O O', 'HPBUILDARGS',          ['option',   'arg',  'value'])),
                          'pythonbuildfailscripts':  (SHOW_PYTHONBUILDFAILSCRIPTS,  rePythonScripts,        ('RRO',    'PYTHONSCRIPTS',        ['pyfile',   'func', 'args'])),
                          'pythonprebuildscripts':   (SHOW_PYTHONPREBUILDSCRIPTS,   rePythonScripts,        ('RRO',    'PYTHONSCRIPTS',        ['pyfile',   'func', 'args'])),
                          'pythonprehpbuildscripts': (SHOW_PYTHONPREHPBUILDSCRIPTS, rePythonScripts,        ('RRO',    'PYTHONSCRIPTS',        ['pyfile',   'func', 'args'])),
                          'pythonpostbuildscripts':  (SHOW_PYTHONPOSTBUILDSCRIPTS,  rePythonScripts,        ('RRO',    'PYTHONSCRIPTS',        ['pyfile',   'func', 'args'])),
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

    ######################
    # Directive handlers #
    ######################

    # Handle the Include directive
    # line: File to be included
    # returns nothing
    def directive_include(self, line):
        global ARGs
        def includeHandler(file):
            ARGs[file] = ChipsetParser(file)
        self.IncludeFile(line, includeHandler)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [EnvironmentVariables] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_environmentvariables(self, idx, match):
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        if match:
            variable = match.group(1)
            value    = match.group(3) if match.group(3) != None else ''
            self.DefineMacro(variable, value.replace('\\', '/'))
            os.environ[variable] = value
        # Else already taken care of

    # Handle a line in the [HpBuildArgs] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_hpbuildargs(self, idx, match):
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        if match:
            if match.group(2) == '-D':
                macro = match.group(4)
                if not macro:
                    self.ReportError(f'Unsupported -D line in HpBuildArgs section {match.group(0)}')
                    return
                value = match.group(6) if match.group(6) != None else ''
                self.DefineMacro(macro, value)
        # Else already taken care of

    def DumpHpBuildArgs(self):
        if bool(self.HPBUILDARGS):
            print('    HpBuildArgs:')
            for i, item in enumerate(self.HPBUILDARGS):
                arg   = '' if not 'arg'   in item else  ' ' + item['arg']
                value = '' if not 'value' in item else  '=' + FixUndefined(item['value'])
                print(f"        {i}:{item['option']}{arg}{value}")

    def Dump(self):
        if bool(self.ENVIRONMENTVARIABLES):
            print('    EnvironmentVariables:')
            for i, item in enumerate(self.ENVIRONMENTVARIABLES):
                value = '' if not 'value' in item else FixUndefined(item['value'])
                print(f"        {i}:{item['variable']}={value}")
        if bool(self.PYTHONSCRIPTS):
            print('    PythonScripts:')
            for i, item in enumerate(self.PYTHONSCRIPTS):
                args  = '' if not 'args'  in item else  FixUndefined(item['args'])
                print(f"        {i}:{FixUndefined(item['pyfile'])}:{item['func']}({args})")

# Class for parsing HPE Chipset files (HpChipsetInfo.txt)
class ChipsetParser(UEFIParser):           #debug,                  regularExpression(s), arguments
    ChipsetSections = { 'binaries':         (SHOW_BINARIES,         reBinariesEqu,        ('RR',     'BINARIES',         ['binary',  'path'])),
                        'hpbuildargs':      (SHOW_HPBUILDARGS,      reHpBuildArgs,        (' R O O', 'HPBUILDARGS',      ['option',  'arg', 'value'])),
                        'platformpackages': (SHOW_PLATFORMPACKAGES, rePlatformPackages,   ('R',      'PLATFORMPACKAGES', ['package'])),
                        'snaps':            (SHOW_SNAPS,            reSnaps,              ('RR',     'SNAPS',            ['version', 'snap'])),
                        'tagexceptions':    (SHOW_TAGEXCEPTIONS,    reTagExceptions,      ('R',      'TAGEXCEPTIONS',    ['tag'])),
                        'upatches':         (SHOW_UPATCHES,         reuPatches,           ('RR',     'UPATCHES',         ['patch',   'name'])),
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

    # Handle a line in the [HpBuildArgs] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_hpbuildargs(self, idx, match):
        ArgsParser.section_hpbuildargs(self, idx, match)

    def DumpSingle(self, lst, title, field, fixup = False):
        if bool(list):
            print(f'    {title}:')
            for i, item in enumerate(lst):
                value = FixUndefined(item[field]) if fixup else item[field]
                print(f"        {i}:{value}")

    def Dump(self):
        if bool(self.BINARIES):
            print('    Binaries:')
            for i, item in enumerate(self.BINARIES):
                print(f"        {i}:{item['binary']} {FixUndefined(item['path'])}")
        ArgsParser.DumpHpBuildArgs(self)
        if bool(self.PLATFORMPACKAGES):
            print('    PlatformPkgs:')
            for i, item in enumerate(self.PLATFORMPACKAGES):
                print(f"        {i}:{FixUndefined(item['package'])}")
        if bool(self.SNAPS):
            print('    Snaps:')
            for i, item in enumerate(self.SNAPS):
                print(f"        {i}:{item['version']}={item['snap']}")
        self.DumpSingle(self.TAGEXCEPTIONS, 'TagExceptions', 'tag')
        if bool(self.UPATCHES):
            print('    uPatches:')
            for i, item in enumerate(self.UPATCHES):
                print(f"        {i}:{item['patch']} {item['name']}")

# Class for handling UEFI DSC files
class DSCParser(UEFIParser):                 #debug,               regularExpression(s),       arguments
    DSCSections = { 'buildoptions':          (SHOW_BUILDOPTIONS,   reBuildOptions,             (" ORO",         'BUILDOPTIONS',   ['tag', 'option', 'value'])),
                    'components':            (SHOW_COMPONENTS,     reComponents,               ("R",            'COMPONENTS',     ['inf'])),
                    'defaultstores':         (SHOW_DEFAULTSTORES,  reDefaultStores,            ("R R",          'DEFAULTSTORES',  ['value', 'name'])),
                    'defines':               (SHOW_DEFINES,        [reDefines, reEdkGlobals],  [("RO",          'DEFINES',        ['macro', 'value']),
                                                                                                ("ORO",         'DEFINES',        ['macro', 'value'])]),
                    'libraryclasses':        (SHOW_LIBRARYCLASSES, reLibraryClasses,           ("R R",          'LIBRARYCLASSES', ['name', 'path'])),
                    'pcdsdynamic':           (SHOW_PCDS,           rePcds,                     ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdsdynamicdefault':    (SHOW_PCDS,           rePcds,                     ("RR R O X X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdsdynamicex':         (SHOW_PCDS,           rePcds,                     ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdsdynamicexdefault':  (SHOW_PCDS,           rePcds,                     ("RR O O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdsdynamicexhii':      (SHOW_PCDS,           rePcds,                     ("RR R R R O O", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'variablename', 'variableguid', 'variableoffset', 'hiidefaultvalue', 'hiiattribute'])),
                    'pcdsdynamicexvpd':      (SHOW_PCDS,           rePcds,                     ("RR R O O X X", 'PCDS',           GetVpdOptionNames)),
                    'pcdsdynamichii':        (SHOW_PCDS,           rePcds,                     ("RR R R R O O", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'variablename', 'variableguid', 'variableoffset', 'hiidefaultvalue'])),
                    'pcdsdynamicvpd':        (SHOW_PCDS,           rePcds,                     ("RR R O O X X", 'PCDS',           GetVpdOptionNames)),
                    'pcdsfeatureflag':       (SHOW_PCDS,           rePcds,                     ("RR O X X X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value'])),
                    'pcdsfixedatbuild':      (SHOW_PCDS,           rePcds,                     ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdspatchableinmodule': (SHOW_PCDS,           rePcds,                     ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'skuids':                (SHOW_SKUIDS,         reSkuIds,                   ("RRO",          'SKUIDS',         ['value', 'skuid', 'parent'])),
                    'userextensions':        (SHOW_USEREXTENSIONS, reUserExtensions,           ("R",            'USEREXTENSIONS', ['ext'])),
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

    # Handle a line in the [BuildOptions] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_buildoptions(self, idx, match):
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        # Look for line continuation character
        if match and match.group(5):
            self.lineContinuation = True

    # Handle a line in the [Components] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_components(self, idx, match):
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        # Look for subsection entry
        if match and match.group(3) and match.group(3) == '{':
            self.EnterSubsection()

    # Handle a line in the [Defines] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_defines(self, idx, match):
        # There are two possible match patterns
        if match:
            macro, value = (match.group(1), match.group(2)) if len(match.groups()) == 2 else (match.group(2), match.group(3))
            self.DefineMacro(macro, value if value != None else '')
        # Else already taken care of

    # Handle a line in the [libraryclasses] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_libraryclasses(self, idx, match):
        global INFs
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        INFs.append( (self.fileName, self.lineNumber, match.group(3).replace('"', '')) )

    def DumpBuildOptions(self):
        if bool(self.BUILDOPTIONS):
            print('    BuildOptions:')
            for i, item in enumerate(self.BUILDOPTIONS):
                tag   = '' if not 'tag'   in item else item['tag'] + ':'
                value = '' if not 'value' in item else '=' + FixUndefined(item['value'])
                print(f"        {i}:{tag}{item['option']}{value}")

    def DumpDefines(self):
        if bool(self.DEFINES):
            print('    Defines:')
            for i, item in enumerate(self.DEFINES):
                value = '' if item['value'] == None else FixUndefined(item['value'])
                print(f"        {i}:{item['macro']}={value}")

    def DumpLibraryClasses(self):
        if bool(self.LIBRARYCLASSES):
            print('    LibraryClasses:')
            for i, item in enumerate(self.LIBRARYCLASSES):
                print(f"        {i}:{item['name']}|{FixUndefined(item['path'])}")

    def DumpPcds(self):
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

    def DumpUserExtensions(self):
        ChipsetParser.DumpSingle(self, self.USEREXTENSIONS, 'UserExtensions', 'ext')

    def Dump(self):
        self.DumpBuildOptions()
        ChipsetParser.DumpSingle(self, self.COMPONENTS, 'Components', 'inf', True)
        if bool(self.DEFAULTSTORES):
            print('    DefaultStores:')
            for i, item in enumerate(self.DEFAULTSTORES):
                print(f"        {i}:{item['value']}|{item['name']}")
        self.DumpDefines()
        self.DumpLibraryClasses()
        self.DumpPcds()
        if bool(self.SKUIDS):
            print('    SkuIds:')
            for i, item in enumerate(self.SKUIDS):
                parent = '' if not 'parent' in item else '|' + item['parent']
                print(f"        {i}:{item['value']}|{item['skuid']}{parent}")
        self.DumpUserExtensions()

# Class for handling UEFI INF files
class INFParser(UEFIParser):                 #debug,               regularExpression(s), arguments
    INFSections = { 'binaries':              (SHOW_BINARIES,       reBinariesBar,        ("RR O O O O",   'BINARIES',       ['kind', 'path', 'tag1', 'tag2', 'tag3', 'tag4'])),
                    'buildoptions':          (SHOW_BUILDOPTIONS,   reBuildOptions,       (" ORO",         'BUILDOPTIONS',   ['tag', 'option', 'value'])),
                    'defines':               (SHOW_DEFINES,        reDefines,            ("RO",           'DEFINES',        ['macro', 'value'])),
                    'depex':                 (SHOW_DEPEX,          reDepex,              ("R",            'DEPEX',          ['depex'])),
                    'featurepcd':            (SHOW_PCDS,           rePcds,               ("RR O O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'fixedpcd':              (SHOW_PCDS,           rePcds,               ("RR O O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'guids':                 (SHOW_GUIDS,          reGuids,              ("R X",          'GUIDS',          ['guid'])),
                    'includes':              (SHOW_INCLUDES,       reIncludes,           ("R",            'INCLUDES',       ['include'])),
                    'libraryclasses':        (SHOW_LIBRARYCLASSES, reLibraryClasses,     ("R O",          'LIBRARYCLASSES', ['name', 'path'])),
                    'packages':              (SHOW_PACKAGES,       rePackages,           ("R",            'PACKAGES',       ['path'])),
                    'patchpcd':              (SHOW_PCDS,           rePcds,               ("RR O O X X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcd':                   (SHOW_PCDS,           rePcds,               ("RR O O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdex':                 (SHOW_PCDS,           rePcds,               ("RR O O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'ppis':                  (SHOW_PPIS,           rePpis,               ("R X",          'PPIS',           ['ppi'])),
                    'protocols':             (SHOW_PROTOCOLS,      reProtocolsBar,       ("R   OOO",      'PROTOCOLS',      ['protocol', 'not', 'pcdtokenspaceguidname', 'pcdname'])),
                    'sources':               (SHOW_SOURCES,        reSources,            ("ROOOOOOO",     'SOURCES',        ['source', 'source2', 'source3', 'source4', 'source5', 'source6', 'source7', 'source8'])),
                    'userextensions':        (SHOW_USEREXTENSIONS, reUserExtensions,     ("R",            'USEREXTENSIONS', ['ext'])),
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
        self.reference      = [(referenceName, referenceLine)]  # This attribute is handled in a special case
        # Call constructor for parent class
        super().__init__(fileName, self.INFSections)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Packages] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_packages(self, idx, match):
        global DECs
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        if match:
            # Just in case there a some trailing C style comment on the line (which should be an error)!
            DECs.append((self.fileName, self.lineNumber, match.group(1)))
        # Else already taken care of

    def Dump(self):
        if bool(self.BINARIES):
            print('    Binaries:')
            for i, item in enumerate(self.BINARIES):
                values = []
                for field in ['tag1', 'tag2', 'tag3', 'tag4']:
                    values.append(eval("'' if not '{field}' in item else '|' + item['{field}']"))
                print(f"        {i}:{item['type']}.{FixUndefined(item['path'])}{values[0]}{values[1]}{values[2]}{values[3]}")
        DSCParser.DumpBuildOptions(self)
        DSCParser.DumpDefines(self)
        if bool(self.DEPEX):
            depex = ''
            for i, item in enumerate(self.DEPEX):
                items = item['depex'].split()
                depex += ' '.join(items) + ' '
            print(f"    DepEx: {depex.rstrip()}")
        ChipsetParser.DumpSingle(self, self.GUIDS, 'GUIDs', 'guid')
        ChipsetParser.DumpSingle(self, self.INCLUDES, 'Includes', 'include', True)
        DSCParser.DumpLibraryClasses(self)
        ChipsetParser.DumpSingle(self, self.PACKAGES, 'Packages', 'path', True)
        DSCParser.DumpPcds(self)
        if bool(self.PROTOCOLS):
            print('    Protocols:')
            for i, item in enumerate(self.PROTOCOLS):
                inv     = '' if not 'not'                   in item else ' not'
                space   = '' if not 'pcdtokenspaceguidname' in item else ' ' + item['pcdtokenspaceguidname']
                pcdname = '' if not 'pcdname'               in item else '.' + item['pcdname']
                print(f"        {i}:{item['protocol']}{inv}{space}{pcdname}")
        if bool(self.SOURCES):
            print('    Sources:')
            for i, item in enumerate(self.SOURCES):
                values = []
                for field in ['source2', 'source3', 'source4', 'source5', 'source6', 'source7', 'source8']:
                    values.append(eval("'' if not '{field}' in item else '|' + item['{field}']"))
                print(f"        {i}:{item['source']}{values[0]}{values[1]}{values[2]}{values[3]}{values[4]}{values[5]}{values[6]}")
        DSCParser.DumpUserExtensions(self)

# Class for handling UEFI DEC files
class DECParser(UEFIParser):                #debug,                regularExpression(s), arguments
    DECSections = { 'defines':               (SHOW_DEFINES,        reDefines,            ("RO",           'DEFINES',        ['macro', 'value'])),
                    'guids':                 (SHOW_GUIDS,          reGuids,              ("R R",          'GUIDS',          ['guid'])),
                    'includes':              (SHOW_INCLUDES,       reIncludes,           ("R",            'INCLUDES',       ['include'])),
                    'libraryclasses':        (SHOW_LIBRARYCLASSES, reLibraryClasses,     ("R R",          'LIBRARYCLASSES', ['name', 'path'])),
                    'pcdsdynamic':           (SHOW_PCDS,           rePcds,               ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdsdynamicex':         (SHOW_PCDS,           rePcds,               ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdsfeatureflag':       (SHOW_PCDS,           rePcds,               ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdsfixedatbuild':      (SHOW_PCDS,           rePcds,               ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'pcdspatchableinmodule': (SHOW_PCDS,           rePcds,               ("RR R O O X X", 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])),
                    'ppis':                  (SHOW_PPIS,           rePpis,               ("R R",          'PPIS',           ['ppi'])),
                    'protocols':             (SHOW_PROTOCOLS,      reProtocolsEqu,       ("R R",          'PROTOCOLS',      ['protocol'])),
                    'userextensions':        (SHOW_USEREXTENSIONS, reUserExtensions,     ("R",            'USEREXTENSIONS', ['ext'])),
                    # Below are specail section handlers that can only occur when processing a subsection!
                    'packages':              (SHOW_PACKAGES,       rePackages,           ("R",            'PACKAGES',       ['path'])),
                    'headerfiles':           (SHOW_HEADERFILES,    reHeaderFiles,        ("R",            'HEADERFILES',    ['path'])),
    }

    ###################
    # Private methods #
    ###################

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
        # Use same handler for all PCD sections
        handler             = self.section_pcds
        for info in self.DECSections:
            if info.startswith('pcds'):
                setattr(self, f'section_{info}', handler)
        # Call constructor for parent class
        super().__init__(fileName, self.DECSections)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Defines] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_defines(self, idx, match):
        # There are two possible match patterns
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        if match:
            macro, value = (match.group(1), match.group(2)) if len(match.groups()) == 2 else (match.group(2), match.group(3))
            self.DefineMacro(macro, value if value != None else '')
        # Else already taken care of

    # Handle a line in any of the PCD sections
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_pcds(self, idx, match):
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        # See if we need to enter subsection
        if match and match.group(13) and match.group(13) == '{':
            self.EnterSubsection()

    #############################################
    # Section handlers (only when inSubsection) #
    #############################################

    # Handle a line in the [Protocols] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_packages(self, idx, match):
        global DECs
        # Only allow this section handler if in a subsection
        if not self.inSubsection:
            self.ReportError('section packages cannot be used outside of braces')
            return
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')
        if match:
            # Just in case there a some trailing C style comment on the line (which should be an error)!
            DECs.append((self.fileName, self.lineNumber, match.group(1)))
        # Else already taken care of

    # Handle a line in the [Protocols] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_headerfiles(self, idx, match):
        # Only allow this section handler if in a subsection
        if not self.inSubsection:
            self.ReportError('section headerfiles cannot be used outside of braces')
        # No regular expression index is expected!
        if idx != None:
            self.ReportError('Unexpected regular expression index encountered')

    def Dump(self):
        DSCParser.DumpDefines(self)
        ChipsetParser.DumpSingle(self, self.GUIDS, 'GUIDs', 'guid')
        ChipsetParser.DumpSingle(self, self.INCLUDES, 'Includes', 'include', True)
        DSCParser.DumpLibraryClasses(self)
        DSCParser.DumpPcds(self)
        ChipsetParser.DumpSingle(self, self.PPIS, 'PPIs', 'ppi')
        ChipsetParser.DumpSingle(self, self.PROTOCOLS, 'Protocols', 'protocol')
        DSCParser.DumpUserExtensions(self)
        ChipsetParser.DumpSingle(self, self.PACKAGES, 'Packages', 'path', True)
        ChipsetParser.DumpSingle(self, self.HEADERFILES, 'HeaderFiles', 'path', True)


# Class for handling UEFI FDF files
class FDFParser(UEFIParser):   #debug,        regularExpression(s),                    handlerArguments
    FdRegExes   = [reDataStart, reData, reEndBrace, reDefine, reDefines, reSet, reOfsSz]
    FvRegExes   = [reDefine, reSet, reDefines, reApriori, reInf, reFile, reSection, reEndBrace, rePath]
    FDFSections = { 'capsule': (SHOW_CAPSULE, [reSet, reCapsule],                      [(" RR",         'CAPSULES',  ['token', 'value']),
                                                                                        ("RR",          'CAPSULES',  ['token', 'value'])]),
                    'defines': (SHOW_FD,      reDefines,                                ("RO",          'DEFINES',   ['macro', 'value'])),
                    'fd':      (SHOW_FD,      FdRegExes,                               [("",            None,        None),                    # reDataStart
                                                                                        ("R",           None,        None),                    # reData
                                                                                        ("",            None,        None),                    # reEndBrace (for reDataStart)
                                                                                        (" RR",         'FDS',       ['token', 'value']),      # reDefine
                                                                                        ("RR",          'FDS',       ['token', 'value']),      # reDefines
                                                                                        (" RR",         'FDS',       ['token', 'value']),      # reSet
                                                                                        ("R R",         'FDS',       ['offset', 'size'])]),    # reOfsSz
                    'fv':      (SHOW_FV,      FvRegExes,                               [(" RR",         'DEFINES',   ['macro', 'value']),      # reDefine
                                                                                        (" RR",         'FVS',       ['token', 'value']),      # reSet
                                                                                        ("RR",          'FVS',       ['token', 'value']),      # reDefines
                                                                                        ("R",           None,        None),                    # reApriori
                                                                                        ("O  R",        None,        None),                    # reInf
                                                                                        ("RRO",         None,        None),                    # reFile
                                                                                        ("R",           None,        None),                    # reSection
                                                                                        ("",            None,        None),                    # end brace (for reApriori, reFile, and some reSection)
                                                                                        ("R",            None,        None)]),                 # rePath
                    'rule':    (SHOW_RULE,    reRule,                                   ("R",           'RULES',     ['rule'])),
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
                else: DSCs[file] = DSCParser(file, [], True, self.OutsideLineHandler)
            else:
                if file in FDFs and FDFs[file].macroVer == MacroVer:
                    if Debug(SHOW_SKIPPED_FDFS): print(f"{self.lineNumber}:Previously loaded:{file}")
                else: FDFs[file] = FDFParser(file)
        self.IncludeFile(line, includeHandler)

    ####################
    # Section handlers #
    ####################

    # Handle a line in the [Defines] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_defines(self, idx, match):
        pass

    # Handle a line in the [Defines] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_fd(self, idx, match):
        if match:
            if idx == 0:    # reDataStart
                self.data = []
                if Debug(SHOW_FD): print(f'{self.lineNumber}:Entering data list')
            elif idx == 1:  # reData
                data = match.group(0).replace(',', '').split()
                for datum in data:
                    self.data.append(datum)
                if Debug(SHOW_FD): print(f'{self.lineNumber}:{match.group(0)}')
            elif idx == 2:  # reEndBrace
                self.FDS.append(self.data)
                self.data = None
                if Debug(SHOW_FD): print(f'{self.lineNumber}:Exiting data list')

    # Handle a line in the [Defines] section
    # idx:   Index of regular expression used
    # match: Results of regex match
    # returns nothing
    def section_fv(self, idx, match):
        global Files
        def HandleOptionValue(token, msg):
            value  = token
            # Get the saves option
            token  = self.file['options'][-1]
            # Save the option and value
            self.file['options'][-1]={'option': token, 'value': value}
            if Debug(SHOW_FV): msg += f" {token}={value}"
            # Nothing else is expected now
            return (msg, None)
        if match:
            # Depends on regex index
            if idx == 3:  # reApriori
                # Get APRIORI type
                self.apriori               = match.group(1)
                # Start apriori list
                self.APRIORI[self.apriori] = []
                if Debug(SHOW_FV): print(f'{self.lineNumber}:Entering {self.apriori} apriori list')
            elif idx == 4:  # reInf
                # Check for Apriori
                inf = match.group(4)
                if self.apriori:
                    self.APRIORI[self.apriori].append(inf)
                    if Debug(SHOW_FV): print(f'{self.lineNumber}:{inf} added to {self.apriori} list (#{len(self.APRIORI[self.apriori])})')
                # Normal INF entry
                else:
                    if Debug(SHOW_FV): msg = ''
                    # Add any detected options
                    opts = []
                    if match.group(1):
                        items = match.group(1).rstrip().split('=')
                        if len(items) % 2 != 0:
                            self.ReportError('Unbalanced INF options encountered')
                            return
                        for i in range(0, len(items), 2):
                            opt = items[i].rstrip()
                            val = items[i + 1].lstrip()
                            opts.append((opt, val))
                            if Debug(SHOW_FV): msg += f'{opt}={val} '
                    self.INFS.append((inf, opts))
                    if Debug(SHOW_FV): print(f'{self.lineNumber}:INF {inf} {msg}')
            elif idx == 5:  # reFile
                msg = ''
                kind = match.group(1)
                guid = match.group(2)
                self.file = {'type': kind, 'guid': guid, 'options': [], 'sections': []}
                options   = match.group(3)
                if options:
                    expect = None
                    for token in options.split():
                        # Is something expected
                        if expect:
                            # Is an equal expected?
                            if expect == '=':
                                # Was an equal found?
                                if token == '=':
                                    # Now the value is expected
                                    expect = 'value'
                                    continue
                                # Handle case where equal attached to value
                                elif token.startswith('='):
                                    msg, expect = HandleOptionValue(token[1:], msg)
                                    continue
                                else:
                                    self.ReportError('Option {option} missing value')
                                    return
                            # Must be the value that is expected
                            else:
                                msg, expect = HandleOptionValue(token, msg)
                                continue     
                        # See if we have a specail case   
                        option =  token.upper()
                        if option in ['CHECKSUM', 'FIXED']:
                            # Save special option and implied value
                            self.file['options'].append({'option': option, 'value': 'TRUE'})
                            if Debug(SHOW_FV): msg += f" {option}=TRUE"
                        else:
                            # Better have ALIGNEMENT in it
                            if not option.startswith('ALIGNMENT'):
                                self.ReportError('Unsupported FILE option encounteres: {opt}')
                                return
                            # Take care of case where option and value are not seprated by spaces
                            if '=' in option:
                                option = option.replace('=', ' ')
                                items = option.split()
                                option = items[0].upper()
                                if len(items) > 1:
                                    # Save the option and value
                                    value = items[1].strip()
                                    self.file['options'].append({'option': option, 'value': value})
                                    if Debug(SHOW_FV): msg += f" {option}={value}"
                                else:
                                    # = was attached so the value is expected
                                    self.file['options'].append(option)   # Save option for later
                                    expect = 'value'
                            else:
                                # = was not attach so the = is expected
                                self.file['options'].append(token)        # Save option for later
                                expect = '='
                if Debug(SHOW_FV): print(f'{self.lineNumber}:FILE {kind} {guid}{msg}')
                if Debug(SHOW_SUBSECTION_ENTER): print(f'{self.lineNumber}:Entering file descriptor')
            elif idx == 6:  # reSection
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
                if Debug(SHOW_FV): print(f'{self.lineNumber}:SECTION {kind} {value} {msg}')
                if Debug(SHOW_SUBSECTION_ENTER) and kind == 'GUIDED': print(f'{self.lineNumber}:Entering guided section')
            elif idx == 7:  # reEndBrace
                # End apriori list (if applicable)
                if self.apriori != None:
                    # Clear Apriori list
                    if Debug(SHOW_SUBSSECTION_EXIT): print(f'{self.lineNumber}:Exiting {self.apriori} apriori list')
                    self.apriori = None
                # End compressed descriptor (if applicable)
                elif self.compress != None:
                    # TBD add compressed info to whereever it belongs
                    self.compress = None
                # End guided descriptor (if applicable)
                elif self.guided != None:
                    # Add guided descriptor to appropriate item
                    if self.compress != None:
                        self.compress['guided'] = self.guided
                        if Debug(SHOW_SUBSSECTION_EXIT): print(f'{self.lineNumber}:Exiting compress descriptor')
                    elif self.sect != None:
                        self.sect['guided']  = self.guided
                        self.file['sections'].append(self.sect)
                        self.sect            = None
                        if Debug(SHOW_SUBSSECTION_EXIT): print(f'{self.lineNumber}:Exiting guided section')
                    else:
                        self.file['guided']     = self.guided
                        if Debug(SHOW_SUBSSECTION_EXIT): print(f'{self.lineNumber}:Exiting guided descriptor')
                    # Clear guided descriptor
                    self.guided = None
                # End file descriptor (if applicable)
                elif self.file != None:
                    # Add file
                    self.FILES.append(self.file)
                    self.file = None
                    if Debug(SHOW_SUBSSECTION_EXIT): print(f'{self.lineNumber}:Exiting file descriptor')
                else:
                    self.ReportError('End brace found without matching start brace')
            elif idx == 8:  # rePath
                if self.file == None:
                    self.ReportError('FV path not allowed outstide of file description')
                    return
                if self.compress != None or self.guided != None or self.sect != None:
                    self.ReportError('FV path not allowed inside other descriptors')
                    return
                # File type must be RAW
                if not self.file['type'] == 'RAW':
                    self.ReportError('FV path only allowed with RAW file types')
                    return
                path = match.group(1)
                self.file['path'] = path
                if Debug(SHOW_FV): print(f'{self.lineNumber}:{path}')
            #elif idx == 0:    # reDefine
            #    # TBD check what is being defined (there are only a limited set of items allowed!)
            #    pass
            #elif idx == 1:  # reSet
            #    # TBD make sure PCD exists and can be set as indicated
            #    pass
            #elif idx == 2:  # reDefines
            #    # TBD look for BLOCK statements
            #    pass

    def OutsideLineHandler(self, this, line):
        global reFile
        # Save current linenumber and filename
        saved = (self.lineNumber, self.fileName)
        # Assume line number and filename this
        self.lineNumber, self.fileName = (this.lineNumber, this.fileName)
        # Process the outside line
        for i, regEx in enumerate([reFile, reSection, reEndBrace, rePath]):
            match = re.match(regEx, line, re.IGNORECASE)
            if match:
                self.section_fv(i + 5, match)
                break
        else:
            self.ReportError('Unsupported line outside of section')
        # Restore linenumber and filename
        self.lineNumber, self.fileName = saved
    
    def DumpTokenValue(self, list, title):
        if bool(list):
            print(f'    {title}:')
            for i, item in enumerate(list):
                print(f"        {i}:{item['token']}={item['value']}")

    def Dump(self):
        def GetOptions(opts):
            options = ''
            for option in opts['options']:
                options += f" {opts['option']}={opts['value']}"
            return options
        self.DumpTokenValue(self.CAPSULES, 'Capsules')
        DSCParser.DumpDefines(self)
        if bool(self.FDS):
            print(f'    FDs:')
            for i, item in enumerate(self.FDS):
                if 'token' in item:
                    print(f"        {i}:{item['token']}={item['value']}")
                elif 'offset' in item:
                    print(f"        {i}:{item['offset']}:{item['size']}")
                else:
                    print(f"        {i}:{','.join(item)}")
        self.DumpTokenValue(self.FVS, 'FVs')
        if bool(self.RULES):
            print(f'    RULES:')
            for item in self.RULES:
                items = FixUndefined(item['rule']).split()
                print(f"        {' '.join(items)}")
        if bool(self.APRIORI):
            for name in self.APRIORI:
                print(f'    {name} Apriori:')
                for i, item in enumerate(self.APRIORI[name]):
                    print(f"        {i+1}:{item}")
        if bool(self.INFS):
            print('    INFs')
            for i, item in enumerate(self.INFS):
                msg = item[0]
                for opt in item[1]:
                    msg += f' {opt[0]}'
                    if len(opt) > 1: msg += f'={opt[1]}'
                print(f'        {i}:{msg}')
        if bool(self.FILES):
            print('    Files')
            for i, item in enumerate(self.FILES):
                options = GetOptions(item['options'])
                if 'guided' in item:
                    pass
                print(f"        {i}:FILE {item['type']} {item['guid']}{options}")
                for j, section in enumerate(item['sections']):
                    options = GetOptions(section['options'])
                    print (f"            {j}:SECTION GUIDED {section['type']['GUIDED']}{options}")
                    if 'guided' in section:
                        for k, sect in enumerate(section['guided']['sections']):
                            sect = sect['type']
                            print (f"                {k}:SECTION {sect['type']} {sect['value']}")
                        continue
                    section = section['type']
                    print (f"            {j}:SECTION {section['type']} {section['value']}{options}")

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

    def __sortedKeys__(self, dict):
        keys = list(dict.keys())
        keys.sort()
        return keys

    def __processArgs__(self):
        global ARGs
        ARGs[self.argsFile] = ArgsParser(self.argsFile)

    def __processDSCs__(self):
        global DSCs
        DSCs[self.dscFile] = DSCParser(self.dscFile)

    def __processINFs__(self):
        global INFs
        self.infs = {}
        for name, number, path in INFs:
            file = FindPath(path)
            if not file:
                Error(f"{name}:{number}-Unable to locate file {path}\n")
                continue
            if file in self.infs:
                if Debug(SHOW_SKIPPED_INFS): print(f"{number}:{name}:Previously loaded:{file}")
                inf = self.infs[file]
                # Only add reference if it is not already there
                if not (name, number) in inf.reference:
                    inf.reference.append((name, number))
            else:
                self.infs[file] = INFParser(file, name, number)
        temp = INFs
        INFs = self.infs
        self.infs = temp

    def __processDECs__(self):
        global DECs
        self.decs = {}
        for name, number, path in DECs:
            file               = FindPath(path)
            if not file:
                Error(f"{name}: {number}-Unable to locate file {path}\n")
                continue
            if file in self.decs:
                if Debug(SHOW_SKIPPED_DECS): print(f"{number}:{name}:Previously loaded:{file}")
            else:
                self.decs[file] = DECParser(file)
        temp = DECs
        DECs = self.decs
        self.decs = temp

    def __processFDFs__(self):
        global FDFs
        FDFs[self.fdfFile] = FDFParser(self.fdfFile)

    # Process a platform and output the results
    # returns nothing
    def __processPlatform__(self):
        global DebugLevel
        global ARGs, DSCs, INFs, DECs, FDFs, BasePath, Macros, PCDs, SHOW_SKIPPED_INFS, SHOW_SKIPPED_DECS, SHOW_SKIPPED_FDFS

        # Parse all of the files
        for name, handler in [('Args', self.__processArgs__), ('DSC', self.__processDSCs__), ('INF', self.__processINFs__), ('DEC', self.__processDECs__), ("FDF", self.__processFDFs__)]:
            if Debug(SHOW_FILENAMES):
                print(f"Parsing {name} files:")
                length = len('Parsing  files:') + len(name)
                print('-'*length)
            handler()

        # Display the results
        # Show results
        print(f"\nRESULTS:")
        print(f"--------")
        print(f"Base Directory:          {BasePath}")
        for item in  [ 'ARGs', 'DSC', 'DEC', 'FDF']:
            spaces = ' ' * (15 - len(item))
            print(f"Platform {item}:{spaces}{getattr(self, item.lower() + 'File')}")
        print(f"Supported Architectures: {','.join(SupportedArchitectures)}")
        values = []
        total  = 0
        for i, item in  enumerate([ 'ARG', 'DSC', 'INF', 'DEC', 'FDF']):
            values.append(eval(f'len({item}s)'))
            print(f"{item} files processed:     {values[i]}")
            total += values[i]
        print(f'Total files processed:   {total}')

        print(f"\nList of Macros:")
        print(f"---------------")
        for macro in self.__sortedKeys__(Macros): print(f"{macro}={Macros[macro]}")

        # Show information from the files processed
        for list in ['ARGs', 'DSCs', 'INFs', 'DECs', 'FDFs']:
            print(f'\n{list[0:-1].upper()} Information:')
            length = len(' Information:') + len(list[0:-1])
            print('-'*length)
            list = eval(list)
            for item in list:
                print(item)
                if item == 'Intel/EagleStreamPlatform/EagleStreamFspPkg/EagleStreamFspPkg.fdf':
                    pass
                list[item].Dump()

# Indicate platform to be processed
#platform = "D:/ROMS/G11/a55/HpeProductLine/Volume/HpPlatforms/A55Pkg"
platform = "D:/ROMS/G11/u54/HpeProductLine/Volume/HpPlatforms/U54Pkg"
PlatformInfo(platform)

###########
### TBD ###
###########
# - Still need to parse Rules sectuions in FDF files
#   (this will mean adding support for COMPRESS and GUIDED FILE items
# - Allow platform directory to be passed in instead of hard coded
# - Convert other file lists to dictionaries and used MacroVer like it is used for DSC?
# - Cross-reference items to make sure things are consistent?
# - Generate files instead of output to the screen so it can be used by other utilites
