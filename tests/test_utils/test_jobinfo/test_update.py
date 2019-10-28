"""
Module to unittest the functions of the `update` module
"""

import logging
import os
import tempfile
import time

import django
from django.contrib.auth import get_user_model
from django.test import TestCase
from mock import patch

# Test setup
from diary.models import Job
from utils.graceful_killer import GracefulKiller
from utils.logger_copy import copy_logger_settings
from tests.test_utils.helper import make_cluster_script

# Functions to be tested
from utils.jobinfo.update import update_status_of_unfinished_jobs_in_DB
from utils.jobinfo.update import update_status_of_job

# Logging
logger = logging.getLogger("testing_control")
copy_logger_settings("testing_subject", "utils.jobinfo.update")

# Make `User` model available
User = get_user_model()


class TestUpdateStatusOfUnfinishedJobsInDB(TestCase):
    """
    Test the `update_not_finished_jobs` method
    """
    def setUp(self):
        # This dummy killer is only needed as input to the update function.
        self.dummy_killer = GracefulKiller(name="Dummy")

        self.user_A = User.objects.create(
            username="usera", email="usera@example.com")

        self.project_A = "3001234"
        self.project_B = "3005678"

        self.job_user_A_project_A = Job(
            job_id=123,
            user=self.user_A,
            project=self.project_A,
            main_name="some_main_title.key",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_PENDING
        )
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()

        self.job_user_A_project_B = Job(
            job_id=456,
            user=self.user_A,
            project=self.project_B,
            main_name="another_main_title.key",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_RUNNING
        )
        self.job_user_A_project_B.full_clean()
        self.job_user_A_project_B.save()

    def test_pending_and_running_to_finished(self):
        logger.info(
            "Testing update of not finished jobs (pending/running) to finished")

        # First job (pending)
        sub_dir_1 = tempfile.TemporaryDirectory()
        # Setup pending job in DB
        self.job_user_A_project_A.job_dir = os.path.join(
            sub_dir_1.name, str(self.job_user_A_project_A.job_id) + ".pending")
        self.job_user_A_project_A.sub_dir = sub_dir_1.name
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        # Create finished job on filesystem
        job_dir_1 = os.path.join(sub_dir_1.name,
                                 str(self.job_user_A_project_A.job_id))
        os.makedirs(job_dir_1)

        # Second job (running)
        sub_dir_2 = tempfile.TemporaryDirectory()
        # Setup running job in DB
        self.job_user_A_project_B.job_dir = os.path.join(
            "/W04_cluster_scratch/", str(self.job_user_A_project_B.job_id))
        self.job_user_A_project_B.sub_dir = sub_dir_2.name
        self.job_user_A_project_B.full_clean()
        self.job_user_A_project_B.save()
        # Create finished job on filesystem
        job_dir_2 = os.path.join(
            sub_dir_2.name, str(self.job_user_A_project_B.job_id))
        os.makedirs(job_dir_2)

        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)

        updated_job_1 = Job.objects.get(
            job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(
            updated_job_1.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job_1.job_status, Job.JOB_STATUS_FINISHED)
        self.assertEqual(updated_job_1.job_dir, job_dir_1)

        updated_job_2 = Job.objects.get(
            job_id=self.job_user_A_project_B.job_id)
        self.assertEqual(
            updated_job_2.job_id, self.job_user_A_project_B.job_id)
        self.assertEqual(updated_job_2.job_status, Job.JOB_STATUS_FINISHED)
        self.assertEqual(updated_job_2.job_dir, job_dir_2)

        sub_dir_1.cleanup()
        sub_dir_2.cleanup()

    @patch("utils.jobinfo.update.update_status_of_job")
    def test_call_of_update_function_for_pending_jobs(self, mock):
        """
        Testing if the update function is called when the only job in
        the DB is pending.
        """
        logger.info("Testing calling job update for only 'pending' jobs in DB")
        for job in Job.objects.all():
            job.job_status = Job.JOB_STATUS_PENDING
            job.full_clean()
            job.save()
        self.assertEqual(
            Job.objects.count(),
            Job.objects.filter(job_status=Job.JOB_STATUS_PENDING).count())
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertTrue(mock.called)

    @patch("utils.jobinfo.update.update_status_of_job")
    def test_call_of_update_function_for_running_jobs(self, mock):
        logger.info("Testing calling job update for only 'running' jobs in DB")
        for job in Job.objects.all():
            job.job_status = Job.JOB_STATUS_RUNNING
            job.full_clean()
            job.save()
        self.assertEqual(
            Job.objects.count(),
            Job.objects.filter(job_status=Job.JOB_STATUS_RUNNING).count())
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertTrue(mock.called)

    @patch("utils.jobinfo.update.update_status_of_job")
    def test_not_updating_finished_job(self, mock):
        """
        When there are only finished jobs in the DB, then there should be no
        call to the function that updates the status of a given job object.

        This kind of test can be achieved with the mock module.
        """
        logger.info("Testing NOT calling job update for only"
                    " 'finished' jobs in DB")
        for job in Job.objects.all():
            job.job_status = Job.JOB_STATUS_FINISHED
            job.full_clean()
            job.save()
        self.assertEqual(
            Job.objects.count(),
            Job.objects.filter(job_status=Job.JOB_STATUS_FINISHED).count())
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertFalse(mock.called)

    @patch("utils.jobinfo.update.update_status_of_job")
    def test_not_updating_none_status_job(self, mock):
        logger.info("Testing NOT calling job update for only"
                    " 'none' status jobs in DB")
        for job in Job.objects.all():
            job.job_status = Job.JOB_STATUS_NONE
            job.full_clean()
            job.save()
        self.assertEqual(
            Job.objects.count(),
            Job.objects.filter(job_status=Job.JOB_STATUS_NONE).count())
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertFalse(mock.called)

    @patch("utils.jobinfo.update.update_status_of_job")
    def test_not_updating_normal_termination_job(self, mock):
        logger.info("Testing NOT calling job update for only"
                    " 'normal termination' jobs in DB")
        for job in Job.objects.all():
            job.job_status = Job.JOB_STATUS_NORMAL_TERMINATION
            job.full_clean()
            job.save()
        self.assertEqual(
            Job.objects.count(),
            Job.objects.filter(
                job_status=Job.JOB_STATUS_NORMAL_TERMINATION).count())
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertFalse(mock.called)

    @patch("utils.jobinfo.update.update_status_of_job")
    def test_not_updating_error_termination_job(self, mock):
        logger.info("Testing NOT calling job update for only"
                    " 'error termination' jobs in DB")
        for job in Job.objects.all():
            job.job_status = Job.JOB_STATUS_ERROR_TERMINATION
            job.full_clean()
            job.save()
        self.assertEqual(
            Job.objects.count(),
            Job.objects.filter(
                job_status=Job.JOB_STATUS_ERROR_TERMINATION).count())
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertFalse(mock.called)
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertFalse(mock.called)

    @patch("utils.jobinfo.update.update_status_of_job")
    def test_not_updating_other_termination_job(self, mock):
        logger.info("Testing NOT calling job update for only"
                    " 'other termination' jobs in DB")
        for job in Job.objects.all():
            job.job_status = Job.JOB_STATUS_OTHER_TERMINATION
            job.full_clean()
            job.save()
        self.assertEqual(
            Job.objects.count(),
            Job.objects.filter(
                job_status=Job.JOB_STATUS_OTHER_TERMINATION).count())
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertFalse(mock.called)
        update_status_of_unfinished_jobs_in_DB(self.dummy_killer)
        self.assertFalse(mock.called)


class TestUpdateStatusOfJob(TestCase):
    """
    Test the `update_status_of_job` method
    """

    def setUp(self):
        self.user_A = User.objects.create(
            username="usera", email="usera@example.com")

        self.project_A = "3001234"

        self.job_user_A_project_A = Job(
            job_id=123,
            user=self.user_A,
            project=self.project_A,
            main_name="some_main_title.key",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_PENDING
        )
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()

    def test_pending_to_pending(self):
        logger.info("Testing job status update pending to pending")

        with tempfile.TemporaryDirectory() as sub_dir:
            job_dir = os.path.join(
                sub_dir, str(self.job_user_A_project_A.job_id) + ".pending")
            os.makedirs(job_dir)

            self.job_user_A_project_A.sub_dir = sub_dir
            self.job_user_A_project_A.job_dir = job_dir
            self.job_user_A_project_A.full_clean()
            self.job_user_A_project_A.save()
            created_job = Job.objects.get(pk=self.job_user_A_project_A.job_id)
            self.assertEqual(created_job.job_status, Job.JOB_STATUS_PENDING)

            update_status_of_job(created_job)

        updated_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_status, Job.JOB_STATUS_PENDING)
        self.assertEqual(updated_job.job_dir, job_dir)
        self.assertEqual(updated_job.updated, created_job.updated)

    def test_pending_to_running(self):
        logger.info("Testing job status update pending to running")

        with tempfile.TemporaryDirectory() as sub_dir:
            # Setup pending job in DB
            self.job_user_A_project_A.sub_dir = sub_dir
            job_dir = os.path.join(
                sub_dir, str(self.job_user_A_project_A.job_id) + ".pending")
            self.job_user_A_project_A.job_dir = job_dir
            self.job_user_A_project_A.full_clean()
            self.job_user_A_project_A.save()

            created_job = Job.objects.get(pk=self.job_user_A_project_A.job_id)
            self.assertEqual(created_job.job_status, Job.JOB_STATUS_PENDING)

            # Create running status on filesystem
            with tempfile.TemporaryDirectory() as scratch_dir:
                make_cluster_script(
                    job_id=self.job_user_A_project_A.job_id,
                    sub_dir=sub_dir,
                    scratch_dir=scratch_dir)

                update_status_of_job(created_job)

        updated_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_status, Job.JOB_STATUS_RUNNING)
        self.assertEqual(updated_job.job_dir, scratch_dir)

    def test_pending_to_running_no_scratch_dir(self):
        logger.info("Testing job status update pending to running."
                    " Scratch dir does not exist.")

        with tempfile.TemporaryDirectory() as sub_dir:
            # Setup pending job in DB
            self.job_user_A_project_A.sub_dir = sub_dir
            job_dir = os.path.join(
                sub_dir, str(self.job_user_A_project_A.job_id) + ".pending")
            self.job_user_A_project_A.job_dir = job_dir
            self.job_user_A_project_A.full_clean()
            self.job_user_A_project_A.save()
            created_job = Job.objects.get(pk=self.job_user_A_project_A.job_id)
            self.assertEqual(created_job.job_status, Job.JOB_STATUS_PENDING)

            not_existing_dir = "/does/not/exist/dir"
            self.assertFalse(os.path.exists(not_existing_dir))
            make_cluster_script(
                job_id=self.job_user_A_project_A.job_id,
                sub_dir=sub_dir,
                scratch_dir=not_existing_dir)

            update_status_of_job(created_job)

        updated_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_status, Job.JOB_STATUS_NONE)
        self.assertEqual(updated_job.job_dir, None)

    def test_pending_to_finished(self):
        logger.info("Testing job status update pending to finished")

        with tempfile.TemporaryDirectory() as sub_dir:
            # Setup pending job in DB
            self.job_user_A_project_A.sub_dir = sub_dir
            job_dir = os.path.join(
                sub_dir, str(self.job_user_A_project_A.job_id) + ".pending")
            self.job_user_A_project_A.job_dir = job_dir
            self.job_user_A_project_A.full_clean()
            self.job_user_A_project_A.save()
            created_job = Job.objects.get(pk=self.job_user_A_project_A.job_id)
            self.assertEqual(created_job.job_status, Job.JOB_STATUS_PENDING)

            # Create finished job on filesystem
            new_job_dir = os.path.join(
                sub_dir, str(self.job_user_A_project_A.job_id))
            os.makedirs(new_job_dir)

            update_status_of_job(created_job)

        updated_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_status, Job.JOB_STATUS_FINISHED)
        self.assertEqual(updated_job.job_dir, new_job_dir)

    def test_pending_to_none(self):
        logger.info("Testing job status update pending to none")

        with tempfile.TemporaryDirectory() as sub_dir:
            # Setup pending job in DB
            self.job_user_A_project_A.sub_dir = sub_dir
            job_dir = os.path.join(
                sub_dir, str(self.job_user_A_project_A.job_id) + ".pending")
            self.job_user_A_project_A.job_dir = job_dir
            self.job_user_A_project_A.full_clean()
            self.job_user_A_project_A.save()
            created_job = Job.objects.get(pk=self.job_user_A_project_A.job_id)
            self.assertEqual(created_job.job_status, Job.JOB_STATUS_PENDING)

            update_status_of_job(created_job)

        updated_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_status, Job.JOB_STATUS_NONE)
        self.assertIsNone(updated_job.job_dir)

    def test_running_to_running(self):
        logger.info("Testing job status update running to running")

        with tempfile.TemporaryDirectory() as sub_dir:
            with tempfile.TemporaryDirectory() as scratch_dir:
                make_cluster_script(job_id=123, sub_dir=sub_dir,
                                    scratch_dir=scratch_dir)
                self.job_user_A_project_A.sub_dir = sub_dir
                self.job_user_A_project_A.job_dir = scratch_dir
                self.job_user_A_project_A.job_status = Job.JOB_STATUS_RUNNING
                self.job_user_A_project_A.full_clean()
                self.job_user_A_project_A.save()
                created_job = Job.objects.get(
                    pk=self.job_user_A_project_A.job_id)
                self.assertEqual(
                    created_job.job_status, Job.JOB_STATUS_RUNNING)

                update_status_of_job(created_job)

        updated_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_status, Job.JOB_STATUS_RUNNING)
        self.assertEqual(updated_job.job_dir, scratch_dir)
        self.assertEqual(updated_job.updated, created_job.updated)

    def test_running_to_finished(self):
        logger.info("Testing job status update running to finished")

        with tempfile.TemporaryDirectory() as sub_dir:
            # Setup running job in DB
            self.job_user_A_project_A.sub_dir = sub_dir
            job_dir = os.path.join(
                "/W04_cluster_scratch/", str(self.job_user_A_project_A.job_id))
            self.job_user_A_project_A.job_dir = job_dir
            self.job_user_A_project_A.job_status = Job.JOB_STATUS_RUNNING
            self.job_user_A_project_A.full_clean()
            self.job_user_A_project_A.save()
            created_job = Job.objects.get(
                pk=self.job_user_A_project_A.job_id)
            self.assertEqual(
                created_job.job_status, Job.JOB_STATUS_RUNNING)

            # Create finished job on filesystem
            new_job_dir = os.path.join(
                sub_dir, str(self.job_user_A_project_A.job_id))
            os.makedirs(new_job_dir)

            update_status_of_job(created_job)

        updated_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_status, Job.JOB_STATUS_FINISHED)
        self.assertEqual(updated_job.job_dir, new_job_dir)

    def test_running_to_none(self):
        logger.info("Testing job status update running to none")

        with tempfile.TemporaryDirectory() as sub_dir:
            # # Setup running job in DB
            self.job_user_A_project_A.sub_dir = sub_dir
            job_dir = os.path.join(
                "/W04_cluster_scratch/", str(self.job_user_A_project_A.job_id))
            self.job_user_A_project_A.job_dir = job_dir
            self.job_user_A_project_A.job_status = Job.JOB_STATUS_RUNNING
            self.job_user_A_project_A.full_clean()
            self.job_user_A_project_A.save()
            created_job = Job.objects.get(
                pk=self.job_user_A_project_A.job_id)
            self.assertEqual(
                created_job.job_status, Job.JOB_STATUS_RUNNING)

            update_status_of_job(created_job)

        updated_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_id, self.job_user_A_project_A.job_id)
        self.assertEqual(updated_job.job_status, Job.JOB_STATUS_NONE)
        self.assertIsNone(updated_job.job_dir)

    def test_wrong_input_type(self):
        logger.info("Testing job status update with integer input")
        update_status_of_job(123)

        logger.info("Testing job status update with string input")
        update_status_of_job("123")

        logger.info("Testing job status update with bool input")
        update_status_of_job(True)
        update_status_of_job(False)

        logger.info("Testing job status update with None input")
        update_status_of_job(None)
