import os

# Global constants
TILDA = os.environ['HOME'] # Home directory of linux
#TILDA = '/home/pi' # Home directory of linux
#PROGRAM_PATH = TILDA+'/PuxHelper'
PROGRAM_PATH = os.getcwd()
SERVER_PATH = TILDA+'/Mount/fileServer/PUBLIC'
CONFIG_PATH = SERVER_PATH+'/Nick/PythonData/Configs'
DATA_PATH = SERVER_PATH+'/Nick/PythonData/Data'
LOG_PATH = DATA_PATH+'/!PuxHelper_log.txt'
UPGRADE_PATH = SERVER_PATH+'/Nick/PythonData/Upgrades/PuxHelper'
LOCAL_PATH = os.environ['HOME']+'/Mount/tempDrive'

# Global variables and their types
globalRecentCompleteTorrents = [] # List of dictionaries
globalCurrentTorrentsProgress = {} # Dictionary of list of dictionaries
joinPlease = [False] # A list that contains one boolean value
joinStatus = {} # A dictionary of {'<module name>':joinStatus (boolean)}
torretSpeedResetTime = [-1] # A list that contains the time transmission's alt_speed_down should be reset. -1 if it's already reset.
