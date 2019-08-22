"""
Module defining the forms for the CAE Job Diary application.
"""
from django.forms import ModelForm

from .models import Job


class JobForm(ModelForm):
    class Meta:
        model = Job
        fields = [
            "job_status",
            "info",
            "analysis_status",
            "result_assessment",
            "result_summary",
            "tags"
        ]
