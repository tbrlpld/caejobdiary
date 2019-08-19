from datetime import date
import logging
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

sys.path.insert(0, settings.TOP_LEVEL_DIR)
from diary.models import Job, Keyword, Tag  # noqa: E402
from utils.logger_copy import copy_logger_settings  # noqa: E402


logger = logging.getLogger("testing_control").getChild(__name__)
copy_logger_settings("testing_subject", "diary.models")

User = get_user_model()


class TestTagValidation(TestCase):
    """Testing the validation of tags"""

    def test_valid_tags(self):
        valid_tag1 = Tag(tag="#alllower")
        self.assertIsNone(valid_tag1.full_clean())
        valid_tag2 = Tag(tag="#chamelCase")
        self.assertIsNone(valid_tag2.full_clean())
        valid_tag3 = Tag(tag="#UpperFirst")
        self.assertIsNone(valid_tag3.full_clean())
        valid_tag4 = Tag(tag="#ALLUPPER")
        self.assertIsNone(valid_tag4.full_clean())
        valid_tag5 = Tag(tag="#withNumber1")
        self.assertIsNone(valid_tag5.full_clean())

    def test_tag_not_starting_with_hashsymbol(self):
        invalid_tag = Tag(tag="newtag")
        self.assertRaises(ValidationError, invalid_tag.full_clean)

    def test_tag_with_space(self):
        invalid_tag = Tag(tag="#new tag")
        self.assertRaises(ValidationError, invalid_tag.full_clean)

    def test_tag_with_underscore(self):
        invalid_tag = Tag(tag="#new_tag")
        self.assertRaises(ValidationError, invalid_tag.full_clean)

    def test_tag_with_hyphen(self):
        invalid_tag = Tag(tag="#new-tag")
        self.assertRaises(ValidationError, invalid_tag.full_clean)

    def test_tag_with_has_in_middle(self):
        invalid_tag = Tag(tag="#new#tag")
        self.assertRaises(ValidationError, invalid_tag.full_clean)


class TestTagFeature(TestCase):
    """Test regarding the tags feature"""

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

    def test_creation_of_tags_in_db(self):
        Tag.objects.create(tag="#newtag1")
        newtag2 = Tag(tag="#newTag2")
        newtag2.full_clean()
        newtag2.save()
        #  Check if creation worked by retrieving objects from db.
        tags = Tag.objects.all()
        for tag in tags:
            self.assertTrue((tag.tag == "#newtag1" or tag.tag == "#newTag2"))

    def test_adding_tag_to_job_and_retrieving_the_job_via_tag(self):
        job_obj = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        newtag = Tag(tag="#newtag")
        newtag.full_clean()
        newtag.save()
        job_obj.tags.add(newtag)
        job_obj.full_clean()
        job_obj.save()
        # Grab job via the tag
        job_by_tag = Job.objects.filter(tags__tag__exact=newtag.tag).first()
        self.assertEqual(job_by_tag.job_id, job_obj.job_id)
        self.assertIn(newtag, job_by_tag.tags.all())
        self.assertEqual(newtag, job_by_tag.tags.first())


