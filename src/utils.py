import colorama
from colorama import Fore, Back, Style

import src.globalVars as gv
import os
import shutil


def sanitizeName(inString):
    for entry in gv.replaceList:
        inString = inString.replace(entry[0], entry[1])
        inString = inString.rstrip(" ")     # get rid of last space, if exist
    
    return inString


def printDataFormatted(data):
    print("== {} - {} | Album: {} - TackNum: {}".format(data.get('title', "NA"), data.get('artist', "NA"), data.get('album', "NA"), data.get('trackNumber', "NA")))
    print("==\t - Release Year: {}".format(data.get('releaseYear', "NA")))
    print("==\t - Label: {}".format(data.get('label', "NA")))
    print("==\t - Tags: {}".format(data.get('tags', "NA")))
    

def printColored(text, color, end):
    print("{}{}{}".format(color, text, Style.RESET_ALL), end=end)

# Moving files from original path to a new destination path
# Respecting errors
def movingFiles(orgPath, destPath, error):
    os.makedirs(destPath, exist_ok=True)
    if (error.empty()):
        tempPath = destPath
        shutil.move(orgPath, tempPath)
    else:
        tempPath = os.path.join(destPath, error)
        shutil.move(orgPath, tempPath)
    
    if gv.verbose:
        print("==\t- {} {} {} - moving file to {}".format(Fore.RED, error, Fore.RESET, tempPath), end="")
