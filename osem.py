#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import matplotlib.pyplot as plt

from skimage.io import imread
from skimage import data_dir
from skimage.transform import radon, rescale, iradon
from skimage.draw import circle
from scipy.ndimage import gaussian_filter1d

parser = argparse.ArgumentParser(description='Simulation of OSEM')
parser.add_argument('--count', '-c', default=2e6, type=float,
                    help='slice total count. Poisson noise equivalent to COUNT is added to sinogram. If COUNT is zero, no noise is added to sinogram (true).')
parser.add_argument('--niter', '-i', default=8, type=int,
                    help='number of iteration')
parser.add_argument('--nsub', '-s', default=10, type=int,
                    help='number of subset')
args = parser.parse_args()

count   = args.count
niter   = args.niter
nsub    = args.nsub

# shepp-logan phantom
image   = imread(data_dir + "/phantom.png", as_grey=True)
image   = rescale(image, 0.4)
shape   = image.shape

# sinogram
theta = np.linspace(0., 180., max(image.shape), endpoint=False)
sinogram    = radon(image, theta=theta, circle=True)

# add noise
if count > 0:
    val = sinogram.sum()
    sinogram    = np.random.poisson(sinogram / val * count).astype(np.float)
    sinogram    *= val / count

# initial
recon   = np.zeros(shape)
rr, cc  = circle(shape[0] / 2 - 0.5, shape[1] / 2 - 0.5, shape[0] / 2 - 1)
recon[rr, cc]   = 1

# normalization matrix
nview   = len(theta)
norm    = np.ones(shape)
wgts    = []
for sub in xrange(nsub):
    views   = range(sub, nview, nsub)
    wgt = iradon(norm[:, views], theta=theta[views], filter=None, circle=True)
    wgts.append(wgt)

# iteration
for iter in xrange(niter):
    print   'iter', iter
    order   = np.random.permutation(range(nsub))
    for sub in order:
        views   = range(sub, nview, nsub)
        fp  = radon(recon, theta=theta[views], circle=True)
        ratio   = sinogram[:, views] / (fp + 1e-6)
        bp  = iradon(ratio, theta=theta[views], filter=None, circle=True)
        recon   *= bp / (wgts[sub] + 1e-6)

# display
plt.figure(figsize = (10, 5))
plt.gray()
plt.subplot(121)
plt.title('FBP, ramp')
plt.imshow(iradon(sinogram, theta=theta, circle=True), vmin = 0, vmax = 1)
plt.axis('off')
plt.subplot(122)
plt.title('OSEM, {} iteration, {} subset'.format(niter, nsub))
plt.imshow(recon, vmax = 1)
plt.axis('off')

plt.subplots_adjust(0, 0, 1, 0.9, 0, 0.1)
plt.savefig('osem.png')
plt.show()
