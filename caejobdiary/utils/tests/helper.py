"""
Helper Functions for Testing
"""

import logging
import os
import tempfile


def add_content_to_temp_inputfilepath(func):
    """
    Define content for an inputfilepath to a function

    The given function should have expect a filepath as input. When that
    function is decorated with this decorator, the content of that filepath
    can be defined. The content is stored in a temporary file and the path
    to the temporary file is used as input for the original function.
    """

    def wrapper(content):
        with tempfile.NamedTemporaryFile(mode="w") as tf:
            # logging.debug("Tempfile name : {}".format(tf.name))

            with open(tf.name, "w") as f:
                # logging.debug("Writing content to tempfile.")
                # logging.debug("Content : {}".format(content))
                f.write(content)

            # Wrapper returns the return of the original function, when the
            # original function is applied to the temporary file
            return func(tf.name)

    return wrapper


def make_readme(job_dir, job_id, sub_dir, username, email, base_runs_str,
                main_name):
    """
    Create a job readme file in the given directory with the passed values

    Returns
    -------
    str, str
        Filename and filepath of the created readme
    """
    logger = logging.getLogger("testing_control")

    logger.debug("Making readme file...")
    readme_content="""
README for {main_name}
base-run (job-id): {base_run}
information      :
Some info text

********Header********
SOLVERVER: mpp.s.R9.1.0.113698.113698_dmp_sp
******Environment******
Sub-User:   {username}
EMail:      {email}
Sub-Date:   2018-06-07__17:21:21
Solver:     dyn
SubDir:     {sub_dir}
FILE:       {main_name}
JOBID:      {job_id}
""".format(username=username,
           email=email,
           sub_dir=sub_dir,
           job_id=str(job_id),
           base_run=base_runs_str,
           main_name=main_name)
    logger.debug(readme_content)

    readme_filename = "README.{main_name}.README".format(main_name=main_name)
    readme_filepath = os.path.join(job_dir, readme_filename)
    with open(readme_filepath, mode="w") as f:
        f.write(readme_content)

    return readme_filename, readme_filepath


def make_cluster_script(job_id, sub_dir, scratch_dir):
    """Create a cluster script for the job id in the sub dir to the scratch dir

    Parameters
    ----------
    job_id : int
        Job id of the job to create the cluster script for
    sub_dir : str
        Path of the directory where the cluster script should be written to
    scratch_dir : dir
        Path of the directory that is supposed to be contained in the cluster
        script. This is essentially the job_dir of a running job.
    """
    cluster_script_filename = str(job_id) + ".dyn-dmp.l01cl012.16.sh"
    cluster_script_content = "cd {}*".format(scratch_dir)
    with open(os.path.join(sub_dir, cluster_script_filename), "w") as f:
        f.write(cluster_script_content)
