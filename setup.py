import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

setup(name='spimagine',
    version='0.1.2',
    description='renders spim data in 3D/4D',
    url='http://mweigert@bitbucket.org/mweigert/spimagine',
    author='Martin Weigert',
    author_email='mweigert@mpi-cbg.de',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'numpy', 'scipy','Pillow',"PyOpenGL","pyopencl"
        ,"sortedcontainers"
    ],

    package_data={"spimagine":['volumerender/kernels/*',
                               'gui/shaders/*',
                               'gui/images/*',
                               'colormaps/*',
                               'data/*',
                               'lib/*']},
      entry_points = {
          'console_scripts': [
              'spimagine_render = spimagine.bin.spim_render:main'
          ],
    'gui_scripts': [
        'spimagine = spimagine.bin.spimagine_gui:main'
    ]
        }
)
