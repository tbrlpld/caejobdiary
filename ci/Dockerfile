# Starting with the official CentOS 6.6 image
FROM centos:6.6

ADD server.cnf /etc/my.cnf.d/server.cnf
ADD mysql.sh /root/mysql.sh
ADD install_python.sh /root/install_python.sh

# Update package repository -- maybe not that is not possible in the environment to be replicated.
# RUN yum -y update && yum -y clean all

# RUN yum -y install mysql-libs

# Install plugin to fix checksum error - https://github.com/moby/moby/issues/10180#issuecomment-266172755
RUN yum install -y yum-plugin-ovl

# Install mysql
RUN yum -y install mysql
RUN yum -y install mysql-server

# Install python3.7
RUN yum -y install wget
RUN yum -y install tar
RUN yum -y install gcc openssl-devel zlib-devel bzip2 bzip2-devel readline-devel sqlite sqlite-devel xz xz-devel libffi-devel 
RUN chmod +x /root/install_python.sh
RUN /root/install_python.sh
RUN yum -y install python-devel python3-devel mysql-devel

# Enable execution of the mysql-script
RUN chmod +x /root/mysql.sh

CMD ["/root/mysql.sh"]
