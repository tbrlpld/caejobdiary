"""
Module defining the forms for the CAE Job Diary application.
"""
from dal import autocomplete
from django import forms

from .models import Job, Tag


class JobForm(forms.ModelForm):

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
        widgets = {
            "tags": autocomplete.ModelSelect2Multiple(
                url="diary:tag-autocomplete",
                attrs={
                    "form": "detail-form",
                    # "class": "form-control",
                    # "style": "border: 1px solid #ced4da !important; border-radius: .25rem !important;",
                },
            ),
        }
