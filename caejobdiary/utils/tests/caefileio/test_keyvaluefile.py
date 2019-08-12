"""
Module to unittest the functions of the `joblogfile` module
"""

import logging

from django.test import TestCase

from utils.logger_copy import copy_logger_settings

from utils.caefileio.keyvaluefile import get_value_string_from_line

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logger = logging.getLogger("testing_control")
copy_logger_settings("testing_subject", "utils.caefileio.keyvaluefile")


# -----------------------------------------------------------------------------
#  Test Helper Function `get_value_string_from_line`
# -----------------------------------------------------------------------------

class TestGetValueStringFromLine(TestCase):
    """
    Test the `get_value_string_from_line` helper function of `poll_jobs` script
    """

    # -------------------------------------------------------------------------
    def test_empty_value(self):
        output = get_value_string_from_line("Some-Key: ")
        self.assertEqual(output, "")

    # -------------------------------------------------------------------------
    def test_missing_colon_after_key(self):
        output = get_value_string_from_line("Some-Key ")
        self.assertEqual(output, "")

    # -------------------------------------------------------------------------
    def test_existing_value(self):
        output = get_value_string_from_line("Some-Key: Some string value")
        self.assertEqual(output, "Some string value")

    # -------------------------------------------------------------------------
    def test_value_including_colon(self):
        output = get_value_string_from_line("Some-Key: String with colon:itself")
        self.assertEqual(output, "String with colon:itself")
