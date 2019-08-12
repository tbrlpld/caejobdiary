import logging.config
from multiprocessing import Process
import os
import sys
import time
import subprocess

import django.conf

# Adding the project directory to the path to make imports of other modules
# of the project possible.
TOP_LEVEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOP_LEVEL_DIR)
DJANGO_PROJECT_DIR = os.path.join(TOP_LEVEL_DIR, "caejobdiary")
sys.path.insert(0, DJANGO_PROJECT_DIR)

from utils.graceful_killer import GracefulKiller
from utils.jobinfo import poll, update
from utils.logger_copy import copy_logger_settings


# -----------------------------------------------------------------------------
# Logging Setting
# -----------------------------------------------------------------------------

logging.config.dictConfig(django.conf.settings.LOGGING)

# -----------------------------------------------------------------------------
# Django Server
# -----------------------------------------------------------------------------


def run_django_server():
    graceful_killer = GracefulKiller(name="Django")

    manage_path = os.path.join(DJANGO_PROJECT_DIR, "manage.py")
    django_call = ["python", manage_path, "runserver", "0:8000"]
    django_proc = subprocess.Popen(
        django_call,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )

    while True:
        time.sleep(1)
        if graceful_killer.kill_now:
            django_proc.terminate()
            break


# -----------------------------------------------------------------------------
# RUN
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    copy_logger_settings(logger.name, "utils.graceful_killer")

    logger.info("CAEJobDiary started...")

    procs = []

    logger.info("Starting polling process.")
    poll_proc = Process(
        target=poll.main,
        name="Polling")
    poll_proc.start()
    procs.append(poll_proc)

    logger.info("Starting update process.")
    update_proc = Process(
        target=update.main,
        name="Update")
    update_proc.start()
    procs.append(update_proc)

    logger.info("Starting Django server.")
    django_server_proc = Process(
        target=run_django_server,
        name="Django Server")
    django_server_proc.start()
    procs.append(django_server_proc)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interruption detected. Stopping processes.")
        for proc in procs:
            logger.info("Stopping process: (pid {}) {}".format(
                proc.pid, proc.name))
            proc.join()
            proc.terminate()
            if proc.exitcode == 0:
                logger.info("Process {} ended successfully.".format(
                    proc.pid))
            else:
                logger.warning("Process {} exitcode: {}".format(
                    proc.pid, proc.exitcode))
    except Exception as err_msg:
        logger.exception(
            "Exception in main process occurred!\n{}".format(err_msg))
        raise

    logger.info("All CAEJobDiary processes stopped.")
    logger.info("Goodbye...")
