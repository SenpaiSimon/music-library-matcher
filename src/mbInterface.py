import musicbrainzngs as mb
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import EasyMP3
from mutagen.id3 import ID3, APIC
import os
import shutil
import urllib

import colorama
from colorama import Fore, Back, Style

import src.globalVars as gv
from .types import *
from .utils import sanitizeName, printDataFormatted, printColored
from .shazamInterface import _call_shazam

def _get_metadata(data):
    # break instantly on ERR
    if(data == Status.ERR):
        return Status.ERR
    
    # break on missing needed information
    if(data.get('title') == Status.MISSING):
        return Status.ERR
    if(data.get('artist') == Status.MISSING):
        return Status.ERR
    
    if gv.verbose:
        print("\n", end="")
        print("==\t\t- Trying release API", end="")

    try:
        artistID = mb.search_artists(data.get('artist', {})).get('artist-list', "NA")[0].get('id', Status.MISSING)
    except IndexError:
        artistID = Status.MISSING
    
    # break instantly on ERR
    if(artistID == Status.MISSING):
        return Status.ERR
        
    try:
        release = mb.search_releases(data.get('title'), arid=artistID).get('release-list', "NA")[0]
    except IndexError:
        release = Status.MISSING
    
    if(release == Status.MISSING):
        fallback = True
    elif(release.get('title', "NA") == data.get('title', "NA")):
        if gv.verbose:
            print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
        releaseID = release.get('id', Status.MISSING)
        # break instantly on ERR
        if(releaseID == Status.MISSING):
            return Status.ERR
        fallback = False
    else:
        fallback = True
        
    if(fallback == True):
        if gv.verbose:
            print(" - {}Failed{}".format(Fore.YELLOW, Style.RESET_ALL))
            print("==\t\t- Falling back to recordings API", end='')
        else:
            print("\33[2K\r== {} - Falling back to recordings API".format(gv.lastStatusPrint), end="")

        recordingSearch = mb.search_recordings(data.get('title'), arid=artistID).get('recording-list', Status.MISSING)
        if(recordingSearch == Status.MISSING):
            return Status.ERR
        
        try:
            recordingID = recordingSearch[0].get('id', Status.MISSING)
        except IndexError:
            return Status.ERR
            
        recording = mb.get_recording_by_id(recordingID, includes=['releases', 'discids', 'artist-credits', 'tags', 'isrcs', 'label-rels']).get('recording', Status.MISSING)
        if(recording == Status.MISSING):
            return Status.ERR
        
        if gv.verbose:
            print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
        else:
            print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL), end="")

    if gv.verbose:
        print("==\t\t- Scraping Metadata from API", end="")
    else: 
        print("\33[2K\r== {} - Scraping Metadata from API".format(gv.lastStatusPrint), end="")
        
    if not fallback:  
        songExtendedData = mb.get_release_by_id(releaseID, includes=['tags', 'artists', 'recordings', 'release-groups', 'labels', 'discids']).get('release', Status.MISSING)
        
        if(songExtendedData == Status.MISSING):
            return Status.ERR
        
        tagList = songExtendedData.get('release-group', {}).get('tag-list', Status.MISSING)
        if (tagList != Status.MISSING):
            data['tags'] = [tag.get('name', "NA") for tag in tagList]
        else:
            data['tags'] = Status.MISSING
        
        try:
            trackNum = songExtendedData.get('medium-list', "NA")[0].get('track-list', "NA")[0].get('position', Status.MISSING)
            
            if(trackNum == Status.MISSING):
                return Status.ERR
            else:
                data['trackNumber'] = trackNum
        except IndexError:
            return Status.ERR
        
        for key, value in data.items():
            if(value == Status.MISSING):
                if(key == "album"):
                    data[key] = songExtendedData.get('release-group', {}).get('title', Status.MISSING)
                if(key == "releaseYear"):
                    data[key] = songExtendedData.get('date', Status.MISSING)
                if(key == "label"):
                    try:
                        data[key] = songExtendedData.get('label-info-list', "NA")[0].get('label', {}).get('name', Status.MISSING)
                    except IndexError:
                        data[key] = Status.MISSING
                        
    else:
        tagList = recording.get('tag-list', Status.MISSING)
        if (tagList != Status.MISSING):
            data['tags'] = [tag.get('name', "NA") for tag in tagList]
        else:
            data['tags'] = Status.MISSING
            
        try:
            trackNum = recording.get('release-list', "NA")[0].get('medium-list', "NA")[0].get('track-list', "NA")[0].get('position', Status.MISSING)
            if(trackNum == Status.MISSING):
                return Status.ERR
            else:
                data['trackNumber'] = trackNum
        except IndexError:
            return Status.ERR
        
        for key, value in data.items():
            if(value == Status.MISSING):
                if(key == "album"):
                    try:
                        data[key] = recording.get('release-list', "NA")[0].get('title', Status.MISSING)
                    except IndexError:
                        data[key] = Status.MISSING
                if(key == "releaseYear"):
                    try:
                        data[key] = recording.get('release-list', "NA")[0].get('date', Status.MISSING)
                    except IndexError:
                        data[key] = Status.MISSING
                if(key == "label"):
                    try:
                        data[key] = recording[0].get('release', {}).get('label-info-list', "NA")[0].get('label', {}).get('name', Status.MISSING)
                    except IndexError:
                        data[key] = Status.MISSING
                    except KeyError:
                        data[key] = Status.MISSING
                        
    if gv.verbose:
        print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
    else:
        print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL), end="")
                  
    return data


