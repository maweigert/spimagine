from distutils.core import setup

setup(name='SpimRender',
      version='0.1',
      description='renders spim data in 3D',
      url='git@bitbucket.org:mweigert/spimrender.git',
      author='Martin Weigert',
      author_email='mweigert@mpi-cbg.de',
      license='MIT',
      packages=['SpimRender'],
      package_data={"SpimRender":['volume_render.cl']},
      scripts=['SpimRender/spim_render.py',"SpimRender/spimagine.py"],
      install_requires=[
          'numpy', 'scipy','Pillow',"PyOpenGL","pyopencl"
          ,"SpimUtils","PyOCL"
          ],

          dependency_links=[
              "http://mweigert@bitbucket.org/mweigert/spimutils",
              "http://mweigert@bitbucket.org/mweigert/pyocl"],
      zip_safe=False)

