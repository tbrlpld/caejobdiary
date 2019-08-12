"""
Simple script to fill the diary DB with some example data.

To remove all data from the DB: `python manage.py flush`
"""

import os
import sys

import django


# Adding the project directory to the path to make imports of other modules
# of the project possible.
TOP_LEVEL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, TOP_LEVEL_DIR)
DJANGO_PROJECT_DIR = os.path.join(TOP_LEVEL_DIR, "caejobdiary")
sys.path.insert(0, DJANGO_PROJECT_DIR)
print(sys.path)

# Setup Django. This initializes Django and makes the installed apps known.
# It then also trys to import the models from their submodules
django.setup()

# print("POLL_DIR : ")
# print(django.conf.settings.POLL_DIR)

# Once Django is setup, I can either import the models from the module
# from ...diary.models import Job  # this actually does not work
# from diary.models import Job
# or grab them from the installed apps that are known to Django.
# https://docs.djangoproject.com/en/2.1/ref/applications/#django.apps.apps.get_model
Job = django.apps.apps.get_model("diary", "Job")
User = django.contrib.auth.models.User

# -----------------------------------------------------------------------------
#  Main Function
# -----------------------------------------------------------------------------


def populate():
    print("Populating database...")
    print("----------------------")

    print("Adding users...")
    usera = add_user(username="usera", email="usera@example.com")
    userb = add_user(username="userb", email="userb@example.com")
    userc = add_user(username="userc", email="userc@example.com")

    print("Adding jobs...")
    add_job(
        job_id=123,
        main_name="main_sled_simulation.key",
        user=usera,
        sub_dir="/W04_prj/3001234/04/model/calc/something",
        job_status=Job.JOB_STATUS_PENDING,
        sub_date="2011-12-13 14:15",
        info="First sled simulation as a baseline.\n"
             + "Vent variation still to be performed"
    )

    add_job(
        job_id=456,
        main_name="0020_EJM_LC01.key",
        user=userb,
        sub_dir="/mnt/w04_pcae/w04_pcae/w04_pcae_09/w04_pcae_09/3001234/04/"
                + "model/calc/something",
        sub_date="2017-06-24 09:05",
        job_status=Job.JOB_STATUS_NORMAL_TERMINATION,
        analysis_status=Job.ANALYSIS_STATUS_DONE,
        result_assessment=Job.RESULT_ASSESSMENT_OK,
        info="Parameter X was set to 0.53.\n\n"
             + "This was to increase the pressure.",
        result_summary="Pressure was increased as desired.\n"
                       + "Influence on the performance was positive."
    )

    add_job(
        job_id=789,
        main_name="0203_SLD_HF_p1_US-NCAP.pc",
        user=userc,
        sub_dir="/W04_prj/3001234v03/04/model/calc/something",
        sub_date="2011-12-13 14:15",
        job_status=Job.JOB_STATUS_ERROR_TERMINATION,
        analysis_status=Job.ANALYSIS_STATUS_ONGOING,
        result_assessment=Job.RESULT_ASSESSMENT_ISSUE,
        info="Validation variation: t_scale = 1.02",
        result_summary="Got NaN error message. Need to check where this is"
                       + "coming from."
    )

    add_job(
        job_id=1234,
        main_name="001c_lc12-175MPa_m01b_v01a_015.dyn",
        user=usera,
        sub_dir="/mnt/w01_pcae/w01_pcae/w01_pcae_08/q000351/04/model/calc/"
                + "something",
        sub_date="2018-01-04 10:45",
        job_status=Job.JOB_STATUS_RUNNING,
        base_runs=[123],
        info="Checking if the part still holds with increased impact energy."
    )

    add_job(
        job_id=5678,
        main_name="main_relax_IP_PAB_E02.pc",
        user=userb,
        sub_dir="/mnt/w01_pcae/w01_pcae/w01_pcae_07/w01_pcae_07/r000301/04/"
                + "model/calc/something",
        sub_date="2018-01-05 11:45",
        job_status=Job.JOB_STATUS_OTHER_TERMINATION,
        analysis_status=Job.ANALYSIS_STATUS_DONE,
        result_assessment=Job.RESULT_ASSESSMENT_OTHER,
        base_runs=[123, 456],
        info="Increased timestep for faster run time.",
        result_summary="Run time is faster but the mesh does not look good."
                       + " Deeper analysis of the relaxed mesh needed."
    )

    add_job(
        job_id=8901,
        main_name="ABC_R460_XYZ_inflation_20180814.key",
        user=userc,
        sub_dir="/mnt/w01_pcae/w01_pcae/w01_pcae_07/w01_pcae_07/r000301/04/"
                + "model/calc/something",
        job_status=Job.JOB_STATUS_PENDING,
        sub_date="2018-08-02 11:45",
        base_runs=[123, 456],
        info="New XYZ, based on old-new_2"
    )


# -----------------------------------------------------------------------------
#  Adding Functions
# -----------------------------------------------------------------------------


def add_user(username, email):
    user, created = User.objects.get_or_create(
        username=username,
        email=email
    )
    print("- User: {user}, created: {created}".format(
        user=user.username,
        created=created
    ))
    return user


def add_job(
    job_id,
    main_name,
    user,
    sub_date,
    sub_dir,
    base_runs=[],
    job_status=Job.JOB_STATUS_PENDING,
    analysis_status=Job.ANALYSIS_STATUS_OPEN,
    result_assessment="",
    info="This is some basic info text",
    result_summary=""
):

    created = False
    try:
        job = Job.objects.get(job_id=job_id)
    except Job.DoesNotExist:
        job = Job.objects.create(
            job_id=job_id,
            job_status=job_status,
            main_name=main_name,
            sub_dir=sub_dir,
            job_dir=os.path.join(sub_dir, str(job_id)),
            info=info,
            # To define a foreign key relation, you
            # have to pass the actual object of that
            # type.
            user=user,
            sub_date=Job.get_timezone_aware_datetime(sub_date),
            analysis_status=analysis_status,
            result_assessment=result_assessment,
            result_summary=result_summary
        )
        created = True

    job.add_base_runs(base_runs)
    print("- Job: {job}, created: {created}".format(
        job=job.job_id,
        created=created
    ))
    return job


# -----------------------------------------------------------------------------
#  Run
# -----------------------------------------------------------------------------


if __name__ == "__main__":
    print("=" * 80 + "\n")

    populate()
    print("\n" + "=" * 80)
