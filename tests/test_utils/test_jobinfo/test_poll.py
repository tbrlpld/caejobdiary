"""
Module to unittest the functions of the `poll` module
"""
import logging
import logging.config
import os
import shutil
import tempfile
from datetime import datetime, timedelta

import before_after
from django.contrib.auth import get_user_model
from django.test import TestCase
import pytz

from diary.models import Job
from utils.caefileio.readme import get_job_info_from_readme
from utils.logger_copy import copy_logger_settings
from tests.test_utils.helper import add_content_to_temp_inputfilepath
from tests.test_utils.helper import make_readme

# Major Functions
from utils.jobinfo.poll import start_job_creation_process_from_joblogfile
# Helper Functions
from utils.jobinfo.poll import is_recent
from utils.jobinfo.poll import required_keys_avaiable


# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

logger = logging.getLogger("testing_control").getChild(__name__)
copy_logger_settings("testing_subject", "utils.jobinfo.poll")


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
# Make `User` model available
# -----------------------------------------------------------------------------

User = get_user_model()

# -----------------------------------------------------------------------------
#  Test Start Job Creation Process From Joblogfile
# -----------------------------------------------------------------------------


class TestStartJobCreationProcessFromJoblogfile(TestCase):
    """
    Test the `start_job_creation_process_from_joblogfile` method of `poll`
    """

    # -------------------------------------------------------------------------
    def setUp(self):
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

        self.free_id = 789

    # -------------------------------------------------------------------------
    def test_not_existing_joblogfile(self):
        logger.info("-"*80)
        logger.info("Test not existing joblogfile")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()

        joblogfile_path = "/this/should/not/exist/file.log"
        self.assertFalse(os.path.exists(joblogfile_path))
        job_created = start_job_creation_process_from_joblogfile(
            joblogfile_path)

        self.assertFalse(job_created)
        # Number of jobs should not have changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)

    # -------------------------------------------------------------------------
    def test_processing_of_joblogfile_with_empty_infos(self):
        logger.info("-"*80)
        logger.info("Test processing of joblogfile with empty infos")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()

        # Defining joblogfile content
        joblogfile_content = """
job_number:
sge_o_workdir:
"""
        # Start processing from joblogfile content
        start_processing_from_content = add_content_to_temp_inputfilepath(
            start_job_creation_process_from_joblogfile)
        job_created = start_processing_from_content(joblogfile_content)

        self.assertFalse(job_created)
        # Number of jobs should not have changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)

    # -------------------------------------------------------------------------
    def test_pending_job_dir_is_file_not_dir(self):
        """
        When job_dir is file error should be thrown and logged

        When the job_dir is actually a file then something went wrong
        determining what the job_dir is. In that case an error should be thrown
        and be logged.
        """
        logger.info("-"*80)
        logger.info("Test processing when the pending 'job_dir' is a file not directory")
        logger.info("-"*80)

        with tempfile.TemporaryDirectory() as sub_dir:
            job_id = self.free_id
            job_dir_file = os.path.join(sub_dir, str(job_id) + ".pending")
            open(job_dir_file, 'a').close()
            logger.info("sub_dir content: {}".format(os.listdir(sub_dir)))

            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)
            logger.info("joblogfile_content: {}".format(joblogfile_content))
            with tempfile.NamedTemporaryFile(mode="w") as joblogfile:
                joblogfile.write(joblogfile_content)
                joblogfile.seek(0)

                with self.assertLogs(logger="utils.jobinfo.poll",
                                     level=logging.ERROR) as cm:
                    start_job_creation_process_from_joblogfile(joblogfile.name)
                    logger.info("Logs of required level: {}".format(cm.output))

    # -------------------------------------------------------------------------
    def test_processing_from_joblogfile_pending_job(self):
        logger.info("-"*80)
        logger.info("Test processing of pending job")
        logger.info("-"*80)

        job_id = self.free_id
        with tempfile.TemporaryDirectory() as tempdir:
            sub_dir = tempdir
            # Make pending job folder
            job_dir = os.path.join(tempdir, str(job_id) + ".pending")
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=self.user_A.username,
                email=self.user_A.email,
                base_runs_str=str(self.job_user_A_project_A.job_id),
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)
            # Start processing from joblogfile content
            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)
            start_processing_from_content(joblogfile_content)

        # Assertions
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 3)  # The setup ones and the new one
        processed_job = Job.objects.get(job_id=job_id)
        self.assertEqual(processed_job.job_id, job_id)
        self.assertEqual(processed_job.sub_dir, sub_dir)
        self.assertEqual(processed_job.job_status, Job.JOB_STATUS_PENDING)
        self.assertEqual(processed_job.job_dir, job_dir)
        self.assertEqual(processed_job.readme_filename, readme_filename)
        self.assertEqual(processed_job.main_name, main_name)
        self.assertEqual(processed_job.solver, "dyn")
        tz = pytz.timezone("Europe/Berlin")
        aware_datetime = tz.localize(datetime(2018, 6, 7, 17, 21, 21))
        self.assertEqual(processed_job.sub_date, aware_datetime)
        self.assertEqual(processed_job.info, "Some info text")
        self.assertIn(self.job_user_A_project_A, processed_job.base_runs.all())
        self.assertEqual(processed_job.user, self.user_A)
        self.assertEqual(processed_job.user.username, self.user_A.username)
        self.assertEqual(processed_job.user.email, self.user_A.email)

    # -------------------------------------------------------------------------
    def test_processing_from_joblogfile_running_job(self):
        logger.info("-"*80)
        logger.info("Test processing of running job")
        logger.info("-"*80)

        job_id = self.free_id

        cluster_temp_dir = tempfile.TemporaryDirectory()
        cluster_scratch_dir = os.path.join(cluster_temp_dir.name, str(job_id))
        os.makedirs(cluster_scratch_dir)
        logger.debug("Cluster scratch dir: {}".format(cluster_scratch_dir))

        with tempfile.TemporaryDirectory() as tempdir:
            sub_dir = tempdir

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            # Create cluster script
            cluster_script_content = "cd {}*".format(cluster_scratch_dir)
            logger.debug("Cluster script content: {}".format(cluster_script_content))
            cluster_script_filename = "{}.dyn-dmp.x01xx012.16.sh".format(job_id)
            cluster_script_filepath = os.path.join(sub_dir, cluster_script_filename)
            with open(cluster_script_filepath, mode="w") as f:
                f.write(cluster_script_content)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=cluster_scratch_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=self.user_A.username,
                email=self.user_A.email,
                base_runs_str=str(self.job_user_A_project_A.job_id),
                main_name=main_name
            )

            # Start processing from joblogfile content
            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)
            start_processing_from_content(joblogfile_content)

        # Cleaning up the cluster scratch dir / tempdir
        cluster_temp_dir.cleanup()

        # Assertions
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 3)
        processed_job = Job.objects.get(job_id=job_id)
        self.assertEqual(processed_job.job_id, job_id)
        self.assertEqual(processed_job.sub_dir, sub_dir)
        self.assertEqual(processed_job.job_status, Job.JOB_STATUS_RUNNING)
        self.assertEqual(processed_job.job_dir, cluster_scratch_dir)
        self.assertEqual(processed_job.readme_filename, readme_filename)
        self.assertEqual(processed_job.main_name, main_name)
        self.assertEqual(processed_job.solver, "dyn")
        tz = pytz.timezone("Europe/Berlin")
        aware_datetime = tz.localize(datetime(2018, 6, 7, 17, 21, 21))
        self.assertEqual(processed_job.sub_date, aware_datetime)
        self.assertEqual(processed_job.info, "Some info text")
        self.assertIn(self.job_user_A_project_A, processed_job.base_runs.all())
        self.assertEqual(processed_job.user, self.user_A)
        self.assertEqual(processed_job.user.username, self.user_A.username)
        self.assertEqual(processed_job.user.email, self.user_A.email)

    # -------------------------------------------------------------------------
    def test_processing_abort_due_to_duplication(self):
        logger.info("-"*80)
        logger.info("Test processing abort due to existing job in DB.")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()
        # Use job id of job already in the DB
        job_id = self.job_user_A_project_A.job_id

        with tempfile.TemporaryDirectory() as tempdir:
            sub_dir = tempdir

            # Defining jonlogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            # Make pending job folder
            job_dir = os.path.join(tempdir, str(job_id) + ".pending")
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=self.user_A.username,
                email=self.user_A.email,
                base_runs_str="",
                main_name=main_name
            )

            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)
            return_value = start_processing_from_content(joblogfile_content)

        self.assertFalse(return_value)
        # Number of jobs should not be changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)

    # -------------------------------------------------------------------------
    def test_no_read_access_to_finished_job(self):
        if running_on_ci:
            return None

        logger.info("-"*80)
        logger.info("Test processing with a not readable `job_dir`")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()
        job_id = self.free_id

        with tempfile.TemporaryDirectory() as sub_dir:
            # Defining jonlogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)
            # Make job folder
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)
            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=self.user_A.username,
                email=self.user_A.email,
                base_runs_str="",
                main_name=main_name
            )

            # Remove read rights on job_dir
            os.chmod(job_dir, 0o222)

            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)
            return_value = start_processing_from_content(joblogfile_content)

            # Adding rights back for deletion
            os.chmod(job_dir, 0o777)

        self.assertFalse(return_value)
        # Number of jobs should not be changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)

    # -------------------------------------------------------------------------
    def test_no_read_access_to_finished_job_README(self):
        if running_on_ci:
            return None

        logger.info("-"*80)
        logger.info("Test processing with a not readable README")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()
        job_id = self.free_id

        with tempfile.TemporaryDirectory() as sub_dir:

            # Defining jonlogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            # Make job folder
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username="doej",
                email="john.doe@example.com",
                base_runs_str="",
                main_name=main_name
            )

            # Remove read rights on job_dir
            os.chmod(readme_filepath, 0o222)

            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)
            return_value = start_processing_from_content(joblogfile_content)

            # Adding rights back for deletion
            os.chmod(readme_filepath, 0o777)

        self.assertFalse(return_value)
        # Number of jobs should not be changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)

    # -------------------------------------------------------------------------
    def test_not_all_required_keys_in_README(self):
        logger.info("-"*80)
        logger.info("Test processing with a README where username is missing")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()
        job_id = self.free_id

        with tempfile.TemporaryDirectory() as sub_dir:

            # Defining jonlogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            # Make job folder
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Create README
            logger.debug("Making readme file...")
            email=self.user_A.email
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_content="""
README for {main_name}
base-run (job-id):
information      :
Some info text

********Header********
SOLVERVER: mpp.s.R9.1.0.113698.113698_dmp_sp
******Environment******
EMail:      {email}
Sub-Date:   2018-06-07__17:21:21
Solver:     dyn
SubDir:     {sub_dir}
FILE:       {main_name}
JOBID:      {job_id}
""".format(
email=email,
sub_dir=sub_dir,
job_id=str(job_id),
main_name=main_name)
            logger.debug(readme_content)
            readme_filename = f"README.{main_name}.README"
            readme_filepath = os.path.join(job_dir, readme_filename)
            with open(readme_filepath, mode="w") as f:
                f.write(readme_content)

            # Making sure that the readme does miss some required keys
            self.assertFalse(
                required_keys_avaiable(
                    get_job_info_from_readme(readme_filepath)))

            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)

            with self.assertLogs(logger="utils.jobinfo.poll",
                                 level=logging.ERROR) as cm:
                job_created = start_processing_from_content(joblogfile_content)
                logger.info("Logs of required level: {}".format(cm.output))

        self.assertFalse(job_created)
        # Number of jobs should not be changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)

    # -------------------------------------------------------------------------
    def test_empty_README(self):
        logger.info("-"*80)
        logger.info("Test processing with an empty README")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()
        job_id = self.free_id

        with tempfile.TemporaryDirectory() as sub_dir:

            # Defining jonlogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            # Make job folder
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Create README
            logger.debug("Making readme file...")
            email=self.user_A.email
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_content=""
            readme_filename = f"README.{main_name}.README"
            readme_filepath = os.path.join(job_dir, readme_filename)
            with open(readme_filepath, mode="w") as f:
                f.write(readme_content)

            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)

            with self.assertLogs(logger="utils.jobinfo.poll",
                                 level=logging.ERROR) as cm:
                job_created = start_processing_from_content(joblogfile_content)
                logger.info("Logs of required level: {}".format(cm.output))

        self.assertFalse(job_created)
        # Number of jobs should not be changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)

    # -------------------------------------------------------------------------
    def test_no_README_in_job_dir(self):
        logger.info("-"*80)
        logger.info("Test processing without a README in the job_dir")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()
        job_id = self.free_id

        with tempfile.TemporaryDirectory() as sub_dir:

            # Defining jonlogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            # Make job folder
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)

            with self.assertLogs(logger="utils.jobinfo.poll",
                                 level=logging.WARNING) as cm:
                job_created = start_processing_from_content(joblogfile_content)
                logger.info("Logs of required level: {}".format(cm.output))

        self.assertFalse(job_created)
        # Number of jobs should not be changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)

    # -------------------------------------------------------------------------
    def test_job_file_not_folder(self):
        logger.info("-"*80)
        logger.info(
            "Test processing with the `job_dir` being a file not a directory")
        logger.info("-"*80)

        number_of_jobs_before_processing = Job.objects.count()
        job_id = self.free_id

        with tempfile.TemporaryDirectory() as sub_dir:

            # Defining jonlogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            # Make job file (not folder)
            job_dir = os.path.join(sub_dir, str(job_id))
            open(job_dir, "w").close()

            start_processing_from_content = add_content_to_temp_inputfilepath(
                start_job_creation_process_from_joblogfile)

            with self.assertLogs(logger="utils.jobinfo.poll",
                                 level=logging.ERROR) as cm:
                job_created = start_processing_from_content(joblogfile_content)
                logger.info("Logs of required level: {}".format(cm.output))

        self.assertFalse(job_created)
        # Number of jobs should not be changed
        self.assertEqual(Job.objects.count(), number_of_jobs_before_processing)


