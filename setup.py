from setuptools import setup

setup(name='SpimRender',
      version='0.1',
      description='renders spim data in 3D',
      url='git@bitbucket.org:mweigert/spimrender.git',
      author='Martin Weigert',
      author_email='mweigert@mpi-cbg.de',
      license='MIT',
      packages=['SpimRender'],
      scripts=['SpimRender/spim_render'],
      install_requires=[
          'numpy', 'scipy','Pillow',"pyopencl"],
          
          # dependency_links=[
          #     "git+http://mweigert@bitbucket.org/mweigert/spimutils.git",
          #     "git+http://mweigert@bitbucket.org/mweigert/pyocl.git"],
      zip_safe=False)
