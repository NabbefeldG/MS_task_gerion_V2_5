import numpy as np
import h5py
import matplotlib.pyplot as plt
from os import path
from glob import glob


def visualize_session(root_path):
    file_list = glob(path.join(root_path, '*.h5'))
    file_list = np.sort(file_list)

    initial_data = True
    data = None
    wheel = None
    photodiode = None

    # file_list = file_list[0:40]

    # for trial_id in [0, 1, 2, 3]:
    trial_id = -1
    # while True:
    d = dict()
    for file_path in file_list:
        try:
            trial_id += 1
            print(trial_id)
            # h5f = h5py.File('%s_%06d.h5' % (file_base, trial_id), 'r')
            h5f = h5py.File(file_path, 'r')
            props = h5f.keys()
            for key in props:
                if key in d:
                    try:
                        d[key].append(h5f[key][0])
                    except:
                        pass
                    #
                else:
                    d[key] = list(h5f[key])
                #
            #
            # print(props)
            #

            print(h5f['airpuff_pressure'][0])
            continue

            print(h5f['both_spouts'][0], h5f['auto_reward'][0], h5f['Response_left'][0])
            print(h5f.attrs['optogenetic_target'], h5f['optogenetic_trial_left'][0], h5f['optogenetic_trial_right'][0], h5f['optogenetic_power'][0])

            # print('both_spouts: ' + str(np.array(h5f['both_spouts'])))
            # print('both_spouts_probability: ' + str(np.array(h5f['both_spouts_probability'])))

            # for value_name in props:
            #     # print((value_name, h5f[value_name].shape))
            #     print((value_name, np.array(h5f[value_name])))
            # #
            temp_data = np.array(h5f['DI']).copy()
            temp_wheel = np.array(h5f['wheel']).copy()
            temp_photodiode = np.array(h5f['photodiode']).copy()
            temp_optogenetic_signal_0 = np.array(h5f['optogenetic_signal_0']).copy()
            temp_n_DI_samples = np.array(h5f['n_DI_samples_since_last_wheel_update']).copy()
            h5f.close()

            if initial_data:
                data = temp_data
                wheel = temp_wheel
                photodiode = temp_photodiode
                n_DI_samples = temp_n_DI_samples
                optogenetic_signal_0 = temp_optogenetic_signal_0
                initial_data = False
            else:
                data = np.concatenate((data, temp_data), axis=1)
                wheel = np.concatenate((wheel, temp_wheel), axis=0)
                photodiode = np.concatenate((photodiode, temp_photodiode), axis=0)
                n_DI_samples = np.concatenate((n_DI_samples, temp_n_DI_samples), axis=0)
                optogenetic_signal_0 = np.concatenate((optogenetic_signal_0, temp_optogenetic_signal_0), axis=0)
            #
        except OSError:
            break
        except Exception as e:
            print(e)
            break
        #
    #

    # data = np.uint8(255*data[:5, :10000000])
    data = np.uint8(255*data)

    interp_wheel = np.interp(np.arange(0, data.shape[1]), np.cumsum(n_DI_samples), wheel)
    interp_photodiode = np.interp(np.arange(0, data.shape[1]), np.cumsum(n_DI_samples), photodiode)

    speed = np.concatenate(([0], np.diff(interp_wheel)))
    # norm_speed = (speed - speed.min()) / (speed.max() - speed.min())

    norm_photodiode = (interp_photodiode - interp_photodiode.min()) / (interp_photodiode.max() - interp_photodiode.min())

    # interp_wheel, interp_photodiode, speed = None, None, None

    # data = np.concatenate((data, np.uint8(norm_speed[np.newaxis, :]), np.uint8(norm_photodiode[np.newaxis, :])), axis=0)
    # data[4, :] = np.uint8(255 * norm_speed[np.newaxis, :])
    data[6, :] = np.uint8(255 * norm_photodiode[np.newaxis, :])

    np.save('temp_data.npy', data)

    # plt.plot(wheel)
    # plt.plot(photodiode)
    plt.imshow(data, interpolation='nearest', aspect='auto')
    # plt.hold(True)
    # plt.plot(norm_speed + 7)
    # plt.plot(norm_photodiode+4)
    plt.show()

    a = data[3, :] > 0
    b = np.concatenate(([0], 1 - data[3, :-1]))
    rising_edges = np.uint8(a) - np.uint8(b > 1)
    rising_edges = np.where(rising_edges)
    rising_edges = rising_edges[:2:]
#


if __name__ == '__main__':
    # # root_path = r'C:\Data\MS_task_V2_0\photodiode_test_2\2020_10_28-17_04_25'
    # # root_path = r'W:\Multisensory_task\MS_task_V2_0\GN06\2020-10-30_14-10-39\task_data'
    # root_path = r'W:\Multisensory_task\MS_task_V2_0\GN10\2020-12-10_13-09-41\task_data'
    # root_path = glob(r'C:\data\MS_task_V2_3\test\*\task_data')[-1]
    # # root_path = r'C:\DATA\MS_task_V2_3\GN07\2021-04-13_16-01-49\task_data'
    # # root_path = r'W:\Multisensory_task\MS_task_V2_1\GN11\2021-01-22_16-26-25\task_data'

    root_path = glob(r'W:\Multisensory_task\DATA_RECORDED_IN_EPHYS_SETUP_SORT THIS_DONT_JUST_MERGE\MS_task_V2_3\GN07\2021-04-20_15-24-39\task_data')[-1]
    # root_path = glob(r'C:\data\MS_task_V2_5\test\*\task_data')[-1]
    # root_path = glob(r'C:\data\MS_task_V2_5_tactile_pressure_control\test\*\task_data')[-1]
    root_path = glob(r'C:\data\MS_task_V2_5\test\*\task_data')[-1]

    # file_base = r'C:\Data\MS_task_V2_0\test\2020_10_26-14_41_00\MS_task_V2_0_test_2020_10_26-14_41_00'
    visualize_session(root_path)
#