class TestRaceConditionInProcessing(TestCase):
    """
    Test the `start_job_creation_process_from_joblogfile` method of `poll`
    """

    # -------------------------------------------------------------------------
    def test_racecondition_running_job_finishes_before_getting_readme_filename(self):
        logger.info("-"*80)
        logger.info("Test processing with running job that finishes during processing")
        logger.info("Job finishes before README filename is determined in job_dir")
        logger.info("-"*80)

        def finish_running_job(*a, **kw):
            """
            Move content of cluster scratch dir to job_dir in sub_dir

            The cluster scratch dir is removed. This simulates the SGE process
            when a job finishes.
            """

            logger.info("Job finished ***********")

            # Make job_dir in sub_dir
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Copy files
            for file in os.listdir(cluster_scratch_dir):
                filepath = os.path.join(cluster_scratch_dir, file)
                shutil.copy(filepath, job_dir)

            # Remove cluster scratch dir
            shutil.rmtree(cluster_scratch_dir)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        cluster_temp_dir = tempfile.TemporaryDirectory()
        cluster_scratch_dir = os.path.join(cluster_temp_dir.name, str(job_id))
        os.makedirs(cluster_scratch_dir)
        logger.debug("Cluster scratch dir: {}".format(cluster_scratch_dir))

        with tempfile.TemporaryDirectory() as tempdir:
            sub_dir = tempdir

            # Create cluster script
            cluster_script_content = "cd {}*".format(cluster_scratch_dir)
            logger.debug("Cluster script content: {}".format(cluster_script_content))
            cluster_script_filename = "{}.dyn-dmp.l01cl012.16.sh".format(job_id)
            cluster_script_filepath = os.path.join(sub_dir, cluster_script_filename)
            with open(cluster_script_filepath, mode="w") as f:
                f.write(cluster_script_content)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=cluster_scratch_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_readme_filename_from_job_dir",
                    finish_running_job):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                start_processing_from_content(joblogfile_content)

        # Cleaning up the cluster scratch dir / tempdir
        cluster_temp_dir.cleanup()

        # Assertions
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 1)  # only the created one

        processed_job = Job.objects.get(job_id=job_id)
        self.assertEqual(processed_job.job_status, Job.JOB_STATUS_FINISHED)

    # -------------------------------------------------------------------------
    def test_racecondition_running_job_finishes_before_getting_readme_info(self):
        logger.info("-"*80)
        logger.info("Test processing with running job that finishes during processing")
        logger.info("Job finishes before info is retrieved from README")
        logger.info("-"*80)

        def finish_running_job(*a, **kw):
            """
            Move content of cluster scratch dir to job_dir in sub_dir

            The cluster scratch dir is removed. This simulates the SGE process
            when a job finishes.
            """

            logger.info("Job finished ***********")

            # Make job_dir in sub_dir
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Copy files
            for file in os.listdir(cluster_scratch_dir):
                filepath = os.path.join(cluster_scratch_dir, file)
                shutil.copy(filepath, job_dir)

            # Remove cluster scratch dir
            shutil.rmtree(cluster_scratch_dir)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        cluster_temp_dir = tempfile.TemporaryDirectory()
        cluster_scratch_dir = os.path.join(cluster_temp_dir.name, str(job_id))
        os.makedirs(cluster_scratch_dir)
        logger.debug("Cluster scratch dir: {}".format(cluster_scratch_dir))

        with tempfile.TemporaryDirectory() as tempdir:
            sub_dir = tempdir

            # Create cluster script
            cluster_script_content = "cd {}*".format(cluster_scratch_dir)
            logger.debug("Cluster script content: {}".format(cluster_script_content))
            cluster_script_filename = "{}.dyn-dmp.l01cl012.16.sh".format(job_id)
            cluster_script_filepath = os.path.join(sub_dir, cluster_script_filename)
            with open(cluster_script_filepath, mode="w") as f:
                f.write(cluster_script_content)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=cluster_scratch_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_job_info_from_readme",
                    finish_running_job):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                start_processing_from_content(joblogfile_content)

        # Cleaning up the cluster scratch dir / tempdir
        cluster_temp_dir.cleanup()

        # Assertions
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 1)  # only the created one

        processed_job = Job.objects.get(job_id=job_id)
        self.assertEqual(processed_job.job_status, Job.JOB_STATUS_FINISHED)

    # -------------------------------------------------------------------------
    def test_racecondition_pending_job_deleted_before_getting_readme_filename(self):
        logger.info("-"*80)
        logger.info("Test processing with job_dir (pending) is deleted after status is determined")
        logger.info("-"*80)

        def delete_job_dir(*a, **kw):
            """
            Delete job_dir
            """

            logger.info("Job folder is deleted ***********")

            # Remove cluster scratch dir
            shutil.rmtree(job_dir)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        with tempfile.TemporaryDirectory() as sub_dir:

            # Make job_dir in sub_dir
            job_dir = os.path.join(sub_dir, str(job_id) + ".pending")
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_readme_filename_from_job_dir",
                    delete_job_dir):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                job_created = start_processing_from_content(joblogfile_content)

        # Assertions
        self.assertFalse(job_created)
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 0)

    # -------------------------------------------------------------------------
    def test_racecondition_running_job_deleted_before_getting_readme_filename(self):
        logger.info("-"*80)
        logger.info("Test processing with job_dir (running) is deleted after status is determined")
        logger.info("-"*80)

        def delete_cluster_job_dir(*a, **kw):
            """
            Delete job_dir in cluster scratch dir
            """

            logger.info("Job folder is deleted ***********")

            # Remove cluster scratch dir
            shutil.rmtree(cluster_scratch_dir)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        cluster_temp_dir = tempfile.TemporaryDirectory()
        cluster_scratch_dir = os.path.join(cluster_temp_dir.name, str(job_id))
        os.makedirs(cluster_scratch_dir)
        logger.debug("Cluster scratch dir: {}".format(cluster_scratch_dir))

        with tempfile.TemporaryDirectory() as tempdir:
            sub_dir = tempdir

            # Create cluster script
            cluster_script_content = "cd {}*".format(cluster_scratch_dir)
            logger.debug("Cluster script content: {}".format(cluster_script_content))
            cluster_script_filename = "{}.dyn-dmp.l01cl012.16.sh".format(job_id)
            cluster_script_filepath = os.path.join(sub_dir, cluster_script_filename)
            with open(cluster_script_filepath, mode="w") as f:
                f.write(cluster_script_content)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=cluster_scratch_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_readme_filename_from_job_dir",
                    delete_cluster_job_dir):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                job_created = start_processing_from_content(joblogfile_content)

        cluster_temp_dir.cleanup()

        # Assertions
        self.assertFalse(job_created)
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 0)

    # -------------------------------------------------------------------------
    def test_racecondition_finished_job_deleted_before_getting_readme_filename(self):
        logger.info("-"*80)
        logger.info("Test processing with job_dir (finished) is deleted after status is determined")
        logger.info("-"*80)

        def delete_job_dir(*a, **kw):
            """
            Delete job_dir
            """

            logger.info("Job folder is deleted ***********")

            # Remove cluster scratch dir
            shutil.rmtree(job_dir)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        with tempfile.TemporaryDirectory() as sub_dir:

            # Make job_dir in sub_dir
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_readme_filename_from_job_dir",
                    delete_job_dir):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                job_created = start_processing_from_content(joblogfile_content)

        # Assertions
        self.assertFalse(job_created)
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 0)

    # -------------------------------------------------------------------------
    def test_racecondition_finished_job_permission_removed_before_getting_readme_filename(self):
        logger.info("-"*80)
        logger.info("Test processing with job_dir (finished) is read permission removed after status is determined")
        logger.info("-"*80)

        def remove_read_permission_job_dir(*a, **kw):
            """
            Remove read permission from job_dir
            """
            logger.info("Job folder read permission removed ***********")
            os.chmod(job_dir, 0o222)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        with tempfile.TemporaryDirectory() as sub_dir:

            # Make job_dir in sub_dir
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_readme_filename_from_job_dir",
                    remove_read_permission_job_dir):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                start_processing_from_content(joblogfile_content)

            # Giving back permission for removal
            os.chmod(job_dir, 0o777)

        # Assert only if not on CI
        if not running_on_ci:
            all_jobs = Job.objects.all()
            self.assertEqual(len(all_jobs), 0)

    # -------------------------------------------------------------------------
    def test_racecondition_README_deleted_before_getting_readme_info(self):
        logger.info("-"*80)
        logger.info("Test processing with README deleted before info is retrieved")
        logger.info("-"*80)

        def delete_README(*a, **kw):
            """
            Delete README from job_dir
            """
            logger.info("REAMDE deleted ***********")
            os.remove(readme_filepath)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        with tempfile.TemporaryDirectory() as sub_dir:

            # Make job_dir in sub_dir
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_job_info_from_readme",
                    delete_README):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                job_created = start_processing_from_content(joblogfile_content)

        # Assertions
        self.assertFalse(job_created)
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 0)

    # -------------------------------------------------------------------------
    def test_racecondition_README_deleted_before_getting_readme_info(self):
        logger.info("-"*80)
        logger.info("Test processing with README deleted before info is retrieved")
        logger.info("-"*80)

        def delete_README(*a, **kw):
            """
            Delete README from job_dir
            """
            logger.info("REAMDE deleted ***********")
            os.remove(readme_filepath)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        with tempfile.TemporaryDirectory() as sub_dir:

            # Make job_dir in sub_dir
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_job_info_from_readme",
                    delete_README):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                job_created = start_processing_from_content(joblogfile_content)

        # Assertions
        self.assertFalse(job_created)
        all_jobs = Job.objects.all()
        self.assertEqual(len(all_jobs), 0)

    # -------------------------------------------------------------------------
    def test_racecondition_README_permission_removed_before_getting_readme_info(self):
        logger.info("-"*80)
        logger.info("Test processing with README read permission removed before info is retrieved")
        logger.info("-"*80)

        def remove_read_permission_README(*a, **kw):
            """
            Remove read permission from job_dir
            """
            logger.info("README read permission removed ***********")
            os.chmod(readme_filepath, 0o222)

        # base_run = Job.objects.create(job_id=123)
        existing_user = User.objects.create(
            username="doej",
            email="John.Doe@example.com")
        job_id = 456

        with tempfile.TemporaryDirectory() as sub_dir:

            # Make job_dir in sub_dir
            job_dir = os.path.join(sub_dir, str(job_id))
            os.makedirs(job_dir)

            # Create README
            main_name = "0123_PRJ_VEHC_SLD_load_case_X_12.5_.key"
            readme_filename, readme_filepath = make_readme(
                job_dir=job_dir,
                job_id=job_id,
                sub_dir=sub_dir,
                username=existing_user.username,
                email=existing_user.email,
                base_runs_str="",
                main_name=main_name
            )

            # Defining joblogfile content
            joblogfile_content = """
job_number: {job_id}
sge_o_workdir: {sub_dir}
""".format(
sub_dir=sub_dir,
job_id=job_id
)

            with before_after.before(
                    "utils.jobinfo.poll.get_job_info_from_readme",
                    remove_read_permission_README):
                # Start processing from joblogfile content
                start_processing_from_content = add_content_to_temp_inputfilepath(
                    start_job_creation_process_from_joblogfile)
                start_processing_from_content(joblogfile_content)

            # Giving back permission for removal
            os.chmod(readme_filepath, 0o777)

        # Assert only if not on CI
        if not running_on_ci:
            all_jobs = Job.objects.all()
            self.assertEqual(len(all_jobs), 0)


