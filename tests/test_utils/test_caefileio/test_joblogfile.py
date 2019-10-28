"""
Module to unittest the functions of the `joblogfile` module
"""

from datetime import datetime
import logging
import tempfile

from django.test import TestCase

from utils.logger_copy import copy_logger_settings
from tests.test_utils.helper import add_content_to_temp_inputfilepath

from utils.caefileio.joblogfile import get_job_info_from_joblogfile
from utils.caefileio.joblogfile import is_joblogfilename


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logger = logging.getLogger("testing_control")
copy_logger_settings("testing_subject", "utils.caefileio.joblogfile")


# -----------------------------------------------------------------------------
#  Testing
# -----------------------------------------------------------------------------

class TestIsJoblogFilename(TestCase):
    """
    Test the `is_joblogfilename` helper method of the `poll_jobs` script
    """

    # -------------------------------------------------------------------------
    def test_different_paths_and_file(self):

        # Test correct joblogfilename with path
        self.assertTrue(is_joblogfilename(
            "/some/more/dirs/2010-07-01__12:34:56-1234567.log"))

        #Test correct joblogfilename without path"""
        self.assertTrue(is_joblogfilename(
            "2010-07-01__12:34:56-1234567.log"))

        # The `a` before the id should not be there.
        self.assertFalse(is_joblogfilename(
            "/some/more/dirs/2018-07-27__08:28:37-a1234567.log"))

        # The `a` before the id should not be there.
        self.assertFalse(is_joblogfilename(
            "2018-07-27__08:28:37-a1234567.log"))

        # Missing id. This seems to happen with some regularity in production.
        # Not sure why these file are generated, but they are no functioning
        # joblogfiles.
        self.assertFalse(is_joblogfilename(
            "2018-07-27__08:28:37-.log"))

        # This testing cluster script filename, which is not a joblogfile name.
        self.assertFalse(is_joblogfilename(
            "1234567.dyn-dmp.x99xx123.16.sh"))


