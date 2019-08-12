Version History
===============


v1.0.0 -- 2019-06-25
--------------------

* Redesigned user interface for more consistent and visually pleasing experience.
  * Complete redesign of page with Bootstrap front-end framework for consistent and visually pleasing experience.
  * Info and result are separated more clearly on the job cards in the job list.
  * Job detail page has been designed for consistency with the job card in the list and to make scrolling less necessary. 
  * Contextual colors are applied to the job status, analysis status and result assessment badges. 
  * Detail view shows alerts about unsaved and successfully applied changes.
  * Favicon added for quick recognition of CAE Job Diary tabs in the bowser.


v0.6.0 -- 2019-05-19
--------------------

* Added search feature.
  Find jobs based on keywords used in its description and meta data. 
  E.g. words from the info or summary fields, main name as a whole or split at underscores, 
  job id, job status, ... 
  The search is case-insensitive and matches with beginnings of words, e.g. `SLE` will find jobs
  containing `sled`. 
  The more words are added to the search query, the fewer jobs will be returned, because the all 
  words from the query need to be found in a job for it to be returned.
* "Issue" result assessment added. 
  This is for issues in the simulation model that led to unexpected behavior, 
  but did not cause an error termination. Migration required.
* "Obsolete" result assessment added.
  Obsolete jobs can are hidden from the index unless the query string `?show_obsolete`
  is used in the URI.
* Database password needs to be set in `secrets.json` as `DB_PASSWORD`. 
  The script to create dummy secrets `bin/make_secrets.py` has been adjusted accordingly.
* Minor formatting improvements on index page.
* Added `poll.warn` log file handler, so that all warnings (and up) can easily be found.


v0.5.2 -- 2019-04-15
--------------------

* Explicit sorting of quick filter drop down lists added.
* Allowing `/opt/caejd/config/` as config directory (where the `secrets.json` file lives).


v0.5.1 -- 2019-04-15
--------------------

* Hotfix: defining config directory in production settings


v0.5.0 -- 2019-04-15
--------------------

* Added quick filters for user and project to the index.
* Made process termination react independently from timeouts.
* Missing info in joblogfile triggers warning log showing the file content.
* Minor logging changes for more clarity.


v0.4.0 -- 2019-03-18
--------------------

* Switched index layout from table to list/card to avoid the horizontal scrolling.
* Refactored `readme` module. Error handling moved from `readme` to `poll` module.
* Adjusted mail log handler name according to use case.
* Defined poll and update timeouts as settings.
* Moved `diary.utils` to `utils` module.
* Adjustments of log statements and levels.
* DB connections are closed on typical poll/update loop to prevent the connection from becoming stale.
* Added database section to README.


v0.3.4 -- 2019-02-08
--------------------

* Fixed production settings for use of mysql database


v0.3.3 -- 2019-02-07
--------------------

* Added script to transfer data from sqlite to mysql database


v0.3.2 -- 2019-02-01
--------------------

* Email credentials are not used in site or production settings, when "localhost" is used as email host.


v0.3.1 -- 2019-01-31
--------------------

* Added email logging for above warning logging events.
  Email settings have to be defined in the `secrets.json`.
* Exceptions occurring in the main process trigger an error level email log event.


v0.3.0 -- 2019-01-28
---------------------

* Added one-off run script to start CAEJobDiary processes.
* Created update functionality to check new statuses of unfinished jobs.
* Logging to rotating log files is defined for Django server, polling and update processes
  (no need for `logrotate`).
* Renamed main django project from `cae_job_diary` to `caejobdiary` to comply with PEP 8 naming
  recommendations. This requires to update the environment variable `DJANGO_SETTINGS_MODULE` to
  define the correct settings module.


v0.2.1 -- 2018-11-21
--------------------

* Fixed polling from running into infinite loop on missing rights on `job_dir`.
* Change font family of web site for readability.
* Small changes in poll script (`job_status` check from `sub_dir`) for speed and logic.


v0.2.0 -- 2018-11-21
--------------------

* Added handling for race condition if job status changes during poll processing.
* Rechecking job status from `sub_dir` only for recent jobs (submitted in the last 24h).
* Updated Django from 2.0.7 to 2.0.9 for security reasons.
* Optimized index page for usability.


v0.1.6 -- 2018-10-24
--------------------

* Added envelope icon to repo.


v0.1.4 -- 2018-10-23
--------------------

* Updated feedback modal icons.
* Added exception to poll job.


v0.1.3 -- 2018-10-22
--------------------

* Created feedback modal.


v0.1.1 -- 2018-10-04
--------------------

* Enable offline install.


v0.1.0 -- 2018-10-03
--------------------

* Initial release.
