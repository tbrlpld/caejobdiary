# coding=utf-8
"""
Module to unittest the functions of the `joblogfile` module
"""

from datetime import datetime
import logging
import os
import tempfile

from django.test import TestCase

from utils.logger_copy import copy_logger_settings
from utils.tests.helper import add_content_to_temp_inputfilepath

from utils.caefileio.readme import get_job_info_from_readme
from utils.caefileio.readme import get_readme_filename_from_job_dir
from utils.caefileio.readme import get_base_runs_from_line


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logger = logging.getLogger("testing_control")
copy_logger_settings("testing_subject", "utils.caefileio.readme")


# -----------------------------------------------------------------------------
#  Check Environment
# -----------------------------------------------------------------------------

# On the CI (gitlab-runner) the defined jobs are run as root.
# root can always read all files, even if permissions are removed.
# Tests for missing permissions are needed though.
# Therefore, certain tests can not be asserted correctly in the CI environment.
# To exclude tests from assertion, I need to know if I am on the CI.

settings_module = os.environ['DJANGO_SETTINGS_MODULE']
running_on_ci = settings_module.endswith(".ci")
logger.info("Tests running on CI: {}".format(running_on_ci))


# -----------------------------------------------------------------------------
# Example File Directory
# -----------------------------------------------------------------------------

# Example files are stored below the top level
TOP_LEVEL_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


# -----------------------------------------------------------------------------
#  Tests
# -----------------------------------------------------------------------------

class TestGetReadmeFilenameFromJobDir(TestCase):
    """
    Test the `get_readme_filename_from_job_dir` helper method of the `poll_jobs`
    script

    Job READMEs usually have names like:
    README.0696_OEM_VHIC_SLD_FRB_56_TH_p1_ident_variant_.key.README
    """

    # -------------------------------------------------------------------------
    def test_non_existing_job_dir(self):
        """
        If the job dir does not exist a FileNotFoundError exception is thrown

        Throwing a special exception (like JobStatusRaceConditionError,
        as it did before) does not make sense. The only purpose of the function
        under testing is to check a directory for a filename.

        The larger context in which the function is used is not known to the
        function. How to handle cases where this function throws an exception
        needs to be done by the caller! Only the caller knows why it is
        requesting the info and what it wants with it.
        """
        self.assertRaises(
            FileNotFoundError,
            get_readme_filename_from_job_dir,
            "/not/existing/directory"
        )

    # -------------------------------------------------------------------------
    def test_job_dir_is_file_not_dir(self):
        """
        If the job dir is a file a NotADirectoryError exception is thrown

        This is a weird case. If this occurs that means something went wrong
        in the code determining the job_dir. This should definitely be met
        with a particular exception and corresponding log message.

        How can you test for log messages?

        ! This is the same mistake again! The function does not know what
        happened before or what the purpose of its call is. The error should be
        raised, but how it is handled needs to be decided in the caller!
        I will there for not require a log message.
        """
        with tempfile.TemporaryFile() as not_a_job_dir_file:
            self.assertRaises(
                NotADirectoryError,
                get_readme_filename_from_job_dir,
                not_a_job_dir_file.name
            )

    # -------------------------------------------------------------------------
    def test_job_dir_no_read_rights(self):
        """
        If the job dir is a file a PermissionError exception is thrown

        Missing read rights can not be tested on CI runner, because the tests
        on the CI are run as root and root can always read everything.
        """
        if running_on_ci:
            return None
        with tempfile.TemporaryDirectory() as job_dir:
            os.chmod(job_dir, 0o222)
            self.assertRaises(
                PermissionError,
                get_readme_filename_from_job_dir,
                job_dir
            )
            os.chmod(job_dir, 0o777)

    # -------------------------------------------------------------------------
    def test_job_dir_wo_readme(self):
        with tempfile.TemporaryDirectory() as tempdir:
            some_other_file_1 = os.path.join(tempdir, "main.key")
            some_other_file_2 = os.path.join(tempdir, "something_longer.inc")
            open(some_other_file_1, "w").close()
            open(some_other_file_2, "w").close()
            output = get_readme_filename_from_job_dir(tempdir)
            self.assertIsNone(output)

    # -------------------------------------------------------------------------
    def test_job_dir_readme(self):
        with tempfile.TemporaryDirectory() as tempdir:
            readme_filename = ("README.0123_OEM_VHCL_LOD_CAS_TH_.key.README")
            readme_filepath = os.path.join(tempdir, readme_filename)
            open(readme_filepath, "w").close()
            output = get_readme_filename_from_job_dir(tempdir)
            self.assertEqual(output, readme_filename)

    # -------------------------------------------------------------------------
    def test_job_dir_readme_similar_file(self):
        with tempfile.TemporaryDirectory() as tempdir:
            # The dots after/before "README" are missing
            readme_filename_similar = (
                "README0123_OEM_VHCL_LOD_CAS_TH_.keyREADME")
            filepath = os.path.join(tempdir, readme_filename_similar)
            open(filepath, "w").close()
            output = get_readme_filename_from_job_dir(tempdir)
            self.assertIsNone(output)


