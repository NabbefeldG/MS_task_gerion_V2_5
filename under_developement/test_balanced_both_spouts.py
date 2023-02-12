import numpy as np
import matplotlib.pyplot as plt


history = np.array((1000, 3))

if __name__ == '__main__':
    for i in range(1000):
        left = int(np.random.rand() < 0.5)
        both_spouts = int(np.random.rand() < 0.2)
        history[i, :] = [left, both_spouts]
    #
#

# history[:, 2] = np.sum((history[:, 0] == 0) and (history[:, 1] == 1))
# history[:, 2] = np.sum((history[:, 0] == 1) and (history[:, 1] == 1))

plt.plot(history)
