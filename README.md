# Spimagine


*Spimagine* is a python package to interactively visualize and process  time lapsed volumetric data as generated with modern light sheet microscopes (hence the *Spim* part). The package provides a generic 3D+t data viewer and makes use of GPU acceleration via OpenCL. 
If provides further an image processor interface for the GPU accelerated denoising and deconvolution methods of [gputools](https://github.com/maweigert/gputools). 

Watch the following screencast for a first impression: 

<p align="left">
<a href = https://vimeo.com/126597994 ><img src=images/poster_vimeo.png width=500/></a>
</p>

or alternatively the [talk at EuroScipy 2015](https://www.youtube.com/watch?v=MeFsmFTU2JQ)


##Overview

[Requirements](#requirements)  
[Installation](#installation)  
[Usage](#usage)


## Requirements

* Python 2.7 or 3.5+
* a working OpenCL environment 

## Installation

### Mac


#### Verify the availability of OpenCL
On OSX the neccessary OpenCL libraries should be provided by default. 
Check with `clinfo` that your GPU is listed as available device:
```
brew install clinfo
clinfo
```
####  Install the package
If you only want to use the standalone application (without installing it as a proper python package and make it usable from within the interpreter) you can just download the [App bundle](https://github.com/maweigert/spimagine/releases/download/v0.2.0/spimagine.dmg):


To install it as a proper package, do

* Python 2
```
brew install pyqt5 --with-python --without-python3
pip install spimagine
```

* Python 3
```
pip3 install spimagine
```

For the most recent versions, install the developmental branch 
```
pip(2|3) install git+https://github.com/maweigert/spimagine@develop
```


### Linux

#### Verify the availability of OpenCL

Check with `clinfo` that your GPU is listed as available device:
```
sudo apt-get install clinfo
clinfo
```
Depending on your graphics card, install relevant the opencl libaries, headers and icd, e.g. for nvidia

```
sudo apt-get install opencl-header  nvidia-libopencl1-352 nvidia-opencl-icd-352
```

On https://wiki.tiker.net/OpenCLHowTo you can find some further information

####  Install the package

* Python 2

```
sudo apt-get install python-pyqt5 python-pyqt5.qtopengl python-pyqt5.qtsvg
pip install spimagine
```

* Python 3

```
pip3 install spimagine
```


### Windows

Install the OpenCL SDK of your graphcis card vendor.
Install pyopencl and PyQt5 prebuilt binaries from http://www.lfd.uci.edu/~gohlke/pythonlibs/

```
git clone https://github.com/maweigert/gputools.git
cd gputools
python setup.py install

git clone https://github.com/maweigert/spimagine.git
cd spimagine
python setup.py install
```


## Usage

Spimagine was designed with the interactive display of volumetric data from ipython in mind, but it can likewise be used as a standalone application.  

### Standalone Application

pip should install the standalone viewer in the local bin folder (e.g. "~/.local/bin" on Linux), run it from the command line like that

```
spimagine [input]
```

Right now the following formats are supported as input 

- tiff files
- a folder containing tiff files
- 16 bit unsigned raw data in the format used by the Myers Group at mpi-cbg


### Interactive 

the package provides interactive visualisation to be used e.g. within IPython

```python 
from spimagine import volshow

# create a 3d or 4d numpy array
data = linspace(0,1,100**3).reshape((100,)*3)          
	
# render the data and returns the widget 
w = volshow(data)       

# manipulate the render states, e.g. rotation and colormap
w.transform.setRotation(.1,1,0,1)
w.set_colormap("hot")

# save the current view to a file  
w.saveFrame("scene.png")
````

### GUI

To load a file (supported: Tiff/czi) just drop it onto the main canvas or use the load button on the middle bottom panel. 

| | | | |
|-------|-------|-------|-----|
|![](images/small_1.png)|![](images/small_2.png)|![](images/small_3.png)|![](images/small_4.png)|
| <ul><li>min/max/gamma slider</li></ul> | <ul><li>timepoint controls</li></ul> | <ul><li>center/animate view</li><li>keyframe editor</li><li>screenshot</li><li>open/save as tiff</li></ul> | <ul><li>iso surface</li><li>slice view</li><li>settings</li></ul> |

#### keyframe editor

*Spimagine* allows the creation of animated sequences of rendering scenes via its keyframe editor. 
After opening the panel, different keyframes can be inserted by right clickling on the timeline. A right click on existing keyframe will open a context menu to update the keyframe or change the interpolation elasticity (the acceleration if the interpolation). Every change in the transform parameters (zoom, gamma, etc) and data timepoints will then be interpolated between consecutive keyframes. Pressing the play button will animate the sequence, pressing the record button will save the rendered images to a folder (set the framerate and folder location in the settings panel) after which they can be composed into a movie (e.g. with ffmpeg). The current keyframes can be saved to json (via a button) and reloaded (drop the json into the timeline).

![](images/gui_5.png)

### configuration 

Some configuration data (e.g. the default OpenCL platform and device, colormaps, etc) can be changed in the config file "$HOME/.spimagine" (create it if necessary)  

```#~/.spimagine

id_platform = 0  
# id_platform =-1 to choose the device with biggest memory) 

id_device = 1 
max_steps  = 400
colormap = viridis

```
See 
```python
spimagine.config.defaults
```
for available keys and their defaults.

As *Spimagine* uses [gputools](https://github.com/maweigert/gputools) as OpenCL backend, it will use gputools' default OpenCL platform/device otherwise (which itself can be changed in "$HOME/.gputools")



### troubleshooting

#### logging (debug mode)

To get a logging output, run it as standalone from the command line with the debug flag   
```
$ spimagine -D
```


#### getting it to work from inside the jupyter notebook / ipython 

As the main widget relies on the qt event loop running, one has to include 

```python
%gui qt5
```
at the beginning of the notebook or start Ipython with the qt5 backend:

```
ipython --matplotlib=qt5
```