class TestJobQuerySetKeywordSearch(TestCase):
    """
    Test the `keyword_search` method of the custom JobQuerySet
    """

    def setUp(self):
        self.user_A = User.objects.create(
            username="usera", email="usera@example.com")
        self.user_B = User.objects.create(
            username="userb", email="userb@example.com")

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

    def test_how_to_access_queryset(self):
        queryset = Job.objects.all()
        self.assertIn(self.job_user_A_project_A, queryset)
        self.assertIn(self.job_user_A_project_B, queryset)
        self.assertIn(self.job_user_B_project_A, queryset)
        self.assertIn(self.job_user_B_project_B, queryset)

    def test_empty_search(self):
        """
        An empty search string should return anything! It is supposed to act
        as a search! Not as a filter.
        """
        logger.info("Testing empty search query")
        queryset = Job.objects.keyword_search("")
        logger.debug("Returned queryset: {}".format(list(queryset)))
        self.assertEqual(len(queryset), 0)

    def test_whitespace_search(self):
        """
        A search for whitespace does not have anymore value than one for an
        empty string. The result should be the same -- empty.
        """
        logger.info("Testing whitespace search query")
        queryset = Job.objects.keyword_search(" ")
        logger.debug("Returned queryset: {}".format(list(queryset)))
        self.assertEqual(len(queryset), 0)

    def test_search_for_not_contained_word_in_main_names(self):
        """
        Searching for a sting that is not contained in the main title should
        produce an empty list.
        """
        logger.info("Testing search for not contained word in main name")
        queryterm = "thishouldnotbeinthere"
        self.assertNotIn(queryterm, self.job_user_A_project_A.main_name)
        self.assertNotIn(queryterm, self.job_user_A_project_B.main_name)
        self.assertNotIn(queryterm, self.job_user_B_project_A.main_name)
        self.assertNotIn(queryterm, self.job_user_B_project_B.main_name)
        queryset = Job.objects.keyword_search(queryterm)
        logger.debug("Returned queryset: {}".format(list(queryset)))
        self.assertNotIn(self.job_user_A_project_A, queryset)
        self.assertNotIn(self.job_user_A_project_B, queryset)
        self.assertNotIn(self.job_user_B_project_A, queryset)
        self.assertNotIn(self.job_user_B_project_B, queryset)

    def test_search_for_exact_main_name(self):
        """
        Searching for the exact main title should produce the defined job.
        """
        logger.info("Testing search for exactly matching main name")
        queryterm = self.job_user_A_project_A.main_name
        self.assertEqual(queryterm, self.job_user_A_project_A.main_name)
        queryset = Job.objects.keyword_search(queryterm)
        logger.debug("Returned queryset: {}".format(list(queryset)))
        self.assertIn(self.job_user_A_project_A, queryset)
        # Since the main name should only be used once in the setup,
        # The query set should only contain one job.
        self.assertEqual(1, len(queryset))

    def test_search_single_word_in_main_name(self):
        """
        Searching for a single word should produce all the jobs in whose
        `main_name` this word is included.
        """
        logger.info("Testing search for single word in `main_name`")
        queryterm = "main"
        queryset = Job.objects.keyword_search(queryterm)
        logger.debug("Returned queryset: {}".format(list(queryset)))
        self.assertIn(self.job_user_A_project_A, queryset)
        self.assertIn(self.job_user_A_project_B, queryset)
        self.assertIn(self.job_user_B_project_A, queryset)
        self.assertNotIn(self.job_user_B_project_B, queryset)

    def test_search_single_word_in_main_name_case_insensitive(self):
        """
        The case of the search term should not matter.
        """
        logger.info("Testing case insensitive search for single word")
        queryterm_lower = "main"
        queryset_lower = Job.objects.keyword_search(queryterm_lower)
        logger.debug("Returned queryset for lower case: {}".format(
            list(queryset_lower)))
        queryterm_upper = "MAIN"
        queryset_upper = Job.objects.keyword_search(queryterm_upper)
        logger.debug("Returned queryset for upper case: {}".format(
            list(queryset_upper)))
        # Every job returned for the lower case query should be in the returned
        # set for the upper case query
        for job in queryset_lower:
            self.assertIn(job, queryset_upper)

    def test_search_two_words_in_main_name(self):
        """
        Searching for a two word should produce all the jobs in whose
        `main_name` both words are included. Each job should only be
        contained once!
        """
        logger.info("Testing search for two words in `main_name`")
        queryterm = "another main"
        queryset = Job.objects.keyword_search(queryterm)
        logger.debug("Returned queryset: {}".format(list(queryset)))
        self.assertNotIn(self.job_user_A_project_A, queryset)
        self.assertIn(self.job_user_A_project_B, queryset)
        self.assertIn(self.job_user_B_project_A, queryset)
        self.assertNotIn(self.job_user_B_project_B, queryset)
        self.assertEqual(len(queryset), 2)


