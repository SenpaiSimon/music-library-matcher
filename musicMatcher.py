import asyncio
import os
from shazamio import Shazam
import musicbrainzngs as mb
import pathlib
import colorama
from colorama import Fore, Back, Style
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import EasyMP3
from mutagen.id3 import ID3, APIC
import urllib
import shutil
from enum import Enum

class Status(Enum):
    ERR = 1
    OK = 2
    SKIP = 3
    MISSING = 4

    
skippedFiles = []

async def _exec_shazam(path):
    shazam = Shazam()

    res = await shazam.recognize(str(path))  # rust version, use this!
    track = res.get('track', Status.ERR)
    
    # break out on error
    if(track == Status.ERR):
        return Status.ERR

    data = {}
    data['title'] = track.get('title', Status.MISSING)
    data['artist'] = track.get('subtitle', Status.MISSING)
    data['coverArtUrl'] = track.get('images', {}).get('coverart', Status.MISSING)
    data['album'] = Status.MISSING
    data['label'] = Status.MISSING
    data['releaseYear'] = Status.MISSING
    
    try:
        metadata = track.get('sections', "NA")[0].get('metadata', "NA")
    except IndexError:
        metadata = Status.ERR
    except AttributeError:
        metadata = Status.ERR
        
    # break out on error
    if(metadata == Status.ERR):
        return Status.ERR
    
    for entry in metadata:
        if(entry['title'] == 'Album'):
            data['album'] = entry.get('text', Status.MISSING)
        if(entry['title'] == 'Label'):
            data['label'] = entry.get('text', Status.MISSING)
        if(entry['title'] == 'Released'):
            data['releaseYear'] = entry.get('text', Status.MISSING)
            
    return data


def _call_shazam(path):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    data = loop.run_until_complete(_exec_shazam(path))
    return data


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
    
    shutil.rmtree("./temp")
    print(" - {}DONE{}".format(Fore.GREEN, Style.RESET_ALL))
    
    # rename the file accordingly
    print("== Renaming and Moving File", end='')
    # move and rename the file accordingly if data is present
    if(data['title'] != Status.MISSING and data['artist'] != Status.MISSING and data['album'] != Status.MISSING and data['trackNumber'] != Status.MISSING):
        # sanitize output shit
        tempArtist = data['artist'].replace("/", "_").rstrip('.').replace(":", "-")
        tempAlbum = data['album'].replace("/", "_").rstrip('.').replace(":", "-")
        tempTitle = data['title'].replace("/", "_").rstrip('.').replace(":", "-")
        tempArtist = data['artist'].replace("/", "_").rstrip('.').replace(":", "-")
        
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
        skippedPath = os.path.join(outputPath, "skipped")
        os.makedirs(skippedPath, exist_ok=True)
        shutil.move(path, skippedPath)


def printDataFormatted(data):
    print("== {} - {} | Album: {} - TackNum: {}".format(data.get('title', "NA"), data.get('artist', "NA"), data.get('album', "NA"), data.get('trackNumber', "NA")))
    print("==\t - Release Year: {}".format(data.get('releaseYear', "NA")))
    print("==\t - Label: {}".format(data.get('label', "NA")))
    print("==\t - Tags: {}".format(data.get('tags', "NA")))

        
def fillMetadata(path):
    data = _scrapeSong(path)
    if(data == Status.ERR):
        skippedFiles.append(path)
        skippedPath = os.path.join(outputPath, "skipped")
        os.makedirs(skippedPath, exist_ok=True)
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
    # paths
    tempPath = "./temp"
    outputPath = "./output"
    inputDir = "./testing"
    
    # files types
    acceptedFilesExtensions = [".mp3", ".flac"]
    main()