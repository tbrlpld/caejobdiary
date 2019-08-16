"""
Functions regarding job README files

The job README files are stored in the `job_dir` (the directory in which the
model and the result files are available). These README files also contain the
most useful information for the user for identifying a model (e.g. the model
name, a user info comment defined during submission, the base runs, etc.).

The job RADME filename is something like:
`README.0696_OEM_VHIC_SLD_FRB_56_TH_p1_ident_variant_.key.README`.
This is the model name pre- and suffixed by dot-separated `README`.

Job README files contain most of their information in form of colon-separated
key-value pairs.
"""

import logging
import os
import re

from datetime import datetime

from .keyvaluefile import get_value_string_from_line
from utils.logger_copy import copy_logger_settings


# -----------------------------------------------------------------------------
def get_readme_filename_from_job_dir(job_dir):
    """
    Get job's README file from the job_dir

    Parameters
    ----------
    job_dir : str
        Path of directory where the job data is stored

    Returns
    -------
    str or None
        First filename fitting the README name pattern for the given
        job id. If no filename matches, then None
    """

    logger = logging.getLogger(__name__).getChild(
        "get_readme_filename_from_job_dir")
    # logger = logging.getLogger("poll_jobs.get_readme_filename_from_job_dir")
    logger.info("Checking existence of README file"
                + " in job_dir: {}".format(job_dir))

    file_list = os.listdir(job_dir)

    # README.0696_OEM_VHIC_SLD_FRB_56_TH_p1_ident_variant_.key.README
    readme_filename_pattern = re.compile(
        "^README\..*\.README$"
    )
    logger.debug("Regex pattern for README: {}".format(
        readme_filename_pattern))
    matches = list(filter(readme_filename_pattern.match, file_list))
    logger.debug("Possible matches for README files: {}".format(matches))

    if matches:
        logger.info("Found job README file: {}".format(
            matches[0]))
        return matches[0]

    logger.info("No job README found in {}".format(job_dir))
    return None


# -----------------------------------------------------------------------------
def get_job_info_from_readme(readme):
    """
    Get job info from job's README file

    Job README files typically reside inside the job_dir.

    Parameters
    ----------
    readme : str
        Path of the job README file

    Returns
    -------
    dict
        Dictionaty containing the found values for:
        * base_runs : list of integers
        * info_block : str (possibly multiple lines)
        * username : str
        * email : str
        * sub_date : datetime
        * solver : str
        The keys only exist if values were found.
    """

    logger = logging.getLogger(__name__).getChild(
        "get_job_info_from_readme")
    copy_logger_settings(__name__, "utils.caefileio.keyvaluefile")
    logger.info("Getting job info from README: {}".format(
        readme))

    readme_info = {}

    # ISO-8859-1 seems to be the encoding used for the README.
    # If this fails, I will need to figure something else out.
    # E.g. read line by line and catch encoding exceptions and replace
    # line with a warning. Or just replace the character in question.
    with open(readme, "r", encoding="ISO-8859-1") as f:
        readme_lines = f.readlines()
    reading_info_block = False
    info_block = ""

    for line in readme_lines:

        # Get main_name
        if "FILE:" in line:
            logger.debug("Line with 'FILE': {}".format(line))
            readme_info["main_name"] = get_value_string_from_line(line)
            logger.info("main_name found in README: {}".format(readme_info[
                "main_name"]))

        # Get base_runs
        if "base-run (job-id):" in line:
            logger.debug("Line with 'base-run': {}".format(line))
            readme_info["base_runs"] = get_base_runs_from_line(line)
            logger.info("base_runs found in README: {}".format(readme_info[
                "base_runs"]))

        # Get info_block
        if reading_info_block:
            if "********Header********" in line:
                # Once the header line is reached, the info block ends
                reading_info_block = False
                readme_info["info_block"] = info_block.rstrip()
                logger.info("info_block found in README: \n{}".format(
                    readme_info["info_block"]))
            else:
                info_block += line
        if "information      :" in line:
            reading_info_block = True

        # Get username
        if "Sub-User:" in line:
            logger.debug("Line with 'Sub-User': {}".format(line))
            readme_info["username"] = get_value_string_from_line(line)
            logger.info("username found in README: {}".format(
                readme_info["username"]))

        # Get email
        if "EMail:" in line:
            logger.debug("Line with 'EMail': {}".format(line))
            readme_info["email"] = get_value_string_from_line(line)
            logger.info("email found in README: {}".format(
                readme_info["email"]))

        # Get sub_date
        if "Sub-Date:" in line:
            logger.debug("Line with 'Sub-Date': {}".format(line))
            sub_date_string = get_value_string_from_line(line)
            # 2018-01-02__12:34:56
            format_string = "%Y-%m-%d__%H:%M:%S"
            # Convert subdate string into datetime object
            readme_info["sub_date"] = datetime.strptime(
                sub_date_string, format_string)
            logger.info("sub_date found in README: {}".format(
                readme_info["sub_date"]))

        # Get solver
        if "Solver:" in line:
            logger.debug("Line with 'Solver': {}".format(line))
            readme_info["solver"] = get_value_string_from_line(line)
            logger.info("solver found in README: {}".format(
                readme_info["solver"]))

    if readme_info:
        return readme_info
    return None


# -----------------------------------------------------------------------------
def get_base_runs_from_line(line):
    """
    Get base_runs from README line

    The line has to be identified beforehand to contain "base-run (job-id)"
    as key. The value string (the part after the colon) is stripped from any
    non-digit characters. The remaining content is turned into integers that
    are returned in a list

    Parameter
    ---------
    line : str, required
        string to extract the base_runs from

    Returns
    -------
    list
        list of integers
    """
    logger = logging.getLogger(__name__).getChild("get_base_runs_from_line")

    base_runs = []
    base_runs_string = get_value_string_from_line(line)
    logger.debug("base_run_string: {}".format(base_runs_string))
    # Replace non-digit characters in string with space " "
    clean_base_run_string = re.sub("\D", " ", base_runs_string)
    logger.debug("clean_base_run_string: {}".format(
        clean_base_run_string))
    base_runs = [int(num) for num in clean_base_run_string.split()]
    logger.debug("base_runs: {}".format(base_runs))
    return base_runs
