from django.urls import path, re_path

from . import views

app_name = "diary"
urlpatterns = [
    path("<int:job_id>/", views.detail, name="detail"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("", views.JobListView.as_view(), name="joblist"),
    re_path(
        r"^tag-autocomplete/$",
        views.TagAutocomplete.as_view(create_field="tag"),
        name="tag-autocomplete"
    )
]
