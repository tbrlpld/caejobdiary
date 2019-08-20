import logging

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, TemplateView

from diary.models import Job
from diary.forms import JobForm


class JobListView(ListView):
    logger = logging.getLogger(__name__)

    # Which model does the view deal with
    model = Job
    # Which template should be used to render the view
    template_name = "diary/joblist.html"
    # Define the name with which the template can reference the queryset
    context_object_name = "jobs_list"

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
    """Django view to show detailed information about a job from the DB

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
        job = get_object_or_404(Job, pk=job_id)
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            logger.debug("Form is valid")
            logger.debug("Tags: {}".format(request.POST.getlist("tags[]")))
            form.save()
            # Define session value for update success
            logger.debug(f"Job update successful! Defining session parameter.")
            request.session["update_success"] = True
        else:
            logger.error(form.errors)

        # If a querystring was present in the POST action URL, this should be
        # passed on the next GET
        querystring = request.GET.urlencode()
        if querystring:
            querystring = "?" + querystring

        return HttpResponseRedirect(
            reverse("diary:detail",
                    kwargs={
                        "job_id": job_id
                    }) + querystring
        )
    else:
        job = get_object_or_404(Job, pk=job_id)
        form = JobForm(instance=job)

        # Check if the form has been used successfully to update the Job
        update_success = request.session.pop("update_success", False)
        logger.debug(f"Update successful: {update_success}")

        context = {
            "job": job,
            "form": form,
            "update_success": update_success
        }
        return render(request, "diary/detail.html", context)


class AboutView(TemplateView):
    template_name = "diary/about.html"
