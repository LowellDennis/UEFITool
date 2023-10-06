#!/usr/bin/env python3

# Standard python modules
import platform
import os
import re
import sys

# Local modules
from debug import DebugLevel

###################
# Program version #
###################
ProgramVersion = 0.2

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

# Regular expression for matching lines with format "package"
# Groups 1=>package
rePackages             = r'^' + reToEOL

# Regular expression for matching lines with format "space.pcd | value [ | type [ | size ]]
# Groups 1=>space, 2=>pcd, 4=>value, 6=>optional type, 8=>optional size
reStart                = r'^([^\.]+)\.([^\s\|]+)'
reVal                  = r'\s*\|\s*(L?\"[^\"]+\"|\{GUID\(\{[0-9A-FX, ]+\{[0-9A-FX, ]+\}\}\)\}|\{[0-9A-FX, ]+\{[0-9A-FX, ]+\}\}|\{?[^\|\{]*)'
reItem                 = r'\s*\|\s*([^\|\{]*)'
rePcdReDef             = fr'{reStart}({reVal}({reItem}({reItem})?)?)?$'

# Regular expression for matching lines with format "space.pcd | item1 [ | item2 [ | item3 [ | item4 [ | item5 [ | item6 ]]]]]
# Groups 1=>space, 2=>pcd, 3=>item1, 5=>optional item2, 7=>optional item3, 9=>optional item4, 11=>optional item5, 13=>optional item6
# Note: Situation              Item1  Item2 Item3   Item4 Item5       Item6
#       . or [] in pcd         value  none  none    none  none        none
#       PCD type is VOID*      name   guid  offset  size  value       attributes
#       PCD type is not VOID*  name   guid  offset  value attributes  none
rePcdHii              = fr'{reStart}{reVal}({reItem}({reItem}({reVal}({reVal}({reItem})?)?)?))??$'

# Regular expression for matching lines with format "space.pcd | value
# Groups 1=>space, 2=>pcd, 3=>value
rePcdVal               = fr'{reStart}{reVal}$'

# Regular expression for matching lines with format "space.pcd | offset [ | item1 [ | item2 ]]
# Groups 1=>space, 2=>pcd, 3=>offset, 5=>optional item1, 7=>optional item2
# Note: If PCD type is VOID*, item1 is size,  item2 is value,;
#       Otherwise             item1 is value, item2 is None!
rePcdVpd              = fr'{reStart}({reItem}({reVal}({reVal})?)?)?$'

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

# Regular expression for matching lines with format "space.pcd [ | value [ | item ]]
# Groups 1=>space, 2=>pcd, 4=>value, 6=>optional item
# Note: Situation                                                 Item
#       PatchPcd under Binaries and Item is a hexadecimal number  offset
#       All other situations                                      flagexpression
rePcdOvr              = fr'{reStart}({reVal}({reItem})?)?$'

# Regular expression for matching lines with format "guid = value"
# Groups 1=>guid, 3=>optional value
reGuids                = r'^([^=\s]+)\s*(=\s*(' + reNext + r'))?$'

# Regular expression for matching lines with format "include"
# Groups 1=>include
reIncludes             = r'^' + reToEOL

# Regular expression for matching lines with format "package"
# Groups 1=>package
# rePackages same as above

# Regular expression for matching lines with format "ppi [ = value ]"
# Groups 1=>ppi 3=>optional value (Note: = only required when optional value is given)
rePpis                 = r'^([^=\s]+)\s*(=\s*(' + reNext + r'))?$'

# Regular expression for matching lines with format "protocol [ | [not] space.pcd ]"
# Groups 1=>protocol, 4=>optional not, 6=>optional space, 7=>optional pcd (Note: | only required when optional pcd is given)
reProtocolsBar         = r'^([^\s\|]+)(\s*\|\s*((NOT)\s+)?(([^\.]+)\.)?(.+))?$'

# Regular Expression for matching lines with format "source1 [ source2 [ source3 [ source4 [ source5 [ source6 [ source7 [ source8 ]]]]]]
# Groups: 1=>source1, 2->optional source2, 3=>optional source3, 4=>optional source4, 5=>optional source5, 6=>optional source6, 7=>optional source7, 8=>optional source8
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

# Regular expression for matching lines with format "space.pcd | value [ | type [ | size ]] [ { ]
# Groups 1=>space, 2=>pcd, 4=>value, 6=>optional type, 8=>optional size 9=> optional sub-element start marker
rePcdDef               = fr'{reStart}({reVal}({reItem}({reItem})?)?)?' + r'\s*(\{)?$'

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
CommandLineResults      = None
Paths                   = []
Apriori                 = {}
Sources                 = {}
Pcds                    = {'dsc': {}, 'dec': {}}
Ppis                    = {}
Protocols               = {}
Guids                   = {}
Worktree                = None

# Macro definitions used in expansion
Macros                  = {}

# For keeping track of the files and lines
Lines                   = 0
References              = {}
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
    global Paths, Worktree
    # First try path as-is
    if os.path.exists(partial.replace('/', "\\")):
        return partial
    # Try partial appended to each path in Paths
    for p in Paths:
        file = JoinPath(p, partial)
        if os.path.exists(file):
            return os.path.relpath(file, Worktree).replace('\\', '/')
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
    global Macros
    if not macro in Macros or str(Macros[macro]) != str(value):
        Macros[macro] = value
    return f'{macro} = {value}'
