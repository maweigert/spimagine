from distutils.core import setup

setup(name='SpimRender',
      version='0.1',
      description='renders spim data in 3D',
      url='git@bitbucket.org:mweigert/spimagine.git',
      author='Martin Weigert',
      author_email='mweigert@mpi-cbg.de',
      license='MIT',
      packages=['spimagine'],
      package_data={"spimagine":['volume_render.cl']},
      data_files=[("images","images/icon_start.png")],
      scripts=['spimagine/spim_render.py',"spimagine/spimagine.py"],
      install_requires=[
          'numpy', 'scipy','Pillow',"PyOpenGL","pyopencl"
          ,"SpimUtils","PyOCL"
          ],

      dependency_links=[
              "http://mweigert@bitbucket.org/mweigert/spimutils",
              "http://mweigert@bitbucket.org/mweigert/pyocl"]
      )
