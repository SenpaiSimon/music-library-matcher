def init():
    global tempPath
    global outputPath
    global inputDir
    global skippedFilesDir
    global replaceList
    global acceptedFilesExtensions
    global verbose
    global skippedFiles
    global lastStatusPrint

    # paths ########################################

    # temp is used for coverart download
    tempPath = "./temp"

    # sucesful files get moved here
    outputPath = "./output"

    # input files are searched here
    inputDir = "./testing"

    # skipped and error files get moved here
    skippedFilesDir = "./skipped"

    # replace 1 with 2 ("1", "2")
    replaceList = [("/", "_"),(":", "-"), ("?", ""), ("\"", "-"), ("*", "oo"), ("<", ""), (">", ""), ("\\", "\\\\")]

    # files types ##################################
    acceptedFilesExtensions = [".mp3", ".flac"]

    # verbosity
    verbose = False




    ################################### DONT TOUCH ##################################
    skippedFiles = []
    lastStatusPrint = ""