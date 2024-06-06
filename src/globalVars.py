import json

def init():
    global tempPath
    global outputPath
    global inputDir
    global skippedFilesDir
    global duplicatedFilesDir
    global dataformatFilesDir
    global replaceList
    global acceptedFilesExtensions
    global unsupportedFilesExtensions
    global verbose
    global skippedFiles
    global lastStatusPrint
    
    with open("config.json", "r") as read_file:
        config = json.load(read_file)

    # paths ########################################

    # temp is used for coverart download
    tempPath = "./temp"

    # sucesful files get moved here
    outputPath = config['outputPath']

    # input files are searched here
    inputDir = config['inputDir']

    # skipped and error files get moved here
    skippedFilesDir = config['skippedFilesDir']

    # duplicated files get moved here (due to already existing)
    duplicatedFilesDir = config['duplicatedFilesDir']

    # wrong dataformats get moved here
    dataformatFilesDir = config['dataformatFilesDir']

    # replace 1 with 2 ("1", "2")
    replaceList = config['replaceList']

    # files types ##################################
    acceptedFilesExtensions = config['acceptedFilesExtensions']

    # files types to be done
    unsupportedFilesExtensions = config['unsupportedFilesExtensions']

    # verbosity
    verbose = config['verbose']


    ################################### DONT TOUCH ##################################
    skippedFiles = []
    lastStatusPrint = ""