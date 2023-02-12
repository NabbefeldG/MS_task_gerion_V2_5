import numpy as np
import h5py
import os
from time import time


class H5Object:
    def __init__(self, file_path, channel_names=None, n_dimensions=None):
        # file_path: Full path to new *.h5 file
        # channel_names: List of all the variables. Data is later saved under this channel names.
        # n_dimensions: Shape of data to be saved (1D or 2D). In the same order as channel_names.
        #               1D: wheel - single value at a time
        #               2D: DI - fixed number of channels e.g.: 8 ('Dev1/port0/line0:7') and multiple values
        #
        # Example:
        # h5f = H5Object(path.join(folder_path, 'test_file.h5'),
        #                     channel_names=['DI', 'wheel'], n_dimensions=[2, 1])

        self._file = h5py.File(file_path, 'w')
        self._all_datasets = dict()

        # initialize channels
        for i, name in enumerate(channel_names):
            if n_dimensions[i] == 1:
                self._all_datasets[name] = self._file.create_dataset(name, (0,), compression="gzip", chunks=True,
                                                                     maxshape=(None,))
            elif n_dimensions[i] == 2:
                self._all_datasets[name] = self._file.create_dataset(name, (0, 0,), compression="gzip", chunks=True,
                                                                     maxshape=(None, None,))
            else:
                raise Exception('Trying to create "dataset" with incompatible shape in h5-file!')
            #
        #
    #

    def add_data(self, channel_name, data):
        # appends data to file initialized with __init__()
        # only data declared in __init__() can be added
        # if using 2D data it is required to provide data for all channels
        data = np.array(data)
        data_shape = data.shape
        n_dim = len(data_shape)
        if n_dim == 0:
            data = [data]
        current_shape = self._all_datasets[channel_name].shape
        if n_dim == 1:
            current_shape = current_shape[0]
            data_size = data_shape[0]
            self._all_datasets[channel_name].resize((current_shape + data_size,))
            self._all_datasets[channel_name][-data_size:] = data
        elif n_dim == 2:
            data_size = data_shape[1]
            self._all_datasets[channel_name].resize((data_shape[0], current_shape[1] + data_size,))
            self._all_datasets[channel_name][:, -data_size:] = data
        else:
            raise Exception('Incompatible data input for h5-file!')
        #
    #

    def close(self):
        try:
            self._file.close()
        except:
            pass
        #
    #

    def __del__(self):
        try:
            self._file.close()
        except:
            pass
        #
    #
#


if __name__ == '__main__':
    file_path = 'test_file.h5'
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass
    #

    parameters = ['wheel', 'DI']
    n_dimensions = [1, 2]

    try:
        h5f = H5Object(file_path, parameters, n_dimensions)
        # h5f = h5py.File(file_path, 'a')
        # data_shape = (1,)
        # ds = np.array(len(parameters),)
        sample_size = 10000
        # ds = list()
        st = time()
        t1 = st

        # for value_id, value_name in enumerate(parameters):
        #     ds.append(h5f.create_dataset(value_name, (0,), compression="gzip", chunks=True, maxshape=(None,)))
        # #
        # print(time() - st)

        for iteration in range(200):
            if iteration == 199:
                t1 = time()
            for value_name in parameters:
                if value_name == 'wheel':
                    new_sample = np.random.rand(1,)
                else:
                    new_sample = np.random.rand(2, sample_size,)
                #

                h5f.add_data(value_name, data=new_sample)
        #
        print(time() - t1)
        print(time() - st)
    except Exception as e:
        print(e)
        pass
    #
    # Try to close the file no matter what
    h5f.close()

    # read
    h5f = h5py.File(file_path, 'r')
    props = h5f.keys()
    print(props)

    for value_name in props:
        print(h5f[value_name].shape)
    #

    # ## CONCLUSION ## #
    # I can quickly write large chunks also split into separate channels.
    # So for the behavior software that means that its best to continuously acquire the data buffered, then hand that
    # to the stimulus part to check if the mouse licked to early and during the reward period check if it answered
    # correctly.
    # After every trial i have time to save the data down to the records file

    #

    # # open to check the file
    # h5f = h5py.File(file_path, 'r')
    # print(np.array(h5f['para0']))
    # print(h5f['para0'].shape)
    #
    # # Try to close the file no matter what
    # try:
    #     h5f.close()
    # except:
    #     pass
    # #
#
