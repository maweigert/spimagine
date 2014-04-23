import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))

setup(name='spimagine',
    version='0.1',
    description='renders spim data in 3D',
    url='http://mweigert@bitbucket.org/mweigert/spimagine',
    author='Martin Weigert',
    author_email='mweigert@mpi-cbg.de',
    license='MIT',
    packages=['spimagine'],
    install_requires=[
        'numpy', 'scipy','Pillow',"PyOpenGL","pyopencl"
        ,"SpimUtils","PyOCL"
    ],

    package_data={"spimagine":['kernels/*','images/*']},
    entry_points = {
    'console_scripts': [
    'spimagine = spimagine.spimagine_gui:main',
    'spimagine_render = spimagine.spim_render:main'
    ] },


)
