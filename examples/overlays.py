import numpy as np
from spimagine import volshow
from spimagine import OverlayData

# create two example stacks - a sphere in the middle and a noisy version 
N = 256
Xs = np.mgrid[:N,N//4:3*N//4,:N]-N/2
R = np.sqrt(np.sum(Xs**2, axis= 0))
img_clean = 100.*((np.exp(-20*R**2/N**2))+(R<N/4))
img_noisy = .8*img_clean + 40*np.random.normal(0,1,img_clean.shape)

# display it as an overlay (i.e. slipping through time changes the overlap) 
volshow(OverlayData(img_noisy, img_clean))
