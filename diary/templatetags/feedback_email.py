from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def get_feedback_email():
    """
    Get feedback email from the secrets file

    To not write the email address to which support mails are supposed to be
    directed at, into the code (which might be public some day), it is defined
    in the secrets config file.

    This template tag allows to show the email address on the website.

    Returns
    -------
    str
        Email address for feedback
    """

    return settings.FEEDBACK_RECIPIENT_EMAIL