def _scrapeSong(path):
    if gv.verbose:
        print("==\t- Calling Shazam API", end="")
    else:
        print(" - Calling Shazam API", end="")
        
    data = _call_shazam(path)
    if(data == Status.ERR):
        if gv.verbose:
            print(" - {}failed{}".format(Fore.RED, Style.RESET_ALL))
        return Status.ERR
    
    if gv.verbose:
        print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
    else: 
        print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL), end="")
        
    if gv.verbose:
        print("==\t- Getting Metadata from Musicbrainz", end="")
    else: 
        print("\33[2K\r== {} - Getting Metadata from Musicbrainz".format(gv.lastStatusPrint), end ="")
    data = _get_metadata(data)
    if(data == Status.ERR):
        if gv.verbose:
            print(" - {}failed{}".format(Fore.RED, Style.RESET_ALL))
        return Status.ERR
    
    return data


def _addMetadata(data, path):
    # first download cover art
    if gv.verbose:
        print("==\t- Processing all Scraped Metadata")
    else:
        print("\33[2K\r== {} - Processing all Scraped Metadata".format(gv.lastStatusPrint), end="")
        
    os.mkdir(gv.tempPath)
    coverFile = os.path.join(gv.tempPath, "cover.jpg")
    if(data['coverArtUrl'] != Status.MISSING):
        if gv.verbose:
            print("==\t\t- Downloading Cover-Art", end="")
        # delete old cover art is something is already there for some reason
        if(os.path.isfile(coverFile)):
            os.remove(coverFile)
        urllib.request.urlretrieve(data['coverArtUrl'], coverFile)
        if gv.verbose:
            print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
    
    if gv.verbose:
        print("==\t\t- Adding Metadata to File", end='')
    
    # first text metadata
    EasyID3.RegisterTextKey('label', 'TPUB')
    audio = EasyMP3(path)
    if(data['title'] != Status.MISSING):
        audio['title'] = data['title']
    if(data['artist'] != Status.MISSING):
        audio['artist'] = data['artist']
    if(data['album'] != Status.MISSING):
        audio['album'] = data['album']
    if(data['trackNumber'] != Status.MISSING):
        audio['tracknumber'] = data['trackNumber']
    if(data['releaseYear'] != Status.MISSING):
        audio['date'] = data['releaseYear']
    if(data['label'] != Status.MISSING):
        audio['label'] = data['label']
    if(data['tags'] != Status.MISSING):
        audio['genre'] = data['tags']
    audio.save()
    
    # now cover art
    audio = ID3(path)
    if(os.path.isfile(coverFile)):
        with open(coverFile, 'rb') as albumart:
            audio['APIC'] = APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3, desc=u'Cover',
                            data=albumart.read()
                            )            
        audio.save()
    
    shutil.rmtree(gv.tempPath)
    if gv.verbose:
        print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
    
    # rename the file accordingly
    if gv.verbose:
        print("==\t\t- Renaming and Moving File", end='')
    # move and rename the file accordingly if data is present
    if(data['title'] != Status.MISSING and data['artist'] != Status.MISSING and data['album'] != Status.MISSING and data['trackNumber'] != Status.MISSING):
        # sanitize output shit
        tempArtist = sanitizeName(data['artist'])
        tempAlbum  = sanitizeName(data['album'])
        tempTitle  = sanitizeName(data['title'])
        tempArtist = sanitizeName(data['artist'])
        
        # gen the output path dir
        outPathAlbum = "{} - {}".format(tempArtist, tempAlbum)
        outPath = os.path.join(gv.outputPath, tempArtist, outPathAlbum)
        # and create it
        os.makedirs(outPath, exist_ok=True)
        finalFileName = "{} - {} - {}{}".format(data['trackNumber'], tempArtist, tempTitle,  path.suffix)
        finalPath = os.path.join(outPath, finalFileName)
        # move the file
        shutil.move(path, finalPath)
        if gv.verbose:
            print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
            print("==\t-> {}New Filename{} is: {}".format(Fore.CYAN, Style.RESET_ALL, finalFileName))
        else: 
            print("\33[2K\r== {} -> New Filename: {}".format(gv.lastStatusPrint, finalFileName), end="")
    else:
        if gv.verbose:
            print(" - {}Skipped{} - needed fields are missing".format(Fore.YELLOW, Style.RESET_ALL))
        
        gv.skippedFiles.append(path)
        skippedPath = os.path.join(gv.skippedFilesDir)
        if gv.verbose:
            print("==\t\t- Moving file to {}".format(skippedPath), end="")
        os.makedirs(skippedPath, exist_ok=True)
        shutil.move(path, skippedPath)
        if gv.verbose:
            print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
        else:
            print("\33[2K\r== {} -> missing fields - moving to {}".format(gv.lastStatusPrint, skippedPath), end="")
        
def fillMetadata(path):
    data = _scrapeSong(path)
    
    if(data == Status.ERR):
        if gv.verbose:
            print("==\t- Error Scraping needed data", end='')
            print(" - {}Skipped{}".format(Fore.YELLOW, Style.RESET_ALL))
        else:
            print("\33[2K\r== {} Error scraping needed data".format(gv.lastStatusPrint), end="")
        
        gv.skippedFiles.append(path)
        skippedPath = os.path.join(gv.skippedFilesDir)
        os.makedirs(skippedPath, exist_ok=True)
        
        if gv.verbose:
            print("==\t- Moving file to {}".format(skippedPath), end="")
        try:
            shutil.move(path, skippedPath)
        except:
            # file already exists --> overwrite it please
            filename = path.name
            skippedPathNew = os.path.join(skippedPath, filename)
            shutil.move(path, skippedPathNew)
        
        if gv.verbose:   
            print("- {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
        else:
            print("\33[2K\r== {} -> err skipped - moving to {}".format(gv.lastStatusPrint, skippedPath), end="")
        return Status.ERR
    _addMetadata(data, path)
