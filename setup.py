from distutils.core import setup

# Get requirements
requirements = [line.strip() for line in open("requirements.txt").readlines()]

setup(
    name="CAEJobDiary",
    version="1.1.0",
    author="Tibor Leupold",
    author_email="tibor@lpld.io",
    packages=[
        "caejobdiary",
        "caejobdiary.caejobdiary",
        "caejobdiary.caejobdiary.settings",
        "caejobdiary.diary",
        "caejobdiary.diary.migrations",
        "caejobdiary.diary.templatetags",
        "caejobdiary.utils",
        "caejobdiary.utils.jobinfo",
        "caejobdiary.utils.caefileio",
    ],
    scripts=["bin/caejd.py"],
    url="https://gitlab.com/tbrlpld/CAEJobDiary",
    license="LICENSE.txt",
    description="Web application to search, track and summarise simulation jobs",
    long_description=open("README.md").read(),
    install_requires=requirements,
)
