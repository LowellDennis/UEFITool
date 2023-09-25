#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
from   debug      import *
import globals    as     gbl
from   argsparser import ArgsParser
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
        self.platform  = platform
        self.__findBase__()
        savedDir = os.getcwd()
        os.chdir(gbl.BasePath)
        self.platform  = os.path.relpath(platform, gbl.BasePath).replace('\\', '/')
        self.argsFile  = gbl.JoinPath(self.platform, "PlatformPkgBuildArgs.txt")
        self.dscFile   = gbl.JoinPath(self.platform, "PlatformPkg.dsc")
        self.decFile   = gbl.JoinPath(self.platform, "PlatformPkg.dec")
        self.fdfFile   = gbl.JoinPath(self.platform, "PlatformPkg.fdf")
        platform = self.platform[-6:-3]
        build_dir = os.path.join(gbl.BasePath, 'Build')
        self.__setEnvironment__('PLATFORM', platform)
        self.__setEnvironment__('TARGET', 'DEBUG')
        self.__setEnvironment__('BUILD_DIR', build_dir)
        self.__setEnvironment__('WORKSPACE', gbl.BasePath)
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
        result = gbl.SetMacro(variable, value.replace('\\', '/'))
        if Debug(SHOW_MACRO_DEFINITIONS): print(f'{result}')
        if gbl.isWindows: value = value.replace('/', '\\')
        os.environ[variable] = value

    # Finds the base directory of the platform tree
    # returns nothing
    # EXITS WIT?H ERROR MESSAGE AND DOES NOT RETURN IF NOT FOUND
    def __findBase__(self):
        gbl.BasePath = self.platform
        while True:
            # Look for Edk2 in current directory
            if os.path.isdir(os.path.join(gbl.BasePath, 'Edk2')):
                break
            # If not base move up one directory level
            old = gbl.BasePath
            gbl.BasePath = os.path.dirname(gbl.BasePath)
            # Get out if not found and no more levels to explore
            if gbl.BasePath == old:
                gbl.Error('Unable to locate base of UEFI platform tree ... exiting!')
                sys.exit(1)
        # Get PATH from the environment
        result = gbl.SetMacro('PATH', os.environ['PATH'].replace('\\', '/'))
        if Debug(SHOW_MACRO_DEFINITIONS):
            print(f'{result}')

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
                    gbl.Error('Invaid format in {lookFor} line ... exiting!')
                    sys.exit(3)
                return items
        gbl.Error(f'Unable to locate {lookFor} in {self.argsFile}')
        sys.exit(2)

    def __getWorkspace__(self):
        # Get workpace and prebuild lines from args file
        workspaceItems = self.__findLine__(';set_platform_workspace')
        # HpCommon is expected to be in this path!
        if not 'HpCommon' in workspaceItems[0]:
            gbl.Error(f'Unable to detect path to HpCommon')
            sys.exit(3)
        index = workspaceItems[0].index('HpCommon')
        self.hppython = os.path.abspath(os.path.join(gbl.BasePath, workspaceItems[0][0:index]))
        sys.path.insert(0,self.hppython)
        # Make workspace path absolute
        workspaceArg = os.path.abspath(os.path.join(gbl.BasePath, workspaceItems[1].replace("set_platform_workspace", "")[2:-2]))
        from HpCommon import HpSetPlatformWorkspace
        HpSetPlatformWorkspace.set_platform_workspace(gbl.JoinPath(gbl.BasePath, workspaceArg))

    # Determines value for PACKAGES_PATH environment variable
    # returns nothing
    def __getPaths__(self):
        paths = os.environ["PACKAGES_PATH"].replace("\\", "/")
        gbl.Paths = paths.split(";")
        result = gbl.SetMacro("PACKAGES_PATH", gbl.Paths)
        if Debug(SHOW_MACRO_DEFINITIONS):
            print(f'{result}')

    # Finds the chipset DSC file
    # returns the chipset file
    # EXITS WIT?H ERROR MESSAGE AND DOES NOT RETURN IF NOT FOUND
    def __getHpPlatformPkg__(self):
        hpPlatformPkg = gbl.GetMacroValue(self.dscFile, "HP_PLATFORM_PKG")
        if not hpPlatformPkg:
            commonFamily = gbl.GetMacroValue(self.dscFile, "COMMON_FAMILY")
            if not commonFamily:
                gbl.Error('Unable to determine value for COMMON_FAMILY ... exiting!')
                sys.exit(2)
            result = gbl.SetMacro("COMMON_FAMILY", commonFamily)
            if Debug(SHOW_MACRO_DEFINITIONS):
                print(f'{result}')
            file = gbl.FindPath(gbl.JoinPath(commonFamily, "PlatformPkgConfigCommon.dsc"))
            if not file:
                gbl.Error('Unable to locate common family file ... exiting!')
                sys.exit(3)
            hpPlatformPkg = gbl.GetMacroValue(file, "HP_PLATFORM_PKG")
            if not hpPlatformPkg:
                gbl.Error('Unable to determine value for HP_PLATFORM_PKG ... exiting!')
                sys.exit(4)
        result = gbl.SetMacro("HP_PLATFORM_PKG", hpPlatformPkg)
        if Debug(SHOW_MACRO_DEFINITIONS):
            print(f'{result}')

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
        # Processing starts with the HPArgs file in the platform directory
        gbl.AddReference(self.argsFile, self.platform, None)
        gbl.ARGs[self.argsFile] = ArgsParser(self.argsFile)

    # Process the DSC file(s)
    # returns nothing
    def __processDSCs__(self):
        # Processing starts with the platform DSC file in the platform directory
        gbl.AddReference(self.dscFile, self.platform, None)
        gbl.DSCs[self.dscFile] = DSCParser(self.dscFile)

    # Process the INF file(s)
    # returns nothing
    def __processINFs__(self):
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
        # Use new dictionary globally
        temp = gbl.INFs
        gbl.INFs = self.infs
        self.infs = temp

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
        gbl.AddReference(self.fdfFile, self.platform, None)
        gbl.FDFs[self.fdfFile] = FDFParser(self.fdfFile)

    # Process a platform and output the results
    # returns nothing
    def __processPlatform__(self):

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
        print(f"Base Directory:          {gbl.BasePath}")
        for item in  [ 'ARGs', 'DSC', 'DEC', 'FDF']:
            spaces = ' ' * (15 - len(item))
            print(f"Platform {item}:{spaces}{getattr(self, item.lower() + 'File')}")
        print(f"Supported Architectures: {','.join(gbl.SupportedArchitectures)}")
        values = []
        total  = 0
        for i, item in  enumerate([ 'ARG', 'DSC', 'INF', 'DEC', 'FDF']):
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
                        for i, apriori in enumerate(gbl.Apriori[item]):
                            lst.write(f"{i+1}. {apriori}\n")

        # Generate sources list (if indicated)
        if not gbl.CommandLineResults.sources:
            print(f"Generating sources.lst ...")
            with open(os.path.join(self.platform, 'sources.lst'), 'w') as lst:
                for source in self.__sortedKeys__(gbl.Sources):
                    lst.write(f"{source}\n")

        # Generate library list (if indicated)
        if not gbl.CommandLineResults.libraries:
            print(f"Generating libraries.lst ...")
            with open(os.path.join(self.platform, 'libraries.lst'), 'w') as lst:
                for library in self.__sortedKeys__(gbl.INFs):
                    ver = ""
                    for item in gbl.INFs[library].DEFINES:
                        if item['macro'] == "VERSION_STRING":
                            ver = ' V' + item['value']
                            break
                    lst.write(f"{library}{ver}\n")

        # Generate PPI list (if indicated)
        if not gbl.CommandLineResults.ppis:
            print(f"Generating ppis.lst ...")
            with open(os.path.join(self.platform, 'ppis.lst'), 'w') as lst:
                for ppi in self.__sortedKeys__(gbl.Ppis):
                    lst.write(f"{ppi} = {gbl.Ppis[ppi]}\n")

        # Generate Protocol list (if indicated)
        if not gbl.CommandLineResults.protocols:
            print(f"Generating protocols.lst ...")
            with open(os.path.join(self.platform, 'protocols.lst'), 'w') as lst:
                for protocol in self.__sortedKeys__(gbl.Protocols):
                    lst.write(f"{protocol} = {gbl.Protocols[protocol]}\n")

        # Generate Guid list (if indicated)
        if not gbl.CommandLineResults.guids:
            print(f"Generating guids.lst ...")
            with open(os.path.join(self.platform, 'guids.lst'), 'w') as lst:
                for guid in self.__sortedKeys__(gbl.Guids):
                    lst.write(f"{guid} = {gbl.Guids[guid]}\n")

        # Generate PCD list (if indicated)
        if not gbl.CommandLineResults.pcds:
            print(f"Generating pdcs.lst ...")
            with open(os.path.join(self.platform, 'pcds.lst'), 'w') as lst:
                # Get PCD settings from DECs
                for name in self.__sortedKeys__(gbl.Pcds['dec']):
                    default, kind, id = gbl.Pcds['dec'][name]
                    # See if there is an override in DSC file
                    if name in gbl.Pcds['dsc']:
                        default = gbl.Pcds['dsc'][name][1]
                    lst.write(f"{name}|{default}|{kind}|{id}\n")

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

    ##################
    # Public methods #
    ##################
    # None
