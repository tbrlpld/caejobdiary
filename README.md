# CAE Job Diary
> Search, track and summarise simulation jobs.
>
> CAE Job Diary is a web application to help staying organized when a lot of jobs need to be handled.
> See which jobs are running, pending or finished. Which jobs still require an analysis? And what was the outcome of that job again? 
>
> CAE Job Diary can help answering these questions. 

CAE Job Diary consists of two main packages. 
First is `diary` this is the Django web application that defines the models and how the user can interact with the application.
The second package is `utils` which defines the backend tools to gather information from the relevant sources and adds them to the database.

The web application `diary` will work fine as long as relevant data is available in the connected database. 
It should be noted, that there is currently no way for the user to create new jobs through the web application. 
The web application is designed to reduce the documentation workload by providing information about submitted jobs automatically.
Thus, the web application expects backend processes to add this information to the database without user interaction.

This is where the `utils` package (the name should probably be changed) comes into play.
The `utils` package defines the backend functionality to poll and update information about submitted jobs automatically.
So far, the development has been very specific to the environment in the company I used to work for and is not transferable to other environments without major code changes. 


----------------------------------------------------------------------------------------------------


## Installation and Deployment


### Dependencies

* MySQL Server version: 5.1.73 Source distribution
* Python 3.7.3


### Prepare the Environment

#### Logon to the Production Server

```sh
$ ssh <username>@production-server
<username>@production-server's password:
...
```

Go to a location where you would like the app to be installed.
The recommended directory is `/opt/`. 
```sh
$ cd /opt/
```

Create a directory for the application.
```sh
$ mkdir caejd
$ cd ./caejd
```

#### MySQL Setup

