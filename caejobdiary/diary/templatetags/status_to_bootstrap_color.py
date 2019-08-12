from django import template

from diary.models import Job

register = template.Library()


@register.simple_tag
def job_status_to_color(status):
    """
    Return bootstrap color string to represent a certain job status

    Parameters
    ----------
    status : str
        String representing the job status.

    Returns
    -------
    str
        Bootstrap color name
    """
    status_to_color_map = {
        Job.JOB_STATUS_PENDING: "primary",
        Job.JOB_STATUS_RUNNING: "secondary",
        Job.JOB_STATUS_FINISHED: "info",
        Job.JOB_STATUS_NORMAL_TERMINATION: "success",
        Job.JOB_STATUS_ERROR_TERMINATION: "danger",
        Job.JOB_STATUS_OTHER_TERMINATION: "warning",
        Job.JOB_STATUS_NONE: "light"
    }
    return status_to_color_map.get(status, "dark")


@register.simple_tag
def analysis_status_to_color(status):
    """
    Return bootstrap color string to represent a certain analysis status

    Parameters
    ----------
    status : str
        String representing the analysis status.

    Returns
    -------
    str
        Bootstrap color name
    """
    status_to_color_map = {
        Job.ANALYSIS_STATUS_OPEN: "primary",
        Job.ANALYSIS_STATUS_ONGOING: "secondary",
        Job.ANALYSIS_STATUS_DONE: "success"
    }
    return status_to_color_map.get(status, "dark")


@register.simple_tag
def result_assessment_to_color(status):
    """
    Return bootstrap color string to represent a certain result assessment

    Parameters
    ----------
    status : str
        String representing the analysis assessment.

    Returns
    -------
    str
        Bootstrap color name
    """
    status_to_color_map = {
        Job.RESULT_ASSESSMENT_OK: "success",
        Job.RESULT_ASSESSMENT_NOK: "danger",
        Job.RESULT_ASSESSMENT_OTHER: "info",
        Job.RESULT_ASSESSMENT_ISSUE: "warning",
        Job.RESULT_ASSESSMENT_OBSOLETE: "light"
    }
    return status_to_color_map.get(status, "dark")
