echo "Installing Python 3.7.3 from source..."
initialdir=$(pwd)
cd /usr/src
wget https://www.python.org/ftp/python/3.7.3/Python-3.7.3.tgz
tar xzf Python-3.7.3.tgz
cd Python-3.7.3
./configure --enable-optimizations
make altinstall
rm /usr/src/Python-3.7.3.tgz
cd $initialdir
