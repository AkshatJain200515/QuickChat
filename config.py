
# Server connection settings
HOST = "127.0.0.1"
PORT = 5555
BUFFER_SIZE = 4096

# Username and message limits
MAX_USERNAME_LEN = 20
MAX_MESSAGE_LEN = 500

# These rooms are created when the server starts
DEFAULT_ROOMS = ["General", "Tech", "Random"]

# We use a pipe "/" to separate parts of each message
# Format: COMMAND/arg1/arg2
# Example: SEND/General/Hello everyone
DELIMITER = "/"

# Commands the server sends to clients
CMD_MESSAGE   = "MSG"
CMD_JOIN_OK   = "JOIN_OK"
CMD_USER_LIST = "USER_LIST"
CMD_ROOM_LIST = "ROOM_LIST"
CMD_ERROR     = "ERROR"
CMD_NOTIFY    = "NOTIFY"

# Commands clients send to the server
CMD_SET_NAME  = "SET_NAME"
CMD_JOIN      = "JOIN"
CMD_SEND      = "SEND"
CMD_CREATE    = "CREATE"
CMD_INVITE    = "INVITE"
CMD_LIST      = "LIST"
CMD_QUIT      = "QUIT"

# Log file path
LOG_FILE = "server.log"
