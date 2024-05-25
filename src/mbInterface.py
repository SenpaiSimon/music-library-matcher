import musicbrainzngs as mb
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import EasyMP3
from mutagen.id3 import ID3, APIC
import os
import shutil
import urllib

import colorama
from colorama import Fore, Back, Style

from .globals import *
from .types import *
from .utils import sanitizeName, printDataFormatted
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
    
    print("==\t- Trying release API", end='')
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
        print(" - {}Success{}".format(Fore.GREEN, Style.RESET_ALL))
        releaseID = release.get('id', Status.MISSING)
        # break instantly on ERR
        if(releaseID == Status.MISSING):
            return Status.ERR
        fallback = False
    else:
        fallback = True
        
    if(fallback == True):
        print(" - {}Failed{}".format(Fore.YELLOW, Style.RESET_ALL))
        print("==\t- Falling back to recordings API", end='')

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
        
        print(" - {}Success{}".format(Fore.GREEN, Style.RESET_ALL))


    print("==\t- Scraping Metadata from API", end='')
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
                        
    print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))                    
    return data


def _scrapeSong(path):
    data = _call_shazam(path)
    if(data == Status.ERR):
        return Status.ERR
    
    data = _get_metadata(data)
    if(data == Status.ERR):
        return Status.ERR
    
    return data


def _addMetadata(data, path):
    # first download cover art
    os.mkdir(tempPath)
    coverFile = os.path.join(tempPath, "cover.jpg")
    if(data['coverArtUrl'] != Status.MISSING):
        # delete old cover art is something is already there for some reason
        if(os.path.isfile(coverFile)):
            os.remove(coverFile)
        urllib.request.urlretrieve(data['coverArtUrl'], coverFile)
    
    print("== Adding Metadata to File", end='')
    
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
    
    shutil.rmtree(tempPath)
    print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
    
    # rename the file accordingly
    print("== Renaming and Moving File", end='')
    # move and rename the file accordingly if data is present
    if(data['title'] != Status.MISSING and data['artist'] != Status.MISSING and data['album'] != Status.MISSING and data['trackNumber'] != Status.MISSING):
        # sanitize output shit
        tempArtist = sanitizeName(data['artist'])
        tempAlbum  = sanitizeName(data['album'])
        tempTitle  = sanitizeName(data['title'])
        tempArtist = sanitizeName(data['artist'])
        
        # gen the output path dir
        outPath = os.path.join(outputPath, tempArtist, tempAlbum)
        outPath = outPath.replace("&", "and")
        # and create it
        os.makedirs(outPath, exist_ok=True)
        finalFileName = "{} - {} - {}{}".format(data['trackNumber'], tempArtist, tempTitle,  path.suffix)
        finalFileName = finalFileName.replace("&", "and")
        finalPath = os.path.join(outPath, finalFileName)
        # move the file
        shutil.move(path, finalPath)
        print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
    else:
        print(" - {}Skipped{}, since needed fields are missing".format(Fore.YELLOW, Style.RESET_ALL))
        skippedFiles.append(path)
        skippedPath = os.path.join(skippedFilesDir)
        os.makedirs(skippedPath, exist_ok=True)
        shutil.move(path, skippedPath)
        
        
def fillMetadata(path):
    data = _scrapeSong(path)
    
    if(data == Status.ERR):
        skippedFiles.append(path)
        skippedPath = os.path.join(skippedFilesDir)
        os.makedirs(skippedPath, exist_ok=True)
        
        try:
            shutil.move(path, skippedPath)
        except:
            # file already exists --> overwrite it please
            filename = path.name
            skippedPath = os.path.join(skippedPath, filename)
            shutil.move(path, skippedPath)
            
        print("== Error Scraping needed data", end='')
        print(" - {}Skipped{}".format(Fore.YELLOW, Style.RESET_ALL))
        return Status.ERR
    
    print("==")
    print("== {}RESULT{}".format(Fore.GREEN, Style.RESET_ALL))
    print("==")
    printDataFormatted(data)
    print("==")
    
    _addMetadata(data, path)
