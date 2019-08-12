"""
Functions regarding joblogfiles

The joblogfiles are the files that are created in a central directory when a
job is submitted. A joblogfile might be `2010-01-02__12:34:56-1234567.log`.
The name does contain a datetime and the `job_id`. The datetime in the name can
be different from the `submission_time` given inside the file itself.

Joblogfiles contain some basic administrative information about the
submitted job. Their content is not really interesting to the end user.
These files are a central source of information about new jobs though.

Information of interest to gather from the joblogfile is the `job_id` (which is
called `job_number` in the joblogfile) and the `sub_dir` (sge_o_workdir).

Other information might be gathered when of interest.

Joblogfiles contain their information in colon-separated key-value pairs.
"""

import logging
import os
import re

from datetime import datetime

from .keyvaluefile import get_value_string_from_line


# -----------------------------------------------------------------------------
def is_joblogfilename(filepath):
    """
    Check if passed filename matches naming pattern for job log files.

    Parameters
    ----------
    filepath : str
        Filepath of the file to check

    Returns
    -------
    boolean
        boolean expressing if passed joblogfilename matches (True) pattern
        or not (False)
    """

    basename = os.path.basename(filepath)
    # module_logger.debug("basename : {}".format(basename))

    # Log file name have names like this: 2010-01-02__12:34:56-1234567.log
    joblogfilename_pattern = re.compile(
        "^[\d]{4}-[\d]{2}-[\d]{2}__[\d]{2}:[\d]{2}:[\d]{2}-\d+\.log$"
    )
    if joblogfilename_pattern.match(basename):
        # module_logger.debug("basename {} matched {}".format(basename, joblogfilename_pattern))
        return True
    else:
        return False


# -----------------------------------------------------------------------------
def get_job_info_from_joblogfile(joblogfile):
    """
    Get job_id and sub_dir from joblogfile

    joblogfiles expected as input are plain text files.
    In the joblogfile the job_id is called `job_number` followed by a
    colon (`:`) and some whitespace. The sub_dir is called `sge_o_workdir`.

    job_id has to able to be converted to integer. Otherwise the respective
    return will be None.

    If `submission_time` entry is found in joblogfile, it is returned as a
    datetime object. Otherwise it will be None

    Parameters
    ----------
    joblogfile : str
        Filepath of the joblogfile to be processed for job information

    Returns
    -------
    job_id : int or None
        Integer job_id if found, else None
    sub_dir : str or None
        Directory path where the job was submitted if found, else None
    log_date : datetime or None
        Datetime of the time in listed in the joblog file,
        or None if not found.
    """

    logger = logging.getLogger(__name__).getChild(
        "get_job_info_from_joblogfile")

    logger.info("Getting job info from joblogfile: {}".format(joblogfile))

    job_id = None
    sub_dir = None
    log_date = None

    with open(joblogfile, "r", encoding='UTF-8', errors='ignore') as f:
        for line in f:
            if "job_number" in line:
                logger.debug("job_number found in joblogfile.")
                try:
                    job_id = int(line.split(":")[-1].strip())
                except ValueError as err_msg:
                    logger.error(str(err_msg)
                                 + " Job ID is not an integer.")
            if "sge_o_workdir" in line:
                logger.debug("sge_o_workdir found in joblogfile.")
                sge_o_workdir = line.split(":")[-1].strip()
                if sge_o_workdir:
                    sub_dir = sge_o_workdir
            if "submission_time" in line:
                logger.debug("submission_time found in joblogfile.")
                log_date_string = get_value_string_from_line(line)
                # Fri Jul 27 08:28:38 2018
                format_string = "%a %b %d %H:%M:%S %Y"
                # Convert date string into datetime object
                try:
                    log_date = datetime.strptime(
                        log_date_string, format_string)
                except ValueError as err_msg:
                    logger.debug(str(err_msg) + ". Date does not match"
                                 + " expected format.")
                logger.debug("log_date: {}".format(log_date))
        if not job_id and not sub_dir:
            f.seek(0)
            content = f.read()
            logger.warning(
                "No relevant content in joblogfile {}!".format(joblogfile)
                + " Here is the content for examination: \n{}".format(content))

    logger.info("Job info from joblogfile : "
                "job_id: {}, sub_dir: {}, log_date: {}".format(
                    job_id, sub_dir, log_date))

    return job_id, sub_dir, log_date
