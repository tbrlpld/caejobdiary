import logging

from django.test import TestCase

from diary.templatetags.status_to_bootstrap_color import job_status_to_color, \
    analysis_status_to_color, result_assessment_to_color
from diary.models import Job

logger = logging.getLogger("testing_control").getChild(__name__)


class TestJobStatusToColor(TestCase):
    """
    Test the `job_status_to_color` function
    """
    def test_known_statuses(self):
        self.assertEqual(
            job_status_to_color(Job.JOB_STATUS_PENDING), "primary")
        self.assertEqual(
            job_status_to_color(Job.JOB_STATUS_RUNNING), "secondary")
        self.assertEqual(
            job_status_to_color(Job.JOB_STATUS_FINISHED), "info")
        self.assertEqual(
            job_status_to_color(Job.JOB_STATUS_NORMAL_TERMINATION), "success")
        self.assertEqual(
            job_status_to_color(Job.JOB_STATUS_ERROR_TERMINATION), "danger")
        self.assertEqual(
            job_status_to_color(Job.JOB_STATUS_OTHER_TERMINATION), "warning")
        self.assertEqual(
            job_status_to_color(Job.JOB_STATUS_NONE), "light")

    def test_unknown_status(self):
        self.assertEqual(job_status_to_color("notastatus"), "dark")


class TestAnalysisStatusToColor(TestCase):
    """
    Test the `job_status_to_color` function
    """
    def test_known_statuses(self):
        self.assertEqual(
            analysis_status_to_color(Job.ANALYSIS_STATUS_OPEN), "primary")
        self.assertEqual(
            analysis_status_to_color(Job.ANALYSIS_STATUS_ONGOING), "secondary")
        self.assertEqual(
            analysis_status_to_color(Job.ANALYSIS_STATUS_DONE), "success")

    def test_unknown_status(self):
        self.assertEqual(analysis_status_to_color("notastatus"), "dark")


class TestResultAssessmentToColor(TestCase):
    """
    Test the `job_status_to_color` function
    """
    def test_known_statuses(self):
        self.assertEqual(
            result_assessment_to_color(Job.RESULT_ASSESSMENT_OK), "success")
        self.assertEqual(
            result_assessment_to_color(Job.RESULT_ASSESSMENT_NOK), "danger")
        self.assertEqual(
            result_assessment_to_color(Job.RESULT_ASSESSMENT_OTHER), "info")
        self.assertEqual(
            result_assessment_to_color(Job.RESULT_ASSESSMENT_ISSUE), "warning")
        self.assertEqual(
            result_assessment_to_color(Job.RESULT_ASSESSMENT_OBSOLETE), "light")

    def test_unknown_status(self):
        self.assertEqual(result_assessment_to_color("notastatus"), "dark")