class TestGetJobInfoFromReadme(TestCase):
    """
    Test the `get_job_info_from_readme` function of the `poll_jobs` script
    """

    # -------------------------------------------------------------------------
    def test_not_exiting_readme(self):
        readme_filepath = "/this/does/not/README.exist.README"
        self.assertFalse(os.path.isfile(readme_filepath))
        self.assertRaises(
            FileNotFoundError,
            get_job_info_from_readme,
            readme_filepath
        )

    # -------------------------------------------------------------------------
    def test_no_read_rights_to_readme(self):
        if running_on_ci:
            return None
        with tempfile.TemporaryDirectory() as job_dir:
            readme_filepath = os.path.join(job_dir, "README.some.README")
            open(readme_filepath, "w").close()
            os.chmod(readme_filepath, 0o222)
            self.assertRaises(
                PermissionError,
                get_job_info_from_readme,
                readme_filepath
            )
            os.chmod(readme_filepath, 0o777)

    # -------------------------------------------------------------------------
    def test_empty_readme(self):
        with tempfile.TemporaryDirectory() as job_dir:
            readme_filepath = os.path.join(job_dir, "README.some.README")
            open(readme_filepath, "w").close()
            readme_data = get_job_info_from_readme(readme_filepath)
        self.assertIsNone(readme_data)

    # -------------------------------------------------------------------------
    def test_existing_readme_with_real_content(self):
        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_readme)
        main_name = "0696_AD_W222_SLD_FRB_56_TH_p1_SIB_relax45_noEnv_.key"
        base_run = 7654321
        info_block = """Dissipate more energy
------
New load limiter level
Load limiter level: x = 5.2 kN
Changed tension flag in spring material.
The spring did not develop any force when streched!"""
        username = "doej"
        email = "john.doe@example.com"
        solver = "dyn"

        content = f"""
README for {main_name}
base-run (job-id): {base_run}
information      :
{info_block}

********Header********
SOLVERVER: mpp.s.R9.1.0.113698.113698_dmp_sp
FEMZIPCOMPRESS: y
FEMZIP: /share/sge/femzip/scripts/femzip_sge_W04_dyn_crash_mmkgms
SGESCHED: i
CORES: 16
SGERES: none=1
SOLVER: dyn
SOLPAR: MEMORY=512M MEMORY2=256M
SGECMD: /some/directory/path/with/multiple-levels/{main_name}/sge_post_script___master-file.sh >> sge_post_script___master-file.log 2>&1
UNIT: mm-kg-ms
******Environment******
Sub-User:   {username}
EMail:      {email}
Sub-Date:   2018-06-07__17:21:21
Sub-Host:   x01xx001
Queue:      dyn
Qsub:       /usr/ge-6.1u6/bin/lx24-amd64/qsub  -S /bin/ksh -M {email} -o /tmp -e /tmp -m b -p -101 -N i_{main_name} -V -pe dmp_16 16 -q dyn -l none=1,dyn=1,sensor_dyn=1 /clients/bin/_sge/_dyn-dmp
OS:     CentOS release 6.6 (Final)
Cores:      16
CPUSUM:     1
R_COUNT:    0
P_COUNT:    0
PRIO:       -101
RES:        none=1,dyn=1,sensor_dyn=1
Solver:     {solver}
SolverVer:  mpp.s.R9.1.0.113698.113698_dmp_sp
SolverPath: /share/sge/dyn/mpp.s.R9.1.0.113698.113698_dmp_sp/x86_64/bin/dyna.bin
DMP/SMP:    dmp
Sched:      i
Scheddef:   i
SubDir:     /some/directory/path/with/multiple-levels/{main_name}
FILE:       {main_name}
Femzip:     y
FemzipConf: /share/sge/femzip/scripts/femzip_sge_W04_dyn_crash_mmkgms
SOLPAR:     MEMORY=512M MEMORY2=256M
SGECMD:     /some/directory/path/with/multiple-levels/{main_name}/sge_post_script___master-file.sh >> sge_post_script___master-file.log 2>&1
SGERES:     none=1
JOBID:      1234567
Exec-Host:  x99xx123.example.com 16 dyn@x99xx123.example.com <NULL>
        """
        readme_info = decorated(content)
        self.assertEqual(type(readme_info), type(dict()))
        self.assertEqual(readme_info["main_name"], main_name)
        self.assertEqual(readme_info["base_runs"], [base_run])
        self.assertEqual(readme_info["info_block"], info_block)
        self.assertEqual(readme_info["username"], username)
        self.assertEqual(readme_info["email"], email)
        self.assertEqual(readme_info["sub_date"], datetime(
            year=2018, month=6, day=7, hour=17, minute=21, second=21))
        self.assertEqual(readme_info["solver"], "dyn")

    # -------------------------------------------------------------------------
    def test_mini_readme_with_two_base_runs(self):
        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_readme)
        base_run_1 = 1234567
        base_run_2 = 7654321
        content = f"""
base-run (job-id): {base_run_1} {base_run_2}
        """
        readme_info = decorated(content)
        self.assertEqual(readme_info["base_runs"], [base_run_1, base_run_2])

    # -------------------------------------------------------------------------
    def test_mini_readme_with_two_comma_sep_base_runs(self):
        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_readme)
        base_run_1 = 1234567
        base_run_2 = 7654321
        content = f"""
base-run (job-id): {base_run_1}, {base_run_2}
        """
        readme_info = decorated(content)
        self.assertEqual(readme_info["base_runs"], [base_run_1, base_run_2])

    # -------------------------------------------------------------------------
    def test_mini_readme_with_empty_base_runs(self):
        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_readme)
        content = """
base-run (job-id):
        """
        readme_info = decorated(content)
        self.assertEqual(readme_info["base_runs"], [])

    # -------------------------------------------------------------------------
    def test_mini_readme_with_non_int_base_runs(self):
        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_readme)
        content = """
base-run (job-id): this is some accident text
        """
        readme_info = decorated(content)
        self.assertEqual(readme_info["base_runs"], [])

    # -------------------------------------------------------------------------
    def test_mini_readme_with_empty_info(self):
        decorated = add_content_to_temp_inputfilepath(
            get_job_info_from_readme)
        content = """
information      :


********Header********
"""
        readme_info = decorated(content)
        self.assertEqual(readme_info["info_block"], "")

    # -------------------------------------------------------------------------
    def test_mini_readme_with_non_utf8(self):
        """
        What am I even testing here? That some of the info text with the weird
        non-Ascii symbol is read out. I don't really care what it does with the
        non-Ascii symbol. If there is anything that replaces it that is fine.
        Maybe I should make that a proper function.

        TODO: Create some handling for non-ascii files.
        """
        example_readme = os.path.join(
            TOP_LEVEL_DIR,
            "data",
            "example_job_info_sources",
            "README.main_deck_name_JOB_funky_encoded_readme_20180814.key." \
            + "README"
        )
        readme_info = get_job_info_from_readme(example_readme)
        self.assertIn("Description of file with some weird symbol",
                      readme_info["info_block"])


