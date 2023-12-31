# UEFITool
HPE UEFI Utility

### What is this repository for? ###

* Retrieves useful information from HPE UEFI files (DSC/DEC/INF/FDF)

### How do I get set up? ###

* To get the source use:
```
    cd <tool-install-directory>
    git clone https://github.com/LowellDennis/UEFITools.git
```

* This assumes that you have python installed and in the path (at least V3.10)
    * You can get it [here](https://www.python.org/)

### How do I use this tool? ###
```
usage: uefitool.py [-h] [-m] [-s] [-p] [-a] [-i] [-r] [-g] [-l] [--dump] [-n | -t | -v | -f | -d [type ...]] path

HPE EDKII UEFI DSC/INF/DEC/FDF Processing Tool: V0.6

positional arguments:
  path                  path to platform directory (default is current directory

options:
  -h, --help            show this help message and exit
  -m, --macros          do not generate macro list (macros.lst)
  -s, --source          do not generate source file list (source.lst)
  -p, --pcds            do not generate pcd list (pcd.lst)
  -a, --apriori         do not generate apiriori list (apriori.lst)
  -i, --ppis            do not generate ppi list (ppis.lst)
  -r, --protocols       do not generate protocol list (protocol.lst)
  -g, --guids           do not generate guid list (guid.lst)
  -l, --libraries       do not generate libraries list (libraries.lst)
  --dump                dump all file results to screen
  -n, --nominal         turn on nominal debug output
  -t, --typical         turn on typical debug output
  -v, --verbose         turn on verbose debug output
  -f, --full            turn on full debug output
  -d [type ...], --debug [type ...]
                        turn on debug to a specific level (64-bit integer, use 0x prefix to specify in hex)
```
### Invocation ###
This is very simple.

python uefitool.py <path-to-HPE-platform-PKG-driectory>

### This will generate the following files in the indicated HPE platform PKG directory ###
* macros.lst      - Macros used in processing the UEFI files and their FINAL values
* apriori_pei.lst - PEI apriori list for the platform and where they are defined
* apriori_dxe.lst - DXE apriori list for the platform and where they are defined
* sources.lst     - Source files used by the platform
* references.lst  - Source files used and where they are referenced by other files
* libraries.lst   - Libraries used, where defined, with useful fields and dependencies
* ppis.lst        - PPIs      used, their values,  where defined, and where referenced
* protocols.lst   - Protocols used, their values,  where defined, and where referenced
* guids.lst       - GUIDs     used, their values,  where defined, and where referenced
* pdcs.lst        - PCDs      used, defined items, where defined, and where referenced

  NOTE: Each of these can be turned off using command line options if desired.

  NOTE: Apriori files will not be present if not defined in the FDF files.

### There is debug output available to be viewed as the files are processed ###
* -n or --nominal - Shows each filename as it is being processed
* -t or --typical - Nominal + shows sections, and macro definitions
* -v or --verbose - Typical + shows individual lines in each section and how conditionals are evaluated
* -f or --full    - Verbose + skipped lines

  NOTE: verbose and full output are very long (even typical is pretty involved)

### Dumping all of the files ###
--dump will dump what the tool collected read from each of the files

  NOTE: dump is HUGE

### Creating the Windows and Linux executables using PyInstaller
Starting with V0.6 of this repo, Windows and Linux executables are being made available.

These are generated using the python pyinstaller module.

To generate these executables the following will need to be executed on Windows AND Linux
```
    python3 -m PyInstaller uefitool.py
```
* For Windows, the executable is dist/uefitool/uefitool.exe
* For Linux,   the executable is dist/uefitool/uefitool
* To use executable, add <tool-install-directory>/EFITool/dist/uefitool/uefitool to the PATH

### Version History ###
| Version | Explanation                                                                            |
|---------|----------------------------------------------------------------------------------------|
| V0.9    | Fixed problem where INFs in component section were not being processed completely      |
| V0.8    | - Fixed failure when run from UEFI base directory (worktree needs to be absolute path) |
|         | - Fixed display of SupportedArchitectures                                              |
| V0.7    | Fixed error where exit is not found                                                    |
| V0.6    | Correctred handling of reGUIDED, added executables to repo (PyInstaller)               |
| V0.5    | Corrected execution in Windows and Linux for Gen11 and Gen12 (no Gen12 Linux yet)      |
| V0.4    | Updated output files to include more useful information                                |
| V0.3	  | Generated output files and is controlled by command line parameters                    |
| V0.2	  | Updates to support Gen12 and Linux                                                     |
| V0.1	  | Original Release                                                                       |
