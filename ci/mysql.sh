#!/bin/sh

#/sbin/chkconfig mysqld on
/sbin/chkconfig --levels 235 mysqld on
/sbin/service mysqld start
/sbin/service mysqld status

 echo "THIS IS THE mysql.sh SCRIPT"