class TestGetBaseRunsFromLine(TestCase):
    """
    Test the `get_base_runs_from_line` helper function of `poll_jobs` script
    """

    # -------------------------------------------------------------------------
    def test_empty_value(self):
        output = get_base_runs_from_line("Base-Runs-Key: ")
        self.assertEqual(output, [])

    # -------------------------------------------------------------------------
    def test_missing_colon_after_key(self):
        output = get_base_runs_from_line("Base-Runs-Key ")
        self.assertEqual(output, [])

    # -------------------------------------------------------------------------
    def test_existing_base_run(self):
        output = get_base_runs_from_line("Base-Runs-Key: 1234 ")
        self.assertEqual(output, [1234])

    # -------------------------------------------------------------------------
    def test_multiple_base_runs(self):
        output = get_base_runs_from_line("Base-Runs-Key: 1234 1234567 ")
        self.assertEqual(output, [1234, 1234567])

    # -------------------------------------------------------------------------
    def test_multiple_comma_sep_base_runs(self):
        output = get_base_runs_from_line("Base-Runs-Key: 1234, 1234567 ")
        self.assertEqual(output, [1234, 1234567])

    # -------------------------------------------------------------------------
    def test_value_with_added_letters(self):
        output = get_base_runs_from_line("Base-Runs-Key: 1234_this_is_extra ")
        self.assertEqual(output, [1234])

    # -------------------------------------------------------------------------
    def test_multiple_colon_sep_base_runs(self):
        output = get_base_runs_from_line("Base-Runs-Key: 1234: 1234567 ")
        self.assertEqual(output, [1234, 1234567])
