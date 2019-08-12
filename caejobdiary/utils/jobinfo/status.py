"""
Functions to determine the current status of a job

Once a job is submitted to the cluster is goes through three statuses:
pending, running and finished.

Each status is marked by a specific condition of files and directories that
are present in the `sub_dir` (the directory from which the job was submitted).

While the job is in status transition it can happen that the filesystem
represents no or multiple statuses. This transition typically only lasts for a
few seconds and can be resolved be rechecking the status.

Attention: jobs could be deleted (no status can be determined) or the whole
project could be archived (the `sub_dir` to check the status from will not
exist). These cases need to be considered. Especially the deletion can happen
at any point in time by user interaction on the filesystem.
"""

import logging
import os
import re
import time

import django

# from diary.models import Job
from utils.caefileio.clusterscript import get_cluster_script_from_list
from utils.caefileio.clusterscript import get_cluster_scratch_dir_from_script
from utils.logger_copy import copy_logger_settings


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
def get_job_status_and_job_dir_from_sub_dir(job_id, sub_dir, recent=False):
    """
    Get job_status for job_id from sub_dir

    If a job is recent, the `sub_dir` will be checked upto 3 times for the
    status. This feature is implemented because it can happen that the job
    switches from pending to running and that the pending folder has already
    disappeared but the cluster script is not yet created.

    Checking this only for recent jobs makes sense because this function will
    be called soon after the job has been submitted (and is thus pending).
    If a job is old and there is no pending folder, no cluster script and
    no finished folder when this function is called the job has probably been
    deleted or moved.

    Old jobs are typically only processed when the polling script is restarted
    and thus the information about previously checked joblogfiles is lost.

    Parameters
    ----------
    job_id : int
        Job id to check the status for
    sub_dir : str
        Path of the directory where the job was submitted
    recent : boolean
        Datetime in joblogfile points to recent submission. If `True`, then
        `sub_dir` is checked for `job_status` upto 3 times. Otherwise, the
        `sub_dir` is only checked once. Default is False.

    Returns
    -------
    job_status : str
        Job status short string as defined in the Job model.

    job_dir : None or str
        None if no job dir (or job_status) could be determined, otherwise the
        directory path where the job data is currently located.
    """

    logger = logging.getLogger(__name__).getChild(
        "get_job_status_and_job_dir_from_sub_dir")
    copy_logger_settings(__name__, "utils.caefileio.clusterscript")
    logger.info("Getting job_status and job_dir from sub_dir: {}".format(
        sub_dir))

    # Setting default return
    job_status = None
    job_dir = None

    checks_counter = 0
    if recent:
        checks_limit = 3
    else:
        checks_limit = 1

    while checks_counter < checks_limit and job_status is None:
        checks_counter += 1
        if checks_counter > 1:
            time.sleep(1)
            logger.debug("Re-checking sub_dir for job_status and job_dir.")
        else:
            logger.debug("Checking sub_dir for job_status and job_dir.")
        logger.debug(" {}/{} checks.".format(checks_counter, checks_limit))
        try:
            sub_dir_content = os.listdir(sub_dir)
            logger.debug(
                "Content of sub_dir: {}".format(sorted(sub_dir_content)))
        except NotADirectoryError as err_msg:
            logger.warning(f"sub_dir is not a directory: {err_msg}")
        except FileNotFoundError as err_msg:
            logger.info(f"sub_dir not found: {err_msg}")
        except PermissionError as err_msg:
            logger.info(f"No access to sub_dir: {err_msg}")
        except OSError as err_msg:
            logger.warning(
                f"OSError occurred. Not sure what causes it: {err_msg}")
        else:
            finished_job_foldername = str(job_id)
            pending_job_foldername = str(job_id) + ".pending"
            cluster_script_filename = get_cluster_script_from_list(
                job_id=job_id, file_list=sub_dir_content)
            # Order finish-running-pending makes sense, because if maybe
            # there are some leftovers (like files) from the previous stage
            # I will not check for them.
            if finished_job_foldername in sub_dir_content:
                logger.debug("Finished job folder name in sub_dir!")
                job_status = Job.JOB_STATUS_FINISHED
                job_dir = os.path.join(sub_dir, finished_job_foldername)
            elif cluster_script_filename is not None:
                job_status = Job.JOB_STATUS_RUNNING
                job_dir = get_cluster_scratch_dir_from_script(
                    os.path.join(sub_dir, cluster_script_filename))
            elif pending_job_foldername in sub_dir_content:
                job_status = Job.JOB_STATUS_PENDING
                job_dir = os.path.join(sub_dir, pending_job_foldername)
                logger.debug(
                    "Pending job folder name in sub dir: {}".format(job_dir))
            # If none of the above was successful, the job folder might be
            # renamed. This is checked here. It has to be after the pending
            # check because it maybe extended with anything.
            else:
                renamed_job_folder = get_renamed_job_folder_from_list(
                    job_id=job_id,
                    file_list=sub_dir_content)
                if renamed_job_folder:
                    renamed_job_folder_path = os.path.join(
                        sub_dir,
                        renamed_job_folder)
                    logger.debug(
                        "Possibly found renamed job folder: {}".format(
                            renamed_job_folder))
                    if os.path.isdir(renamed_job_folder_path):
                        logger.debug("Renamed job folder is dir: {}".format(
                            renamed_job_folder_path))
                        logger.debug("Assuming finished job.")
                        job_status = Job.JOB_STATUS_FINISHED
                        job_dir = renamed_job_folder_path

    if job_status is not None and checks_counter > 1:
        logger.debug(
            "=" * 80 + "\nRe-checking sub_dir is worth it!\n" + ("=" * 80))

    if job_status is not None and job_dir is not None:
        if os.path.isdir(job_dir):
            logger.info("job_status determined from sub_dir: {}".format(
                job_status))
            logger.info("job_dir determined from sub_dir: {}".format(job_dir))
            return job_status, job_dir
        else:
            logger.error("Found job_dir is not a directory: {}".format(
                job_dir))

    logger.info("No job_status or job_dir could be determined from sub_dir")
    return Job.JOB_STATUS_NONE, None


# -----------------------------------------------------------------------------
def get_renamed_job_folder_from_list(job_id, file_list):
    """
    Get renamed job folder from list of filenames

    Parameters
    ----------
    job_id : int
        job_id to check the existence of a renamed job folder for
    file_list : list
        List of filenames to check the existence of the job folder in.

    Returns
    -------
    str or None
        If a renamed job folder was found, the name is returned. If there are
        multiple matches, only the first one is returned. If no matching
        folder name was found, None is returned.
    """

    logger = logging.getLogger(__name__).getChild(
        "get_renamed_job_folder_from_list")
    # logger = logging.getLogger("poll_jobs.get_renamed_job_folder_from_list")
    logger.info("Checking for renamed job folders for job_id {}".format(
        job_id))

    renamed_job_folder_pattern = re.compile("^" + str(job_id) + "(?!.pending).*$")
    logger.debug("Regex pattern for renamed job folder: {}".format(
        renamed_job_folder_pattern))

    matches = list(filter(renamed_job_folder_pattern.match,
                          file_list))
    logger.debug("Renamed job folder matches: {}".format(matches))
    if matches:
        logger.info("Renamed job folder: {}".format(matches[0]))
        return matches[0]
    else:
        logger.info("No renamed job folder found")
        return None
