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
SHOW_SKIPPED_SECTIONS        = 0x4000000000000000    # Show lines being skipped due to section limitation
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
SHOW_SUBELEMENT_ENTER        = 0x0000800000000000    # Show entry into sub-elements
SHOW_SUBELEMENT_EXIT        = 0x0000400000000000    # Show exit  from sub-elements
# Section entry handling
SHOW_USEREXTENSIONS          = 0x0000000200000000    # Show lines in UserExtensions      sections
SHOW_TAGEXCEPTIONS           = 0x0000000100000000    # Show lines in TagException        sections
SHOW_SOURCES                 = 0x0000000800000000    # Show lines in Sources             sections
SHOW_SNAPS                   = 0x0000000400000000    # Show lines in Snaps               sections
SHOW_SKUIDS                  = 0x0000000020000000    # Show lines in SkuIds              sections
SHOW_RULE                    = 0x0000000010000000    # Show lines in Rule                sections
SHOW_PYTHONSCRIPTS           = 0x0000000008000000    # Show lines in PythonScripts       sections
SHOW_PROTOCOLS               = 0x0000000004000000    # Show lines in Protocols           sections
SHOW_PPIS                    = 0x0000000002000000    # Show lines in PPIs                sections
SHOW_PLATFORMPACKAGES        = 0x0000000001000000    # Show lines in PlatformPackages    sections
SHOW_PCDS                    = 0x0000000000800000    # Show lines in PCDs                sections
SHOW_UPATCHES                = 0x0000000000400000    # Show lines in uPatches            sections
SHOW_PACKAGES                = 0x0000000000200000    # Show lines in Packages            sections
SHOW_LIBRARYCLASSES          = 0x0000000000100000    # Show lines in LibraryClasses      sections
SHOW_INCLUDES                = 0x0000000000080000    # Show lines in Includes            sections
SHOW_HPBUILDARGS             = 0x0000000000040000    # Show lines in HpBuildArgs         sections
SHOW_HEADERFILES             = 0x0000000000020000    # Show lines in HeaderFiles         sections
SHOW_GUIDS                   = 0x0000000000010000    # Show lines in GUIDs               sections
SHOW_FV                      = 0x0000000000008000    # Show lines in FV                  sections
SHOW_FMPPAYLOAD              = 0x0000000000004000    # Show lines in FmpPayload          sections
SHOW_FD                      = 0x0000000000001000    # Show lines in FD                  sections
SHOW_ENVIRONMENTVARIABLES    = 0x0000000000000800    # Show lines in EnvironmentVariable sections
SHOW_DEPEX                   = 0x0000000000000400    # Show lines in Depex               sections
SHOW_DEFINES                 = 0x0000000000000200    # Show lines in Defines             sections
SHOW_DEFAULTSTORES           = 0x0000000000000100    # Show lines in DefaultStores       sections
SHOW_COMPONENTS              = 0x0000000000000080    # Show lines in Components          sections
SHOW_CAPSULE                 = 0x0000000000000040    # Show lines in Capsule             sections
SHOW_BUILDOPTIONS            = 0x0000000000000020    # Show lines in BuildOptions        sections
SHOW_BINARIES                = 0x0000000000000010    # Show lines in Binaries            sections
# Basic stuf f
SHOW_ERROR_DIRECT1VE         = 0x0000000000000008    # Show lines with error directives
SHOW_MACRO_DEFINITIONS       = 0x0000000000000004    # Show macro definitions
SHOW_SECTION_CHANGES         = 0x0000000000000002    # Show changes in sections
SHOW_FILENAMES               = 0X0000000000000001    # Show names of files being processed

# All in one setting values
DEBUG_NONE                   = 0x0000000000000000
DEBUG_MINIMAL                = 0x0000000000000001
DEBUG_NORMAL                 = 0x000000000000000F
DEBUG_SUBSTANTIAL            = 0x00FFFFFFFFFFFFFF
DEBUG_VERBOSE                = 0xFFFFFFFFFFFFFFFF

# Set the debug level
DebugLevel                   = DEBUG_NONE

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
# Groups 1=>inf, 3=>optional sub-element start marker
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
# Groups 1=>space, 2=>pcd, 4=>optional item1, 6=>optional item2, 8=>optional item3, 10=>optional item4, 12=>optional item5, 13=>optional sub-element marker
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
# Groups 1=>space, 2=>pcd, 4=>optional item1, 6=>optional item2, 8=>optional item3, 10=>optional item4, 12=>optional item5, 13=>optional sub-element start marker
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
# Groups 1=>DXE|PEI, 2=>sub-element start marker
reApriori              = r'^APRIORI\s+(PEI|DXE)\s*(\{)$'

# Regular expression for matching lines with format "token = value"
# Groups 1=>token, 2=>value
reCapsule              = r'^' + reFirmEquate

# Regular expression for matching lines with format "value = name"
# Groups 1=>value, 2=>name
# reDefines same as above

# Regular expression for matching lines with format "0x??, 0x?? ..."
# Groups 1=>multiple data entries follwoed by ',', 2=>optional data entry not followed by ','
# Must process group(0).replace(',', ' ').split() to get to individual data entries
reHexNumber            = r'0x[0-9A-F][0-9A-F]?'
reDataAdd              = r'^((' + reHexNumber + r'\s*,\s*)+(' + reHexNumber + ')?)$'

