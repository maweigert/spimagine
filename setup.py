import os
from setuptools import setup, find_packages



exec(open('spimagine/version.py').read())


setup(name='spimagine',
    version=__version__,
    description='OpenCL volume rendering in 3D/4D',
    url='https://github.com/maweigert/spimagine',
    author='Martin Weigert',
    author_email='mweigert@mpi-cbg.de',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'Pillow>=3.3',
        "PyOpenGL",
        "pyopencl",
        "sortedcontainers"
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
