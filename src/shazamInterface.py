from shazamio import Shazam
import asyncio

import colorama
from colorama import Fore, Back, Style

from .types import *
import src.globalVars as gv

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