# Regular expression for matching lines with format "COMPRESS [type] {"
# Groups 1=>optional type, 2=>{
reCompress             = r'^COMPRESS\s+([^\s\{]+)?\s*\{$'

# Regular expression for matching lines with format "DATA = {"
# Groups 1=>optional options, 2=>inf
reDataStart            = r'^DATA\s+=\s+{$'

# Regular expression for matching lines with format "}"
# Groups None
reEndDesc              = r'^\}'

# Regular expression for matching lines with format "kind [kind2] [options] path.ext"
# Groups 3=>path, 4=>ext
# Note: Must process group[0:-len(group(3))+len(group(4)].split() to get kind, kind2, and options
reExt                  = r'^(([^\s]+)\s+)*([^\.]+)\.(.+)$'

# Regular expression for matching lines with format "FILE type = guid [options]"
# Groups 1=>type, 2=>quid, 3=optional options
# Must process groups(3).split() to look for individial options
reFile                 = r'^FILE\s*([^=\s]+)\s*=\s*([^\s\{]+)\s*([^\{]+)?\{$'

# Regular expression for matching lines with format "GUIDED [guid] {"
# Groups 1=>optional guid, 2=>{
reGuided              = r'^GUIDED\s+([^\s\{]+)?\s*\{$'

# Regular expression for matching lines with format "INF [options] inf"
# Groups 1=>optional options, 2=>inf
reInf                  = r'^INF\s+(([^\s=]+)\s*=\s*(\"[^\"]+\"|[^\s]+)\s+)*' + reToEOL

# Regular expression for matching lines with format "offset | size"
# Groups 1=>offset, 2=>size
reOfsSz                = r'^' + re1Bar

# Regular expression for matching lines with format "path"
# Groups 1=>path, 2=>options descriptor continuaton character, {
rePath                = r'^([^\{]+)(\{)?$'

# Regular expression for matching lines with format "FILE kind = guid [{]]"
# Groups 1=>kind, 2=>guid, 3=>optional options, 4=>optional {
reRule                 = r'^FILE ([^\s=]+)\s*=\s*([^\s\{]+)\s*([^\{]+)({)$'

# Regular expression for matching lines with format FILE type = guid [CHECKSUM]"
# Groups 1=>type, 2=>quid, 3=optional CHECKSUM
reSection              = r'^SECTION\s+([^\{]+)(\{)?$'

# Regular expression for matching lines with format "value = name"
# Groups 1=>set, 2=>pcd, 2=>value
reSet                 = r'^(set)\s+' + reFirmEquate

# Regular expression for matching lines with format "VERSION|UI [options]"
# Groups 1=>VERSION or UI, 2=>optional options
reVer                 = r'(VERSION|UI)\s+(.+)$'

# Global Variables
BasePath                = None
Paths                   = []

# Macro definitions used in expansion
MacroVer                = 0
Macros                  = {}

# For keeping track of the files and lines
Lines                   = 0
References              = {}
ARGs                    = {}
DSCs                    = {}
INFs                    = []
DECs                    = []
FDFs                    = {}

# For limiting the architectures
SupportedArchitectures  = []

# Determine if this is Windows OS
isWindows  = 'WINDOWS' in platform.platform().upper()

# Add a new refernce
# reference: File being referenced
# refererer: File (or platform) making the reference)
# line:      Line number of the reference
#            (this will be None for references from the platform directory)
# returns nothing
def AddReference(reference, referer, line):
    global References
    if not reference in References: References[reference] = []
    References[reference].append( (referer, line) )

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

# Replace all occurances of __<macro>__UNDEFINED__ with $(<macro>) within a string.
# string: String in which to look for replacements
# returns string with any appropriate substrings replaced
def FixUndefined(string):
        # Look for all macros in the line (format "$(<macroName>)")
        matches = re.findall(r'__([a-zA-Z0-9_]+)__UNDEFINED__', string)
        # Loop through all ocurrances
        for match in matches:
            # Replace __macroName__UNDEFINED__ with $(macroName)
            string = string.replace(f'__{match}__UNDEFINED__', f'$({match})')
        # Return expanded line
        return string

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

