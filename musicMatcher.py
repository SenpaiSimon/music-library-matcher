import os
import musicbrainzngs as mb
import pathlib
import colorama
from colorama import Fore, Back, Style

import src.globalVars as gv
from src.utils import printColored
from src.mbInterface import fillMetadata
    
    
def main():
    colorama.init()
    mb.set_useragent("MB-Application", version="2.7.3")
    
    # first get total number of files
    totalFileCount = 0
    for root, dirs, files in os.walk(gv.inputDir):
        for filename in files:
            file = pathlib.Path(filename)
            if file.suffix in gv.acceptedFilesExtensions:
                totalFileCount += 1
       
    if(totalFileCount == 0):
        print("=========================================================================")
        print("==")
        print("== Found no files matching {}".format(gv.acceptedFilesExtensions))     
        print("==")       
        print("=========================================================================")
        exit(0)

    # now actually loop over them
    curFileIndex = 1
    print("=========================================================================")
    if not gv.verbose:
        print("==")
    for root, dirs, files in os.walk(gv.inputDir):
        for filename in files:
            curPath = pathlib.Path(os.path.join(root, filename))
            if curPath.suffix in gv.acceptedFilesExtensions:
                
                gv.lastStatusPrint = "{} of {} - File: {}".format(Fore.CYAN + str(curFileIndex) + Style.RESET_ALL, Fore.GREEN + str(totalFileCount) + Style.RESET_ALL, curPath.name)
                if gv.verbose:
                    print("==")
                    print("== {}".format(gv.lastStatusPrint))
                    print("==")
                else:
                    print("== {}".format(gv.lastStatusPrint), end="")
                    
                #  scrape all the metadata for current file
                fillMetadata(curPath)
                if gv.verbose:
                    print("==\n==")
                else:
                    print("")
                               
                curFileIndex += 1
    
    if not gv.verbose:
        print("==")
    print("=========================================================================")
    
    if(len(gv.skippedFiles) != 0):
        print("==")
        print("== {}Skipped Files{}".format(Fore.YELLOW, Style.RESET_ALL))
        for entry in gv.skippedFiles:
            print("==\t - {}".format(entry))
        print("==")
        print("=========================================================================")


if __name__ == "__main__":
    gv.init()
    main()