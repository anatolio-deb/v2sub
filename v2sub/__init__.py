import os

__version__ = '1.2'

# define all global variables in here
user = os.getenv("USER")
BASE_PATH = os.path.join(os.path.expanduser("~%s" % user), ".v2sub")
SUBSCRIBE_CONFIG = os.path.join(BASE_PATH, 'subscribes.json')
SERVER_CONFIG = os.path.join(BASE_PATH, 'servers.json')
DEFAULT_SUBSCRIBE = "default"
