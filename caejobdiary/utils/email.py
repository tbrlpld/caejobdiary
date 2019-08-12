"""
Utility functions regarding emails
"""

import os
import sys
import re
import logging
import logging.config

import django

from django.conf import settings


def get_name_from_email(email):
    """
    Extract first and last name from an email address.

    Expected format of the email address is `first_name.last_name@example.com`.
    The function returns two values. The first name and the last name.
    If the function fails to extract both from the email, both returns will be
    empty.

    Parameters
    ----------
    email : str
        Email address to extract the first name and last name from

    Return
    ------
    str
        First name extracted from the email address
    str
        Last name extracted from the email address
    """
    first_name = ""
    last_name = ""

    email_before_at = email.split("@")[0]
    email_before_at_split = email_before_at.split(".")
    if len(email_before_at_split) > 1:
        possible_first_name = email_before_at_split[0]
        possible_last_name = email_before_at_split[1]

        # Only if both name parts are found, set the return values
        if possible_first_name and possible_last_name:
            first_name = possible_first_name
            last_name = possible_last_name

    return first_name, last_name