class TestGetJobInfoFromJoblogfile(TestCase):
    """
    Test the `get_job_info_from_joblogfile` method from the `poll_jobs` script
    """

    # -------------------------------------------------------------------------
    def test_not_existing_joblogfile(self):
        """
        Test not existing joblogfile

        The function should not hide this issue. If the file passed in does not
        exist, this needs to be handles by the caller. It might mean different
        things in different caller circumstances.
        """
        logger.info("Test not existing joblogfile")

        # job_id, sub_dir, log_date = get_job_info_from_joblogfile(
        #     "/some/not/existing/joblogfile.log"
        # )
        self.assertRaises(
            FileNotFoundError,
            get_job_info_from_joblogfile,
            "/some/not/existing/joblogfile.log"
        )

    # -------------------------------------------------------------------------
    def test_read_existing_info_id_first(self):
        """
        Test output for info existing in file (job number then sub dir)
        """
        logger.info("Test joblogfile with expected content -- number first")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        with tempfile.TemporaryDirectory() as tempdir:
            given_job_id = 1234567
            content = """
job_number:                 {}
sge_o_workdir:              {}
submission_time:            Fri Jul 27 08:28:38 2018
            """.format(given_job_id, tempdir)
            extracted_job_id, sub_dir, log_date = decorated(content)
            self.assertEqual(extracted_job_id, given_job_id)
            self.assertEqual(sub_dir, tempdir)
            self.assertEqual(log_date, datetime(
                year=2018, month=7, day=27, hour=8, minute=28, second=38))

    # -------------------------------------------------------------------------
    def test_read_existing_info_dir_first(self):
        """
        Test output for info existing in file (sub dir then job id)
        """
        logger.info("Test joblogfile with expected content -- directory first")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        # tempdir =
        with tempfile.TemporaryDirectory() as tempdir:
            given_job_id = 1234567
            content = """
sge_o_workdir:              {}
job_number:                 {}
submission_time:            Fri Jul 27 08:28:38 2018
            """.format(tempdir, given_job_id)
            extracted_job_id, sub_dir, log_date = decorated(content)
            self.assertEqual(extracted_job_id, given_job_id)
            self.assertEqual(sub_dir, tempdir)
            self.assertEqual(log_date, datetime(
                year=2018, month=7, day=27, hour=8, minute=28, second=38))

    # -------------------------------------------------------------------------
    def test_read_empty_joblogfile(self):
        """Test output for info missing from file"""
        logger.info("Test empty joblogfile")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        content = ""
        job_id, sub_dir, log_date = decorated(content)
        self.assertIsNone(job_id)
        self.assertIsNone(sub_dir)
        self.assertIsNone(log_date)

    # -------------------------------------------------------------------------
    def test_warning_log_when_empty_joblogfile(self):
        """Test logging of warning when file is empty"""
        logger.info("Test warning log when empty joblogfile")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        content = ""
        with self.assertLogs(logger="utils.caefileio.joblogfile",
                             level=logging.WARNING) as cm:
            job_id, sub_dir, log_date = decorated(content)
        logger.info("Logs of required level: {}".format(cm.output))

    # -------------------------------------------------------------------------
    def test_warning_log_when_useless_content_joblogfile(self):
        """Test logging of warning when file contains useless text"""
        logger.info("Test warning log when joblogfile contains useless text")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        content = """This is just some text.
It is completely useless to derive information from.
This is not what a joblogfile should look like.
If this happens... something when wrong.
"""
        with self.assertLogs(logger="utils.caefileio.joblogfile",
                             level=logging.WARNING) as cm:
            job_id, sub_dir, log_date = decorated(content)
        logger.info("Logs of required level: {}".format(cm.output))

    # -------------------------------------------------------------------------
    def test_non_int_job_id(self):
        """
        Test job id in log file being not an integer

        Once the not-integer job id is discovered, the processing should end
        and the sub_dir should not be found e.g. stay empty.
        """
        logger.info("Test non-integer value for job_number")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        with tempfile.TemporaryDirectory() as tempdir:
            content = """
job_number:                 a1040629
sge_o_workdir:              {}
submission_time:            Fri Jul 27 08:28:38 2018
            """.format(tempdir)
            job_id, sub_dir, log_date = decorated(content)
            self.assertIsNone(job_id)
            self.assertEqual(sub_dir, tempdir)
            self.assertEqual(log_date, datetime(
                year=2018, month=7, day=27, hour=8, minute=28, second=38))

    # -------------------------------------------------------------------------
    def test_job_id_value_missing_in_content(self):
        """
        Test job id values missing from content.

        Once the missing job id is discovered, the processing should end and
        the sub_dir should not be found e.g. stay empty.
        """
        logger.info("Test job_number value missing")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        with tempfile.TemporaryDirectory() as tempdir:
            content = """
job_number:
sge_o_workdir:              {}
submission_time:            Fri Jul 27 08:28:38 2018
            """.format(tempdir)
            job_id, sub_dir, log_date = decorated(content)
            self.assertIsNone(job_id)
            self.assertEqual(sub_dir, tempdir)
            self.assertEqual(log_date, datetime(
                year=2018, month=7, day=27, hour=8, minute=28, second=38))

    # -------------------------------------------------------------------------
    def test_sub_dir_value_missing_in_content(self):
        """
        Test sub dir value missing from content
        """
        logger.info("Test sge_o_workdir value missing")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        given_job_id = 1234567
        content = """
job_number:                 {}
sge_o_workdir:
submission_time:            Fri Jul 27 08:28:38 2018
        """.format(given_job_id)
        extracted_job_id, sub_dir, log_date = decorated(content)
        self.assertEqual(extracted_job_id, given_job_id)
        self.assertIsNone(sub_dir)
        self.assertEqual(log_date, datetime(
            year=2018, month=7, day=27, hour=8, minute=28, second=38))

    # -------------------------------------------------------------------------
    def test_time_value_missing_in_content(self):
        """
        Test job id values missing from content.

        Once the missing job id is discovered, the processing should end and
        the sub_dir should not be found e.g. stay empty.
        """
        logger.info("Test submission_time value missing")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        with tempfile.TemporaryDirectory() as tempdir:
            given_job_id = 1234567
            content = """
job_number:                 {}
sge_o_workdir:              {}
submission_time:
            """.format(given_job_id, tempdir)
            extracted_job_id, sub_dir, log_date = decorated(content)
            self.assertEqual(extracted_job_id, given_job_id)
            self.assertEqual(sub_dir, tempdir)
            self.assertIsNone(log_date)

    # -------------------------------------------------------------------------
    def test_sub_dir_in_content_not_exsits(self):
        logger.info("Test sub dir does not exist")

        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_joblogfile)
        given_job_id = 1234567
        content = """
job_number:                 {}
sge_o_workdir:              /this/sub_dir/does/not/exsit
submission_time:            Fri Jul 27 08:28:38 2018
        """.format(given_job_id)
        extracted_job_id, sub_dir, log_date = decorated(content)
        self.assertEqual(extracted_job_id, given_job_id)
        self.assertEqual(sub_dir, "/this/sub_dir/does/not/exsit")
        self.assertEqual(log_date, datetime(
            year=2018, month=7, day=27, hour=8, minute=28, second=38))