class TestParsedMainNameProperty(TestCase):
    """
    Tests for the property that returns the parsed main_name

    Parsing currently means that undesired characters from the main_name are
    being removed. Undesired characters are the last "dot" separating the
    file extension, and underscores.

    Switched from using a private method and a field to just a private
    property. This reduced what needs to be defined. Also, the parsed main name
    does not need to be stored in the DB. It was updated with every save
    anyhow. Parsing the `main_name` is mainly a preliminary step to building
    the jobs keyword string.
    """

    logger = logger.getChild("TestParsedMainNameProperty")

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

    def test_empty_main_name(self):
        """
        Usually empty main_names should not occur, but the function should
        still be robust against it.
        """
        given_main_name = ""
        expected_parsed = ""
        self.logger.info(f"Test stripping of empty main name ")
        self.job_user_A_project_A.main_name = given_main_name
        self.job_user_A_project_A.save()
        self.assertEqual(self.job_user_A_project_A.main_name, given_main_name)
        actual_parsed = self.job_user_A_project_A._keyword_parsed_main_name
        self.assertEqual(actual_parsed, expected_parsed)

    def test_stripping_of_simple_main_name(self):
        given_main_name = "some_main_title.key"
        expected_parsed = "some main title key"
        self.logger.info(f"Test stripping of main name `{given_main_name}`")
        self.assertEqual(self.job_user_A_project_A.main_name, given_main_name)
        actual_parsed = self.job_user_A_project_A._keyword_parsed_main_name
        self.assertEqual(actual_parsed, expected_parsed)

    def test_stripping_of_main_name_w_multiple_dots(self):
        """
        Only the last dot (separating the file extension) should be removed

        There are many use cases when the name might contain a dot in the
        middle of the name. Therefore, the main name should only be parsed
        of the last dot.
        """
        given_main_name = "some_main_v1.2_title.key"
        expected_parsed = "some main v1.2 title key"
        self.logger.info(f"Test stripping of main name `{given_main_name}`")
        self.job_user_A_project_A.main_name = given_main_name
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(self.job_user_A_project_A.main_name, given_main_name)
        actual_parsed = self.job_user_A_project_A._keyword_parsed_main_name
        self.assertEqual(actual_parsed, expected_parsed)

    def test_stripping_of_main_name_w_hyphens(self):
        """
        Hyphens are treated as word connector. The connected word should
        main intact.
        """
        given_main_name = "some_main_title_with-hyphen.key"
        expected_parsed = "some main title with-hyphen key"
        self.logger.info(f"Test stripping of main name `{given_main_name}`")
        self.job_user_A_project_A.main_name = given_main_name
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(self.job_user_A_project_A.main_name, given_main_name)
        actual_parsed = self.job_user_A_project_A._keyword_parsed_main_name
        self.assertEqual(actual_parsed, expected_parsed)

    def test_keyword_parsed_main_name_in_retrieved_object(self):
        self.logger.info(
            f"Test parsed main name of object when retrieved from DB")
        initial_main_name = "some_main_title.key"
        initial_parsed = "some main title key"
        initial_retrieved_object = Job.objects.get(
            job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(
            initial_retrieved_object.main_name, initial_main_name)
        self.assertEqual(
            initial_retrieved_object._keyword_parsed_main_name, initial_parsed)
        new_main_name = "some_main_v1.2_title.key"
        expected_new_parsed = "some main v1.2 title key"
        initial_retrieved_object.main_name = new_main_name
        initial_retrieved_object.full_clean()
        initial_retrieved_object.save()
        new_retrieved_object = Job.objects.get(
            job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(
            new_retrieved_object.main_name, new_main_name)
        self.assertEqual(
            new_retrieved_object._keyword_parsed_main_name,
            expected_new_parsed)


class TestParsedSubDirProperty(TestCase):
    """
    Test values of the parsed `sub_dir`

    This is fairly similar to the _keyword_parsed_main_name property.
    The difference is that here the slashs "/" are removed.
    The folder names also contain valuable information. Therefore, the
    underscores separating words should also be stripped.

    But, as with the main_name, it also makes sense to be
    able to find the actual folder name (with underscore). Therefore, parsed
    `sub_dir` is twice as long in characters. Each word is once contained
    separately and also in the folder name it was extracted from.
    """
    logger = logger.getChild("TestParsedSubDirProperty")

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

    def test_splitting_at_slashes(self):
        self.logger.info("Testing splitting of `sub_dir` at slashes `/`")
        self.job_user_A_project_A.sub_dir = "/some/directory/with/slashes/"
        expected_words = ["some", "directory", "with", "slashes"]
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        parsed_sub_dir = self.job_user_A_project_A._keyword_parsed_sub_dir
        self.logger.debug(f"parsed_sub_dir: {parsed_sub_dir}")
        words_in_keyword_parsed_sub_dir = parsed_sub_dir.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, words_in_keyword_parsed_sub_dir)

    def test_underscore_in_folder_name(self):
        """
        Folder names with underscore should be available as one word and
        as the separate words split at the underscore.
        """
        self.logger.info("Testing folder name with underscore")
        self.job_user_A_project_A.sub_dir = "/some/directory/with_underscore/"
        expected_words = [
            "some", "directory", "with_underscore", "with", "underscore"]
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        parsed_sub_dir = self.job_user_A_project_A._keyword_parsed_sub_dir
        self.logger.debug(f"parsed_sub_dir: {parsed_sub_dir}")
        words_in_keyword_parsed_sub_dir = parsed_sub_dir.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, words_in_keyword_parsed_sub_dir)

    def test_multiple_underscores_in_folder_name(self):
        """
        Folder names with multiple underscores should be available as one word
        and as the separate words split at the underscores.
        """
        self.logger.info("Testing folder names with multiple underscores")
        self.job_user_A_project_A.sub_dir = \
            "/some/directory/with_under_scores/"
        expected_words = ["some", "directory", "with_under_scores", "with",
                          "under", "scores"]
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        parsed_sub_dir = self.job_user_A_project_A._keyword_parsed_sub_dir
        self.logger.debug(f"parsed_sub_dir: {parsed_sub_dir}")
        words_in_keyword_parsed_sub_dir = parsed_sub_dir.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, words_in_keyword_parsed_sub_dir)