# Join two paths together and make sure slashes are consistent
# path1: First path to join
# path2: Second path to join
# returns conjoined path
def JoinPath(path1, path2):
    return os.path.join(path1, path2).replace('\\', '/')

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
    #    Child class MAY  provide a handler for regular expression  matches (use None if no handler is proviced)
    #        If specified this handler must be present and will only be called if the appropriate regulare expression matches.
    #    Child class MUST provide a handler for "directive_<name>"  for each name in additionalDirectives.
    #        If no handler is found an error will be generated.
    #    Child class MUST provide a hanlder for "directive_include" if allowIncludes is se to True.
    #        If no handler is found an error will be generated.
    #    Child class MAY  provide "onentry_<name>" handler to be called when section "name" is entered.
    #    Child class MAY  provide "onexit_<name>"  handler to be called when section "name" is exited.
    #    Child class MAY  provide "macro_<name>"   handler to be called when macro "name" is set.
    #    This class provides handlers for all conditional directives (except include).

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
        global SupportedArchitectures, SHOW_SKIPPED_SECTIONS
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
        if Debug(SHOW_SKIPPED_SECTIONS): print(f"{self.lineNumber}:SKIPPED - unsupported section {GetSection(section)}")
        return False

    # Looks for and handles section headers
    # line: line on which to look for potential section header
    # returns True if line was a setion header and processed, False otherwise
    def __handleNewSection__(self, line):
        global SHOW_SECTION_CHANGES
        # Look for section header (format "[<sections>]")
        match = re.match(r'\[([^\[\]]+)\]', line)
        if not match: return False
        # Check for unended sub-element
        if self.inSubsection and bool(self.sections):
            self.ReportError(f"{self.section[0]} section missing closing brace")
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
                regex = eval(regEx)
                match = re.match(regex, line, re.IGNORECASE)
                if match: break
        else:
            idx   = None
            regEx = regExes
            regex = eval(regEx)
            match = re.match(regex, line, re.IGNORECASE)
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
            # Call the match handler if present and callable
            handler = getattr(self, f'match_{regEx}', None)
            if handler and callable:
                handler(match)
            # Call the section handler if present and callable
            handler = getattr(self, f"section_{section}", None)
            if handler and callable(handler):
                handler(idx, match)
        # else taken care of in __handleMatch__

    # Handle sub-element processing
    # (not called unless section supports sub-elements)
    # line: Line which is to be handled
    def __handleSubsection__(self, line):
        global SHOW_SUBELEMENT_EXIT
        # Just in case there a some trailing C style comment on the line (which should be an error)!
        line = line.split(" //")[0]
        # Look for end of sub-element block
        if line.endswith("}") and self.inSubsection:
            # Signal end of sub-element block and sub-element
            self.inSubsection = False
            self.subsections  = None
            if Debug(SHOW_SUBELEMENT_EXIT): print(f"{self.lineNumber}:Exiting sub-element")
            return
        # Look for sub-element marker
        if "<" in line:
            # Convert to normal section format
            line              = line.lower().replace("<", "[").replace(">", "]")
            # Save current section informarion
            sections          = self.sections
            # Don't call exit section handlers
            self.sections     = []
            # Handle sub-element entry
            self.__handleNewSection__(line)
            # Save sub-element information
            self.subsections  = self.sections
            # Restore the original section info
            self.sections     = sections
            return
        # Handle case where a sub-element was already marked
        elif self.subsections:
            # Save current section info
            sections          = self.sections
            # Set sub-element info
            self.sections     = self.subsections
            # Process the section line (ignoring sub-elements)
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
        # See if sub-element is being processed
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
        global reDefine, Lines, SHOW_FILENAMES, SHOW_CONDITIONAL_SKIPS
        if Debug(SHOW_FILENAMES): print(f"Processing {self.fileName}")
        # Read in the file
        try:
            with open(self.fileName, 'r') as file:
                content = file.readlines()
            # Go through the content one at a time
            self.lineNumber = 0
            for line in content:
                Lines           += 1
                self.lineNumber += 1
