#!/usr/bin/env python3

# Standard python modules
import re

# Local modules
from   debug   import *
import globals as     gbl

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
    # process:              Starting processing state (default is True, conditionals can set this to False)
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
    #    Child class MAY  provide "macro_<name>"   handler to be called when macro "name" is set.
    #    This class provides handlers for all conditional directives (except include).

    def __init__(self, fileName, sectionsInfo, allowIncludes = False, allowConditionals = False, additionalDirectives = [], sections = [], process = True, outside = None):
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
        self.subElementState      = -1                         # Indicates state if sub-element processing (-1: Not Allowed, 0: Allowed, 1: Processing)
        self.subElements          = []                         # Sub-elements being processed
        self.hasDirectives        = bool(additionalDirectives) # Indicates if the file supports any directives other than include and conditionals
        self.lineNumber           = 0                          # Current line being processed
        self.commentBlock         = False                      # Indicates if currently processing a comment block
        self.section              = None                       # Indicates the current section being processed (one of self.sections)
        self.sectionStr           = ""                         # String representing current section (for messaging)
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
        placeholders = []
        def replaceString(match):
            # Replace string literal with a placeholder
            placeholders.append(match.group(0))
            return f'__STRING_LITERAL_{len(placeholders)-1}__'
        line = line.strip()
        # Handle case where currently in a comment block
        if self.commentBlock:
            # Look for exit from comment block
            if line.endswith("*/"):
                self.commentBlock = False
            if Debug(SHOW_COMMENT_SKIPS):
                print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
            return None
        else:
            # Look for comment lines 
            if not line or (line.startswith('#') or line.startswith(';') or line.startswith("/*")):
                if Debug(SHOW_COMMENT_SKIPS):
                    print(f"{self.lineNumber}:SKIPPED - Blank or Comment")
                # Look for entry into comment block
                if line.startswith("/*"):
                    self.commentBlock = True
                return None
        # Replace strings with placeholders
        line    = re.sub(r'".*?"', replaceString, line)
        line    = re.sub(r"'.*?'", replaceString, line)
        # Remove any trailing comments
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
        if not self.allowIncludes and not self.allowConditionals and not self.hasDirectives:
            return False
        # Get out if line is not a directive
        if not line.startswith('!'):
            return False
        # Isolate directive
        items = line.split(maxsplit=1)
        directive = items[0][1:].lower()
        # Change elif directive to elseif!
        if directive == 'elif':
            directive = 'elseif'
        # Make sure directive is allowed
        if (self.allowIncludes and directive == 'include') or (self.allowConditionals and directive in self.ConditionalDirectives) or (directive in self.additionalDirectives):
            # Make sure directive has a handler
            handler = getattr(self, f"directive_{directive}", None)
            if handler and callable(handler):
                handler(items[1].strip() if len(items) > 1 else None)
            else:
                self.ReportError(f"Handler for directive not found: {directive}")
        else:
            self.ReportError(f"Unknown directive: {directive}")
        return True

    # Indicates if a particular section is a supported architecture and tooling
    # section: section to check
    # returns True if supported, False otherwise
    def __sectionSupported__(self, section):
        # Sections that do not stipulate architecture are always supported
        if len(section) < 2:
            return True
        arch = section[1].upper()
        # Patchup arch
        if   arch == 'peim':
            arch = 'IA32'
        elif arch == 'arm':
            arch = 'AARCH64'
        elif arch == 'ipf':
            arch = 'X64'
        # Eliminate sections that do not conform to the architecture convention
        if not arch in self.AllArchitectures:
            return True
        if arch in gbl.SupportedArchitectures:
            # Eliminate sections that do not have a tooling portion
            if len(section) < 3:
                return True
            third = section[2].upper
            # Eliminate sections that do not conform to tooling convention
            if not third in self.AllTooling:
                return True
            if third == 'EDKII':
                return True
        if Debug(SHOW_SKIPPED_SECTIONS):
            print(f"{self.lineNumber}:SKIPPED - unsupported section {gbl.GetSection(section)}")
        return False

    # Looks for and handles section headers
    # line:          Line on which to look for potential section header
    # ignoreCurrent: Ignore current sections (don't process sub-element or exit handling)
    # returns True if line was a section header and processed, False otherwise
    def __handleNewSection__(self, line, ignoreCurrent = False):
        # Look for section header (format "[<sections>]")
        match = re.match(r'\[([^\[\]]+)\]', line)
        if not match:
            return False
        if not ignoreCurrent:
            if not self.subElementState == -1:
                # Check for unended sub-elements
                for handler, sections in reversed(self.subElements):
                    self.ReportError(f"Missing closing brace for {handler()}")
                self.subElementState = -1
                self.subElements  = []
            # Exit current sections (if any)
            if bool(self.sections):
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
                    sectionStr = gbl.GetSection(items)
                    if Debug(SHOW_SECTION_CHANGES):
                        print(f"{self.lineNumber}:{sectionStr}")
                # Else taken care of in __sectionSupported method!
                # No need to look for handler here because some section may use the default handler
            else:
                self.ReportError(f"Unknown section: {section}")
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
        if not match:
            self.ReportError(f'Invalid {self.section[0]} format: {line}')
        else:
            # Loop through groups to check
            for g, u in enumerate(usage):
                if u == ' ':            # Skip unused groups
                    continue
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
        if Debug(debug):
            msg = f"{self.lineNumber}:{self.sectionStr}"
        for i, name in enumerate(names):
            value = values[i]
            entry[name] = value
            if Debug(debug):
                if value == None or type(value) is str and value == '':
                    continue
                msg = msg + f"{name}={value} "
        # Add entry to the attribute
        attribute.append(entry)
        # Show info if debug is enabled
        if Debug(debug):
            print(msg.rstrip())

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
                regex = eval('gbl.'+regEx)
                match = re.match(regex, line, re.IGNORECASE)
                if match:
                    break
        else:
            idx   = None
            regEx = regExes
            regex = eval('gbl.'+regEx)
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
                if callable(names):
                    names = names(self, match, line)
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
    def __handleSubElement__(self, line):
        def SignalExit(save = False):
            # Signal end of sub-element
            msg = self.subElements[-1][0](self)
            tmp = self.subElements.pop()
            self.subElementState = 1 if save else -1
            if not bool(self.subElements) and save:
                self.subElements.append(tmp)
            if Debug(SHOW_SUBELEMENT_EXIT):
                print(f"{self.lineNumber}:Exiting {msg}")
        # Look for end of sub-element block
        if line.endswith("}") and not self.subElementState == -1:
            # Signal end of sub-element
            SignalExit()
            return
        # Look for sub-element marker
        if "<" in line:
            # Generate automatic sub-element exit for any current sub-element
            if self.subElementState > 0:
                for section in self.sections:
                    if self.__sectionSupported__(section):
                        SignalExit(True)
            # Convert to normal section format
            line              = line.lower().replace("<", "[").replace(">", "]")
            # Save current section informarion
            sections          = self.sections
            # Handle sub-element entry (ignoring sub-elements and section exits)
            self.sections     = []
            self.__handleNewSection__(line, True)
            # Save sub-element section
            self.subElements[-1] = (self.subElements[-1][0], self.sections)
            self.subElementState = 1
            # Restore the original section info
            self.sections     = sections
            return
        # Handle case where a sub-element was already marked
        elif self.subElementState > 0:
            # Save current section info
            sections          = self.sections
            # Set sub-element info
            self.sections     = self.subElements[-1][1]
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
    # ignoreSubElement: When True, will ignore the sub-element procesing
    # returns nothing
    def __handleIndividualLine__(self, line, ignoreSubElement = False):
        # See if a line continuation is being processed
        if self.lineContinuation:
            self.__handleLineContinuation__(line)
        # See if sub-element is being processed
        elif not ignoreSubElement and not self.subElementState == -1:
            self.__handleSubElement__(line)
        # Must be in a section
        elif bool(self.sections):
            # Process line inside of each of the current sections
            for self.section in self.sections:
                # Make sure architecture is supported
                if self.__sectionSupported__(self.section):
                    self.sectionStr = gbl.GetSection(self.section)
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
        # Look for all macros in the line (format "$(<macroName>)")
        matches = re.findall(r'\$\(([^\)]+)\)', line)
        # Loop through all ocurrances
        for match in matches:
            #if not match in gbl.Macros:
            #    reAllow = r'^!((ifndef)|(ifdef)|(((elseif)|(elif)|(else\s+if)|(if)).*defined\(.+\)))'
            #    allow   = re.match(reAllow, line)
            #    if not allow:
            #        self.ReportError(f'Undefined macro encountered: {match}')
            # Replace the macro with its value (or __<macroName>__UNDEFINED__ if it is not defined)
            value = str(gbl.Macros[match]).replace('"', '') if match in gbl.Macros else F"__{match}__UNDEFINED__"
            line = line.replace(f"$({match})", '""' if not value else value)
        # Return expanded line
        return line

    # Method for parsing a file file line by line
    # filePath:  file to be parsed
    def __parse__(self):
        if Debug(SHOW_FILENAMES):
            print(f"Processing {self.fileName}")
        # Read in the file
        try:
            with open(self.fileName, 'r') as file:
                content = file.readlines()
            # Go through the content one at a time
            self.lineNumber = 0
            for line in content:
                gbl.Lines       += 1
                self.lineNumber += 1
                line = self.__removeComments__(line)
                if not line:
                    continue
                # Expand macros before parsing
                line = self.__expandMacros__(line)
                # Handle directives (if any)
                if self.__handleDirective__(line):
                    continue
                # Conditional processing may indicate to ignore
                if not self.process:
                    if Debug(SHOW_CONDITIONAL_SKIPS):
                        print(f"{self.lineNumber}:SKIPPED - Conditionally")
                    continue
                # Handle DEFINE lines anywhere
                match = re.match(gbl.reDefine, line, re.IGNORECASE)
                if match:
                    macro, value = (match.group(2), match.group(3))
                    self.DefineMacro(macro, value if value != None else '')
                    continue
                # Handle EQUATE lines anywhere
                match = re.match(gbl.reDefines, line, re.IGNORECASE)
                if match:
                    macro, value = (match.group(1), match.group(2))
                    # Do not include "DATA = {" lines or lines defining GUID values!
                    if not value.startswith('{'):
                        self.DefineMacro(macro, value if value != None else '')
                        continue
                # Look for section change
                if self.__handleNewSection__(line):
                    continue
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
        self.conditionHandled    = False
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
            if token in self.ConversionMap:
                token = self.ConversionMap[token]
            # Substitute items with the macro values (if appropriate)
            elif token in gbl.Macros:
                token = gbl.Macros[token]
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
        if Debug(SHOW_CONVERTED_CONDITIONAL):
            print(f"{self.lineNumber}:ConvertedCondition: {result}")
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
                    # Surround any un evaluated values with quotes and try one more time
                    items = result.split()
                    for i, item in enumerate(items):
                        if item[0] == '"':
                            continue
                        if item[0] in '+-*/%=&|^><!':
                            continue
                        if item in ['and', 'or', 'not']:
                            continue
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
        try:
            # See if value can be interpreted
            value = eval(value)
        except Exception:
            value = '"' + value + '"'
        # Save result
        if not value:
            macrovalue = '""'
        result = gbl.SetMacro(macro, value)
        if Debug(SHOW_MACRO_DEFINITIONS):
            print(f'{self.lineNumber}:{result}')
        # Call handler for this macro (if found)
        handler = getattr(self, f"macro_{macro}", None)
        if handler and callable(handler):
            handler(value)

    # Handling for generic sub-element exits
    def ExitSubElement(self):
        return 'sub-element'

    # Handles error repoting
    # message: error message
    # returns nothing
    def ReportError(self, message):
        # Display error message with file name and line number where error is encountered to stderr
        gbl.Error(f"{self.fileName}, line: {self.lineNumber}\n              {message}\n")

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
        file = gbl.FindPath(path)
        if not file:
            self.ReportError(f"Unable to locate file {path}")
        return file

    # Include a file
    # partial: Partial path of file being included
    # handler: Routine to handle the inclusion
    # returns full path to file or None if file could not be found
    def IncludeFile(self, partial, handler):
        if self.process:
            # Get full path to file to be incuded
            file = self.FindFile(partial)
            # Make sure full path was found
            if file:
               # Include the file!
                if Debug(SHOW_INCLUDE_DIRECTIVE):
                    print(f"{self.lineNumber}:Including {file}")
                handler(file)
                if Debug(SHOW_INCLUDE_RETURN):
                    print(f"{self.lineNumber}:Returning to {self.fileName}")
            # Note else error handled in self.FindFile!
        else:
            if Debug(SHOW_CONDITIONAL_SKIPS):
                print(f"{self.lineNumber}:SKIPPED - Conditionally")

    # Used to mark entry into a sub-element
    def EnterSubElement(self, handler = ExitSubElement, msg = 'sub-element'):
        # Mark entry into sub-element
        self.subElementState = 0
        self.subElements.append ((handler, self.section) )
        if Debug(SHOW_SUBELEMENT_ENTER):
            print(f'{self.lineNumber}:Entering {msg}')

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
        # if is always allowed
        if Debug(SHOW_CONDITIONAL_DIRECTIVES):
            print(f"{self.lineNumber}:if {condition}")
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
        # ifdef is always allowed
        if Debug(SHOW_CONDITIONAL_DIRECTIVES):
            print(f"{self.lineNumber}:ifdef {condition}")
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
        # ifndef is always allowed
        if Debug(SHOW_CONDITIONAL_DIRECTIVES):
            print(f"{self.lineNumber}:ifndef {condition}")
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
        # See if this is really an elseif
        if condition and condition.startswith('if '):
            self.directive_elseif(condition.replace('if ', '').rstrip())
        else:
            # Make sure else is allowed at this time
            if Debug(SHOW_CONDITIONAL_DIRECTIVES):
                print(f"{self.lineNumber}:else")
            if not "Else" in self.allowedConditionals:
                self.ReportError("Unexpected else directive encountered.")
            # Set allowedConditonals
            self.allowedConditionals = ['Endif']
            # Set processing flag apprpriately
            self.process = False    # Assume no processing
            if bool(self.conditionalStack):
                if self.conditionalStack[-1][0]:
                    self.process = not self.conditionHandled
                # else already taken care of by setting it to False above
            else:
                self.process = not self.conditionHandled
            # Handle elseif (if appropriate)
            if self.process and not self.conditionHandled:
                self.process = self.conditionHandled
            if Debug(SHOW_CONDITIONAL_LEVEL):
                print(f"{self.lineNumber}:ConditionalLevel:{len(self.conditionalStack)}, Process: {self.process}, allowedConditionals: if, idef, indef, {', '.join(self.allowedConditionals)}")

    # Handle the ElseIf directive
    # condition: If condition
    # returns nothing
    def directive_elseif(self, condition):
        # Make sure elseif is allowed at this time
        if Debug(SHOW_CONDITIONAL_DIRECTIVES):
            print(f"{self.lineNumber}:elseif {condition}")
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
                value = gbl.FixUndefined(item[field]) if fixup else item[field]
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
