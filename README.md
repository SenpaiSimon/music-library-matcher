# music-library-matcher

This utility will
* Try to match any given media-file to a song using [shazam](https://pypi.org/project/shazamio/)
* Try to scrape any missing metadata using [musicbrainz](https://pypi.org/project/musicbrainzngs/)
* Add the metadata to the media-file using [mutagen](https://pypi.org/project/mutagen/)
* Download the cover and embed it
* Order the Mediafiles using a sensible folder structure

## Setup

```bash
python -m venv venv
# On Windows
source venv/Scripts/activate
# On Linux
source venv/bin/activate

pip install -r requirements.txt
```



## First Run

Just run the script once and a `config.json` will be created in the root directory.

```json
    // path were the finished music is put
    "outputPath": "./output",
    // path were the input files are
    "inputDir": "./input",
    // path were the skipped files are put
    "skippedFilesDir": "./output/skipped",
    // all the media types that are accepted
    "acceptedFilesExtensions": [
        ".mp3",
        ".wav",
        ".m4a"
    ],
    // all the characters that are replaced
    // first is the character to replace, 
    //second is the character to replace it with
    "replaceList": [
        [
            ".",
            ""
        ],
        [
            "/",
            "_"
        ],
        [
            //...
        ]
    ],
    // if the running output should be verbose
    "verbose": false
```
