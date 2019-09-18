"""
Module to unittest the functions of the `clusterscript` module
"""

import logging
import os
import tempfile

from django.test import TestCase

from utils.logger_copy import copy_logger_settings
from test_utils.helper import add_content_to_temp_inputfilepath

from utils.caefileio.clusterscript import get_cluster_script_from_list
from utils.caefileio.clusterscript import get_cluster_scratch_dir_from_script

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logger = logging.getLogger("testing_control")
copy_logger_settings("testing_subject", "utils.caefileio.clusterscript")


# -----------------------------------------------------------------------------
#  Test Function `get_cluster_script_from_list`
# -----------------------------------------------------------------------------

class TestGetClusterScriptFromList(TestCase):

    # -------------------------------------------------------------------------
    def test_empty_list(self):
        file_list = []
        self.assertIsNone(get_cluster_script_from_list(
            job_id=7654321,
            file_list=file_list
        ))

    # -------------------------------------------------------------------------
    def test_only_correct_cluster_script_in_list_dyn(self):
        cluster_script_filename = "1234567.dyn-dmp.x99xx123.16.sh"
        file_list = [cluster_script_filename]
        self.assertEqual(
            get_cluster_script_from_list(
                job_id=1234567,
                file_list=file_list),
            cluster_script_filename
        )

    # -------------------------------------------------------------------------
    def test_only_correct_cluster_script_in_list_pam_1(self):
        cluster_script_filename = "1234567.pam-dmp.x99xx321.8.sh"
        file_list = [cluster_script_filename]
        self.assertEqual(
            get_cluster_script_from_list(
                job_id=1234567,
                file_list=file_list),
            cluster_script_filename
        )

    # -------------------------------------------------------------------------
    def test_only_correct_cluster_script_in_list_pam_2(self):
        cluster_script_filename = "1234567.pam-dmp.x12xx123.16.sh"
        file_list = [cluster_script_filename]
        self.assertEqual(
            get_cluster_script_from_list(
                job_id=1234567,
                file_list=file_list),
            cluster_script_filename
        )

    # -------------------------------------------------------------------------
    def test_another_correct_cluster_script_in_list(self):
        cluster_script_filename = "1234567.dyn-dmp.x99xx012.8.sh"
        file_list = [cluster_script_filename]
        self.assertEqual(
            get_cluster_script_from_list(
                job_id=1234567,
                file_list=file_list),
            cluster_script_filename
        )

    # -------------------------------------------------------------------------
    def test_correct_and_wrong_cluster_script_in_list(self):
        wrong_cluster_script_filename = "999999.dyn-dmp.x01xx012.16.sh"
        correct_cluster_script_filename = "1234567.dyn-dmp.x99xx123.16.sh"
        file_list = [wrong_cluster_script_filename,
                     correct_cluster_script_filename]
        self.assertEqual(
            get_cluster_script_from_list(
                job_id=1234567,
                file_list=file_list),
            correct_cluster_script_filename
        )

    # -------------------------------------------------------------------------
    def test_wrong_cluster_script_in_list(self):
        cluster_script_filename = "999999.dyn-dmp.l01cl012.16.sh"
        file_list = [cluster_script_filename]
        self.assertIsNone(get_cluster_script_from_list(
            job_id=1234567,
            file_list=file_list
        ))


# -----------------------------------------------------------------------------
#  Test Helper Function `get_cluster_scratch_dir_from_script`
# -----------------------------------------------------------------------------

class TestGetClusterScratchDirFromScript(TestCase):

    # -------------------------------------------------------------------------
    def test_non_existing_script(self):
        output = get_cluster_scratch_dir_from_script("/not/existing/script.sh")
        self.assertIsNone(output)

    # -------------------------------------------------------------------------
    def test_empty_script(self):
        decorated = add_content_to_temp_inputfilepath(
            get_cluster_scratch_dir_from_script)
        content = ""
        self.assertIsNone(decorated(content))

    # -------------------------------------------------------------------------
    def test_missing_directory(self):
        decorated = add_content_to_temp_inputfilepath(
            get_cluster_scratch_dir_from_script)
        content = "cd "
        self.assertIsNone(decorated(content))

    # -------------------------------------------------------------------------
    def test_non_existing_directory(self):
        """
        The cluster scratch directory that is contained in the file should be
        returned even if it is not existing. The handling/check if the
        directory exists should be handled on the caller level.

        The purpose of this function is merely to read the available
        information from the clusterscript.
        """
        decorated = add_content_to_temp_inputfilepath(
            get_cluster_scratch_dir_from_script)
        scratch_dir = "/this/is/not/existing/1234"
        content = "cd {}*".format(scratch_dir)
        self.assertEqual(decorated(content), scratch_dir)

    # -------------------------------------------------------------------------
    def test_existing_directory(self):
        decorated = add_content_to_temp_inputfilepath(
            get_cluster_scratch_dir_from_script)
        with tempfile.TemporaryDirectory() as tempdir:
            scratch_dir = os.path.join(tempdir, "1234")
            os.makedirs(scratch_dir)
            content = "cd {}*".format(scratch_dir)
            self.assertEqual(decorated(content), scratch_dir)

    # -------------------------------------------------------------------------
    def test_existing_directory_with_following_space(self):
        logger.info("Testing existing directory  with following space")
        decorated = add_content_to_temp_inputfilepath(
            get_cluster_scratch_dir_from_script)
        with tempfile.TemporaryDirectory() as tempdir:
            scratch_dir = os.path.join(tempdir, "1234")
            os.makedirs(scratch_dir)
            content = "cd {}* ".format(scratch_dir)
            self.assertEqual(decorated(content), scratch_dir)

    # -------------------------------------------------------------------------
    def test_existing_directory_with_following_tab(self):
        logger.info("Testing existing directory  with following tab")
        decorated = add_content_to_temp_inputfilepath(
            get_cluster_scratch_dir_from_script)
        with tempfile.TemporaryDirectory() as tempdir:
            scratch_dir = os.path.join(tempdir, "1234")
            os.makedirs(scratch_dir)
            content = "cd {}*\t".format(scratch_dir)
            self.assertEqual(decorated(content), scratch_dir)

    # -------------------------------------------------------------------------
    def test_existing_directory_with_following_newline(self):
        logger.info("Testing existing directory  with following newline")
        decorated = add_content_to_temp_inputfilepath(
            get_cluster_scratch_dir_from_script)
        with tempfile.TemporaryDirectory() as tempdir:
            scratch_dir = os.path.join(tempdir, "1234")
            os.makedirs(scratch_dir)
            content = "cd {}*\n".format(scratch_dir)
            self.assertEqual(decorated(content), scratch_dir)

    # -------------------------------------------------------------------------
    def test_similar_existing_directories(self):
        decorated = add_content_to_temp_inputfilepath(
            get_cluster_scratch_dir_from_script)
        with tempfile.TemporaryDirectory() as tempdir:
            scratch_dir = os.path.join(tempdir, "1234")
            os.makedirs(scratch_dir)
            similar_scratch_dir = os.path.join(tempdir, "12345")
            os.makedirs(similar_scratch_dir)
            content = "cd {}*".format(scratch_dir)
            self.assertEqual(decorated(content), scratch_dir)