#                if (self.lineNumber, self.fileName) == (133, 'Intel/EagleStreamPlatform/EagleStreamFspPkg/EagleStreamFspPkg.fdf'):
#                    pass
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
        global Macros
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
        global SHOW_CONVERTED_CONDITIONAL
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

    ##################
    # Public methods #
    ##################

    # Defines a new macro
    # line: line containing the macro
    # returns nothing
    def DefineMacro(self, macro, value):
        global SHOW_MACRO_DEFINITIONS
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
        # Make sure there are no undefined macros in the file path'
        if '_UNDEFINED__' in path:
            items = path.split("__")
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

    # Used to mark entry into a sub-element
    def EnterSubsection(self):
        global SHOW_SUBELEMENT_ENTER
        # This only needs to happen for first section in sections that are grouped together
        if self.sections.index(self.section) == 0:
            # Make sure previous sub-element is done
            if self.inSubsection:
                self.ReportError('Unable to enter sub-element because already in sub-element')
                return
            self.inSubsection = True
            if Debug(SHOW_SUBELEMENT_ENTER): print(f'{self.lineNumber}:Entering sub-element')

    ####################
    # Special handlers #
    ####################
    # None

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
    # Match handlers #
    ##################
    # None

    #################
    # Dump handlers #
    #################

    # Generic attribute dump method for dumping a list attribute with one field
    # lst:   List attribute to dump
    # title: Title to show for this list
    # field: Dictionary name given to the attribute
    # fixup: When True, any __MACRO__UNDEFINED__ substrings will be converted back to $(MACRO) 
    def DumpSingle(self, lst, title, field, fixup = False):
        if bool(lst):
            print(f'    {title}:')
            for i, item in enumerate(lst):
                value = FixUndefined(item[field]) if fixup else item[field]
                print(f"        {i}:{value}")

    # Dump information from the class
    def Dump(self):
        # Loop through attributes
        for item in dir(self):
            # Only care about attributes that are ALL CAPS
            if not item.upper() == item: continue
            # Just in case
            if item.startswith('__'):    continue
            # Get and call dump method for this attribute
            handler = getattr(self, f'Dump{item}')
            handler()

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
        global ARGs
        def includeHandler(file):
            AddReference(file, self.fileName, self.lineNumber)     # Indicate reference to included file
            ARGs[file] = ChipsetParser(file)
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
                value = '' if not 'value' in item else FixUndefined(item['value'])
                print(f"        {i}:{item['variable']}={value}")

    # Dump [HpBuildArgs] section
    def DumpHPBUILDARGS(self):
        if bool(self.HPBUILDARGS):
            print('    HpBuildArgs:')
            for i, item in enumerate(self.HPBUILDARGS):
                arg   = '' if not 'arg'   in item else  ' ' + item['arg']
                value = '' if not 'value' in item else  '=' + FixUndefined(item['value'])
                print(f"        {i}:{item['option']}{arg}{value}")

    # Dump [*PythonScripts] sections
    def DumpPYTHONSCRIPTS(self):
        if bool(self.PYTHONSCRIPTS):
            print('    PythonScripts:')
            for i, item in enumerate(self.PYTHONSCRIPTS):
                args  = '' if not 'args'  in item else  FixUndefined(item['args'])
                print(f"        {i}:{FixUndefined(item['pyfile'])}:{item['func']}({args})")

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
                print(f"        {i}:{item['binary']} {FixUndefined(item['path'])}")

    # Dump [HpBuildArgs] section
    def DumpHPBUILDARGS(self):
        ArgsParser.DumpHPBUILDARGS(self)

    # Dump [PlatformPackages] section
    def DumpPLATFORMPACKAGES(self):
        if bool(self.PLATFORMPACKAGES):
            print('    PlatformPkgs:')
            for i, item in enumerate(self.PLATFORMPACKAGES):
                print(f"        {i}:{FixUndefined(item['package'])}")

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
    ArgsPcdsDynamicExVpd      = ('RR R O O X X', 'PCDS',           GetVpdOptionNames)
    ArgsPcdsDynamicHii        = ('RR R R R O O', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'variablename', 'variableguid', 'variableoffset', 'hiidefaultvalue'])
    ArgsPcdsDynamicVpd        = ('RR R O O X X', 'PCDS',           GetVpdOptionNames)
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
        global SupportedArchitectures, SHOW_SPECIAL_HANDLERS
        SupportedArchitectures = value.upper().replace('"', '').split("|")
        if Debug(SHOW_SPECIAL_HANDLERS): print(f"{self.lineNumber}: Limiting architectires to {','.join(SupportedArchitectures)}")

    ######################
    # Directive handlers #
    ######################

    # Handle the Error directive
    # message: Error message
    # returns nothing
    def directive_error(self, message):
        global SHOW_ERROR_DIRECT1VE
        # Display error message (if currently processsing)
        if Debug(SHOW_ERROR_DIRECT1VE): print(f"{self.lineNumber}:error {message}")
        if self.process: self.ReportError(f"error({message})")

    # Handle the Include directive
    # includeFile: File to be included
    # returns nothing
    def directive_include(self, includeFile):
        global DSCs, MacroVer, SHOW_SKIPPED_DSCS
        def includeDSCFile(file):
            AddReference(file, self.fileName, self.lineNumber)      # Indicate reference to included file
            if file in DSCs and  DSCs[file].macroVer == MacroVer:
                    if Debug(SHOW_SKIPPED_DSCS): print(f"{self.lineNumber}:Previously loaded:{file}")
            else: DSCs[file] = DSCParser(file, self.sections, self.process)
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
            self.EnterSubsection()

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
        global INFs
        file = match.group(3).replace('"', '')
        AddReference(file, self.fileName, self.lineNumber)      # Indicate reference to INF file
        INFs.append(file)

    #################
    # Dump handlers #
    #################

    # Dump [BuildOptions] section
    def DumpBUILDOPTIONS(self):
        if bool(self.BUILDOPTIONS):
            print('    BuildOptions:')
            for i, item in enumerate(self.BUILDOPTIONS):
                tag   = '' if not 'tag'   in item else item['tag'] + ':'
                value = '' if not 'value' in item else '=' + FixUndefined(item['value'])
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
                value = '' if item['value'] == None else FixUndefined(item['value'])
                print(f"        {i}:{item['macro']}={value}")

    # Dump [LibraryClasses] section
    def DumpLIBRARYCLASSES(self):
        if bool(self.LIBRARYCLASSES):
            print('    LibraryClasses:')
            for i, item in enumerate(self.LIBRARYCLASSES):
                print(f"        {i}:{item['name']}|{FixUndefined(item['path'])}")

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

