import os

from .base import *

print("Loading production settings.")

# DEBUG = False

ALLOWED_HOSTS = ["u304jdb01"]

# No email credentials required for use of localhost
if OUTGOING_MAIL_HOST[0] == "localhost":
    LOGGING["handlers"]["error_mail"]["credentials"] = None
    LOGGING["handlers"]["error_mail"]["secure"] = None

# In production, the databse should be kept outside the repo.
DATABASE_DIR = "/opt/caejd/db/"
if not os.path.exists(DATABASE_DIR):
    os.makedirs(DATABASE_DIR)
DATABASES['sqlite']['NAME'] = os.path.join(DATABASE_DIR, 'jdb.sqlite3')

# Saving log files outside the repo
LOG_DIR = "/opt/caejd/logs/"
LOGGING["handlers"]["pollRotateHandler"]["filename"] = LOG_DIR + "poll.log"
LOGGING["handlers"]["pollWarnRotateHandler"]["filename"] = LOG_DIR + "poll.warn"
LOGGING["handlers"]["updateRotateHandler"]["filename"] = LOG_DIR + "update.log"
LOGGING["handlers"]["diaryRotateHandler"]["filename"] = LOG_DIR + "diary.log"
LOGGING["handlers"]["djangoRotateHandler"]["filename"] = LOG_DIR + "django.log"

# Environment specific constants for CAE Job Diary
POLL_DIR = os.path.realpath("/DB/.qstat/")