class TestParseFulltext(TestCase):
    """
    The for the fulltext parse method of the Job model
    """
    logger = logger.getChild("TestParseFulltext")

    def test_empty_input(self):
        self.logger.info("Testing empty input")
        parsed_fulltext = Job._keyword_parse_fulltext("")
        self.assertEqual(parsed_fulltext, "")

    def test_removal_of_parenthesis(self):
        self.logger.info("Testing removal of parentheses `()`")
        fulltext = "Text with (parentheses)"
        self.logger.debug(fulltext)
        expected_words = ["Text", "with", "parentheses"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_removal_of_brackets(self):
        self.logger.info("Testing removal of brackets `[]`")
        fulltext = "Text with [brackets]"
        self.logger.debug(fulltext)
        expected_words = ["Text", "with", "brackets"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_removal_of_curly_braces(self):
        self.logger.info("Testing removal of curly braces `\{\}`")
        fulltext = "Text with \{curly braces\}"
        self.logger.debug(fulltext)
        expected_words = ["Text", "with", "curly", "braces"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_removal_of_exclamation_point(self):
        self.logger.info("Testing removal of exclamation point `!`")
        fulltext = "Text with exclamation point!"
        expected_words = ["Text", "with", "exclamation", "point"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_removal_of_question_mark(self):
        self.logger.info("Testing removal of question mark `?`")
        fulltext = "Text with question mark?"
        expected_words = ["Text", "with", "question", "mark"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_removal_of_colon(self):
        self.logger.info("Testing removal of colon `:` mid sentence")
        fulltext = "Text with: colon"
        expected_words = ["Text", "with", "colon"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_removal_of_double_comma(self):
        self.logger.info("Testing removal of double comma `,,`")
        fulltext = "Text with,, double comma"
        expected_words = ["Text", "with", "double", "comma"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_removal_of_duplicate_word(self):
        self.logger.info("Testing removal of duplicate  word")
        fulltext = "Text with word word in there twice"
        expected_words = ["Text", "with", "word", "in", "there", "twice"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)
        self.assertEqual(len(expected_words), len(parsed_fulltext_split))

    def test_maintaining_dash_in_word(self):
        self.logger.info("Testing maintaining dash in word")
        fulltext = "Text with dashed-word"
        expected_words = ["Text", "with", "dashed-word"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_maintaining_underscore_in_word(self):
        self.logger.info("Testing maintaining underscore in word")
        fulltext = "Text with underscore_word"
        expected_words = ["Text", "with", "underscore_word"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)

    def test_maintaining_dot_in_word(self):
        self.logger.info("Testing maintaining dot in word")
        fulltext = "Text with 1.5 words"
        expected_words = ["Text", "with", "1.5", "words"]
        parsed_fulltext = Job._keyword_parse_fulltext(fulltext)
        self.logger.debug(parsed_fulltext)
        parsed_fulltext_split = parsed_fulltext.split()
        for expected_word in expected_words:
            self.assertIn(expected_word, parsed_fulltext_split)


class TestKeywordParsedJobStatusProperty(TestCase):
    """
    Test for the _keyword_parsed_job_status property
    """

    logger = logger.getChild("TestKeywordParsedJobStatusProperty")

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

    def test_pending(self):
        self.assertEqual(
            self.job_user_A_project_A.job_status,
            Job.JOB_STATUS_PENDING)
        self.assertEqual(
            self.job_user_A_project_A._keyword_parsed_job_status,
            "pending")

    def test_normal_termination(self):
        self.job_user_A_project_A.job_status = \
            Job.JOB_STATUS_NORMAL_TERMINATION
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.job_status,
            Job.JOB_STATUS_NORMAL_TERMINATION)
        self.assertEqual(
            self.job_user_A_project_A._keyword_parsed_job_status,
            "normal termination")

    def test_none(self):
        self.job_user_A_project_A.job_status = \
            Job.JOB_STATUS_NONE
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.job_status,
            Job.JOB_STATUS_NONE)
        self.assertEqual(
            self.job_user_A_project_A._keyword_parsed_job_status,
            "none undefined")


class TestKeywordParsedResultAssessment(TestCase):
    """
    Tests for the property that returns the parsed result assessment
    """
    logger = logger.getChild("TestKeywordParsedResultAssessment")

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

    def test_ok(self):
        self.job_user_A_project_A.result_assessment = \
            Job.RESULT_ASSESSMENT_OK
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.result_assessment,
            Job.RESULT_ASSESSMENT_OK)
        self.assertEqual(
            self.job_user_A_project_A._keyword_parsed_result_assessment,
            "ok")

    def test_nok(self):
        self.job_user_A_project_A.result_assessment = \
            Job.RESULT_ASSESSMENT_NOK
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.result_assessment,
            Job.RESULT_ASSESSMENT_NOK)
        self.assertEqual(
            self.job_user_A_project_A._keyword_parsed_result_assessment,
            "not ok nok")

    def test_other(self):
        self.job_user_A_project_A.result_assessment = \
            Job.RESULT_ASSESSMENT_OTHER
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.result_assessment,
            Job.RESULT_ASSESSMENT_OTHER)
        self.assertEqual(
            self.job_user_A_project_A._keyword_parsed_result_assessment,
            "other")

    def test_issue(self):
        self.job_user_A_project_A.result_assessment = \
            Job.RESULT_ASSESSMENT_ISSUE
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.result_assessment,
            Job.RESULT_ASSESSMENT_ISSUE)
        self.assertEqual(
            self.job_user_A_project_A._keyword_parsed_result_assessment,
            "issue")


class TestBuildKeywordString(TestCase):
    """
    Tests for the method that build the keyword string

    The keyword string should contain each keyword from the job once. Keywords
    are words or string sections that are considered valuable to identify the
    job in a search.
    """
    logger = logger.getChild("TestBuildKeywordString")

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

    def test_keywords_from_main_name_are_returned(self):
        self.logger.info(
            "Test that all main name keywords are in keyword string")
        given_main_name = "some_main_title.key"
        self.assertEqual(self.job_user_A_project_A.main_name, given_main_name)
        main_name_keywords = {"some", "main", "title", "key"}
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        for main_name_keyword in main_name_keywords:
            self.assertIn(main_name_keyword, returned_keyword_string)

    def test_keywords_in_string_once(self):
        self.logger.info(
            "Test that all main name keywords are in keyword string"
            " exactly once!")
        given_main_name = "some_main_title.key"
        self.assertEqual(self.job_user_A_project_A.main_name, given_main_name)
        main_name_keywords = {"some", "main", "title", "key"}
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        list_from_string = returned_keyword_string.split()
        for main_name_keyword in main_name_keywords:
            self.assertEqual(list_from_string.count(main_name_keyword), 1)

    def test_job_id_in_returned_string(self):
        self.logger.info(
            "Test that `job_id` is in returned keyword_string")
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertIn(
            str(self.job_user_A_project_A.job_id), returned_keyword_string)

    def test_main_name_in_returned_string(self):
        self.logger.info(
            "Test that whole `main_name` is in returned keyword_string")
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertIn(
            self.job_user_A_project_A.main_name, returned_keyword_string)

    def test_username_in_returned_string(self):
        self.logger.info("Test that `username` is in returned keyword_string")
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertIn(self.user_A.username, returned_keyword_string)

    def test_project_in_returned_string(self):
        self.logger.info("Test that `project` is in returned keyword_string")
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertIn(
            self.job_user_A_project_A.project, returned_keyword_string)

    def test_sub_dir_folder_names_and_words(self):
        self.logger.info("Test that folder names and words from `sub_dir` are"
                         " in returned keyword_string")
        self.job_user_A_project_A.sub_dir = "/my-directory/with_underscore/"
        expected_words = ["my-directory", "with_underscore", "with",
                          "underscore"]
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        for expected_word in expected_words:
            self.assertIn(expected_word, returned_keyword_string)

    def test_words_from_info(self):
        self.logger.info("Test that words from `info` are"
                         " in returned keyword_string")
        self.job_user_A_project_A.info = """The info text can be longer.
        This is, it really depends on what the user types.
        """
        expected_words = ["The", "info", "text", "can", "be", "longer",
                          "This", "is", "it", "really", "depends", "on",
                          "what", "the", "user", "types"]
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        for expected_word in expected_words:
            self.assertIn(expected_word, returned_keyword_string)

    def test_words_from_result_summary(self):
        self.logger.info("Test that words from `result_summary` are"
                         " in returned keyword_string")
        self.job_user_A_project_A.result_summary = """
        The result_summary text can be longer.
        This is, it really depends on what the user types.
        """
        expected_words = ["The", "result_summary", "text", "can", "be",
                          "longer",
                          "This", "is", "it", "really", "depends", "on",
                          "what", "the", "user", "types"]
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        for expected_word in expected_words:
            self.assertIn(expected_word, returned_keyword_string)

    def test_verbose_job_status_pending(self):
        self.logger.info("Test that verbose job status (pending) in returned"
                         " keyword string")
        self.assertEqual(
            self.job_user_A_project_A.job_status,
            Job.JOB_STATUS_PENDING)
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertIn("pending", returned_keyword_string.split())

    def test_verbose_job_status_normal_termination(self):
        self.logger.info("Test that verbose job status (normal termination) in"
                         " returned keyword string")
        self.job_user_A_project_A.job_status = \
            Job.JOB_STATUS_NORMAL_TERMINATION
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.job_status,
            Job.JOB_STATUS_NORMAL_TERMINATION)
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertNotIn("pending", returned_keyword_string.split())
        self.assertIn("normal", returned_keyword_string.split())
        self.assertIn("termination", returned_keyword_string.split())

    def test_verbose_job_status_none(self):
        self.logger.info("Test that verbose job status (none / undefined) in"
                         " returned keyword string")
        self.job_user_A_project_A.job_status = \
            Job.JOB_STATUS_NONE
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.job_status,
            Job.JOB_STATUS_NONE)
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertNotIn("/", returned_keyword_string.split())
        self.assertIn("none", returned_keyword_string.split())
        self.assertIn("undefined", returned_keyword_string.split())

    def test_verbose_analysis_status_open(self):
        self.logger.info("Test that verbose analysis status (open) in"
                         " returned keyword string")
        self.job_user_A_project_A.analysis_status = \
            Job.ANALYSIS_STATUS_OPEN
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.analysis_status,
            Job.ANALYSIS_STATUS_OPEN)
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertIn("open", returned_keyword_string.split())

    def test_verbose_result_assessment_not_ok(self):
        self.logger.info("Test that verbose result assessment (nok) in"
                         " returned keyword string")
        self.job_user_A_project_A.result_assessment = \
            Job.RESULT_ASSESSMENT_NOK
        self.job_user_A_project_A.full_clean()
        self.job_user_A_project_A.save()
        self.assertEqual(
            self.job_user_A_project_A.result_assessment,
            Job.RESULT_ASSESSMENT_NOK)
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertIn("not", returned_keyword_string.split())
        self.assertIn("ok", returned_keyword_string.split())
        self.assertIn("nok", returned_keyword_string.split())

    def test_date(self):
        self.logger.info("Test that sub_date ISO date string in"
                         " returned keyword string")
        sub_date_datetime = self.job_user_A_project_A.sub_date
        sub_date_date = date(
            year=sub_date_datetime.year,
            month=sub_date_datetime.month,
            day=sub_date_datetime.day,
        )
        sub_date_isostring = sub_date_date.isoformat()
        self.logger.debug(sub_date_isostring)
        returned_keyword_string = \
            self.job_user_A_project_A._build_keyword_string()
        self.assertIn(sub_date_isostring, returned_keyword_string.split())


