import logging

from django.test import TestCase

from diary.models import Job
from utils.logger_copy import copy_logger_settings

from utils.email import get_name_from_email


logger = logging.getLogger("testing_control").getChild(__name__)
copy_logger_settings("testing_subject", "diary.utils")


class TestGetNameFromEmail(TestCase):
    """
    Tests for get_name_from_email function of the utils module
    """

    def test_expected_email_format(self):
        first_name = "Test"
        last_name = "User"
        email = "{first}.{last}@example.com".format(
            first=first_name,
            last=last_name
        )
        self.assertEqual(first_name, get_name_from_email(email)[0])
        self.assertEqual(last_name, get_name_from_email(email)[1])

    def test_missing_last_name(self):
        first_name = "Test"
        last_name = ""
        email = "{first}.{last}@example.com".format(
            first=first_name,
            last=last_name
        )
        self.assertEqual("", get_name_from_email(email)[0])
        self.assertEqual("", get_name_from_email(email)[1])

    def test_missing_first_name(self):
        first_name = ""
        last_name = "User"
        email = "{first}.{last}@example.com".format(
            first=first_name,
            last=last_name
        )
        self.assertEqual("", get_name_from_email(email)[0])
        self.assertEqual("", get_name_from_email(email)[1])

    def test_non_dot_email(self):
        first_name = "Test"
        last_name = "User"
        email = "{first}{last}@example.com".format(
            first=first_name,
            last=last_name
        )
        self.assertEqual("", get_name_from_email(email)[0])
        self.assertEqual("", get_name_from_email(email)[1])

    def test_non_email_string(self):
        first_name = "Test"
        last_name = "User"
        email = "thisisnotanemailaddress"
        self.assertEqual("", get_name_from_email(email)[0])
        self.assertEqual("", get_name_from_email(email)[1])
