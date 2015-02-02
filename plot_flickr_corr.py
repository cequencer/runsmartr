#!/Library/Frameworks/Python.framework/Versions/2.7/bin/python


import numpy as np
from matplotlib import pyplot as plt

# Read data from file
datafile = 'flickr_corr.dat'
a = np.loadtxt(datafile)

x = a[:,0]
y = a[:,1]

fig = plt.figure()
plt.scatter(x, y)
fig.set_size_inches(6, 4)
plt.ylim(0,100)
plt.xlim(0,100000)
plt.savefig('flickr_corr.png', dpi=128, alpha=True)
