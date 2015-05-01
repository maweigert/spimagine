# SpImagine

A python package to interactively visualize and process  time lapsed volumetric data as generated with modern light sheet microscopes. The package provides a generic 3D+t data viewer as well as denoising and deconvolution methods and makes use of GPU acceleration via OpenCL. 


[![Alt text for your video](poster_vimeo.png)](https://vimeo.com/126597994)

## Installing

### Mac

#### as app bundle

just find the dmg in the download section, open and drag to Applications

you wanna install libtiff to speed up opening of tiff files   
> brew install libtiff

The app essentially bundles all dependencies and extracts them on the fly  so startup might be slow

#### as python package
  
On Mac, clang might complain about non supported compiler flags, a quick fix to which is

> export CFLAGS=-Qunused-arguments

> export CPPFLAGS=-Qunused-arguments


install PyQt4, e.g. with homebrew:
> brew install pyqt

install libtiff (optional)
> brew install libtiff


then with pip

> pip install --user git+http://mweigert@bitbucket.org/mweigert/pyocl

> pip install --user git+http://mweigert@bitbucket.org/mweigert/spimagine

or the developmental branch

> pip install --user git+http://mweigert@bitbucket.org/mweigert/spimagine@develop


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

the package provides interactive visualisation to be used e.g. within IPython

    :::python 
	from spimagine import volshow, volfig

	data = ...          #3d or 4d numpy array
	
	volfig(0)           #optional: similar behaviour like matplotlib.figure, e.g. can be omitted
	
	volshow(data)       #render the data

### setting the GPU to be used:

interactively:

    :::python 
	import spimagine 
	spimagine.setOpenCLDevice(1)  #optional: set the GPU to use


or put a config file ".spimagine" in your home folder

    OPENCLDEVICE = 1
