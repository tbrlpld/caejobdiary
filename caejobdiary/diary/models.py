from datetime import datetime, date
import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from django.db import models, IntegrityError
from django.db.models import Q
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from utils.email import get_name_from_email
from utils.project import get_project_from_path


class Keyword(models.Model):
    """
    Simple model to store keywords to aid search for a Job
    """
    word = models.CharField(
        unique=True,
        max_length=200,
        db_index=True
    )

    def __str__(self):
        return self.word


class JobQuerySet(models.QuerySet):
    """
    Defines additional methods that can applied on Job querysets.
    """
    logger = logging.getLogger(__name__)

    def keyword_search(self, search_query):
        """
        Get QuerySet of Jobs for which all words of the search query are
        found in the keyword associations.

        If the search is conducted for an empty search term, no results
        should be presented. This is not a filter. It is a search.
        It might act like a filter most of the time, but this is the
        difference. If you search for nothing you will find nothing.
        If you search for something, you till find something, given that it
        can be found/exists.
        """
        self.logger.debug("Search query: {}".format(search_query))
        if search_query.strip():
            for word in search_query.split():
                self = self.filter(keywords__word__istartswith=word).distinct()
        else:
            self = self.none()
        return self


class Job(models.Model):
    logger = logging.getLogger(__name__).getChild("Job")

    objects = JobQuerySet.as_manager()

    job_id = models.PositiveIntegerField(primary_key=True)

    main_name = models.CharField(
        max_length=200,
        blank=False,
    )

    @property
    def _keyword_parsed_main_name(self):
        """
        Return string of the parsed `main_name` of the job

        The returned string should only contain whitespace separated words
        that are considered useful e.g. to search for this job.
        """
        # Remove last dot
        # Inspired by https://stackoverflow.com/a/2556252
        split_at_last_dot = str(self.main_name).rsplit(".", 1)
        last_dot_replaced = " ".join(split_at_last_dot)
        stripped_underscore = last_dot_replaced.replace("_", " ")
        return stripped_underscore

    JOB_STATUS_NONE = "non"
    JOB_STATUS_PENDING = "pen"
    JOB_STATUS_RUNNING = "run"
    JOB_STATUS_FINISHED = "fin"
    JOB_STATUS_NORMAL_TERMINATION = "nor"
    JOB_STATUS_ERROR_TERMINATION = "err"
    JOB_STATUS_OTHER_TERMINATION = "oth"
    JOB_STATUS_CHOICES = (
        (JOB_STATUS_NONE, "none / undefined"),
        (JOB_STATUS_PENDING, "pending"),
        (JOB_STATUS_RUNNING, "running"),
        (JOB_STATUS_FINISHED, "finished"),
        (JOB_STATUS_NORMAL_TERMINATION, "normal termination"),
        (JOB_STATUS_ERROR_TERMINATION, "error termination"),
        (JOB_STATUS_OTHER_TERMINATION, "other termination"),
    )
    job_status = models.CharField(
        max_length=3,
        choices=JOB_STATUS_CHOICES,
        blank=False
    )

    @property
    def _keyword_parsed_job_status(self):
        status_string = self.get_job_status_display()
        status_string = status_string.replace("/", "")
        return " ".join(status_string.split())

    job_dir = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    sub_date = models.DateTimeField(
        default=timezone.now,
        blank=True
    )

    @property
    def sub_date_isostring(self):
        sub_date_date = date(
            year=self.sub_date.year,
            month=self.sub_date.month,
            day=self.sub_date.day,
        )
        return sub_date_date.isoformat()

    sub_dir = models.CharField(
        max_length=500,
        blank=False,
    )

    @property
    def _keyword_parsed_sub_dir(self):
        """
        Return parsed `sub_dir` string

        The parsing replaced the directory separating slashes `/`. Also, each
        folder name is contained once without out further modification and once
        each word of the folder names (words are separated by underscores) is
        contained in the `_keyword_parsed_sub_dir`.
        """
        split_at_slashes = self.sub_dir.split("/")
        parsed_words = set()
        for folder_name in split_at_slashes:
            parsed_words.add(folder_name)
            if "_" in folder_name:
                for word in folder_name.split("_"):
                    parsed_words.add(word)
        return " ".join(parsed_words)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    project = models.CharField(
        max_length=10,
        blank=True,
        null=True
    )

    solver = models.CharField(
        max_length=10,
        blank=True
    )

    logfile_path = models.CharField(
        max_length=200,
        blank=True
    )

    readme_filename = models.CharField(
        max_length=200,
        blank=True
    )

    # -------------------------------------------------------------------------
    # User information, open for editing
    # -------------------------------------------------------------------------
    info = models.TextField(
        blank=True,
    )

    # A job can have many base runs and each job can be a base run of many jobs
    # -> Many to many
    base_runs = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False
        # null=True
    )

    ANALYSIS_STATUS_OPEN = "opn"
    ANALYSIS_STATUS_ONGOING = "ong"
    ANALYSIS_STATUS_DONE = "don"
    ANALYSIS_STATUS_CHOICES = (
        (ANALYSIS_STATUS_OPEN, "open"),
        (ANALYSIS_STATUS_ONGOING, "ongoing"),
        (ANALYSIS_STATUS_DONE, "done"),
    )
    analysis_status = models.CharField(
        max_length=3,
        choices=ANALYSIS_STATUS_CHOICES,
        blank=False,
        default=ANALYSIS_STATUS_OPEN
    )

    RESULT_ASSESSMENT_OK = "ok"
    RESULT_ASSESSMENT_NOK = "nok"
    RESULT_ASSESSMENT_OTHER = "oth"
    RESULT_ASSESSMENT_ISSUE = "isu"
    RESULT_ASSESSMENT_OBSOLETE = "obs"
    RESULT_ASSESSMENT_CHOICES = (
        (RESULT_ASSESSMENT_OK, "ok"),
        (RESULT_ASSESSMENT_NOK, "not ok"),
        (RESULT_ASSESSMENT_OTHER, "other"),
        (RESULT_ASSESSMENT_ISSUE, "issue"),
        (RESULT_ASSESSMENT_OBSOLETE, "obsolete"),
    )
    result_assessment = models.CharField(
        max_length=3,
        choices=RESULT_ASSESSMENT_CHOICES,
        blank=True
    )

    @property
    def _keyword_parsed_result_assessment(self):
        """
        Return keyword parsed result assessment

        The parsing adds the abbreviated form `nok` for to the `not ok`
        assessment display string. This is, because that is a common form and
        should allow the job to be search with one word instead of two.
        """
        display_string = self.get_result_assessment_display()
        if display_string == "not ok":
            display_string += " nok"
        return display_string

    result_summary = models.TextField(
        blank=True,
    )

    # -------------------------------------------------------------------------
    # Database/Admin info
    # -------------------------------------------------------------------------
    created = models.DateTimeField(
        default=timezone.now,
    )

    updated = models.DateTimeField(
        default=timezone.now,
    )

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------
    @staticmethod
    def _keyword_parse_fulltext(fulltext_string):
        """
        Return parsed version of input string

        Some fields (like `info` or `result_summary`) might contain longer
        texts with full sentences. The punctuation of these "fulltext" fields
        should be ignored during search.
        This functions can be used to parse these fulltext fields to make them
        more useful for search. The punctuation `()[]{}!?,."':;-_`
        in the beginning or end of a word is removed.

        Punctuation in the middle of a word is maintained. Words are separated
        by spaces " ".

        The returned string will only contain each word once. Duplicates are
        removed.

        This is implemented as a static method so that it will not receive an
        implicit first argument (`self`). This is important when the function
        is called inside the class via `self._keyword_parse_fulltext(args)`.
        See: https://docs.python.org/3.7/library/functions.html?highlight=stat
        icmethod#staticmethod
        """
        parsed_words = set()
        for word in fulltext_string.split():
            parsed_words.add(word.strip("()[]\{\}!?,.\"':;-_"))
        return " ".join(parsed_words)

    def _build_keyword_string(self):
        """
        Build a string of unique keywords describing the job

        The returned string contains whitespace separated words that help
        identify the job, e.g. to make it searchable.
        """
        unique_keywords = set()
        unique_keywords.add(str(self.job_id))
        unique_keywords.add(self.main_name)
        for word in self._keyword_parsed_main_name.split():
            unique_keywords.add(word)
        if self.user:
            unique_keywords.add(self.user.username)
        if self.project:
            unique_keywords.add(self.project)
        for word in self._keyword_parsed_sub_dir.split():
            unique_keywords.add(word)
        for word in self._keyword_parse_fulltext(self.info).split():
            unique_keywords.add(word)
        for word in self._keyword_parse_fulltext(self.result_summary).split():
            unique_keywords.add(word)
        for word in self._keyword_parsed_job_status.split():
            unique_keywords.add(word)
        unique_keywords.add(self.get_analysis_status_display())
        for word in self._keyword_parsed_result_assessment.split():
            unique_keywords.add(word)
        unique_keywords.add(self.sub_date_isostring)
        return " ".join(unique_keywords)

    keyword_string = models.TextField(
        blank=True,
    )

    def _update_keyword_association_with_string(self):
        """
        Update the keyword associations with the word in the keyword_string

        For words that are in the `keyword_string` but do not have a keyword
        that represents them in the many-to-many field `keywords`, a keyword
        association is created.

        The other way around, keyword associations that do not represent a word
        in the `keyword_string` are removed.

        Returns:
        --------
        list of Keyword objects
            Keyword objects to which an association was added to the Job.
        list of Keyword objects
            Keyword objects to the association to the Job was removed.
        """
        words_from_associated_keywords = set([
            keyword.word for keyword in self.keywords.all()])
        words_from_string = set(self.keyword_string.split())
        # Words that are in the string but are not represented by a keyword yet
        new_word_from_string = words_from_string.difference(
            words_from_associated_keywords)
        # Words that have associated keywords but are not in the string anymore
        removed_keyword_words = words_from_associated_keywords.difference(
            words_from_string)

        added_keywords = []
        max_word_length = Keyword._meta.get_field('word').max_length
        for word in new_word_from_string:
            word = (word[0:max_word_length] if len(word) > max_word_length
                    else word)  # Trim long words
            keyword, created = Keyword.objects.get_or_create(word=word)
            if created:
                keyword.full_clean()
                keyword.save()
            self.keywords.add(keyword)
            added_keywords.append(keyword)

        removed_keywords = []
        for word in removed_keyword_words:
            keyword = self.keywords.get(word=word)
            self.keywords.remove(keyword)
            removed_keywords.append(keyword)
        return added_keywords, removed_keywords

    keywords = models.ManyToManyField(Keyword)

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------
    def __str__(self):
        return "{id}".format(
            id=self.job_id,
        )

    def __iter__(self):
        for field in self._meta.get_fields():
            fieldname = field.name
            value = None
            # If a special display method for the field exists,
            # the use that. Otherwise just take the attrubites value.
            if hasattr(self, "get_" + fieldname + "_display"):
                display_method = getattr(self, "get_" + fieldname + "_display")
                value = display_method()
            elif field.get_internal_type() == 'ManyToManyField':
                if hasattr(self, fieldname):
                    value = getattr(self, fieldname, None).all()
            else:
                value = getattr(self, fieldname, None)

            yield (fieldname, value)

    def save(self, *args, **kwargs):
        """
        Custom save to update the `updated` time on save.

        According to this thread, the original functions (auto_now and
        auto_now_add) do not work that well:
        https://stackoverflow.com/questions/1737017/
        django-auto-now-and-auto-now-add#1737078

        This topic is also discussed in this Django ticket:
        https://code.djangoproject.com/ticket/22995
        """
        self.keyword_string = self._build_keyword_string()
        self.updated = timezone.now()
        if not self.project:
            self.project = get_project_from_path(str(self.sub_dir))
        # You need a primary key to associate objects over many-to-many
        # relations. Usually that means that the object creating the
        # association needs to be saved beforehand. This is not necessary
        # here, I guess because the job_id is used as the primary key.
        # See https://docs.djangoproject.com/en/2.2/topics/db/examples/
        # many_to_many/
        self._update_keyword_association_with_string()
        return super(Job, self).save(*args, **kwargs)

    def add_base_runs(self, base_runs_list):
        """
        Add base runs (defined by job_id) to the job.

        Parameters
        ----------
        base_runs_list : list
            list of job ids of the base runs to be added
        """
        logger = logging.getLogger(__name__)

        for base_run_id in base_runs_list:
            try:
                base_run_obj = Job.objects.get(job_id=base_run_id)
            except ObjectDoesNotExist:
                logger.debug("No job_id {} in DB. Can't add base run.".format(
                    base_run_id))
            else:
                logger.debug("Adding base run {} to job {}".format(
                    base_run_id, self.job_id))
                self.base_runs.add(base_run_obj)

    def add_user(self, username, email):
        """
        Add user to job

        User is defined by username and email. If User does not exist in DB,
        the user is created first and then added to the job.

        Parameters
        ----------
        username : str
            Username of the user to be added
        email : str
            Email address of the user to be added
        """

        User = get_user_model()
        try:
            first_name, last_name = get_name_from_email(email)
            user_obj, created = User.objects.get_or_create(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
        except IntegrityError:
            # The user does seem to exist but with a different email or name.
            # The email address is only defined before, in case the user does
            # not exist at all, so that it can be created correctly.
            # Get user based on username only.
            user_obj = User.objects.get(username=username)

        self.user = user_obj

    def get_timezone_aware_datetime(datetime_string):
        """
        Make datetime string timezone aware.

        Based on this: https://stackoverflow.com/questions/8636760/
        parsing-a-datetime-string-into-a-django-datetimefield

        Parameters
        ----------
        datetime_string : str or datetime
            String of datetime object to be turned into a timezone aware
            datetime object.

        Returns
        -------
        Timezone aware datetime object
        """

        # Check if the input is already a datetime object. if not, make it one.
        if isinstance(datetime_string, datetime):
            datetime_string_parsed = datetime_string
        else:
            datetime_string_parsed = parse_datetime(datetime_string)

        # print(datetime_string_parsed)

        # print("Checking if datetime_string is timezone aware.")
        if timezone.is_aware(datetime_string_parsed):
            # print("Yup, it is")
            output = datetime_string_parsed
        else:
            # print("Nope, it is not")
            # print("Making it aware")
            datetime_string_aware = timezone.make_aware(datetime_string_parsed)
            # print("And checking again")
            if timezone.is_aware(datetime_string_aware):
                # print("Yup, now it is")
                output = datetime_string_aware
        return output
