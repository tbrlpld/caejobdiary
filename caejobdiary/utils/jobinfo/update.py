"""
Functions to regularly update the status of unfinished jobs

The unfinished jobs are retrieved from the DB on a regular basis. 10 minutes
seems like a fair update cycle.
"""

import logging
import time

import django
from django.conf import settings
from django.db.models import Q

from diary.models import Job
from utils.graceful_killer import GracefulKiller
from utils.jobinfo.status import get_job_status_and_job_dir_from_sub_dir
from utils.logger_copy import copy_logger_settings


def main():
    """
    Start loop to update the job status of all not-finished jobs regularly

    The loop time out is set to 5 min
    """

    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Starting update loop")
    logger.info("=" * 80)

    graceful_killer = GracefulKiller(name="Update")

    try:
        while not graceful_killer.kill_now:
            # Closing old connections to prevent attempting to use a stale one.
            django.db.close_old_connections()

            logger.info("Checking for unfinished jobs in DB.")
            update_status_of_unfinished_jobs_in_DB(killer=graceful_killer)
            # In stead of sleeping for the entire timeout at once, the killer
            # status is checked every second until the number of timeout
            # seconds is reached.
            for i in range(settings.UPDATE_TIMEOUT_SECONDS):
                if graceful_killer.kill_now:
                    break
                time.sleep(1)
    except Exception as err_msg:
        logger.exception("Exception in update process!\n{}".format(err_msg))
        raise

    logger.info("=" * 80)
    logger.info("Exiting update loop")
    logger.info("=" * 80)


def update_status_of_unfinished_jobs_in_DB(killer):
    """
    Get all the objects of the not-finished jobs and pass them on for updating
    """

    logger = logging.getLogger(__name__)

    # Getting queryset for all jobs
    jobs_list = Job.objects.all()
    # Defining Q query object for job status pending or running
    Q_lookup = (
        Q(job_status=Job.JOB_STATUS_PENDING)
        | Q(job_status=Job.JOB_STATUS_RUNNING)
    )
    jobs_list = jobs_list.filter(Q_lookup)

    if jobs_list:
        logger.info("Updating jobs: {}".format(jobs_list))
        for job in jobs_list:
            logger.debug("Current job for update: {}".format(job))
            update_status_of_job(job)
            if killer.kill_now:
                logger.debug("Loop break is triggered...")
                break
        logger.debug("Update loop finished.")
    else:
        logger.info("No unfinished jobs for update in DB.")


def update_status_of_job(job):
    """
    Update the status of the given job
    """

    logger = logging.getLogger(__name__)
    copy_logger_settings(__name__, "utils.jobinfo.status")

    if isinstance(job, Job):
        logger.info("Updating status of job: {}".format(job.job_id))

        before_update_status = job.job_status
        job.job_status, job.job_dir = get_job_status_and_job_dir_from_sub_dir(
            job_id=job.job_id, sub_dir=job.sub_dir, recent=True)
        after_update_status = job.job_status

        if after_update_status != before_update_status:
            logger.debug("New status: {}".format(job.job_status))
            logger.debug("New job_dir: {}".format(job.job_dir))
            job.full_clean()
            job.save()
        else:
            logger.debug("Job status not changed.")
        logger.info("Status update finished (job {})".format(job.job_id))
    else:
        logger.error("Input is not a Job object!")