class TestKeywordStringField(TestCase):
    """
    Tests for the keyword_string field

    The keyword string should contain each keyword from the job once. Keywords
    are words or string sections that are considered valuable to identify the
    job in a search.

    The content of the field should be determined by the
    `_build_keyword_string` method. This test case is only to check that the
    `keyword_string` is properly saved in the DB.
    """
    logger = logger.getChild("TestKeywordStringField")

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

    def test_keywords_in_string_once(self):
        self.logger.info(
            "Test that all main name keywords are in keyword string"
            " exactly once!")
        given_main_name = "some_main_title.key"
        retrieved_object = Job.objects.get(
            job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(retrieved_object.main_name, given_main_name)
        main_name_keywords = {"some", "main", "title", "key"}
        keyword_string = retrieved_object.keyword_string
        list_from_string = keyword_string.split()
        for main_name_keyword in main_name_keywords:
            self.assertEqual(list_from_string.count(main_name_keyword), 1)

    def test_keywords_string_update(self):
        self.logger.info(
            "Test that keyword string changes when main_name does")
        given_main_name = "some_main_title.key"
        initial_retrieved_object = Job.objects.get(
            job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(initial_retrieved_object.main_name, given_main_name)
        new_main_name = "new_" + given_main_name
        new_main_name_keywords = {"new", "some", "main", "title", "key"}
        initial_retrieved_object.main_name = new_main_name
        initial_retrieved_object.full_clean()
        initial_retrieved_object.save()
        updated_retrieved_object = Job.objects.get(
            job_id=self.job_user_A_project_A.job_id)
        keyword_string = updated_retrieved_object.keyword_string
        list_from_string = keyword_string.split()
        for main_name_keyword in new_main_name_keywords:
            self.assertEqual(list_from_string.count(main_name_keyword), 1)


class TestUpdateKeywordAssociationWithString(TestCase):
    """
    Tests for the private method that associates each keyword of the
    `keyword_string` with the job via the `keywords` many-to-many field
    """
    logger = logger.getChild("TestUpdateKeywordAssociationWithString")

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

        # Remove all associated keywords in case they are created automatically
        self.job_user_A_project_A.keywords.clear()
        self.assertEqual(self.job_user_A_project_A.keywords.count(), 0)

        # Delete all possibly existing keywords in the DB
        Keyword.objects.all().delete()

        # Based on the main_name, these words are to be in the keywords
        self.expected_words = {"some", "main", "title", "key"}
        # Just making sure there are some words in the keyword_string
        for expected_word in self.expected_words:
            self.assertIn(expected_word,
                          self.job_user_A_project_A.keyword_string)

    def test_return_of_added_keywords(self):
        self.logger.info("Testing return value for words that should be added")
        # Double checking the initial condition (no keywords associated)
        self.assertEqual(self.job_user_A_project_A.keywords.count(), 0)
        # Calling the association method
        returned_added_keywords_list = \
            self.job_user_A_project_A.\
            _update_keyword_association_with_string()[0]
        # Now there need to be keywords associated (because the string is not
        # empty)
        self.assertNotEqual(self.job_user_A_project_A.keyword_string, "")
        self.assertNotEqual(self.job_user_A_project_A.keywords.count(), 0)
        # Checking that each expected word has been added
        words_from_return = [keyword.word for keyword in
                             returned_added_keywords_list]
        for word in self.expected_words:
            self.assertIn(word, words_from_return)

    def test_return_on_repeated_method_call(self):
        """
        While keywords should be added on the first call there should not be
        any on the second call, because the keywords should be existing.
        """
        self.logger.info("Testing return value repeated method call")
        # Double checking the initial condition (no keywords associated)
        self.assertEqual(self.job_user_A_project_A.keywords.count(), 0)
        # Calling the association method
        first_returned_added_keywords_list = \
            self.job_user_A_project_A.\
            _update_keyword_association_with_string()[0]
        # Some keywords should be added
        self.assertNotEqual(len(first_returned_added_keywords_list), 0)
        # Second calling of the association method
        second_returned_added_keywords_list = \
            self.job_user_A_project_A.\
            _update_keyword_association_with_string()[0]
        # No keywords should have been added
        self.assertEqual(len(second_returned_added_keywords_list), 0)

    def test_association_on_retrieved_objects(self):
        self.logger.info("Testing association of keywords with objects"
                         " retrieved from DB")
        job_id = self.job_user_A_project_A.job_id
        # Job from DB has no associations to Keywords
        initial_job = Job.objects.get(job_id=job_id)
        self.assertEqual(initial_job.keywords.count(), 0)
        # Checking that no Keyword in DB
        self.assertEqual(Keyword.objects.count(), 0)

        # Calling the method
        initial_job._update_keyword_association_with_string()

        # Each expected word should have a corresponding keyword in the DB
        keywords_from_db = Keyword.objects.all()
        words_from_db = [keyword.word for keyword in keywords_from_db]
        for word in self.expected_words:
            self.assertIn(word, words_from_db)
        # Each keyword should be associated with the Job
        newly_retrieved_job = Job.objects.get(job_id=job_id)
        associated_keywords_from_job = newly_retrieved_job.keywords.all()
        for keyword in keywords_from_db:
            self.assertIn(keyword, associated_keywords_from_job)

    def test_disassociation_of_words_removed_from_keyword_string(self):
        self.logger.info("Test disassociation of words that are removed from"
                         " the keyword string")
        test_word = list(self.expected_words)[0]  # Just getting a test word
        initial_job = Job.objects.get(job_id=self.job_user_A_project_A.job_id)
        # So far the word should be in the string
        # and end up in the associations
        self.assertIn(test_word, initial_job.keyword_string)
        initial_job._update_keyword_association_with_string()
        words_from_keywords = [keyword.word for keyword
                               in initial_job.keywords.all()]
        self.assertIn(test_word, words_from_keywords)
        # Removing the example word
        keyword_string_word_list = initial_job.keyword_string.split()
        self.logger.debug("Before removal: {}".format(
            keyword_string_word_list))
        reduced_word_list = [word for word in keyword_string_word_list
                             if word != test_word]
        self.logger.debug("After removal: {}".format(
            reduced_word_list))
        initial_job.keyword_string = " ".join(reduced_word_list)
        # Now the example word should not be in the string.
        # Since there could be long words (like the main_name) which contain
        # the test word, each word has to be tested separately.
        for word in initial_job.keyword_string.split():
            self.assertNotEqual(test_word, word)
        # And after applying the function it should not be associated anymore
        removed_keywords_list = initial_job.\
            _update_keyword_association_with_string()[1]
        self.assertEqual(len(removed_keywords_list), 1)
        words_from_keywords = [keyword.word for keyword
                               in initial_job.keywords.all()]
        self.assertNotIn(test_word, words_from_keywords)

    def test_trimming_of_too_long_word(self):
        """
        The word field can only take 200 characters. Longer word should be
        trimmed to this length.
        """
        self.logger.info("Test trimming of too long words")
        max_word_length = Keyword._meta.get_field('word').max_length
        long_word = "thisisalonglonglonglonglonglonglonglonglonglonglonglong" \
                    + "longlonglonglonglonglonglonglonglonglonglonglonglong" \
                    + "longlonglonglonglonglonglonglonglonglonglonglonglong" \
                    + "longlonglonglonglonglonglonglonglonglongword"
        self.assertGreater(len(long_word), max_word_length)

        self.job_user_A_project_A.keyword_string += " " + long_word

        self.job_user_A_project_A._update_keyword_association_with_string()

        words_from_keywords = [keyword.word for keyword
                               in Keyword.objects.all()]
        self.assertNotIn(long_word, words_from_keywords)
        self.assertIn(long_word[0:max_word_length], words_from_keywords)


class TestKeywordsManyToManyField(TestCase):
    """
    Tests for the keywords many-to-many field
    """
    logger = logger.getChild("TestKeywordsManyToManyField")

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

        # Remove all associated keywords in case they are created automatically
        self.job_user_A_project_A.keywords.clear()
        self.assertEqual(self.job_user_A_project_A.keywords.count(), 0)

        # Delete all possibly existing keywords in the DB
        Keyword.objects.all().delete()

        # Based on the main_name, these words are to be in the keywords
        self.expected_words = {"some", "main", "title", "key"}
        # Just making sure there are some words in the keyword_string
        for expected_word in self.expected_words:
            self.assertIn(expected_word,
                          self.job_user_A_project_A.keyword_string)

    def test_manual_creation_of_keywords(self):
        self.logger.info("Testing manual creation of keywords and association"
                         " with a job")
        # Create the keywords
        k1 = Keyword(word="1234")
        k1.full_clean()
        k1.save()
        k2 = Keyword(word="some12")
        k2.full_clean()
        k2.save()
        k3 = Keyword(word="thing")
        k3.full_clean()
        k3.save()
        # Add them to the job (which was already saved)
        self.job_user_A_project_A.keywords.add(k1)
        self.job_user_A_project_A.keywords.add(k2)
        self.job_user_A_project_A.keywords.add(k2)
        # Check that the keyword association also worked in the DB
        retrieved_obj = Job.objects.get(
            job_id=self.job_user_A_project_A.job_id)
        keyword_of_retrieved = retrieved_obj.keywords.all()
        self.assertIn(k1, keyword_of_retrieved)
        self.assertIn(k2, keyword_of_retrieved)
        self.assertIn(k2, keyword_of_retrieved)

    def test_automatic_association_of_keywords_pre_saved_job(self):
        self.logger.info(
            "Testing automatic association of keywords from"
            " keywords string with (previously saved) job during save")
        # Before save is called, there should not be any keyword associated
        retrieved_job = Job.objects.get(
            job_id=self.job_user_A_project_A.job_id)
        self.assertEqual(retrieved_job.keywords.count(), 0)
        # No keywords should be in the DB at all
        self.assertEqual(Keyword.objects.count(), 0)
        # Saving the job
        retrieved_job.save()
        # Each expected word should have a corresponding keyword in the DB
        keywords_from_db = Keyword.objects.all()
        words_from_db = [keyword.word for keyword in keywords_from_db]
        for word in self.expected_words:
            self.assertIn(word, words_from_db)
        # Grabbing the new object from the DB
        again_retrieved_job = Job.objects.get(job_id=retrieved_job.job_id)
        # Each keyword should be associated with the Job
        associated_keywords_from_job = again_retrieved_job.keywords.all()
        for keyword in keywords_from_db:
            self.assertIn(keyword,
                          associated_keywords_from_job)

    def test_automatic_association_of_keywords_w_new_job(self):
        self.logger.info("Testing automatic association of keywords from"
                         " keywords string with new job during save")
        # No keywords should be in the DB at all
        self.assertEqual(Keyword.objects.count(), 0)
        # Creating a new job
        new_job = Job(
            job_id=456,
            user=self.user_A,
            project=self.project_A,
            main_name="totally_different_description.key",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_PENDING
        )
        # Before save is called there should be no keyword associated
        self.assertEqual(new_job.keywords.count(), 0)
        # Saving the job
        new_job.full_clean()
        new_job.save()
        new_expected_words = ["totally", "different", "description", "key"]
        # Each expected word should have a corresponding keyword in the DB
        keywords_from_db = Keyword.objects.all()
        words_from_db = [keyword.word for keyword in keywords_from_db]
        for word in new_expected_words:
            self.assertIn(word, words_from_db)
        # Each keyword should be associated with the Job
        new_retrieved_job = Job.objects.get(job_id=new_job.job_id)
        associated_keywords_from_job = new_retrieved_job.keywords.all()
        for keyword in keywords_from_db:
            self.assertIn(keyword,
                          associated_keywords_from_job)


class TestAddBaseRuns(TestCase):
    """
    Tests for add_base_runs method of the Job model
    """

    logger = logger.getChild("TestAddBaseRuns")

    def setUp(self):
        self.user_A = User.objects.create(
            username="usera", email="usera@example.com")

        self.project_A = "3001234"

        self.base_run_1 = Job(
            job_id=123,
            main_name="main_first_base.key",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_FINISHED,
            project=self.project_A,
            user=self.user_A
        )
        self.base_run_1.full_clean()
        self.base_run_1.save()

        self.base_run_2 = Job(
            job_id=321,
            main_name="main_second_base.key",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_FINISHED,
            project=self.project_A,
            user=self.user_A
        )
        self.base_run_2.full_clean()
        self.base_run_2.save()

        self.new_run = Job(
            job_id=456,
            main_name="main_new_model.key",
            sub_dir="/some/not/existing/path",
            job_status=Job.JOB_STATUS_PENDING,
            project=self.project_A,
            user=self.user_A
        )
        self.new_run.full_clean()
        self.new_run.save()

    def test_add_single_base_run(self):
        self.logger.info("Test adding of single base run")
        self.new_run.add_base_runs([self.base_run_1.job_id])
        self.new_run.full_clean()
        self.new_run.save()
        self.assertIn(self.base_run_1, self.new_run.base_runs.all())

    def test_add_two_base_runs(self):
        self.logger.info("Test adding of two base runs")
        self.new_run.add_base_runs(
            [self.base_run_1.job_id, self.base_run_2.job_id])
        self.new_run.full_clean()
        self.new_run.save()
        self.assertIn(self.base_run_1, self.new_run.base_runs.all())
        self.assertIn(self.base_run_2, self.new_run.base_runs.all())

    def test_add_not_existing_base_run(self):
        self.logger.info("Test adding of not existing base run")
        non_existing_job_id = 123321123
        self.new_run.add_base_runs([non_existing_job_id])
        self.new_run.full_clean()
        self.new_run.save()
        self.assertNotIn(non_existing_job_id, self.new_run.base_runs.all())


class TestAddUser(TestCase):
    """
    Tests for add_user method of Job model
    """

    def test_add_existing_user(self):
        existing_user = User.objects.create(
            username="testuser",
            email="test.user@example.com",
            first_name="test",
            last_name="user"
        )
        self.assertIn(existing_user, User.objects.all())

        new_job = Job()
        new_job.job_id = 123
        new_job.main_name = "this_is_a_main_name.key"
        new_job.sub_dir = "/some/not/existing/path"
        new_job.job_status = Job.JOB_STATUS_PENDING
        new_job.add_user(
            username=existing_user.username,
            email=existing_user.email
        )
        new_job.full_clean()
        new_job.save()
        self.assertEqual(existing_user, Job.objects.get(job_id=123).user)
        self.assertEqual(
            existing_user.username,
            Job.objects.get(job_id=123).user.username
        )
        self.assertEqual(
            existing_user.email,
            Job.objects.get(job_id=123).user.email
        )
        self.assertEqual(
            "test",
            Job.objects.get(job_id=123).user.first_name
        )
        self.assertEqual(
            "user",
            Job.objects.get(job_id=123).user.last_name
        )

    def test_add_existing_user_but_different_email(self):
        existing_user = User.objects.create(
            username="testuser",
            email="test.user@example.com"
        )
        self.assertIn(existing_user, User.objects.all())

        new_job = Job()
        new_job.job_id = 123
        new_job.main_name = "this_is_a_main_name.key"
        new_job.sub_dir="/some/not/existing/path"
        new_job.job_status = Job.JOB_STATUS_PENDING
        new_job.add_user(
            username=existing_user.username,
            email="some.other@example.com"
        )
        new_job.full_clean()
        new_job.save()
        self.assertEqual(existing_user, Job.objects.get(job_id=123).user)
        self.assertEqual(
            existing_user.username,
            Job.objects.get(job_id=123).user.username
        )
        self.assertEqual(
            existing_user.email,
            Job.objects.get(job_id=123).user.email
        )

    def test_create_user_while_adding(self):
        new_job = Job()
        new_job.job_id = 123
        new_job.main_name = "this_is_a_main_name.key"
        new_job.sub_dir ="/some/not/existing/path",
        new_job.job_status = Job.JOB_STATUS_PENDING
        new_job.add_user(
            username="testuser",
            email="test.user@example.com"
        )
        new_job.full_clean()
        new_job.save()
        self.assertEqual(
            "testuser",
            Job.objects.get(job_id=123).user.username
        )
        self.assertEqual(
            "test.user@example.com",
            Job.objects.get(job_id=123).user.email
        )
        self.assertEqual(
            "test",
            Job.objects.get(job_id=123).user.first_name
        )
        self.assertEqual(
            "user",
            Job.objects.get(job_id=123).user.last_name
        )


class TestProjectExtractionFromSubDir(TestCase):
    """
    Testing the automatic extraction of the project from the sub_dir during
    save.
    """

    logger = logger.getChild("TestProjectExtractionFromSubDir")

    def setUp(self):
        self.user_A = User.objects.create(
            username="usera", email="usera@example.com")

    def test_project_from_subdir(self):
        job = Job()
        job.job_id = 123
        job.main_name = "main_of_job.key"
        job.sub_dir = "/W04_prj/3001234/04/model/calc/somthing"
        job.user = self.user_A
        job.job_status = Job.JOB_STATUS_PENDING
        job.full_clean()
        job.save()
        self.assertEqual(Job.objects.get(job_id=123).project, "3001234")

