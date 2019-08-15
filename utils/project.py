"""
Utility functions regarding project numbers
"""

import os
import sys
import re
import logging
import logging.config

import django

from django.conf import settings


def get_project_from_path(path):
    """
    Get project number/identifier from path

    Parameters
    ----------
    path : str
        Path like object from which the project number/identifier should be
        derived.

    Returns
    -------
    str: Project number/identifier as string. Default return, if nothing was
    found is the empty string.
    """
    logger = logging.getLogger(__name__)

    project = ""

    split_path = path.split("/")

    for counter, directory in enumerate(split_path):
        logger.debug(str(counter) + ": " + str(directory))
        if is_project_identifier(directory) and (
                "_pcae_" in split_path[counter-1]
                or "_prj" in split_path[counter-1]):
            project = directory

    return project


def is_project_identifier(input_string):
    """
    Determine if input matches pattern for project identifiers

    Parameters
    ----------
    input : str
        String to be checked if it matches the project identifier pattern.

    Returns
    -------
    boolean
        True if the input matches the project identifier pattern, False
        otherwise.
    """

    # Making sure the input is string, by converting it
    input_string = str(input_string)

    # Defining the pattern
    project_pattern = re.compile(
        "^[\drq]{1}[\d]{6}(v[\d]{2})?$"
    )

    # Checking the pattern match
    if project_pattern.match(input_string):
        return True
    else:
        return False
