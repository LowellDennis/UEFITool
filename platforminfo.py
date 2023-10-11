#!/usr/bin/env python3

# Standard python modules
import os
import shutil
import subprocess
import sys

# Local modules
from   debug      import *
import globals    as     gbl
from   dscparser  import DSCParser
from   infparser  import INFParser
from   decparser  import DECParser
from   fdfparser  import FDFParser

class PlatformInfo:
    content = []

    # Class constructor
    # platform: Platform directory
    # returns nothing
    def __init__(self, platform):
        # Save platform
        self.platform  = platform
        # Find Worktree and change to it (this is where builds happen!)
        self.__findWorktree__()
        savedDir = os.getcwd()
        os.chdir(gbl.Worktree)
        self.platform  = os.path.relpath(platform, gbl.Worktree).replace('\\', '/')
        self.dscFile   = gbl.JoinPath(self.platform, "PlatformPkg.dsc")
        self.decFile   = gbl.JoinPath(self.platform, "PlatformPkg.dec")
        self.fdfFile   = gbl.JoinPath(self.platform, "PlatformPkg.fdf")
        self.__initializeEnvironment__()
        out = self.__spoofBuild__()
        self.__processOutput__(out)
        self.__processPlatform__()
        os.chdir(savedDir)

    ###################
    # Private methods #
    ###################

    # Set environment variable and also save in Macros
    def __setEnvironment__(self, variable, value):
        result = gbl.SetMacro(variable, value.replace('\\', '/'))
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')
        if gbl.isWindows: value = value.replace('/', '\\')
        os.environ[variable] = value

    # Get a list of sorted key from a dictionary
    # dictionary: Dictionary from which the sortk key list is desired
    # returns sorted key list
    def __sortedKeys__(self, dictionary):
        keys = list(dictionary.keys())
        keys.sort()
        return keys
    
    # Process the DSC file(s)
    # returns nothing
    def __processDSCs__(self):
        # Processing starts with the platform DSC file in the platform directory
        gbl.ReferenceSource(self.dscFile, self.platform, None)
        gbl.DSCs[self.dscFile] = DSCParser(self.dscFile)

    # Process the INF file(s)
    # returns nothing
    def __processINFs__(self):
        def GetDefinedValue(defines, macro):
            for item in defines:
                if item['macro'] == macro:
                    return item['value']
            return None
        # Build a new dictionary of INF files
        self.infs = {}
        # Loop through the list of INFs generated by processing DSCs
        for inf in gbl.INFs:
            file = gbl.FindPath(inf)
            if not file:
                info = gbl.References[inf][0]
                gbl.Error(f"Unable to locate INF file: {inf} (reference {info[1]}:{info[0]})\n")
                continue
            # See if file has already been processed
            if file in self.infs:
                if Debug(SHOW_SKIPPED_INFS):
                    print(f"{file} already processed")
            else:
                self.infs[file] = INFParser(file)
        # Create global dictionary of INF class items indexed by BASE_NAME
        gbl.INFs = {}
        for file in self.infs:
            this = self.infs[file]
            name = GetDefinedValue(this.DEFINES, 'BASE_NAME')
            if not name:
                gbl.Error(f'INF file does not define BASE_NAME: {file}')
                continue
            gbl.INFs[name] = inf = gbl.INF(file)
            inf.SetItem('parser', this)
            if bool(this.DEPEX):
                depex = ''
                for item in this.DEPEX:
                    items = item['depex'].split()
                    depex += ' '.join(items) + ' '
                inf.SetItem('depex', depex.rstrip())
            for define in ("FILE_GUID", "LIBRARY_CLASS", "MODULE_TYPE", "VERSION_STRING"):
                value = GetDefinedValue(this.DEFINES, define)
                if value:
                    inf.SetItem(define, value)

    # Process the INF file(s)
    # returns nothing
    def __processDECs__(self):
        # Build a new dictionary of DEC files
        self.decs = {}
        # Loop through the list of DECs generated by processing DSCs and INFs
        for dec in gbl.DECs:
            file = gbl.FindPath(dec)
            if not file:
                info = gbl.References[dec][0]
                gbl.Error(f"Unable to locate DEC file: {dec} (reference {info[1]}:{info[0]})\n")
                continue
            if file in self.decs:
                if Debug(SHOW_SKIPPED_DECS):
                    print(f"{file} already processed")
            else:
                self.decs[file] = DECParser(file)
        # Use new dictionary globally
        temp = gbl.DECs
        gbl.DECs = self.decs
        self.decs = temp

    # Process the FDF file(s)
    # returns nothing
    def __processFDFs__(self):
        # Processing starts with the platform DSC file in the platform directory
        gbl.ReferenceSource(self.fdfFile, self.platform, None)
        gbl.FDFs[self.fdfFile] = FDFParser(self.fdfFile)

    # Finds the base directory of the platform tree
    # returns nothing
    # EXITS WIT?H ERROR MESSAGE AND DOES NOT RETURN IF NOT FOUND
    def __findWorktree__(self):
        gbl.Worktree = self.platform
        while True:
            # Look for Edk2 in current directory
            if os.path.isdir(os.path.join(gbl.Worktree, 'Edk2')):
                break
            # If not base move up one directory level
            old = gbl.Worktree
            gbl.Worktree = os.path.dirname(gbl.Worktree)
            # Get out if not found and no more levels to explore
            if gbl.Worktree == old:
                gbl.Error('Unable to locate base of UEFI platform tree ... exiting!')
                sys.exit(1)

    # Initializes the environment
    # returns nothing
    def __initializeEnvironment__(self):
        # Get PATH from the environment
        path = os.environ['PATH'].replace('\\', '/')
        result = gbl.SetMacro('PATH', path)
        if Debug(SHOW_MACRO_DEFINITIONS):
            print(f'{result}')
        self.__setEnvironment__('PLAT_PKG_PATH', self.platform)
        platform = self.platform[-6:-3]
        self.__setEnvironment__('PLATFORM', platform)
        self.__setEnvironment__('TARGET', 'DEBUG')
        build_dir = os.path.join(gbl.Worktree, 'Build')
        self.__setEnvironment__('BUILD_DIR', build_dir)
        self.__setEnvironment__('WORKSPACE', gbl.Worktree)
    
    # Take over build.py and cause it to spit out needed information
    # returns output from spoofed build.by usage
    # Note: build.py is returned to its previous state afterwards
    def __spoofBuild__(self):
        # Directories and filenames of interest
        tgtDir = gbl.JoinPath(gbl.Worktree, 'Edk2/BaseTools/Source/Python/build')
        build  = gbl.JoinPath(tgtDir, 'build.py')
        old    = gbl.JoinPath(tgtDir, 'build_old.py')
        # Make sure old file does not exist (that means last spoof did not complete)
        if os.path.exists(old):
            gbl.Error('Unable to spoof build.py ... exiting!')
            sys.exit(2)
        # Rename build.py to build_old.py and remove build.py
        shutil.copyfile(build, old)
        os.remove(build)
        # Copy build_old.py to build.py line by line and insert spoof code where needed
        with open(build, 'w') as b:
            with open(old, 'r') as o:
                line = o.readline()
                while line:
                    if not line == "if __name__ == '__main__':\n":
                        b.write(line)
                    else:
                        b.write("def DumpInfo():\n")
                        b.write("    print('UEFITool DumpInfo Start')\n")
                        b.write("    for i in sys.argv:\n")
                        b.write("        print(i)\n")
                        b.write("    print('UEFITool DumpInfo Middle')\n")
                        b.write("    for i in os.environ:\n")
                        b.write("        print(f'{i}={os.environ[i]}')\n")
                        b.write("    print('UEFITool DumpInfo End')\n")
                        b.write("    sys.exit(-1)\n\n")
                        b.write("\n")
                        b.write("if __name__ == '__main__':\n")
                        b.write("    DumpInfo()\n")
                    line = o.readline()
        # Execute spoof build
        script   = "hpbuild.bat" if gbl.isWindows else 'source hpbuild.sh'
        cmd    = f'{script} -P {os.environ["PLATFORM"]} -b DEBUG'
        proc     = subprocess.Popen(cmd , shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        # Move build_old.py back to build.py
        shutil.copyfile(old, build)
        os.remove(old)
        out = out.decode()
        err = err.decode()
        return out if 'UEFITool DumpInfo Start' in out else err

    # Process the spoofed output
    # out: output of spoofed run of build.py
    # returns nothing
    def __processOutput__(self, out):
        # Convert output to ascii and split into lines
        lines = out.split('\r\n' if gbl.isWindows else '\n')
        # Find UEFITool spoofed information
        for i, l in enumerate(lines):
            if not 'UEFITool DumpInfo' in l:
                continue
            if ' Start' in l:
                cmdStart = i + 1
            elif ' Middle' in l:
                cmdEnd   = i
                envStart = i + 1
            elif ' End' in l:
                envEnd   = i
                break
        else:
            gbl.Error('Spoof output not as expected ... exiting!')
            sys.exit(3)
        # Loop throgh command line
        i = cmdStart
        while i < cmdEnd:
            # Look for -D options (define)
            if lines[i].strip() == '-D':
                # Get and save definition
                i += 1
                tokens = lines[i].strip().split('=', 1)
                result = gbl.SetMacro(tokens[0], '' if len(tokens) < 2 else tokens[1].replace('\\', '/'))
                if Debug(SHOW_MACRO_DEFINITIONS):
                    print(f'{result}')
            i += 1
        # Loop through environment
        for i in range(envStart, envEnd):
            # Get environment variable and its value
            env, value = lines[i].strip().split('=', 1)
            # See if it is already set and is the same
            if env in os.environ and os.environ[env] == value:
                continue
            result = gbl.SetMacro(env, value.replace('\\', '/'))
            if Debug(SHOW_MACRO_DEFINITIONS):
                print(f'{result}')

    # Process a platform and output the results
    # returns nothing
    def __processPlatform__(self):
        
        # Set of the library package path
        paths     = gbl.Macros["PACKAGES_PATH"]
        gbl.Paths = paths.split(";" if gbl.isWindows else ":")

        # Parse all of the files
        for name, handler in [('DSC', self.__processDSCs__), ('INF', self.__processINFs__), ('DEC', self.__processDECs__), ("FDF", self.__processFDFs__)]:
            if Debug(SHOW_FILENAMES):
                print(f"Parsing {name} files:")
                length = len('Parsing  files:') + len(name)
                print('-'*length)
            handler()

        # Display the results
        # Show results
        print(f"\nRESULTS:")
        print(f"--------")
        print(f"Worktree:                {gbl.Worktree}")
        for item in  [ 'DSC', 'DEC', 'FDF']:
            spaces = ' ' * (15 - len(item))
            print(f"Platform {item}:{spaces}{getattr(self, item.lower() + 'File')}")
        print(f"Supported Architectures: {','.join(gbl.SupportedArchitectures)}")
        values = []
        total  = 0
        for i, item in  enumerate([ 'DSC', 'INF', 'DEC', 'FDF']):
            values.append(eval(f'len(gbl.{item}s)'))
            print(f"{item} files processed:     {values[i]}")
            total += values[i]
        print(f'Total files processed:   {total}')
        print(f'Total lines processed:   {gbl.Lines}')

        # Generate macro list (if indicated)
        if not gbl.CommandLineResults.macros:
            print(f"\nGenerating macros.lst ...")
            with open(os.path.join(self.platform, 'macros.lst'), 'w') as lst:
                for macro in self.__sortedKeys__(gbl.Macros):
                    lst.write(f"{macro}={gbl.Macros[macro]}\n")

        # Generate apriori lists (if indicated)
        if not gbl.CommandLineResults.apriori:
            for item in ('PEI', 'DXE'):
                if item in gbl.Apriori:
                    print(f"Generating apriori_{item.lower()}.lst ...")
                    with open(os.path.join(self.platform, f'apriori_{item.lower()}.lst'), 'w') as lst:
                        lst.write(f"Define: {gbl.Apriori[item].lineNumber}:{gbl.Apriori[item].fileName}\n")
                        for i, apriori in enumerate(gbl.Apriori[item].list):
                            lst.write(f"{i+1}. {apriori}\n")

        # Generate sources and references lists (if indicated)
        if not gbl.CommandLineResults.sources:
            print(f"Generating sources.lst and references.lst ...")
            with open(os.path.join(self.platform, 'sources.lst'), 'w') as lst:
                with open(os.path.join(self.platform, 'references.lst'), 'w') as lst2:
                    for source in self.__sortedKeys__(gbl.Sources):
                        lst.write(f"{source}\n")
                        lst2.write(f"{source}\n")
                        for ref in gbl.Sources[source].references:
                            lst2.write(f"    ref: {ref['lineNumber']}:{ref['fileName']}\n")

        # Generate library list (if indicated)
        if not gbl.CommandLineResults.libraries:
            print(f"Generating libraries.lst ...")
            with open(os.path.join(self.platform, 'libraries.lst'), 'w') as lst:
                for library in self.__sortedKeys__(gbl.INFs):
                    this = gbl.INFs[library]
                    lst.write(f'{library}\n')
                    lst.write(f'    fileName:       {this.fileName}\n')
                    lst.write(f'    FILE_GUID:      {this.file_guid}\n')
                    lst.write(f'    MODULE_TYPE:    {this.module_type}\n')
                    lst.write(f'    LIBRARY_CLASS:  {this.library_class}\n')
                    if this.version_string:
                        lst.write(f'    VERSION_STRING: {this.version_string}\n')
                    if this.depex:
                        lst.write(f'    DepEx:          {this.depex}\n')
                    dependency = self.__dependancies__(library)
                    if dependency:
                        lst.write(f'    Dependency:     ')
                        space = ''
                        for i, depends in enumerate(dependency):
                            lst.write(f'{space}{i+1}. {depends}\n')
                            space = '                    '

        # Generate PPI list (if indicated)
        if not gbl.CommandLineResults.ppis:
            print(f"Generating ppis.lst ...")
            with open(os.path.join(self.platform, 'ppis.lst'), 'w') as lst:
                for ppi in self.__sortedKeys__(gbl.Ppis):
                    this = gbl.Ppis[ppi]
                    refs = gbl.Ppis[ppi].references
                    lst.write(f'{ppi}\n')
                    lst.write(f"    value:   {this.value}\n")
                    lst.write(f'    defined: {this.lineNumber}:{this.fileName}\n')
                    if refs:
                        for ref in refs:
                            lst.write(f'    ref:     {ref["lineNumber"]}:{ref["fileName"]}\n')                            

        # Generate Protocol list (if indicated)
        if not gbl.CommandLineResults.protocols:
            print(f"Generating protocols.lst ...")
            with open(os.path.join(self.platform, 'protocols.lst'), 'w') as lst:
                for protocol in self.__sortedKeys__(gbl.Protocols):
                    this = gbl.Protocols[protocol]
                    refs = gbl.Protocols[protocol].references
                    lst.write(f'{protocol}\n')
                    lst.write(f"    value:   {this.value}\n")
                    lst.write(f'    defined: {this.lineNumber}:{this.fileName}\n')
                    if refs:
                        for ref in refs:
                            lst.write(f'    ref:     {ref["lineNumber"]}:{ref["fileName"]}\n')                            

        # Generate Guid list (if indicated)
        if not gbl.CommandLineResults.guids:
            print(f"Generating guids.lst ...")
            with open(os.path.join(self.platform, 'guids.lst'), 'w') as lst:
                for guid in self.__sortedKeys__(gbl.Guids):
                    this = gbl.Guids[guid]
                    refs = gbl.Guids[guid].references
                    lst.write(f'{guid}\n')
                    lst.write(f"    value:   {this.value}\n")
                    lst.write(f'    defined: {this.lineNumber}:{this.fileName}\n')
                    if refs:
                        for ref in refs:
                            lst.write(f'    ref:     {ref["lineNumber"]}:{ref["fileName"]}\n')                            

        # Generate PCD list (if indicated)
        if not gbl.CommandLineResults.pcds:
            print(f"Generating pdcs.lst ...")
            with open(os.path.join(self.platform, 'pcds.lst'), 'w') as lst:
                # Get PCD settings from DECs
                for name in self.__sortedKeys__(gbl.Pcds):
                    pcd = gbl.Pcds[name]
                    # Don't include subtype PCDs
                    if '[' in name or len(name.split('.')) > 2:
                        continue
                    lst.write(f"{name}\n")
                    definer = pcd.definer
                    if definer:
                        lst.write(f"    defined:  {pcd.definer['lineNumber']}:{pcd.definer['fileName']}\n")
                    lst.write(f"    default:  {pcd.default}\n")
                    lst.write(f"    type:     {pcd.datum}\n")
                    lst.write(f"    token:    {pcd.token}\n")
                    overrider = pcd.overrider
                    if overrider:
                        lst.write(f"    override: {pcd.overrider['lineNumber']}:{pcd.overrider['fileName']}\n")
                        lst.write(f"    value:    {pcd.value}\n")
                        lst.write(f"    size:     {pcd.size}\n")
                    references = pcd.references
                    if references:
                        for ref in references:
                            lst.write(f'    ref:      {ref["lineNumber"]}:{ref["fileName"]}\n')                            

        # Show file dumps (if indicated)
        if gbl.CommandLineResults.dump:
            for list in ['ARGs', 'DSCs', 'INFs', 'DECs', 'FDFs']:
                print(f'\n{list[0:-1].upper()} Information:')
                length = len(' Information:') + len(list[0:-1])
                print('-'*length)
                list = eval('gbl.'+list)
                for item in list:
                    print(item)
                    list[item].Dump()

    def __dependancies__(self, name):
        def AddDependencies(name, dependency):
            # Nothing to do if this library is already in dependency list
            if not name in dependency:
                # Make sure this is a defined library
                if name in gbl.INFs:
                    #  Add this library
                    dependency.append(name)
                    # Add all of the libraries upon which this one depends
                    libraries = []
                    for library in gbl.INFs[name].parser.LIBRARYCLASSES:
                        name = library['name']
                        # Unless dependency is alredy in the list
                        if not name in dependency:
                            # Make sure dependency is a defined library
                            if name in gbl.INFs:
                                AddDependencies(name, dependency)
            return dependency
        dependency = []
        dependency = AddDependencies(name, dependency)
        return dependency[1:]

    ##################
    # Public methods #
    ##################
    # None
