#!/usr/bin/env python

# Standard python modules
import sys

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
SHOW_SUBELEMENT_EXIT         = 0x0000400000000000    # Show exit  from sub-elements
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
DEBUG_MINIMUM                = 0x0000000000000001
DEBUG_TYPICAL                = 0x000000000000000F
DEBUG_VERBOSE                = 0x00FFFFFFFFFFFFFF
DEBUG_ALL                    = 0xFFFFFFFFFFFFFFFF

# Set the debug level
DebugLevel                   = DEBUG_NONE

# Debug output checker
# check: Debug item to check
# retuns True if item is enabled, False otherwise
def Debug(check):
    global DebugLevel
    result = DebugLevel & check
    return result != 0
