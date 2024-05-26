import colorama
from colorama import Fore, Back, Style

from src.globals import *


def sanitizeName(inString):
    for entry in replaceList:
        inString = inString.replace(entry[0], entry[1])
    
    inString.rstrip('.')
    return inString


def printDataFormatted(data):
    print("== {} - {} | Album: {} - TackNum: {}".format(data.get('title', "NA"), data.get('artist', "NA"), data.get('album', "NA"), data.get('trackNumber', "NA")))
    print("==\t - Release Year: {}".format(data.get('releaseYear', "NA")))
    print("==\t - Label: {}".format(data.get('label', "NA")))
    print("==\t - Tags: {}".format(data.get('tags', "NA")))
    

def printColored(text, color, end):
    print("{}{}{}".format(color, text, Style.RESET_ALL), end=end)