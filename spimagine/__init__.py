

import logging
logging.basicConfig(format='%(levelname)s:%(name)s | %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)


from volume_render import *

# import gui_mainwindow 
# import gui_glwidget 

from volshow import volshow, volfig