Install MySQL if necessary. 
It should come pre-installed with certain linux distributions like CentOS 6.6.
Here is an [installation tutorial](https://devops.ionos.com/tutorials/install-mysql-on-centos-6/#install-mysql-packages).
For security reasons it is recommended that to run the `/usr/bin/mysql_secure_installation`.

To enable proper timezone handling, add the timezone tables to mysql (see this [article](https://dev.mysql.com/doc/refman/8.0/en/time-zone-support.html)).
```shell
$ mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root -p mysql
```

[Create a new user](https://www.digitalocean.com/community/tutorials/how-to-create-a-new-user-and-grant-permissions-in-mysql) and grant rights.
```shell
$ mysql -u root -p
```
```mysql
mysql> CREATE USER 'caejd'@'localhost' IDENTIFIED BY 'password';
mysql> GRANT ALL PRIVILEGES ON * . * TO 'caejd'@'localhost';
mysql> FLUSH PRIVILEGES;
mysql> EXIT;
```

When creating the user, make sure to use a more secure password then `password`!

Login to MySQL with the new user and create a new database.
```shell
$ mysql -u caejd -p
```
```mysql
mysql> CREATE DATABASE caejd CHARACTER SET utf8;
mysql> EXIT;
```

After the installation, the MySQL service should automatically run on start up.
In case you change the MySQL config you need to be able to stop/start or restart the service.
It might also be helpful to check the status of the service.
These are the commands (to be run as root):
```bash
$ /etc/init.d/mysqld start
$ /etc/init.d/mysqld stop
$ /etc/init.d/mysqld restart
$ /etc/init.d/mysqld status
```

For reference, here is the example MySQL config  (`/etc/my.cnf`).
The important settings are the timeouts.
Both need to be larger than the `CONN_MAX_AGE` in the Django setting for the DB connection.
If the MySQL timeouts are smaller than the Django value, the connection might go stale.
In these cases Django tries to reuse an old connection and can not reach the DB anymore.
This will throw error like: `(2006, 'MySQL server has gone away')`.

```
[mysqld]
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
user=mysql
# Disabling symbolic-links is recommended to prevent assorted security risks
symbolic-links=0
interactive_timeout=28800
wait_timeout=28800

[mysqld_safe]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
```

#### Setup the Virtual Environment

Assuming that Python 3.7 is installed on the server, you can set up a virtual environment to run the app.
This will help in case the server needs to run other applications later on.

Create and activate a virtual environment:
```sh
$ python3.7 -m venv env
```

#### Defining the `DJANGO_SETTINGS_MODULE`

For Django to know which settings file (or more accurate which Python module) it is supposed to use, you need to define an environment variable that contains that information.
There are other ways to pass that information to Django, but using the environment variables for this is the most stable and only needs to be done once.

Since there is already a virtual environment that will contain the Python modules for CAE Job Diary, this environment can also be used to set the required environment variables. 
Thereby, every time the virtual environment is activated, the correct environment variables are also defined.
   
To do this, add the following to the end of the `env/bin/activate` script.

```sh
DJANGO_SETTINGS_MODULE="caejobdiary.settings.production"
export DJANGO_SETTINGS_MODULE
```

Also, at the beginning of that `activate` script you will find the function definition for the `deactivate` command.
At the end of the function definition just add the following to unset the environment variable when the virtual environment is deactivated.

```sh
deactivate () {
	...
    unset DJANGO_SETTINGS_MODULE
}
```

This way, every time the environment to run the application is started, the correct setting module is declared via the environment variable.
When the environment is deactivated, the variable is unset too.

This becomes especially handy when using different settings in production and development (as this project does and basically all Django projects do).
See  [this StackOverflow thread](https://stackoverflow.com/questions/1626326/how-to-manage-local-vs-production-settings-in-django) for a discussion of different ways to handle multiple settings files in Django. 

#### Start the Virtual Environment

To activate the previously created virtual environment, activate it like so:

```sh
$ source env/bin/activate
```


### Get the Repo

#### Production Server is not Connected to the Internet

This step is only necessary if the production server is only configured for the internal network and not connected to the internet.
If the server is connected to the internet, than the local machine is not needed as an intermediate step.

##### Get the Repo to Your Local Machine

To get the repository to the local machine for the first time, clone the repository to a directory of your choice. 

```sh
$ cd /some/local/directory
$ git clone https://gitlab.com/tbrlpld/CAEJobDiary.git
```

If you have the repository already on your machine somewhere, then just fetch the latest changes.
```sh
$ git fetch origin
$ git pull
```

##### Get the Repo from Local Machine to the Production Server

Connect to the production server and change into the installation directory.
```sh
$ ssh <username>@production-server
<username>@production-server's password:
...
$ cd /opt/caejd
```

To get the repository from you local machine to the production server you have two options:
 - If the directory where you cloned the repository to is a machine local directory then you can use `ssh` to clone it from there to the production server: 
    ```sh
    $ git clone ssh://<username>@<host>/some/local/directory/CAEJobDiary/ --branch production --single-branch
    ```
 - Or, if the directory you cloned the repository to is a network directory that is also mounted on the production server, then you can just clone it directly from there:
    ```sh
    $ git clone /some/network/directory/CAEJobDiary/ --branch production --single-branch
    Cloning into 'CAEJobDiary'...
    done.
    ```

In either case, fetch the latest changes from you local machine and check out the `production` branch to the server:
```sh
$ git fetch
$ git pull --ff-only origin production
 ```

#### Production Server is Connected to the Internet

In case that the production sever is connected to the internet, you can skip the cloning of the repository onto the local machine. 
So, the only necessary commands to run on the production server are:
```sh
$ git clone https://gitlab.com/tbrlpld/CAEJobDiary.git --branch production --single-branc
$ git fetch
$ git pull --ff-only origin production
```

### Install the  Requirements

To allow production servers that are not connected to the internet,  the requirements are delivered with the repo and can be installed locally.
To do so, switch into the create repositiory directory and install the requirements with `pip`.

```sh
$ cd CAEJobDiary
$ pip install -r requirements.txt --no-index --find-links wheelhouse
```

### Define a Secret Key

For its encryption functionality, Django needs a secret key, which is uses in the generation of certain encryption patterns.
This secret key is not supposed to be made public and therefore has to be kept out of version control.
This also means you need to define one on the production server itself.

To store the secret key, I have decided to use the "secrets files pattern" (as defined in "Two Scoops of Django 1.11", Section 5.4).
It would also be possible to use environment variables for this, but I will apply the solution that is more robust, because it will work in any environment -- even PaaS ones or Apache Servers where the environment variable may not be editable without generating conflicts.

Enough about the philosophy, let's get to it.

To create a dummy secrets file, there is a little commandline tool provided.
Execute the tools like so (from the top level directory):
```sh
python bin/make_secrets.py /opt/caejd/config/
```

This will create a dummy `secrets.json` file in the directory passed as the argument -- in this case `/opt/caejd/config/`.

There are two possible locations in which the `secrets.json` may be stored.
One is `/opt/caejd/config/`, which is suggested for production.
The other is a `config/` directory under the repo top level directory (which is useful for development setups).
Both directory are checked for a `secrets.json` and the files are loaded.
In case the `secrets.json` file exists in both locations, the latter configuration is used.

When the dummy file creation script is used, be sure to replace the `SECRET_KEY` value with something secure and secret!


### Migrate the Database

For the app to store persistent information, it is necessary to create the  correct schema in the database.
To be able to connect Django to the database, you need to define the password for the created user `caejd` in the `secrets.json`:
```json
{
    ...
    "DB_PASSWORD": "password"
}
```

Now Django can connect to the database using the `caejd` user and the given password and the database schema can be migrated.

```sh
$ python manage.py migrate
```

### Start the CAE Job Diary Backend Process in a Screen

Currently it is not yet possible to run CAE Job Diary as a service. 
That means, to start and stop the main process is needs to be in the foreground. 

Since the production server is probably running on a remote server and not on a local machine, you are probably connected to it via `ssh`. 
To be able to send a process into the background, exit the `ssh` session and bring the process back to the foreground in a new `ssh` session, the processes needs to be started in a `screen`.   
For more information about `screen`, see this [StackOverflow thread](https://stackoverflow.com/questions/8184717/how-to-send-ssh-job-to-background).

To create a `screen` run:
```sh
$ screen
```

In that screen you want to activate the virtual environment in which the requirements are installed and the environment variable for the settings module is defined.
```sh
$ source env/bin/activate
```

All processes that are needed to run on the server for CAE Job Diary to work can be started with one single script:
```sh
$ python bin/caejd.py
[2019-01-02 21:11:01,012 - __main__ - INFO]:  CAEJobDiary started...
[2019-01-02 21:11:01,013 - __main__ - INFO]:  Starting polling process.
[2019-01-02 21:11:01,014 - __main__ - INFO]:  Starting update process.
[2019-01-02 21:11:01,016 - __main__ - INFO]:  Starting Django server.
[2019-01-02 21:11:01,018 - utils.graceful_killer.Polling - DEBUG]:  Creating kill singal listeners.
[2019-01-02 21:11:01,019 - utils.graceful_killer.Update - DEBUG]:  Creating kill singal listeners.
[2019-01-02 21:11:01,020 - utils.graceful_killer.Django - DEBUG]:  Creating kill singal listeners.
Performing system checks...

System check identified no issues (0 silenced).
January 02, 2019 - 21:11:01
Django version 2.0.9, using settings 'caejobdiary.settings.local'
Starting development server at http://0:8000/
Quit the server with CONTROL-C.

```
You will see some diagnostics output and then the process should be in the foreground.
To terminate the main process and all of it's child processes just hit \[ctrl+c\].

The main process should be kept running for CAE Job Diary to work.
To detach the screen \[ctrl+-a\] then \[ctrl+d\].
```sh
[detached]
```

Now you can leave the `ssh` session with `exit`  without terminating the main CAE Job Diary process.


#### Dealing with the Screen

To get the server process back, log on to the production server per `ssh`.
To retrieve the last screen, use
```sh
screen -r 
```

You can get a list of active screens with `screen -ls`.
If there are more than one, you can select which one to retrieve by adding the name to the command, e.g.: `screen -r 2477.pts-0.server1`.

To switch between screens, [ctrl+a] then [ctrl+p] goes to the previous one.
[ctrl+a] then [ctrl+n] goes to the next screen. 

[Here](https://www.howtoforge.com/linux_screen) is some more info on how to deal with screens. 


-------------------------------------------------------------------------------


## Database Backup

This is crucial for the production environment: make database backups!

The backups should be done regularly and possibly automatically.
For the MySQL database backend there is a tool called `automysqlbackup` that can be installed and configured very easily --  even on CentOS and without being able pull package from the outside.

The official project website is here: https://sourceforge.net/projects/automysqlbackup/

The initial project is not maintained by the original developer anymore, but the last version is newer than CentOS 6.6 and works fine.
For further updates there are probably newer and maintained forks out there, but for now the latest version (v3.0 rc6) is fine and works.

The following website is a good reference on how to install and configure `automysqlbackup` on CentOS: https://www.sudoadmin.com/install-configure-schedule-automysqlbackup/


-------------------------------------------------------------------------------


## Update

To update CAE Job Diary, make sure you can reach the repository form the production server. 
If the production server is connected to the internet, than no steps are needed.
If the production server only works in the local network, you need to update a local version of the repository before you can update the version on the server.  

In either cases to update the version of CAE Job Diary on the production server, logon to it per `ssh`.
Retrieve the screen with `screen -r` in which the CAE Job Diary main process is running.
Stop the CAE Job Diary main process from running [ctrl+c].
```sh
...
Quit the server with CONTROL-C.
...
^C[2019-01-02 21:20:55,356 - utils.graceful_killer.Update - INFO]:  Received termination signal.
[2019-01-02 21:20:55,356 - utils.graceful_killer.Django - INFO]:  Received termination signal.
[2019-01-02 21:20:55,356 - __main__ - INFO]:  Keyboard interruption detected. Stopping processes.
[2019-01-02 21:20:55,358 - __main__ - INFO]:  Stopping process: (pid 2345) Polling
[2019-01-02 21:20:55,358 - utils.graceful_killer.Polling - INFO]:  Received termination signal.
[2019-01-02 21:20:55,363 - __main__ - INFO]:  Process 2345 ended successfully.
[2019-01-02 21:20:55,363 - __main__ - INFO]:  Stopping process: (pid 2346) Update
[2019-01-02 21:20:55,420 - __main__ - INFO]:  Process 2346 ended successfully.
[2019-01-02 21:20:55,421 - __main__ - INFO]:  Stopping process: (pid 2347) Django Server
[2019-01-02 21:20:55,421 - __main__ - INFO]:  Process 2347 ended successfully.
[2019-01-02 21:20:55,421 - __main__ - INFO]:  All CAEJobDiary processes stopped.
[2019-01-02 21:20:55,421 - __main__ - INFO]:  Goodbye...
```

Get the latest production version.
```sh
$ git fetch
$ git pull --ff-only origin production
```

Install new requirements.
```sh
$ pip install -r requirements.txt --no-index --find-links wheelhouse
```

Migrate the DB changes.
```sh
$ python manage.py migrate
```

Start the backend process again.
```sh
$ python bin/caejd.py
```


----------------------------------------------------------------------------------------------------


## Development Setup

Target version for the application (the environment where the app is supposed to be run) is Python 3.7.3 on CentOS 6.6.
Therefore, development should also be done in an environment as close as possible to that.

### Vagrant

To be able to develop in an environment that is as close as possible to the production environment I have created a `Vagrantfile`.
Vagrant is a management system for virtual machines by HashiCorp. 
The `Vagrantfile` defines the configuration of a virtual machine that is managed by Vagrant.
The actual virtualisation is done by VirtualBox or VMware. 
To learn more about Vagrant visit the [official website](https://www.vagrantup.com/).
Their [Getting Started](https://www.vagrantup.com/intro/getting-started/index.html) give a good introduction into how Vagrant can be installed and used.

Once Vagrant is installed and you have the `vagrant` command available on the command line you can get the local development environment set up. 
 
### Get Source Code

Clone the source code form [GitLab](https://gitlab.com/tbrlpld/CAEJobDiary.git) (or download and unpack the zip) in a directory of your choosing.

```sh
$ cd ~/projects
$ git clone https://gitlab.com/tbrlpld/CAEJobDiary.git
```

### Create the Virtual Machine with `vagrant`

Navigate into the repository. 
```sh
$ cd CAEJobDiary
``` 

Start the virtual machine. 
```sh
$ vagrant up
```
You don not need to define anything else since `vagrant up` expects a `Vagrantfile` to be present in the working directory. 
Since there is a `Vagrantfile` in the repo it will start up the defined machine. 
The first time this can take a while, since the required images have to be downloaded.

Once the command finishes, you can run the following to connect to the new virtual machine: 
```sh
$ vagrant ssh
Last login: Tue Jan 01 05:30:18 2019 from 1.1.1.1
[13:18:04 vagrant@localhost:~] $ 
``` 
You are now connected to the virtual machine via `ssh`.
This machine has Python 3.7.3 and MySQL installed and is ready for development. 

The virtual machine is configured to forward port 8080 of the host (your machine) to port 8000 of the guest (the VM). 
That means, to connect to a HTTP server listening on the VM on port 8000 you have to request the URL `http://localhost:8080`.

Also, the files from the project directory (the repo) are synced to the VMs directory `/vagrant`.
Change into that directory to have access to the files of the repository.
```sh
[13:18:04 vagrant@localhost:~] $ cd /vagrant
``` 

### Create a Virtual Environment on the VM 

Because of Python had to be installed from source on the VM is is not readily available on the `PATH`.
You can find the executables in `/usr/local/bin`.
To make it easier to call the correct Python version during development it is recommended to create a virtual environment.
```sh
[13:18:04 vagrant@localhost:~] $ cd /vagrant
[13:18:04 vagrant@localhost:~] $ /usr/local/bin/python3.7 -m venv env
``` 

### Set the `DJANGO_SETTINGS_MODULE` for Development

To see how to the define the `DJANGO_SETTINGS_MODULE`, see the [installation and deployment section](installation-and-deployment).
But, instead of `caejobdiary.settings.production` use `caejobdiary.settings.local`.

Do **NOT** adjust the `local.py` settings to your own needs.
You can derive your own though, e.g. `local-myname.py`.
In you personal settings files add `from local import *`.
Then override what ever needs to be changed for you. 

And don't forget to update the `DJANGO_SETTINGS_MODULE` environment variable to your own settings module.


### Install or Create New Requirements

To not require the production server to have an internet connection, the requirements are be packed with the repo.

If new requirements are created, the packages should be downloaded from [PyPI](https://pypi.org/) as wheels or tarballs and added to the `wheelhouse` directory.

See the [install requirements section](install-requirements) for information on how to install the requirements from the wheelhouse.

### Define a Secret Key for Development

See the [corresponding section](define-a-secret-key) in the deployment instruction to define the secret key properly.

### Setup Development Database

Run database migrations.

```sh
python manage.py migrate
```

To create some sample entries in the development database, just run:

```sh
python populate_diary.py
```


### Run Web Server

To run the web server(without the backend polling and update processes):
```sh
python manage.py runserver
```

Since the development machine is probably not embedded in the production environment and thus does not have access to the polled and checked directories, it does not make sense to run these processes on the development machine. 


### Testing

The tests are defined in the `tests/` directory.
Within the testing directory, define the same structure as in the actual package.
Create separate test modules/packages for separate modules/packages. 

To run all tests:
```sh
python manage.py test tests
```

Or specify which package or module should be tested.
```sh
python manage.py test tests/test_diary
python manage.py test tests/test_utils
```

Since it is not possible to use the actual info sources for the `poll` and `update` processes, it is even more important for dem to be developed with a test driven development approach.
That means the first task before creating any features is to define a test in which the situation in the production environment is recreated.
After that, the feature can be developed to implement the desired functionality.  

### Distribution

*This section is only preliminary and has currently no explicit use*

To build the latest distribution, make sure the changes for are added in the `CHANGES.txt`.
Pay close attention to the version number used there.
This version number has to be matched in the `setup.py`.

To create a distribution of the lastest version, just run the following in the top level directory:
```sh
python setup.py sdist
```

This will create a `tar.gz` in the `dist/` directory.
It will also create the directory if it does not exist.

As of now, I am not sure how to make use of the distributions.
If I can manage to pack all dependencies with the app, then it might make sense to install it that way.
But then I also need to create an install script or something, because I using `pip` to install the
tarball has totally different assumptions.
Doing that, the scripts end up as executable in the python installation directory (or the virtual environment's).
That is not really meant for this kind of application. It seems to be more for libraries and some
utilities that work with them.

It should be possible though.
The created tarball only needs to be extracted and the application run from that directory.
In that case, the configuration would need to be reset after starting to use a new version (update).
Therefore, if probably makes sense to have a install or update script.
That would move the files from the tarball into a definable directory.
That would allow to just extract the tarball somewhere on the system and then define the install target:

```sh
$ ./CAEJobDiary-x.y.z/install /opt/caejd
```

If there was a previous version that would be overridden.
How to remove deleted files though?
Deleting everything does not make sense, because then the config files are also gone...
Should the config files be saved somewhere else?




----------------------------------------------------------------------------------------------------


## Release History

See release history in [CHANGES.md](CHANGES.md)


## Bug Reporting

Please report bugs at <https://gitlab.com/tbrlpld/CAEJobDiary>.


## Meta

Distributed under the MIT license. 
See [LICENSE.txt](LICENSE.txt) for more information.

Repository: <https://gitlab.com/tbrlpld/CAEJobDiary>


## Contributing

1. Fork it <https://gitlab.com/tbrlpld/CAEJobDiary/forks/new>
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

