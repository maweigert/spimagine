from setuptools import setup

setup(name='SpimRender',
      version='0.1',
      description='renders spim data in 3D',
      url='git@bitbucket.org:mweigert/spimrender.git',
      author='Martin Weigert',
      author_email='mweigert@mpi-cbg.de',
      license='MIT',
      packages=['SpimRender'],
      install_requires=[
          'numpy', 'Pillow',"pyopencl"],
      zip_safe=False)
