import logging

from django.test import TestCase
from django.contrib.auth.models import User

from ..models import Job
from utils.logger_copy import copy_logger_settings


logger = logging.getLogger("testing_control").getChild(__name__)
copy_logger_settings("testing_subject", "diary.views")


# ======================================================================
# Job Index View Tests
# ======================================================================
class TestJobListView(TestCase):
    """
    Tests for the index view
    """

    def setUp(self):
        self.user_A = User.objects.create(
            username="usera", email="usera@example.com")
        self.user_B = User.objects.create(
            username="userb", email="userb@example.com")
        self.user_S = User.objects.create(
            username="super", email="super@example.com",
            is_superuser=True)

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

        self.job_user_B_project_A = Job(
            job_id=789,
            user=self.user_B,
            project=self.project_A,
            main_name="yet_another_main_title.key",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_FINISHED
        )
        self.job_user_B_project_A.full_clean()
        self.job_user_B_project_A.save()

        self.job_user_B_project_B = Job(
            job_id=1011,
            user=self.user_B,
            project=self.project_B,
            main_name="this_is_different.pc",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_NONE
        )
        self.job_user_B_project_B.full_clean()
        self.job_user_B_project_B.save()

    def test_unfiltered(self):
        """
        The URL filter for user and project can be used in combination and
        in any order. This behavior is tested here.
        """
        logger.info("Testing unfiltered response")
        response_unfiltered = self.client.get("")
        self.assertEqual(response_unfiltered.status_code, 200)
        usernames_in_jobs_list = [job.user.username for job in
                                  response_unfiltered.context["jobs_list"]]
        projects_in_jobs_list = [job.project for job in
                                 response_unfiltered.context["jobs_list"]]
        self.assertIn(self.user_A.username, usernames_in_jobs_list)
        self.assertIn(self.user_B.username, usernames_in_jobs_list)
        self.assertIn(self.project_A, projects_in_jobs_list)
        self.assertIn(self.project_B, projects_in_jobs_list)
        self.assertIn(self.job_user_A_project_B,
                      response_unfiltered.context["jobs_list"])
        self.assertIn(self.job_user_B_project_A,
                      response_unfiltered.context["jobs_list"])
        self.assertIn(self.job_user_A_project_A,
                      response_unfiltered.context["jobs_list"])
        self.assertIn(self.job_user_B_project_B,
                      response_unfiltered.context["jobs_list"])

    def test_user_filter(self):
        """
        The URL filter for user and project can be used in combination and
        in any order. This behavior is tested here.
        """
        logger.info("Testing filtering for user")
        response_filtered_for_user = self.client.get("/?user={}".format(
            self.user_A.username))
        self.assertEqual(response_filtered_for_user.status_code, 200)
        usernames_in_jobs_list = [job.user.username for job in
                                  response_filtered_for_user.context[
                                      "jobs_list"]]
        projects_in_jobs_list = [job.project for job in
                                 response_filtered_for_user.context[
                                     "jobs_list"]]
        self.assertIn(self.user_A.username, usernames_in_jobs_list)
        self.assertNotIn(self.user_B.username, usernames_in_jobs_list)
        self.assertIn(self.project_A, projects_in_jobs_list)
        self.assertIn(self.project_B, projects_in_jobs_list)
        self.assertIn(self.job_user_A_project_B,
                      response_filtered_for_user.context["jobs_list"])
        self.assertNotIn(self.job_user_B_project_A,
                         response_filtered_for_user.context["jobs_list"])
        self.assertIn(self.job_user_A_project_A,
                      response_filtered_for_user.context["jobs_list"])
        self.assertNotIn(self.job_user_B_project_B,
                         response_filtered_for_user.context["jobs_list"])

    def test_project_filter(self):
        """
        The URL filter for user and project can be used in combination and
        in any order. This behavior is tested here.
        """

        logger.info("Testing filtering for project")
        response_filtered_for_project = self.client.get(
            "/?project={}".format(
                self.project_A))
        self.assertEqual(response_filtered_for_project.status_code, 200)
        usernames_in_jobs_list = [job.user.username for job in
                                  response_filtered_for_project.context[
                                      "jobs_list"]]
        projects_in_jobs_list = [job.project for job in
                                 response_filtered_for_project.context[
                                     "jobs_list"]]
        self.assertIn(self.user_A.username, usernames_in_jobs_list)
        self.assertIn(self.user_B.username, usernames_in_jobs_list)
        self.assertIn(self.project_A, projects_in_jobs_list)
        self.assertNotIn(self.project_B, projects_in_jobs_list)
        self.assertNotIn(self.job_user_A_project_B,
                         response_filtered_for_project.context["jobs_list"])
        self.assertIn(self.job_user_B_project_A,
                      response_filtered_for_project.context["jobs_list"])
        self.assertIn(self.job_user_A_project_A,
                      response_filtered_for_project.context["jobs_list"])
        self.assertNotIn(self.job_user_B_project_B,
                         response_filtered_for_project.context["jobs_list"])

    def test_project_and_user_filter(self):
        """
        The URL filter for user and project can be used in combination and
        in any order. This behavior is tested here.
        """

        logger.info("Testing filtering for project and user (in this order)")
        response_filtered_for_project_user = self.client.get(
            "/?project={proj}&user={user}".format(
                proj=self.project_A,
                user=self.user_A.username
            ))
        self.assertEqual(response_filtered_for_project_user.status_code, 200)
        usernames_in_jobs_list = [job.user.username for job in
                                  response_filtered_for_project_user.context[
                                      "jobs_list"]]
        projects_in_jobs_list = [job.project for job in
                                 response_filtered_for_project_user.context[
                                     "jobs_list"]]
        self.assertIn(self.user_A.username, usernames_in_jobs_list)
        self.assertNotIn(self.user_B.username, usernames_in_jobs_list)
        self.assertIn(self.project_A, projects_in_jobs_list)
        self.assertNotIn(self.project_B, projects_in_jobs_list)
        self.assertNotIn(
            self.job_user_A_project_B,
            response_filtered_for_project_user.context["jobs_list"])
        self.assertNotIn(
            self.job_user_B_project_A,
            response_filtered_for_project_user.context["jobs_list"])
        self.assertIn(
            self.job_user_A_project_A,
            response_filtered_for_project_user.context["jobs_list"])
        self.assertNotIn(
            self.job_user_B_project_B,
            response_filtered_for_project_user.context["jobs_list"])

    def test_user_and_project_filter(self):
        """
        The URL filter for user and project can be used in combination and
        in any order. This behavior is tested here.
        """

        logger.info("Testing filtering for user and project (in this order)")
        response_filtered_for_user_project = self.client.get(
            "/?user={user}&project={proj}".format(
                proj=self.project_A,
                user=self.user_A.username
            ))
        self.assertEqual(response_filtered_for_user_project.status_code, 200)
        usernames_in_jobs_list = [job.user.username for job in
                                  response_filtered_for_user_project.context[
                                      "jobs_list"]]
        projects_in_jobs_list = [job.project for job in
                                 response_filtered_for_user_project.context[
                                     "jobs_list"]]
        self.assertIn(self.user_A.username, usernames_in_jobs_list)
        self.assertNotIn(self.user_B.username, usernames_in_jobs_list)
        self.assertIn(self.project_A, projects_in_jobs_list)
        self.assertNotIn(self.project_B, projects_in_jobs_list)
        self.assertNotIn(
            self.job_user_A_project_B,
            response_filtered_for_user_project.context["jobs_list"])
        self.assertNotIn(
            self.job_user_B_project_A,
            response_filtered_for_user_project.context["jobs_list"])
        self.assertIn(
            self.job_user_A_project_A,
            response_filtered_for_user_project.context["jobs_list"])
        self.assertNotIn(
            self.job_user_B_project_B,
            response_filtered_for_user_project.context["jobs_list"])

    def test_list_of_all_usernames_in_context(self):
        """
        There should be a list of all usernames in the DB in the context.

        This list is needed to create a quick filter option to filter for the
        user without the need to type the username.
        Also, the list should show all usernames from the DB.

        The list should only contain the username strings and not the user
        objects to prevent sensitive data from being available in the response
        object.
        """

        logger.info("Testing for username list object in context")
        response = self.client.get("")
        # List exists
        self.assertIn("usernames", response.context)
        logger.debug(response.context["usernames"])
        # Users are in the list
        self.assertIn(self.user_A.username, response.context["usernames"])
        self.assertIn(self.user_B.username, response.context["usernames"])
        # Super user is not in the list (because it is a super user)
        self.assertNotIn(self.user_S.username, response.context["usernames"])
        # The user objects it self should not be in the context
        self.assertNotIn(self.user_A, response.context["usernames"])
        self.assertNotIn(self.user_B, response.context["usernames"])

    def test_list_of_all_usernames_in_context_with_user_filter(self):
        """
        The list of usernames should show all usernames from the DB. It shall
        not be influenced by the filtering of the jobs_list.
        """

        logger.info("Testing for username list object in context"
                    " while filtering jobs_list for one user")
        response = self.client.get("/?user={}".format(self.user_A.username))
        self.assertIn(self.user_A.username, response.context["usernames"])
        self.assertIn(self.user_B.username, response.context["usernames"])

    def test_list_of_all_projects_in_context(self):
        """
        There should be a list of all projects in the DB in the context.

        This list is needed to create a quick filter option to filter for the
        user without the need to type the project number.
        Also, the list should show all projects that have been used by jobs in
        the DB, but no duplicates.
        """

        logger.info("Testing for projects list object in context")
        response = self.client.get("")
        # List exists
        self.assertIn("projects", response.context)
        logger.debug(response.context["projects"])
        # Projects are in the list
        self.assertIn(self.project_A, response.context["projects"])
        self.assertIn(self.project_B, response.context["projects"])
        # ... but they do appear only once. The queryset count method works
        # differently than the list method. The list method is what I am
        # looking for (how often does "something" occur in the list).
        self.assertEqual(
            1, list(response.context["projects"]).count(self.project_A))
        self.assertEqual(
            1, list(response.context["projects"]).count(self.project_B))

    def test_current_user_filter_in_context_when_applied(self):
        """
        User quick filter should show currently applied user filter

        Since I can not extract the user filter from the URL by pure HTML,
        I want it to be passed on by the view.
        """

        logger.info("Testing for current user filter in context")
        response = self.client.get("/?user={}".format(self.user_A.username))
        self.assertIn("current_user_filter", response.context)
        self.assertEqual(response.context["current_user_filter"],
                         self.user_A.username)
        response = self.client.get("/?user={}".format(self.user_B.username))
        self.assertIn("current_user_filter", response.context)
        self.assertEqual(response.context["current_user_filter"],
                         self.user_B.username)

    def test_current_user_filter_in_context_empty_when_not_applied(self):
        """
        Currently applied user filter in context should be None when not used
        """

        logger.info("Testing for current user filter in context is empty"
                    " when not used.")
        response = self.client.get("/")
        self.assertIn("current_user_filter", response.context)
        self.assertEqual(response.context["current_user_filter"], None)

    def test_current_project_filter_in_context_when_applied(self):
        """
        User quick filter should show currently applied project filter

        Since I can not extract the project filter from the URL by pure HTML,
        I want it to be passed on by the view.
        """

        logger.info("Testing for current project filter in context")
        response = self.client.get("/?project={}".format(self.project_A))
        self.assertIn("current_project_filter", response.context)
        self.assertEqual(response.context["current_project_filter"],
                         self.project_A)
        response = self.client.get("/?project={}".format(self.project_B))
        self.assertIn("current_project_filter", response.context)
        self.assertEqual(response.context["current_project_filter"],
                         self.project_B)

    def test_current_project_filter_in_context_empty_when_not_applied(self):
        """
        Currently applied project filter in context should be None
        when not used
        """

        logger.info("Testing for current project filter in context is empty"
                    " when not used.")
        response = self.client.get("/")
        self.assertIn("current_project_filter", response.context)
        self.assertEqual(response.context["current_project_filter"], None)

    def test_obsolete_job_is_not_in_index(self):
        """
        When a job has the result assessment "obsolete", it should not show up
        in the index.
        """
        logger.info("Testing that obsolete jobs are not in the index")
        response = self.client.get("/")
        # Before the status is set obsolete it is there
        self.assertIn(self.job_user_A_project_A, response.context["jobs_list"])
        logger.info("Current assessment is: {}".format(
            self.job_user_A_project_A.result_assessment))
        self.job_user_A_project_A.result_assessment = \
            Job.RESULT_ASSESSMENT_OBSOLETE
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        logger.info("New assessment is: {}".format(
            self.job_user_A_project_A.result_assessment))
        new_response = self.client.get("/")
        self.assertNotIn(
            self.job_user_A_project_A, new_response.context["jobs_list"])

    def test_show_obsolete_job_with_query_string_parameter(self):
        """
        When a job has the job status "obsolete", it should not show up in the
        index.
        """
        logger.info(
            "Testing showing of obsolete jobs with query string parameter")
        self.job_user_A_project_A.result_assessment = \
            Job.RESULT_ASSESSMENT_OBSOLETE
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        response = self.client.get("/?show_obsolete")
        self.assertIn(self.job_user_A_project_A, response.context["jobs_list"])

    def test_empty_search(self):
        """
        Due to the implementation, the search is combined with the filters in
        one form. This also requires that all jobs are shown when the search
        field is empty.
        """
        logger.info("Testing empty search query")
        response = self.client.get("/?q=")
        jobs_list = response.context["jobs_list"]
        # Not empty
        self.assertNotEqual(len(jobs_list), 0)
        # All jobs are available
        self.assertIn(self.job_user_A_project_A, jobs_list)
        self.assertIn(self.job_user_B_project_A, jobs_list)
        self.assertIn(self.job_user_A_project_B, jobs_list)
        self.assertIn(self.job_user_B_project_B, jobs_list)

    def test_whitespace_search(self):
        """
        Whitespace search does not offer anymore value than an empty one.
        Therefore, their results should be the same.

        Due to the implementation, the search is combined with the filters in
        one form. This also requires that all jobs are shown when the search
        field is empty.
        """
        logger.info("Testing whitespace search query")
        response = self.client.get("/?q= ")
        jobs_list = response.context["jobs_list"]
        # Not empty
        self.assertNotEqual(len(jobs_list), 0)
        # All jobs are available
        self.assertIn(self.job_user_A_project_A, jobs_list)
        self.assertIn(self.job_user_B_project_A, jobs_list)
        self.assertIn(self.job_user_A_project_B, jobs_list)
        self.assertIn(self.job_user_B_project_B, jobs_list)

    def test_search_for_not_contained_word_in_main_names(self):
        """
        Searching for a sting that is not contained in the main title should
        produce an empty list.
        """
        logger.info("Testing search for not contained word in main name")
        queryterm = "thishouldnotbeinthere"
        self.assertNotIn(queryterm, self.job_user_A_project_A.main_name)
        self.assertNotIn(queryterm, self.job_user_A_project_B.main_name)
        response = self.client.get(f"/?q={queryterm}")
        jobs_list = response.context["jobs_list"]
        self.assertEqual(len(jobs_list), 0)

    def test_search_for_exact_main_name(self):
        """
        Searching for the exact main title should produce the defined job.
        """
        logger.info("Testing search for exactly matching main name")
        queryterm = self.job_user_A_project_A.main_name
        self.assertEqual(queryterm, self.job_user_A_project_A.main_name)
        response = self.client.get(f"/?q={queryterm}")
        jobs_list = response.context["jobs_list"]
        self.assertIn(self.job_user_A_project_A, jobs_list)
        # Since the main name should only be used once in the setup,
        # The query set should only contain one job.
        self.assertEqual(1, len(jobs_list))

    def test_search_single_word(self):
        """
        Searching for a single word should produce all the jobs in whose
        `main_name` this word is included.
        """
        logger.info("Testing search for single word in `main_name`")
        queryterm = "main"
        response = self.client.get(f"/?q={queryterm}")
        jobs_list = response.context["jobs_list"]
        self.assertIn(self.job_user_A_project_A, jobs_list)
        self.assertIn(self.job_user_A_project_B, jobs_list)
        self.assertIn(self.job_user_B_project_A, jobs_list)
        self.assertNotIn(self.job_user_B_project_B, jobs_list)

    def test_search_two_words(self):
        """
        Searching for a two word should produce all the jobs in whose
        `main_name` both words are included
        """
        logger.info("Testing search for two words in `main_name`")
        queryterm = "another+main"
        response = self.client.get(f"/?q={queryterm}")
        jobs_list = response.context["jobs_list"]
        logger.debug("Jobs list: {}".format(jobs_list))
        self.assertNotIn(self.job_user_A_project_A, jobs_list)
        self.assertIn(self.job_user_A_project_B, jobs_list)
        self.assertIn(self.job_user_B_project_A, jobs_list)
        self.assertNotIn(self.job_user_B_project_B, jobs_list)

    def test_combination_of_search_and_user_filter(self):
        """
        The if there are filters active, then the search should only act on
        the filtered jobs.
        """
        logger.info("Testing combination of search and user filter")
        queryterm = "main"
        unfilered_response = self.client.get(f"/?q={queryterm}")
        unfiltered_jobs_list = unfilered_response.context["jobs_list"]
        logger.debug("Unfiltered jobs list: {}".format(
            list(unfiltered_jobs_list)))
        self.assertIn(self.job_user_A_project_A, unfiltered_jobs_list)
        self.assertIn(self.job_user_A_project_B, unfiltered_jobs_list)
        self.assertIn(self.job_user_B_project_A, unfiltered_jobs_list)
        self.assertNotIn(self.job_user_B_project_B, unfiltered_jobs_list)
        # Adding a user filter
        filtered_response = self.client.get(
            f"/?q={queryterm}&user={self.user_A.username}")
        filtered_jobs_list = filtered_response.context["jobs_list"]
        logger.debug("Filtered jobs list: {}".format(
            list(filtered_jobs_list)))
        self.assertIn(self.job_user_A_project_A, filtered_jobs_list)
        self.assertIn(self.job_user_A_project_B, filtered_jobs_list)
        self.assertNotIn(self.job_user_B_project_A, filtered_jobs_list)
        self.assertNotIn(self.job_user_B_project_B, filtered_jobs_list)

    def test_combination_of_search_and_project_filter(self):
        """
        The if there are filters active, then the search should only act on
        the filtered jobs.
        """
        logger.info("Testing combination of search and project filter")
        queryterm = "main"
        unfilered_response = self.client.get(f"/?q={queryterm}")
        unfiltered_jobs_list = unfilered_response.context["jobs_list"]
        logger.debug("Unfiltered jobs list: {}".format(
            list(unfiltered_jobs_list)))
        self.assertIn(self.job_user_A_project_A, unfiltered_jobs_list)
        self.assertIn(self.job_user_A_project_B, unfiltered_jobs_list)
        self.assertIn(self.job_user_B_project_A, unfiltered_jobs_list)
        self.assertNotIn(self.job_user_B_project_B, unfiltered_jobs_list)
        # Adding a user filter
        filtered_response = self.client.get(
            f"/?q={queryterm}&project={self.project_B}")
        filtered_jobs_list = filtered_response.context["jobs_list"]
        logger.debug("Filtered jobs list: {}".format(
            list(filtered_jobs_list)))
        self.assertNotIn(self.job_user_A_project_A, filtered_jobs_list)
        self.assertIn(self.job_user_A_project_B, filtered_jobs_list)
        self.assertNotIn(self.job_user_B_project_A, filtered_jobs_list)
        self.assertNotIn(self.job_user_B_project_B, filtered_jobs_list)


