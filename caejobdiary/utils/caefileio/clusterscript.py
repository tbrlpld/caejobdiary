"""
Functions regarding cluster script files

Cluster script files are the little (typically one-line-scripts) that are
created in the `sub_dir` when the job is running.
The content of the `clusterscript` is typically on one change directory
shell command (e.g. `cd /W04_cluster_scratch/1234*`).

The cluster script filenames are usually something like :
`1234567.dyn-dmp.x99xx123.16.sh`. The name contains the `job_id`, some info
about the solver and the machine where the job is run.
"""

import logging
import re


# -----------------------------------------------------------------------------
def get_cluster_script_from_list(job_id, file_list):
    """
    Get first filename in file_list that is a cluster script for job_id

    Parameters
    ----------
    job_id : int
        job_id that the existence of the cluster script is checked for
    file_list : list
        List of filenames possibly containing the cluster script

    Returns
    -------
    str or None
        First filename fitting the a cluster script name pattern for the given
        job id. If no filename matches, then None
    """

    logger = logging.getLogger(__name__).getChild(
        "get_cluster_script_from_list")
    # logger = logging.getLogger("poll_jobs.get_cluster_script_from_list ")
    logger.info("Checking existence of cluster script"
                + " for job_id {} ".format(job_id))
    logger.debug("Checking file_list: {}".format(file_list))

    # 1234567.dyn-dmp.x99xx123.16.sh
    cluster_script_pattern = re.compile(
        "^"
        + str(job_id)
        + "\.[a-z]{3}-[a-z]{3}\.[a-z][\d]{2}[a-z]{2}[\d]{3}\.[\d]{1,2}\.sh$"
    )
    logger.debug("Regex pattern for cluster scripts: {}".format(
        cluster_script_pattern))

    # If no files matching the pattern is found, the list will be empty,
    # which means False.
    matches = list(filter(cluster_script_pattern.match, file_list))

    if matches:
        logger.info("Found cluster script: {}".format(
            matches[0]))
        return matches[0]
    else:
        logger.info("No cluster script found")
        return None


# -----------------------------------------------------------------------------
def get_cluster_scratch_dir_from_script(cluster_script_filepath):
    """
    Get cluster scratch directory from cluster script

    The cluster scratch directory is where all job data is saved while the job
    is running. This directory also contains the README.

    The cluster script typically only one line with a shell command like:
    `cd /W01_cluster_scratch/1234567*`

    Parameters
    ----------
    cluster_script_filepath : str
        Filepath of the cluster script from which to retrieve the cluster
        scratch directory.

    Returns
    -------
    str or None
        Directory path of the cluster scratch directory found in the script.
        Globbing is applied to the string. So the directory should exist.
        If no directory is found, return is None
    """

    logger = logging.getLogger(__name__).getChild(
        "get_cluster_scratch_dir_from_script")
    # logger = logging.getLogger("poll_jobs.get_cluster_scratch_dir_from_script")
    logger.info("Getting scratch dir from cluster script: {}".format(
        cluster_script_filepath))

    cluster_scratch_path = None

    try:
        with open(cluster_script_filepath, "r") as f:
            # Reding the first line
            line = f.readline()
    except (FileNotFoundError, PermissionError) as err_msg:
        logger.error(err_msg)
        logger.error("Cluster script not found or no access."
                     " Can not check for cluster scratch dir.")
    else:
        if "cd" in line:
            line_split = line.split(" ")
            if len(line_split) > 1:
                # The strip() is necessary is to remove the trailing newline
                # that is included in the clusterscript files in production.
                cluster_scratch_path = line_split[1].strip()
                if cluster_scratch_path.endswith("*"):
                    cluster_scratch_path = cluster_scratch_path[:-1]

    if cluster_scratch_path:
        logger.info("Cluster scratch directory found: {}".format(
            cluster_scratch_path))
        return cluster_scratch_path
    else:
        logger.info("No cluster scratch directory found")
        return None
