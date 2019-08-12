"""
Module defining functions to regularly poll for new jobs and add them to the DB

The information about new jobs is retrieved from a directory that is to
be defined in the settings files via `POLL_DIR`.
The directory will probably be different between development and
production environment.

In the `POLL_DIR` the script will check for new joblogfiles, which are
created by the SGE queuing system every time a new job is submitted.
This script should be run as a continuously running deamon.
Log files that already existed at a previous poll are stored in a
dictionary. Only files that are not in that dictionary will be checked for
information about the new job.

Methods
-------
main()
    Start regular polling for new jobs and add them to the DB

start_job_creation_process_from_joblogfile(joblogfile)
    Controls the process flow to get from a joblogfile to a job added to the DB
"""

import logging
import logging.config
import os
import time

from datetime import datetime, timedelta

import django
from django.conf import settings

from .status import get_job_status_and_job_dir_from_sub_dir
from utils.graceful_killer import GracefulKiller
from utils.logger_copy import copy_logger_settings
from utils.caefileio.joblogfile import is_joblogfilename
from utils.caefileio.joblogfile import get_job_info_from_joblogfile
from utils.caefileio.readme import get_readme_filename_from_job_dir
from utils.caefileio.readme import get_job_info_from_readme


# -----------------------------------------------------------------------------
# Django Setup
# -----------------------------------------------------------------------------

# Setup Django. This initializes Django and makes the installed apps known.
# It then also trys to import the models from their submodules
django.setup()

# Once Django is setup, I can either import the models from the module
# from diary.models import Job
# or grab them from the installed apps that are known to Django.
# https://docs.djangoproject.com/en/2.1/ref/applications/#django.apps.apps.get_model
Job = django.apps.apps.get_model("diary", "Job")


# -----------------------------------------------------------------------------
def main():
    """
    Start regular polling for new jobs and add them to the DB
    """
    logger = logging.getLogger(__name__).getChild("main")

    # Get the POLL_DIR to use from the Django settings
    POLL_DIR = settings.POLL_DIR
    logger.info("="*80)
    logger.info("Polling started from : {}".format(POLL_DIR))
    logger.info("="*80)

    graceful_killer = GracefulKiller(name="Polling")

    # Start polling on regular intervals
    old = dict()
    try:
        while not graceful_killer.kill_now:
            allfiles = dict([(f, None) for f in os.listdir(POLL_DIR)])
            added = [os.path.abspath(os.path.join(POLL_DIR, f))
                     for f in allfiles if f not in old]
            logger.debug("Added files in poll dir: {}".format(added))
            for file in sorted(added):
                # Checking killer before every file, because many files might
                # be added at once (which would block the process for some
                # time).
                if graceful_killer.kill_now:
                    break
                if is_joblogfilename(file) and os.path.exists(file):
                    # Closing old connections to prevent attempting to use a
                    # stale one.
                    django.db.close_old_connections()

                    start_job_creation_process_from_joblogfile(joblogfile=file)
                else:
                    logger.debug("File is not a joblogfile or "
                                 "does not exist: {}".format(file))
            old = allfiles
            # In stead of sleeping for the entire timeout at once, the killer
            # status is checked every second until the number of timeout
            # seconds is reached.
            for i in range(settings.POLL_TIMEOUT_SECONDS):
                if graceful_killer.kill_now:
                    break
                time.sleep(1)
    except Exception as err_msg:
        logger.exception("Exception in polling process!\n{}".format(err_msg))
        raise

    logger.info("="*80)
    logger.info("Exiting polling")
    logger.info("="*80)