class EmptyDBJobIndexViewTest(TestCase):
    """
    Tests for the index view to be performed against an empty DB

    Not many tests make sense here. This might even be considered more of a
    test for the template. For now I will leave it here though.
    """

    def test_no_jobs(self):
        """
        If no jobs exist, the jobs list is empty
        """
        response = self.client.get("")
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["jobs_list"], [])

# ======================================================================
# Job Detail View Tests
# ======================================================================
class JobDetailViewTest(TestCase):
    """
    Tests for the detail view
    """

    # TODO: Add more tests for the detail view

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

    def test_not_existing_job(self):
        """
        Detail view for not existing job results in 404
        """
        not_existing_id = 789
        self.assertNotIn(
            not_existing_id,
            Job.objects.all().values_list("job_id", flat=True))
        response = self.client.get(f"/{not_existing_id}/")
        self.assertEqual(response.status_code, 404)

    def test_existing_job(self):
        """
        Detail view for existing job results in success response, transmission
        of the job and display of the job details
        """
        existing_id = self.job_user_A_project_A.job_id
        self.assertIn(
            existing_id,
            Job.objects.all().values_list("job_id", flat=True))
        response = self.client.get(f"/{existing_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["job"], self.job_user_A_project_A)
        self.assertContains(response, self.job_user_A_project_A.job_id)
        self.assertContains(response, self.job_user_A_project_A.project)

    def test_link_to_index(self):
        """
        Detail view for a job should contain a link to the index view
        """
        existing_id = self.job_user_A_project_A.job_id
        self.assertIn(
            existing_id,
            Job.objects.all().values_list("job_id", flat=True))
        response = self.client.get(f"/{existing_id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["job"], self.job_user_A_project_A)
        self.assertContains(response, 'href="/')

    def test_display_of_and_link_to_baseruns(self):
        """
        If a job has base runs, it should be in the context and a link to it
        should exist.
        """

        self.job_user_A_project_B.base_runs.add(self.job_user_A_project_A)
        response = self.client.get(f"/{self.job_user_A_project_B.job_id}/")

        # Check that the base run is in the context
        self.assertIn(
            self.job_user_A_project_A,
            response.context["job"].base_runs.all()
        )

        # Check there is a link to the base run
        self.assertContains(
            response, f'href="/{self.job_user_A_project_A.job_id}/"')

    def test_display_of_and_link_to_project_and_user_filtered_index(self):
        """
        There should be links to the index view filtering for the job's user
        and project on the detail view
        """
        response = self.client.get(f"/{self.job_user_A_project_A.job_id}/")
        self.assertEqual(response.status_code, 200)

        # Check there is a link to the base run
        self.assertContains(
            response,
            f'href="/?project={self.job_user_A_project_A.project}"')
        self.assertContains(
            response,
            f'href="/?user={self.job_user_A_project_A.user.username}"')
