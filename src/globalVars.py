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
    outputPath = "/media/sven/ssd_1tb/2_postShazam"

    # input files are searched here
    inputDir = "/media/sven/ssd_1tb/0_waiting"

    # skipped and error files get moved here
    skippedFilesDir = "/media/sven/ssd_1tb/99_error"

    # replace 1 with 2 ("1", "2")
    replaceList = [(".",""),("/", "_"),(":", "-"), ("?", ""), ("\"", "-"), ("*", "x"), ("<", ""), (">", ""), ("\\", "\\\\")]

    # files types ##################################
    # ".flac", not working at the moment
    acceptedFilesExtensions = [".mp3", ".wav", ".m4a"]

    # verbosity
    verbose = False




    ################################### DONT TOUCH ##################################
    skippedFiles = []
    lastStatusPrint = ""