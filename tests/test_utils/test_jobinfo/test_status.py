"""
Module to unittest the functions of the `status` module
"""

import logging
import os
import tempfile

import before_after
from django.test import TestCase

from diary.models import Job
from utils.logger_copy import copy_logger_settings
from test_utils.helper import make_cluster_script

from utils.jobinfo.status import get_job_status_and_job_dir_from_sub_dir
from utils.jobinfo.status import get_renamed_job_folder_from_list


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logger = logging.getLogger("testing_control")
copy_logger_settings("testing_subject", "utils.jobinfo.status")

# -----------------------------------------------------------------------------
class TestGetJobStatusAndJobDirFromSubDir(TestCase):
    """
    Test the `get_job_status_and_job_dir_from_sub_dir` method from the `status` module
    """

    # -------------------------------------------------------------------------
    def test_pending_job(self):
        with tempfile.TemporaryDirectory() as tempdir:
            job_id = 1234
            pending_folder = os.path.join(tempdir, str(job_id) + ".pending")
            os.makedirs(pending_folder)

            job_status, job_dir = get_job_status_and_job_dir_from_sub_dir(
                job_id=job_id, sub_dir=tempdir, recent=False)
            self.assertEqual(job_status, Job.JOB_STATUS_PENDING)
            self.assertEqual(job_dir, pending_folder)

    # -------------------------------------------------------------------------
    def test_running_job(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with tempfile.TemporaryDirectory() as tempscratch:
                logger.debug("temporary cluster scratch dir: {}".format(tempscratch))
                job_id = 1234

                make_cluster_script(job_id, tempdir, tempscratch)

                job_status, job_dir = get_job_status_and_job_dir_from_sub_dir(
                    job_id=job_id, sub_dir=tempdir, recent=False)
                self.assertEqual(job_status, Job.JOB_STATUS_RUNNING)
                self.assertEqual(job_dir, tempscratch)

    # -------------------------------------------------------------------------
    def test_running_job_not_existing_scratch_dir(self):
        logger.info("Test status determination for running job."
                    " Scratch dir does not exist.")
        with tempfile.TemporaryDirectory() as tempdir:
            job_id = 1234
            scratch_dir = "/this/does/not/exist/1234"
            make_cluster_script(job_id, tempdir, scratch_dir)

            job_status, job_dir = get_job_status_and_job_dir_from_sub_dir(
                job_id=job_id, sub_dir=tempdir, recent=False)
            self.assertEqual(job_status, Job.JOB_STATUS_NONE)
            self.assertEqual(job_dir, None)

    # -------------------------------------------------------------------------
    def test_recent_running_job(self):
        """
        The job has just been switched to running. Initially though, there is
        no cluster script. The cluster script is only created after the status
        was at least checked once.
        """
        with tempfile.TemporaryDirectory() as temp_sub_dir:
            with tempfile.TemporaryDirectory() as temp_scratch_dir:
                logger.debug("temporary cluster scratch dir: {}".format(
                    temp_scratch_dir))
                job_id = 1234

                def create_this_cluster_script(*a, **kw):
                    make_cluster_script(job_id, temp_sub_dir, temp_scratch_dir)
                    logger.info("Cluster script created" + "*" * 80)
                    logger.info("Content of sub_dir: {}".format(os.listdir(
                        temp_sub_dir)))

                with before_after.after(
                        "utils.jobinfo.status.get_cluster_script_from_list",
                        create_this_cluster_script):
                    job_status, job_dir = \
                        get_job_status_and_job_dir_from_sub_dir(
                            job_id=job_id, sub_dir=temp_sub_dir, recent=True)
                self.assertEqual(job_status, Job.JOB_STATUS_RUNNING)
                self.assertEqual(job_dir, temp_scratch_dir)

    # -------------------------------------------------------------------------
    def test_finished_job(self):
        with tempfile.TemporaryDirectory() as tempdir:
            job_id = 1234
            finished_folder = os.path.join(tempdir, str(job_id))
            os.makedirs(finished_folder)

            job_status, job_dir = get_job_status_and_job_dir_from_sub_dir(
                job_id=job_id, sub_dir=tempdir, recent=False)
            self.assertEqual(job_status, Job.JOB_STATUS_FINISHED)
            self.assertEqual(job_dir, finished_folder)

    # -------------------------------------------------------------------------
    def test_renamed_finished_job(self):
        with tempfile.TemporaryDirectory() as tempdir:
            job_id = 1234
            renamed_finished_folder = os.path.join(
                tempdir, str(job_id) + "_some_rename")
            os.makedirs(renamed_finished_folder)
            job_status, job_dir = get_job_status_and_job_dir_from_sub_dir(
                job_id=job_id, sub_dir=tempdir, recent=False)
            self.assertEqual(job_status, Job.JOB_STATUS_FINISHED)
            self.assertEqual(job_dir, renamed_finished_folder)

    # -------------------------------------------------------------------------
    def test_job_file_not_folder_pending(self):
        with tempfile.TemporaryDirectory() as tempdir:
            job_id = 9999999
            job_file = os.path.join(
                tempdir, str(job_id) + ".pending")
            open(job_file, "w").close()

            with self.assertLogs(logger="utils.jobinfo.status",
                                 level=logging.ERROR) as cm:
                    job_status, job_dir = \
                        get_job_status_and_job_dir_from_sub_dir(
                            job_id=job_id, sub_dir=tempdir, recent=False)
                    logger.info("Logs of required level: {}".format(cm.output))
            self.assertEqual(job_status, Job.JOB_STATUS_NONE)
            self.assertIsNone(job_dir)

    # -------------------------------------------------------------------------
    def test_job_file_not_folder_finished(self):
        with tempfile.TemporaryDirectory() as tempdir:
            job_id = 9999999
            job_file = os.path.join(
                tempdir, str(job_id))
            open(job_file, "w").close()

            with self.assertLogs(logger="utils.jobinfo.status",
                                 level=logging.ERROR) as cm:
                    job_status, job_dir = \
                        get_job_status_and_job_dir_from_sub_dir(
                            job_id=job_id, sub_dir=tempdir, recent=False)
                    logger.info("Logs of required level: {}".format(cm.output))
            self.assertEqual(job_status, Job.JOB_STATUS_NONE)
            self.assertIsNone(job_dir)

    # -------------------------------------------------------------------------
    def test_sub_dir_is_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            sub_dir_file = os.path.join(
                tempdir, "some_file")
            open(sub_dir_file, "w").close()
            job_id = 9999999
            job_status, job_dir = get_job_status_and_job_dir_from_sub_dir(
                job_id=job_id, sub_dir=sub_dir_file, recent=False)
            self.assertEqual(job_status, Job.JOB_STATUS_NONE)
            self.assertIsNone(job_dir)

    # -------------------------------------------------------------------------
    def test_no_files_in_subdir(self):
        with tempfile.TemporaryDirectory() as tempdir:
            job_id = 1234

            job_status, job_dir = get_job_status_and_job_dir_from_sub_dir(
                job_id=job_id, sub_dir=tempdir, recent=False)
            # self.assertIsNone(job_status)
            self.assertEqual(job_status, Job.JOB_STATUS_NONE)
            self.assertIsNone(job_dir)

    # -------------------------------------------------------------------------
    def test_not_existing_subdir(self):
        non_dir = "/this/is/not/existing/"
        job_id = 1234

        job_status, job_dir = get_job_status_and_job_dir_from_sub_dir(
            job_id=job_id, sub_dir=non_dir, recent=False)
        # self.assertIsNone(job_status)
        self.assertEqual(job_status, Job.JOB_STATUS_NONE)
        self.assertIsNone(job_dir)


# -----------------------------------------------------------------------------
#  Test Helper Function `get_renamed_job_folder_from_list`
# -----------------------------------------------------------------------------

class TestGetRenamedJobFolderFromList(TestCase):
    """
    Test the `get_renamed_job_folder_from_list` helper method of the
    `poll_jobs` script
    """

    # -------------------------------------------------------------------------
    def test_empty_list(self):
        file_list = []
        self.assertIsNone(
            get_renamed_job_folder_from_list(
                job_id=1234567,
                file_list=file_list
            )
        )

    # -------------------------------------------------------------------------
    def test_added_suffix(self):
        renamed_job_folder = "1234567_this_is_the_renaming"
        file_list = [renamed_job_folder]
        self.assertEqual(
            get_renamed_job_folder_from_list(
                job_id=1234567,
                file_list=file_list
            ),
            renamed_job_folder
        )

    # -------------------------------------------------------------------------
    def test_added_prefix(self):
        renamed_job_folder = "this_is_the_renaming_1234567"
        file_list = [renamed_job_folder]
        self.assertIsNone(get_renamed_job_folder_from_list(
            job_id=1234567,
            file_list=file_list
        ))

    # -------------------------------------------------------------------------
    def test_not_renamed(self):
        not_renamed_job_folder = "1234567"
        file_list = [not_renamed_job_folder]
        self.assertEqual(
            get_renamed_job_folder_from_list(
                job_id=1234567,
                file_list=file_list
            ),
            not_renamed_job_folder
        )

    # -------------------------------------------------------------------------
    def test_pending_folder(self):
        pending_job_folder = "1234567.pending"
        file_list = [pending_job_folder]
        self.assertIsNone(
            get_renamed_job_folder_from_list(
                job_id=1234567,
                file_list=file_list
            )
        )