# Class for handling UEFI INF files
class INFParser(UEFIParser):
    # Section Arguments    R/O             List              Names
    Argsbinaries       = ('RR O O O O',   'BINARIES',       ['kind', 'path', 'tag1', 'tag2', 'tag3', 'tag4'])
    ArgsBuildOptions   = (' ORO',         'BUILDOPTIONS',   ['tag', 'option', 'value'])
    ArgsDefines        = ('RO',           'DEFINES',        ['macro', 'value'])
    ArgsDepEx          = ('R',            'DEPEX',          ['depex'])
    ArgsFeaturePcd     = ('RR O O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsFixedPcd       = ('RR O O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsGuids          = ('R X',          'GUIDS',          ['guid'])
    ArgsIncludes       = ('R',            'INCLUDES',       ['include'])
    ArgsLibraryClasses = ('R O',          'LIBRARYCLASSES', ['name', 'path'])
    ArgsPackages       = ('R',            'PACKAGES',       ['path'])
    ArgsPatchPcd       = ('RR O O X X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcd            = ('RR O O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPcdEx          = ('RR O O O X X', 'PCDS',           ['pcdtokenspaceguidname', 'pcdname', 'value', 'datumtype', 'maximumdatumsize'])
    ArgsPpis           = ('R X',          'PPIS',           ['ppi'])
    ArgsProtocols      = ('R   OOO',      'PROTOCOLS',      ['protocol', 'not', 'pcdtokenspaceguidname', 'pcdname'])
    ArgsSources        = ('ROOOOOOO',     'SOURCES',        ['source', 'source2', 'source3', 'source4', 'source5', 'source6', 'source7', 'source8'])
    ArgsUserExtensions = ('R',            'USEREXTENSIONS', ['ext'])
    #                Section                  Debug                 regEx(s)               Arguments
    INFSections = { 'binaries':              (SHOW_BINARIES,       'reBinariesBar',        Argsbinaries),
                    'buildoptions':          (SHOW_BUILDOPTIONS,   'reBuildOptions',       ArgsBuildOptions),
                    'defines':               (SHOW_DEFINES,        'reDefines',            ArgsDefines),
                    'depex':                 (SHOW_DEPEX,          'reDepex',              ArgsDepEx),
                    'featurepcd':            (SHOW_PCDS,           'rePcds',               ArgsFeaturePcd),
                    'fixedpcd':              (SHOW_PCDS,           'rePcds',               ArgsFixedPcd),
                    'guids':                 (SHOW_GUIDS,          'reGuids',              ArgsGuids),
                    'includes':              (SHOW_INCLUDES,       'reIncludes',           ArgsIncludes),
                    'libraryclasses':        (SHOW_LIBRARYCLASSES, 'reLibraryClasses',     ArgsLibraryClasses),
                    'packages':              (SHOW_PACKAGES,       'rePackages',           ArgsPackages),
                    'patchpcd':              (SHOW_PCDS,           'rePcds',               ArgsPatchPcd),
                    'pcd':                   (SHOW_PCDS,           'rePcds',               ArgsPcd),
                    'pcdex':                 (SHOW_PCDS,           'rePcds',               ArgsPcdEx),
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

    # Handle a match in the [Packages] section for rePackages
    # match: Results of regex match
    # returns nothing
    def match_rePackages(self, match):
        global DECs
        file = match.group(1)
        AddReference(file, self.fileName, self.lineNumber)      # Indicate reference to DEC file
        DECs.append(file)

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
                print(f"        {i}:{item['type']}.{FixUndefined(item['path'])}{values[0]}{values[1]}{values[2]}{values[3]}")

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

    # Handle a match in any of the PCD sections for rePcd
    # match: Results of regex match
    # returns nothing
    def match_rePcds(self, match):
        # See if we need to enter a sub-element
        if match.group(13) and match.group(13) == '{':
            self.EnterSubsection()

    ###########################################
    # Match handlers (only when inSubsection) #
    ###########################################

    # Handle a match in the <Packages> sub-element
    # match: Results of regex match
    # returns nothing
    def matchPackages(self, match):
        global DECs
        # Only allow this section handler if in a sub-element
        if not self.inSubsection:
            self.ReportError('section packages cannot be used outside of braces')
            return
        file = match.group(1)
        AddReference(file, self.fileName, self.lineNumber)      # Indicate reference to DEC file
        DECs.append(self.fileName)

    # Handle a match in the <HeaderFiles> sub-element
    # match: Results of regex match
    # returns nothing
    def matchHeaderFiles(self, match):
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
        global reFile, reSection, reEndDesc, rePath
        # Save current lineNumber and fileName
        saved = (self.lineNumber, self.fileName)
        # Assume lineNumber and fileName object where outside line has been encounteered
        self.lineNumber, self.fileName = (this.lineNumber, this.fileName)
        # Process the outside line
        for i, regEx in enumerate([reFile, reSection, reEndDesc, rePath]): # These are all that are allowed!
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
        global DSCs, MacroVer, FDFs, SHOW_SKIPPED_DSCS, SHOW_SKIPPED_FDFS
        def includeHandler(file):
            AddReference(file, self.fileName, self.lineNumber)      # Indicate reference to included file
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
    # None

    ##################
    # Match handlers #
    ##################

    # Handle a match in the [FD] section that matchs reDataStart
    # match: Results of regex match
    # returns nothing
    def match_reDataStart(self, match):
        global SHOW_FD
        # Previous data list must have been completed
        if not self.data == None:
            self.ReportError('Previous data list not terminated')
            return
        self.data = []
        if Debug(SHOW_FD): print(f'{self.lineNumber}:Entering data list')

    # Handle a match in the [FD] section that matchs reDataAdd
    # match: Results of regex match
    # returns nothing
    def match_reDataAdd(self, match):
        global SHOW_FD
        # reDataStart must have been already encountered
        if self.data == None:
            self.ReportError('Data list not allowed here')
            return
        data = match.group(0).replace(',', '').split()
        for datum in data:
            self.data.append(datum)
        if Debug(SHOW_FD): print(f'{self.lineNumber}:{match.group(0)}')

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
        global SHOW_FV
        # Previous apriori list must have been completed
        if not self.apriori == None:
            self.ReportError('Previous apriori list not terminated')
            return
        # Get APRIORI type
        self.apriori = match.group(1)
        # Start apriori list
        self.APRIORI[self.apriori] = []
        if Debug(SHOW_FV): print(f'{self.lineNumber}:Entering {self.apriori} apriori list')

    # Handle a match in the [rule] section that matches reCompress
    # match: Results of regex match
    # returns nothing
    def match_reCompress(self, match):
        global SHOW_FV
        # Previous compressed descriptor list must have been completed
        if not self.compress == None:
            self.ReportError('Previous compressed descriptor not terminated')
            return
        self.compress = { 'type': match.group(1)}
        if Debug(SHOW_FV): print(f'{self.lineNumber}:COMPRESS {"" if match.group(1) == None else match.group(1)}')
        if Debug(SHOW_FV): print(f'{self.lineNumber}:Entering compressed descriptor')

    # Handle a match in the [fv] or [fd] sections that matches reEndDesc
    # match: Results of regex match
    # returns nothing
    def match_reEndDesc(self, match):
        # End apriori list (if applicable)
        if self.apriori != None:
            # Clear Apriori list
            if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting {self.apriori} apriori list')
            self.apriori = None
        # End guided descriptor (if applicable)
        elif self.guided != None:
            # Add guided descriptor to appropriate item
            if self.compress != None:
                self.compress['guided'] = self.guided
                if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting compress descriptor')
            elif self.sect != None:
                self.sect['guided']  = self.guided
                self.file['sections'].append(self.sect)
                self.sect            = None
                if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting guided section')
            elif self.file:
                self.file['guided']     = self.guided
                if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting guided descriptor')
            elif self.rule:
                self.rule['guided'] = self.guided
                if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting guided descriptor')
            else:
                self.ReportError('Unmatched ending brace characrter encountered: }')
            # Clear guided descriptor
            self.guided = None
        # End file descriptor (if applicable)
        elif self.file != None:
            # Add file
            self.FILES.append(self.file)
            self.file = None
            if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting file descriptor')
        # End data list (if applicable)
        elif self.data != None:
            self.FDS.append(self.data)
            self.data = None
            if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting data list')
        # End compressed descriptor (if applicable)
        elif self.compress != None:
            self.rule['compress'] = self.compress
            self.compress = None
            if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting compressed descriptor')
        # End rule descriptor (if applicable)
        elif self.rule != None:
            self.RULES.append(self.rule)
            self.rule = None
            if Debug(SHOW_SUBELEMENT_EXIT): print(f'{self.lineNumber}:Exiting rule descriptor')
        else:
            self.ReportError('End brace found without matching start brace')

    # Handle a match in the [rules] section that matches reExt
    # match: Results of regex match
    # returns nothing
    def match_reExt(self, match):
        global SHOW_RULE
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
            if Debug(SHOW_RULE): print(f'{self.guided[kind]}')
        elif self.compress:
            self.compress[kind] = f'{kind2}:{path}.{ext}{self.__optionStr__(opts)}'
            if Debug(SHOW_RULE): print(f'{self.compress[kind]}')
        else:
            self.rule[kind] = f'{kind2}:{path}.{ext}{self.__optionStr__(opts)}'
            if Debug(SHOW_RULE): print(f'{self.rule[kind]}')

    # Handle a match in the [fv] section that matches reFile
    # match: Results of regex match
    # returns nothing
    def match_reFile(self, match):
        global SHOW_FV, SHOW_SUBELEMENT_ENTER
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
        # Previous file descriptor must have been completes
        if not self.file == None:
            self.ReportError('Previous file descriptor not terminated')
            return
        msg = ''
        kind = match.group(1)
        guid = match.group(2)
        self.file = {'type': kind, 'guid': guid, 'options': self.__getOptions__(match.group(3), True), 'sections': []}
        if Debug(SHOW_FV): print(f'{self.lineNumber}:FILE {kind} {guid}{msg}')
        if Debug(SHOW_SUBELEMENT_ENTER): print(f'{self.lineNumber}:Entering file descriptor')

    # Handle a match in the [rules] section that matches reGuided
    # match: Results of regex match
    # returns nothing
    def match_reGuided(self, match):
        global SHOW_FV
        # Previous guidede descriptor list must have been completed
        if not self.guided == None:
            self.ReportError('Previous guided descriptor not terminated')
            return
        self.guided = { 'guid': match.group(1)}
        if Debug(SHOW_FV): print(f'{self.lineNumber}:GUIDED {"" if match.group(1) == None else match.group(1)}')
        if Debug(SHOW_FV): print(f'{self.lineNumber}:Entering guided descriptor')

    # Handle a match in the [fv] section that matches reInf
    # match: Results of regex match
    # returns nothing
    def match_reInf(self, match):
        global SHOW_FV
        # Check for Apriori
        inf = match.group(4)
        AddReference(inf, self.fileName, self.lineNumber)       # Add reference to INF file
        if self.apriori:
            self.APRIORI[self.apriori].append(inf)
            if Debug(SHOW_FV): print(f'{self.lineNumber}:{inf} added to {self.apriori} list (#{len(self.APRIORI[self.apriori])})')
        # Normal INF entry
        else:
            # Add any detected options
            opts = self.__getOptions__(match.group(1))
            self.INFS.append((inf, opts))
            if Debug(SHOW_FV): print(f'{self.lineNumber}:INF {inf}{self.__optionStr__(opts)}')

    # Handle a match in the [fv] section that matches rePath
    # match: Results of regex match
    # returns nothing
    def match_rePath(self, match):
        global SHOW_FV
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
        if Debug(SHOW_FV): print(f'{self.lineNumber}:{path}')

    # Handle a match in the [rules] section that matches reRule
    # match: Results of regex match
    # returns nothing
    def match_reRule(self, match):
        global SHOW_RULE
        kind, guid, opts = (match.group(1), match.group(2), self.__getOptions__(match.group(3), True))
        self.rule = {'type': kind, 'guid': guid, 'options': opts}
        if Debug(SHOW_RULE): print(f'{self.lineNumber}:{kind}={guid}{self.__optionStr__(opts)}')
        if not match.groups(4) == None:
            if Debug(SHOW_SUBELEMENT_ENTER): print(f'{self.lineNumber}:Entering rule descriptor')
        else:
            self.RULES.append(self.rule)
            self.rule = None
            

    # Handle a match in the [fv] section that matches reSection
    # match: Results of regex match
    # returns nothing
    def match_reSection(self, match):
        global SHOW_FV, SHOW_SUBELEMENT_ENTER
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
        if Debug(SHOW_SUBELEMENT_ENTER) and kind == 'GUIDED': print(f'{self.lineNumber}:Entering guided section')

    # Handle a match in the [rules] section that matches reVer
    # match: Results of regex match
    # returns nothing
    def match_reVer(self, match):
        global SHOW_RULE
        # Can only have this when a rule is being described
        if self.rule == None:
            self.ReportError('RULE must start with FILE description')
            return
        kind, opts = (match.group(1), self.__getOptions__(match.group(2).strip(), True))
        if self.guided:
            self.guided[kind] = self.__optionStr__(opts)[1:]
            if Debug(SHOW_RULE): print(f'{self.lineNumber}:{kind}{self.guided[kind]}')
        elif self.compress:
            self.compress[kind] = self.__optionStr__(opts)[1:]
            if Debug(SHOW_RULE): print(f'{self.lineNumber}:{kind}{self.compress[kind]}')
        else:
            self.rule[kind] = self.__optionStr__(opts)[1:]
            if Debug(SHOW_RULE): print(f'{self.lineNumber}:{kind}{self.rule[kind]}')

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
                if type(value) is str: result += f"\n{indent}{attr} {FixUndefined(value)}"
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
                kind = FixUndefined(item['type'])
                opts = self.__optionStr__(item['options'])
                guid = FixUndefined(item['guid'])
                msg = f"        FILE {kind}={guid}{opts}"
                msg += DumpItems(item, ['type', 'guid', 'options'], '            ', DumpLevel1)
                print(msg)

    def DumpAPRIORI(self):
        if bool(self.APRIORI):
            for name in self.APRIORI:
                print(f'    {name} Apriori:')
                for i, item in enumerate(self.APRIORI[name]):
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

class PlatformInfo:
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

    ###################
    # Private methods #
    ###################

    # Set environment variable and also save in Macros
    def __setEnvironment__(self, variable, value):
        global isWindows, SHOW_MACRO_DEFINITIONS
        result = SetMacro(variable, value.replace('\\', '/'))
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')
        if isWindows: value = value.replace('/', '\\')
        os.environ[variable] = value

    # Finds the base directory of the platform tree
    # returns nothing
    # EXITS WIT?H ERROR MESSAGE AND DOES NOT RETURN IF NOT FOUND
    def __findBase__(self):
        global BasePath, SHOW_MACRO_DEFINITIONS
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
        global Paths, SHOW_MACRO_DEFINITIONS
        paths = os.environ["PACKAGES_PATH"].replace("\\", "/")
        Paths = paths.split(";")
        result = SetMacro("PACKAGES_PATH", Paths)
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')

    # Finds the chipset DSC file
    # returns the chipset file
    # EXITS WIT?H ERROR MESSAGE AND DOES NOT RETURN IF NOT FOUND
    def __getHpPlatformPkg__(self):
        global SHOW_MACRO_DEFINITIONS
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

    # Get a list of sorted key from a dictionary
    # dictionary: Dictionary from which the sortk key list is desired
    # returns sorted key list
    def __sortedKeys__(self, dictionary):
        keys = list(dictionary.keys())
        keys.sort()
        return keys
    
    # Process the HPAgrs file(s)
    # returns nothing
    def __processArgs__(self):
        global ARGs
        # Processing starts with the HPArgs file in the platform directory
        AddReference(self.argsFile, self.platform, None)
        ARGs[self.argsFile] = ArgsParser(self.argsFile)

    # Process the DSC file(s)
    # returns nothing
    def __processDSCs__(self):
        global DSCs
        # Processing starts with the platform DSC file in the platform directory
        AddReference(self.dscFile, self.platform, None)
        DSCs[self.dscFile] = DSCParser(self.dscFile)

    # Process the INF file(s)
    # returns nothing
    def __processINFs__(self):
        global References, INFs, SHOW_SKIPPED_INFS
        # Build a new dictionary of INF files
        self.infs = {}
        # Loop through the list of INFs generated by processing DSCs
        for inf in INFs:
            file = FindPath(inf)
            if not file:
                info = References[inf][0]
                Error(f"Unable to locate INF file: {inf} (reference {info[1]}:{info[0]})\n")
                continue
            # See if file has already been processed
            if file in self.infs:
                if Debug(SHOW_SKIPPED_INFS): print(f"{file} already processed")
            else:
                self.infs[file] = INFParser(file)
        # Use new dictionary globally
        temp = INFs
        INFs = self.infs
        self.infs = temp

    # Process the INF file(s)
    # returns nothing
    def __processDECs__(self):
        global References, DECs, SHOW_SKIPPED_DECS
        # Build a new dictionary of DEC files
        self.decs = {}
        # Loop through the list of DECs generated by processing DSCs and INFs
        for dec in DECs:
            file = FindPath(dec)
            if not file:
                info = References[dec][0]
                Error(f"Unable to locate DEC file: {dec} (reference {info[1]}:{info[0]})\n")
                continue
            if file in self.decs:
                if Debug(SHOW_SKIPPED_DECS): print(f"{file} already processed")
            else:
                self.decs[file] = DECParser(file)
        # Use new dictionary globally
        temp = DECs
        DECs = self.decs
        self.decs = temp

    # Process the FDF file(s)
    # returns nothing
    def __processFDFs__(self):
        global FDFs
        # Processing starts with the platform DSC file in the platform directory
        AddReference(self.fdfFile, self.platform, None)
        FDFs[self.fdfFile] = FDFParser(self.fdfFile)

    # Process a platform and output the results
    # returns nothing
    def __processPlatform__(self):
        global Lines, ARGs, DSCs, INFs, DECs, FDFs, BasePath, Macros, PCDs, SupportedArchitectures, SHOW_FILENAMES

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
        print(f'Total lines processed:   {Lines}')

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

    ##################
    # Public methods #
    ##################
    # None


################
# Main Program #
################

# Display usage information
# msg: Option error message
# DOES NOT RETURN!
def Usage(msg = None):
    if msg: Error(msg)
    print(f"UEFI Tool V0.1")
    print(f"usage {sys.argv[0]} [-?] [-m | -n | -v | | -a | -d level] [path]")
    print(f"  -?:   This usage")
    print(f"  -m:   Set debug output to minimal")
    print(f"  -n:   Set debug output to normal")
    print(f"  -v:   Set debug output to verbose")
    print(f"  -a:   Set debug output to all")
    print(f"  -d:   Sets debug output indicated level (64-bit hex number)")
    print(f"        NOTE: debug output will be set to last one of the above encountered")
    print(f"              By default there is no debug output")
    print(f"  path: Path to BIOS source code platform directory")
    print(f"        NOTE: Any arguments after path will be ignored")
    print(f"              If no path is given the current directory is used")
    sys.exit(1)

def DbgMinimal():
    global DebugLevel, DEBUG_MINIMAL
    DebugLevel = DEBUG_MINIMAL

def DbgNormal():
    global DebugLevel, DEBUG_NORMAL
    DebugLevel = DEBUG_NORMAL

def DbgSubstantial():
    global DebugLevel, DEBUG_SUBSTANTIAL
    DebugLevel = DEBUG_SUBSTANTIAL

def DbgVerbose():
    global DebugLevel, DEBUG_VERBOSE
    DebugLevel = DEBUG_VERBOSE

ExpectLevel = False     # -d option has not been used, so level value is not expected
def DbgLevel():
    global ExpectLevel
    ExpectLevel = True

# For option handling
OptHandler = {'?': Usage, 'h': Usage, 'm': DbgMinimal, 'n': DbgNormal, 's': DbgSubstantial, 'v': DbgVerbose, 'd': DbgLevel}

# Defaults
platform    = os.getcwd()

# Handle command line input
for arg in sys.argv[1:]:
    if ExpectLevel:
        try:
            # Convert from hex ASCII to integer
            ExpectLevel = False
            DebugLevel  = int(arg, 16)
        except ValueError:
            Usage(f"Invalid value for debug level: {arg}")
            # Does not return!
    else:
        # Look for possible options
        if len(arg) == 2 and arg[0] in '-/':    # Linux uses '-', Windows uses '/'
            opt = arg[1].lower()                # For now make this case insensitive
            # Validate option
            if not opt in OptHandler:
                Usage(f"Unsupported command line option: {arg}")
                # Does not return!
            # Handle option
            OptHandler[opt]()
        else:
            # Must be the path
            platform = arg
            break
else:
    # Gets here when loop exits without break
    # Make sure value ExpectLevel was answered
    if ExpectLevel:
        Usage(f"-d must be followed by a debug setting")
        # Does not return!

print(f'Processing {platform} as HPE platform directory')
PlatformInfo(platform.replace('\\', '/'))

###########
### TBD ###
###########
# - Cross-reference items to make sure things are consistent?
# - Generate files instead of output to the screen so it can be used by other utilites
# - Fully check syntax of files!
