import logging

from django.test import TestCase

from diary.models import Job
from utils.logger_copy import copy_logger_settings

from utils.project import get_project_from_path, is_project_identifier

logger = logging.getLogger("testing_control").getChild(__name__)
copy_logger_settings("testing_subject", "diary.utils")


class TestGetProjectFromPath(TestCase):
    """
    Tests for get_project_from_path function of the utils module
    """

    def test_prj_like_path(self):
        path = "/W04_prj/3001234/04/model/calc/something"
        project = get_project_from_path(path=path)
        self.assertEqual(project, "3001234")

    def test_pcae_like_path(self):
        path = "/mnt/w04_pcae/w04_pcae/w04_pcae_09/w04_pcae_09/3001234/04/" \
               "model/calc/something"
        project = get_project_from_path(path=path)
        self.assertEqual(project, "3001234")

    def test_versioned_project_path(self):
        path = "/W04_prj/3001234v03/04/model/calc/something"
        project = get_project_from_path(path=path)
        self.assertEqual(project, "3001234v03")

    def test_q_project(self):
        path = "/mnt/w01_pcae/w01_pcae/w01_pcae_08/q000351/04/model/calc/" \
               "something"
        project = get_project_from_path(path=path)
        self.assertEqual(project, "q000351")

    def test_r_project(self):
        path = "/mnt/w01_pcae/w01_pcae/w01_pcae_07/w01_pcae_07/r000301/04/" \
               "model/calc/something"
        project = get_project_from_path(path=path)
        self.assertEqual(project, "r000301")


class TestIsProjectIdentifier(TestCase):
    """
    Tests for is_project_identifier function of the utils module
    """

    # Assert for True
    def test_basic_proj_ident(self):
        self.assertTrue(is_project_identifier("3001234"))

    def test_versioned_proj_ident(self):
        self.assertTrue(is_project_identifier("3001234v03"))

    def test_q_proj_ident(self):
        self.assertTrue(is_project_identifier("q000351"))

    def test_versioned_q_proj_ident(self):
        self.assertTrue(is_project_identifier("q000351v01"))

    def test_r_proj_ident(self):
        self.assertTrue(is_project_identifier("r000301"))

    def test_versioned_r_proj_ident(self):
        self.assertTrue(is_project_identifier("r000301v02"))

    # Assert for False
    def test_empty_string(self):
        self.assertFalse(is_project_identifier(""))

    def test_random_string(self):
        self.assertFalse(is_project_identifier("asasdasdaonrogmnspmfsohg9jn4"))

    def test_integer_string(self):
        self.assertFalse(is_project_identifier("123456"))

    def test_integer(self):
        self.assertFalse(is_project_identifier(123456))
