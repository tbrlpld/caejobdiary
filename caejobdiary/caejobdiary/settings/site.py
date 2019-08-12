from .base import *

print("Loading site settings.")

DEBUG = True

ALLOWED_HOSTS = ["localhost"]

DATABASES["default"] = DATABASES.pop("sqlite")

if OUTGOING_MAIL_HOST[0] == "localhost":
    LOGGING["handlers"]["error_mail"]["credentials"] = None
    LOGGING["handlers"]["error_mail"]["secure"] = None

# Environment specific constants for CAE Job Diary
POLL_DIR = os.path.realpath("/DB/.qstat/")
POLL_TIMEOUT_SECONDS = 5
UPDATE_TIMEOUT_SECONDS = 5 * 31
