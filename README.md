# SpImagine

renders spim data in 3D


### Installing

On Mac, clang might complain about non supported compiler flags, a quick fix to which is

> export CFLAGS=-Qunused-arguments
> export CPPFLAGS=-Qunused-arguments


install PyQt4, e.g. with homebrew:
> brew install pyqt


then with pip

> pip install git+http://mweigert@bitbucket.org/mweigert/spimutils

> pip install git+http://mweigert@bitbucket.org/mweigert/pyocl

> pip install git+http://mweigert@bitbucket.org/mweigert/spimrender


or standard python 

> git clone http://mweigert@bitbucket.org/mweigert/spimrender

> cd spimrender

> python setup.py install

-----