# -----------------------------------------------------------------------------
def start_job_creation_process_from_joblogfile(joblogfile):
    """
    Start processing to add job to DB based on a given joblogfile

    The joblogfile is the initial source of information required to start
    gathering of information about a job. The joblogfile is therefore required
    as input. Input file is assumed to be joblogfile.

    If the given file is an existing joblogfile, the job creation process is
    started from it and continued. The job creation processing ends with the
    saving of the job to the Django database, or with an error message log
    if some required information can not be determined.

    Parameters
    ----------
    joblogfiles : str, required
        Path for joblogfile to start the job creation from.

    Returns
    -------
    boolean
        Returns True if a job was saved to the DB. Otherwise, a message
        is logged and returns False.
    """

    logger = logging.getLogger(__name__).getChild(
        "start_job_creation_process_from_joblogfile")
    copy_logger_settings(__name__, "utils.caefileio.readme")
    copy_logger_settings(__name__, "utils.caefileio.joblogfile")
    copy_logger_settings(__name__, "utils.jobinfo.status")
    copy_logger_settings(__name__, "diary.models")

    logger.info("Processing joblogfile: {}".format(joblogfile))

    job = Job()
    job.logfile_path = joblogfile

    # Get job_id and sub_dir from joblogfile
    try:
        job.job_id, job.sub_dir, log_date = get_job_info_from_joblogfile(
            joblogfile)
    except FileNotFoundError as err_msg:
        logger.warning("{}. Joblogfile not found.".format(err_msg)
                       + " No further processing possible.")
        return False
    # Further processing only makes sense when job_id and sub_dir
    # have been found successfully.
    logger.info("job_id: {}, sub_dir: {}".format(job.job_id, job.sub_dir))
    if job.job_id is None or job.sub_dir is None:
        logger.error("No valid job_id or sub_dir found in joblogfile. "
                     " No further processing possible."
                     " joblogfile: {}".format(joblogfile))
        return False

    # Further processing is NOT necessary if the job_id already exists
    # in the DB.
    if Job.objects.filter(pk=job.job_id).exists():
        logger.info("Job ID {} already in database. Skipping job.".format(
            job.job_id))
        return False

    # After the job_status and job_dir have been determined, it can happen that
    # the status changes and the directory is moved. This is a race condition
    # that would make the processing fail, because the information can not be
    # found in the expected location.
    # If the race condition occurs the status should be rechecked.
    # This handling is done by the while-loop.
    job_status_checked_counter = 0
    job_status_racecondition_occured = False
    while (job_status_checked_counter == 0
            or job_status_racecondition_occured is True):
        # Resetting the race condition to its default. This is important to
        # prevent getting stuck in the loop once the race condition occurred.
        job_status_racecondition_occured = False

        # Get job_status and job_dir based on job_id and sub_dir
        job.job_status, job.job_dir = \
            get_job_status_and_job_dir_from_sub_dir(
                job_id=job.job_id,
                sub_dir=job.sub_dir,
                recent=is_recent(log_date)
            )
        job_status_checked_counter += 1
        logger.debug("Job status checks: {}".format(
            job_status_checked_counter))
        # Further processing requires the job_status and the job_dir
        logger.info("job_status: {}, job_dir: {}".format(
                    job.job_status, job.job_dir))
        if job.job_status is Job.JOB_STATUS_NONE or job.job_dir is None:
            # TODO: Since there is a defined "none/undefined" status for the
            # jobs, these can be added to the DB too. There should also be
            # defined errors that give additional info on why the status could
            # not be determined. This can be included in the refactoring in #90
            logger.info("No valid job_status or job_dir"
                        " could be determined from sub_dir."
                        " No further processing possible.")
            return False

        try:
            # Get filename of README from from job_dir
            job.readme_filename = \
                get_readme_filename_from_job_dir(job.job_dir)
        except PermissionError as err_msg:
            logger.warning("No permission to read job_dir: {}".format(err_msg))
            return False
        except FileNotFoundError as err_msg:
            logger.info("Determined job_dir not found."
                        + " Status might have changed. {}".format(err_msg))
            job_status_racecondition_occured = True
            continue  # Move to next loop
        logger.info(
            "Determined README filename: {}".format(job.readme_filename))
        # Further processing requires the filename of the README
        if job.readme_filename is None:
            logger.warning(
                "No README found in job_dir ({}).".format(job.job_dir)
                + " No further processing possible.")
            return False

        # Get required information from README
        readme_filepath = os.path.join(
            job.job_dir, job.readme_filename)
        try:
            readme_info = get_job_info_from_readme(
                readme_filepath)
        except PermissionError as err_msg:
            logger.info("No permission to read README. "
                        "No further processing possible. {}".format(err_msg))
            return False
        except FileNotFoundError as err_msg:
            logger.info("Determined README filepath does not exist."
                        " Status might have changed. {}".format(err_msg))
            job_status_racecondition_occured = True
            continue  # Move to next loop
        # Further processing is not possible if not all required info from
        # README is available.
        if not required_keys_avaiable(readme_dict=readme_info):
            logger.error("Not all required info from README is available!"
                         + " README processing should be checked!\n"
                         + " Affected README: {}\n".format(readme_filepath)
                         + " Extracted data: {}\n".format(readme_info))
            return False

    # Save job to DB
    job.main_name = readme_info["main_name"]
    job.solver = readme_info["solver"]
    job.sub_date = Job.get_timezone_aware_datetime(
        readme_info["sub_date"])
    job.info = readme_info["info_block"]
    job.add_user(
        username=readme_info["username"],
        email=readme_info["email"],
    )
    job.full_clean()
    job.save()
    job.add_base_runs(readme_info["base_runs"])
    logger.info("Job {} is saved to DB.".format(job.job_id))
    return True


# -----------------------------------------------------------------------------
def is_recent(datetime_obj):
    """
    Check if datetime object represents time within the past 24 hours

    Parameters
    ----------
    datetime_obj : datetime
        Datetime object to be checked if recent

    Returns
    -------
    boolean
        True if given datetime object lays within the past 24 hours,
        False otherwise or if passed object is not a datetime object.
    """

    now = datetime.now()
    recent_limit = timedelta(hours=24)
    if type(datetime_obj) is datetime:
        delta = now - datetime_obj
        if delta <= recent_limit:
            return True
        else:
            return False
    else:
        return False


# -----------------------------------------------------------------------------
def required_keys_avaiable(readme_dict):
    """
    Check if the required key in the readme dictionary are available

    Required key are the ones I need for further processing.
    These are:
     * base_runs
     * username
     * email
     * info_block
     * sub_date
     * solver

     Parameters
     ----------
     readme_dict : dict
        Dictionary to be tested for containing all required keys

    Returns
    -------
    boolean
        True if all required keys are available, False otherwise.
    """

    REQUIRED_KEYS = [
        "main_name",
        "base_runs",
        "username",
        "email",
        "info_block",
        "sub_date",
        "solver"
    ]
    return all(req_key in readme_dict.keys() for req_key in REQUIRED_KEYS)
