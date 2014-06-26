# SpImagine

OpenCL accelerated rendering of 3D and 4D data


## Installing

On Mac, clang might complain about non supported compiler flags, a quick fix to which is

> export CFLAGS=-Qunused-arguments
> export CPPFLAGS=-Qunused-arguments


install PyQt4, e.g. with homebrew:
> brew install pyqt


then with pip

> pip install git+http://mweigert@bitbucket.org/mweigert/spimutils

> pip install git+http://mweigert@bitbucket.org/mweigert/pyocl

> pip install git+http://mweigert@bitbucket.org/mweigert/spimagine


-----

## Usage

### Gui Application

Run the  Qt Gui Application to render 3d/4d Data either via  


> python -m spimagine

or via the app bundle in the binary folder (currently only for Mac OSX 10.9) 

> SpImagine.app


Right now the following formats are supported

- tiff files
- 16 bit unsigned raw data in the format used by the Myers Group at mpi-cbg

### Command line

> spimagine_render -h

list the options for the command line tool



### interactive usage

the package provides an interactive visualisation to be used e.g. within IPython

    :::python 
	from spimagine import volshow, volfig
	data = ... #3d or 4d numpy array
	volfig()   #similar behaviour like matplotlib.figure, e.g. can be omitted
	volshow(data)