# -----------------------------------------------------------------------------
#  Test Helper Function `is_recent`
# -----------------------------------------------------------------------------

class TestIsRecent(TestCase):
    """
    Test the `is_recent` helper method of the `poll_jobs` script
    """

    # -------------------------------------------------------------------------
    def test_now(self):
        datetime_obj = datetime.now()
        self.assertTrue(is_recent(datetime_obj))

    # -------------------------------------------------------------------------
    def test_24h_ago(self):
        datetime_obj = datetime.now() - timedelta(hours=24)
        # Testing true fails, because the now in the test is older than the now
        # in the function.
        # self.assertTrue(is_recent(datetime_obj))
        # Therefore I need to tests false.
        self.assertFalse(is_recent(datetime_obj))

    # -------------------------------------------------------------------------
    def test_12h_ago(self):
        datetime_obj = datetime.now() - timedelta(hours=12)
        self.assertTrue(is_recent(datetime_obj))

    # -------------------------------------------------------------------------
    def test_12h_in_future(self):
        datetime_obj = datetime.now() + timedelta(hours=12)
        self.assertTrue(is_recent(datetime_obj))

    # -------------------------------------------------------------------------
    def test_365days_ago(self):
        datetime_obj = datetime.now() - timedelta(days=365)
        self.assertFalse(is_recent(datetime_obj))

    # -------------------------------------------------------------------------
    def test_None(self):
        datetime_obj = None
        self.assertFalse(is_recent(datetime_obj))

    # -------------------------------------------------------------------------
    def test_string(self):
        datetime_obj = "this is a string"
        self.assertFalse(is_recent(datetime_obj))


