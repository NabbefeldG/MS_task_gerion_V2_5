import numpy as np


def determine_modality_id_with_bias_correction(data, max_modality_imbalance_factor=4):
    # data has to be a 2D array in the shape of (n_trials, 2), with each inner element consisting of:
    # [modality_id, correct_response]
    # max_modality_imbalance_factor: determines the maximum ratio of
    # e.g.: tact/(vis + tact) < (1 / max_modality_imbalance_factor)

    # returns modality_id as: [0:vis, 1:tact, 2:vis-tact]

    data = np.array(data)
    if data.shape[0] == 0:
        # fix it for the first trial
        data = np.array([[-1, -1]])
    #
    modality_ids = data[:, 0]
    n_trials = np.nan_to_num(np.array([(modality_ids == 0).sum(),
                                       (modality_ids == 1).sum(),
                                       (modality_ids == 2).sum()]))
    # print('MBC:')
    # print(data.shape)
    # print(data)
    # print(n_trials)
    if n_trials.sum() < 20:
        # this applies for the first 20 trial and is just supposed to balance the modalities
        temp = np.sort(n_trials)
        if (temp[1] - temp[0]) > 1:
            # next trials is the modality that was presented least fo far
            return np.argmin(n_trials)
        else:
            # if they are sufficiently balance, then just pick at random
            return np.random.randint(0, 3, 1)[0]
        #
    else:
        # due to the no more than 1 n_trial difference above I, have 6-7 trials per modality here to start with
        if n_trials[2] / n_trials.sum() < (1. / 3.):
            # stick to the 33% vis-tact for now
            return 2
        else:
            # if there were enough (>= 33%) vis-tact trials, then pick one of the [vis, tact] based on performance

            # use a maximum ratio of imbalance to avoid exclusively one modality!
            n_visual_ratio = n_trials[0] / n_trials[:2].sum()

            if n_visual_ratio < (1. / max_modality_imbalance_factor):
                # checks if there are too few visual trial
                return 0
            elif (1 - n_visual_ratio) < (1. / max_modality_imbalance_factor):
                # checks for too few tactile trials
                return 1
            else:
                # otherwise balance based on performance

                performance = np.array([data[modality_ids == 0, 1].mean(),
                                        data[modality_ids == 1, 1].mean(),
                                        data[modality_ids == 2, 1].mean()])
                # print(performance)

                # print('vis (%d): %f' % (n_trials[0], performance[0]))
                # print('tact (%d): %f: ' % (n_trials[1], performance[1]))
                # print('vis-tact (%d): %f: ' % (n_trials[2], performance[2]))

                # map the range 50% to 100% to 0-1
                performance = 2 * (performance - 0.5)
                performance[performance < 0] = 0

                # ratio of tactile / (vis + tact) performance
                performance_ratio = performance[1] / (performance[:2].sum())
                # print(performance_ratio)
                # print('')

                return int(np.random.rand() > performance_ratio)
            #
        #
    #
#
