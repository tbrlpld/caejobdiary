from .base import *

print("Loading local settings.")

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "192.168.0.13",
                 # Required for requests with django.test.Client from the shell
                 "testserver"
                 ]

# Environment specific constants for CAE Job Diary

POLL_DIR = os.path.abspath(
    os.path.join(TOP_LEVEL_DIR, "data", "example_job_info_sources"))
UPDATE_TIMEOUT_SECONDS = 10  # Every 5 minutes