# -----------------------------------------------------------------------------
#  Test Helper Function `required_keys_avaiable`
# -----------------------------------------------------------------------------

class TestRequiredKeysAvailable(TestCase):
    """
    Test the `required_keys_avaiable` helper method of the `poll_jobs` script
    """

    # -------------------------------------------------------------------------
    def test_dict_with_all_required_keys(self):
        """Test dictionary with all required key available"""
        readme_dict = {}
        readme_dict["main_name"] = "something"
        readme_dict["base_runs"] = "something"
        readme_dict["username"] = "something"
        readme_dict["email"] = "something"
        readme_dict["info_block"] = "something"
        readme_dict["sub_date"] = "something"
        readme_dict["solver"] = "something"
        self.assertTrue(required_keys_avaiable(readme_dict))

    # -------------------------------------------------------------------------
    def test_dict_with_missing_base_runs(self):
        """Test dictionary with all required key available"""
        readme_dict = {}
        # readme_dict["base_runs"] = "something"
        readme_dict["username"] = "something"
        readme_dict["email"] = "something"
        readme_dict["info_block"] = "something"
        readme_dict["sub_date"] = "something"
        readme_dict["solver"] = "something"
        self.assertFalse(required_keys_avaiable(readme_dict))

    # -------------------------------------------------------------------------
    def test_dict_with_missing_username(self):
        """Test dictionary with all required key available"""
        readme_dict = {}
        readme_dict["base_runs"] = "something"
        # readme_dict["username"] = "something"
        readme_dict["email"] = "something"
        readme_dict["info_block"] = "something"
        readme_dict["sub_date"] = "something"
        readme_dict["solver"] = "something"
        self.assertFalse(required_keys_avaiable(readme_dict))

    # -------------------------------------------------------------------------
    def test_dict_with_missing_email(self):
        """Test dictionary with all required key available"""
        readme_dict = {}
        readme_dict["base_runs"] = "something"
        readme_dict["username"] = "something"
        # readme_dict["email"] = "something"
        readme_dict["info_block"] = "something"
        readme_dict["sub_date"] = "something"
        readme_dict["solver"] = "something"
        self.assertFalse(required_keys_avaiable(readme_dict))

    # -------------------------------------------------------------------------
    def test_dict_with_missing_info_block(self):
        """Test dictionary with all required key available"""
        readme_dict = {}
        readme_dict["base_runs"] = "something"
        readme_dict["username"] = "something"
        readme_dict["email"] = "something"
        # readme_dict["info_block"] = "something"
        readme_dict["sub_date"] = "something"
        readme_dict["solver"] = "something"
        self.assertFalse(required_keys_avaiable(readme_dict))

    # -------------------------------------------------------------------------
    def test_dict_with_missing_sub_date(self):
        """Test dictionary with all required key available"""
        readme_dict = {}
        readme_dict["base_runs"] = "something"
        readme_dict["username"] = "something"
        readme_dict["email"] = "something"
        readme_dict["info_block"] = "something"
        # readme_dict["sub_date"] = "something"
        readme_dict["solver"] = "something"
        self.assertFalse(required_keys_avaiable(readme_dict))

    # -------------------------------------------------------------------------
    def test_dict_with_missing_solver(self):
        """Test dictionary with all required key available"""
        readme_dict = {}
        readme_dict["base_runs"] = "something"
        readme_dict["username"] = "something"
        readme_dict["email"] = "something"
        readme_dict["info_block"] = "something"
        readme_dict["sub_date"] = "something"
        # readme_dict["solver"] = "something"
        self.assertFalse(required_keys_avaiable(readme_dict))

    # -------------------------------------------------------------------------
    def test_dict_with_missing_main_name(self):
        """Test dictionary with all required key available"""
        readme_dict = {}
        # readme_dict["main_name"] = "something"
        readme_dict["base_runs"] = "something"
        readme_dict["username"] = "something"
        readme_dict["email"] = "something"
        readme_dict["info_block"] = "something"
        readme_dict["sub_date"] = "something"
        readme_dict["solver"] = "something"
        self.assertFalse(required_keys_avaiable(readme_dict))
