import logging

from dal import autocomplete
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, TemplateView

from diary.models import Job, Tag
from diary.forms import JobForm


class JobListView(ListView):
    logger = logging.getLogger(__name__)

    # Which model does the view deal with
    model = Job
    # Which template should be used to render the view
    template_name = "diary/joblist.html"
    # Define the name with which the template can reference the queryset
    context_object_name = "jobs_list"

    def dispatch(self, request, *args, **kwargs):
        self.logger.debug("Dispatching JobListView")
        # Write the current querystring to the session. This allows other views
        # to retrieve this information, e.g. to link back to the filtered
        # joblist view
        request.session["joblist_querystring"] = request.GET.urlencode()
        self.logger.debug("Saved querystring: "
                          f"{request.session['joblist_querystring']}")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        self.logger.debug("JobListView.get_queryset called.")

        jobs_list = Job.objects.order_by("-job_id")

        # Exclude obsolete jobs if not otherwise defined per query parameter
        self.show_obsolete = "show_obsolete" in self.request.GET
        self.logger.debug(f"Show obsolete: {self.show_obsolete}")
        if not self.show_obsolete:
            jobs_list = jobs_list.exclude(
                result_assessment=Job.RESULT_ASSESSMENT_OBSOLETE
            )

        # Apply filters if they where defined in the URL
        self.current_project_filter = self.request.GET.get("project")
        self.current_user_filter = self.request.GET.get("user")
        if self.current_project_filter:
            jobs_list = jobs_list.filter(project=self.current_project_filter)
        if self.current_user_filter:
            jobs_list = jobs_list.filter(
                user__username=self.current_user_filter)

        # Apply search query
        self.search_query = self.request.GET.get("q")
        self.logger.debug(f"Search query: {self.search_query}")
        if self.search_query is not None:
            # Stripping whitespaces from string to make whitespace search same
            # as empty one.
            self.search_query = self.search_query.strip()
        # A falsey (empty search) bypasses the actual search
        if self.search_query:
            jobs_list = jobs_list.keyword_search(self.search_query)

        paginated_jobs_list = Paginator(jobs_list, 25)
        page_number = self.request.GET.get("page")
        page_of_jobs = paginated_jobs_list.get_page(page_number)

        return page_of_jobs

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Get all users, but not the superusers
        context["usernames"] = \
            User.objects.all().filter(is_superuser=False).values_list(
                'username', flat=True).distinct().order_by('username')
        context["current_user_filter"] = self.current_user_filter
        # Get list of projects. This needs to be done via the jobs, because
        # there is no project model.
        context["projects"] = Job.objects.exclude(project="").values_list(
            'project', flat=True).distinct().order_by('project')
        context["current_project_filter"] = self.current_project_filter
        # Pass on the used search query
        context["current_search_query"] = self.search_query
        # Pass on the showing of obsolete jobs
        context["show_obsolete"] = self.show_obsolete
        return context


def detail(request, job_id):
    """
    Django view to show detailed information about a job from the DB

    Queries the defined job_id from the database and returns all
    available information rendered in the associated template.

    Parameters
    ----------
    job_id : int
        Job id of the job the detail view is desired for.
    """
    logger = logging.getLogger(__name__)
    logger.debug("detail() function called. Request: {}".format(request))

    if request.method == "POST":
        logger.debug("POST request received.")
        # Grab the job object that corresponds with the id defined in the URL
        job = get_object_or_404(Job, pk=job_id)
        # Map the form info from the request to the Django form instance in
        # python for further usage
        form = JobForm(request.POST, instance=job)
        logger.debug("Form Data: {}".format(form.data))
        logger.debug("Form Errors: {}".format(form.errors))

        if form.is_valid():
            logger.debug("Form is valid")
            logger.debug("Cleaned Data: {}".format(form.cleaned_data))
            logger.debug("getlist('tags'): {}".format(
                request.POST.getlist("tags")))
            form.save()
            # Define session value for update success
            logger.debug(f"Job update successful! Defining session parameter.")
            request.session["update_success"] = True

            return HttpResponseRedirect(
                reverse("diary:detail", kwargs={"job_id": job_id}))
        else:
            # In case of a form error, continue similarly as with the GET
            # request. The form contains its errors and they can be displayed.
            logger.debug("Form errors occurred: {}".format(form.errors))

    else:
        # In case of a GET request just create the form with already existing
        # data
        job = get_object_or_404(Job, pk=job_id)
        form = JobForm(instance=job)

    # Check if the form has been used successfully to update the Job
    update_success = request.session.pop("update_success", False)
    logger.debug(f"Update successful: {update_success}")

    context = {
        "job": job,
        "form": form,
        "update_success": update_success,
        "joblist_querystring": request.session.get("joblist_querystring", None)
    }
    return render(request, "diary/detail.html", context)


class AboutView(TemplateView):
    template_name = "diary/about.html"


class TagAutocomplete(autocomplete.Select2QuerySetView):
    """
    View to return a queryset to build a autocomplete of existing tags.

    This will be used in the widget to create, update and delete tags in the
    job form.
    """
    logger = logging.getLogger(__name__).getChild("TagAutocomplete")

    def get_queryset(self):
        self.logger.debug("Building the queryset")
        queryset = Tag.objects.all()

        # If there is a query defined, limit the query to tags starting with
        # the given query
        if self.q:
            queryset = queryset.filter(tag__istartswith=self.q)

        return queryset

    def has_add_permission(self, request):
        """
        Overriding the normal check for user permission, because there are no
        users as of now. This gives everybody the right to create new tags,
        which is usually limited to registered staff users.
        """
        return True
