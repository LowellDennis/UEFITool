# UEFITool
HPE UEFI Utility

### What is this repository for? ###

* Retreiving usful information from HPE UEFI files (DSC/DEC/INF/FDF)

### How do I get set up? ###

* To get the source use:
```
    cd ~
    git clone https://github.com/LowellDennis/UEFITools.git
```

* This assumes that you have python installed and in the path (at least V3.10)
    * You can get it [here](https://www.python.org/)

### How do I use this tool? ###

usage: uefitool.py [-h] [-m] [-s] [-p] [-a] [-i] [-r] [-g] [-l] [--dump] [-n | -t | -v | -f | -d [type ...]] path

HPE EDKII UEFI DSC/INF/DEC/FDF Processing Tool: V0.1

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

### Invocation ###
This is very simple.

python uefitool.py <path-to-HPE-platform-PKG-driectory>

### This will generate the following files in the indicated HPE platform PKG directory ###
* macros.lst      - List of all of the macros used in processing the UEFI files and their FINAL values 
* apriori_pei.lst - The PEI apriori list for the platform
* apriori_dxe.lst - The DXE apriori list for the platform
* sources.lst     - List of all of the source files used by the platorm
* libraries.lst   - List of all of the libraries used by the platform
* ppis.lst        - List of all of the PPIs used by the platform (and their values)
* protocols.lst   - List of all of the Protocols used by the platform (and their values)
* guids.lst       - List of all of the GUIDs used by the platform (and their values)
* pdcs.lst        - List of all of the PCDs used by the platform (and the default value, their type, and their id)

 NOTE: Each of these can be turned off using command line options if desired.

### There is debug output available to be viewed as the files are processed ###
* -n or --nominal - Shows each filename as it is being processed
* -t or --typical - Nominal + shows sections, and macro definitions
* -v or --verbose - Typical + shows individual lines in each section and how conditionals are evaluated
* -f or --full    - Verbose + skipped lines
s
 NOTE: verbose and full output are very long (even typical is pretty involved)

### Dumping all of the files ###
--dump will dump what the tool collected read from each of the files
 NOTE: dump is HUGE

### Version History ###
| Version | Explanation                                                                            |
|---------|----------------------------------------------------------------------------------------|
| V0.1	  | Original Release                                                                       |
