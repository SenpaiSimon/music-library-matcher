import os
import musicbrainzngs as mb
import pathlib
import colorama
from colorama import Fore, Back, Style

from src.globals import *
from src.mbInterface import fillMetadata
    
    
def main():
    colorama.init()
    mb.set_useragent("MB-Application", version="2.7.3")
    
    # first get total number of files
    totalFileCount = 0
    for root, dirs, files in os.walk(inputDir):
        for filename in files:
            file = pathlib.Path(filename)
            if file.suffix in acceptedFilesExtensions:
                totalFileCount += 1
       
    if(totalFileCount == 0):
        print("=========================================================================")
        print("==")
        print("== Found no files matching {}".format(acceptedFilesExtensions))     
        print("==")       
        print("=========================================================================")
        exit(0)

    # now actually loop over them
    curFileIndex = 1
    for root, dirs, files in os.walk(inputDir):
        for filename in files:
            curPath = pathlib.Path(os.path.join(root, filename))
            if curPath.suffix in acceptedFilesExtensions:
                
                print("=========================================================================")
                print("==")
                print("== {} of {} - File: {}".format(Fore.CYAN + str(curFileIndex) + Style.RESET_ALL, Fore.GREEN + str(totalFileCount) + Style.RESET_ALL, curPath.name))
                #  scrape all the metadata for current file
                fillMetadata(curPath)
                print("==")
                print("=========================================================================")
                
                # add metadata to the audio file and rename it TODO
                
                curFileIndex += 1
                print("\n")
    
    if(len(skippedFiles) != 0):
        print("=========================================================================")
        print("==")
        print("== {}Skipped Files{}".format(Fore.YELLOW, Style.RESET_ALL))
        for entry in skippedFiles:
            print("==\t - {}".format(entry))
        print("==")
        print("=========================================================================")



if __name__ == "__main__":
    main()