import os
from setuptools import setup, find_packages

exec (open('spimagine/version.py').read())

setup(name='spimagine',
      version=__version__,
      description='OpenCL volume rendering in 3D/4D',
      url='https://github.com/maweigert/spimagine',
      author='Martin Weigert',
      author_email='mweigert@mpi-cbg.de',
      license='BSD 3-Clause License',
      packages=find_packages(),

      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Science/Research',
          'Topic :: Scientific/Engineering',
          'License :: OSI Approved :: BSD License',

          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ],

      install_requires=[
          'numpy',
          'scipy',
          'Pillow>=3.3',
          "PyOpenGL",
          "pyopencl",
          "gputools",
          "imageio",
          "sortedcontainers"
      ],
      extras_require={
          ':python_version<"3.0"': [
              #"scikit-tensor",
              "ConfigParser",
          ],
          ':python_version>="3.2"': [
              "configparser",
              "pyqt5"
          ],
      },

      package_data={"spimagine": ['volumerender/kernels/*',
                                  'gui/shaders/*',
                                  'gui/images/*',
                                  'colormaps/*',
                                  'data/*',
                                  'lib/*']},
      entry_points={
          'console_scripts': [
              'spimagine_render = spimagine.bin.spim_render:main'
          ],
          'gui_scripts': [
              'spimagine = spimagine.bin.spimagine_gui:main'
          ]
      }
      )
