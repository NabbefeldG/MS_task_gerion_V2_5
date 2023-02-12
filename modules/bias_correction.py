import numpy as np


def same_opposite_correction(stimulus_site_record):
    # Bias correction according to Knutsen et al. 2006
    # Same-opposite bias
    # over the last 10 trials
    # ##
    # stimulus_site_record: a 10-value long vector containing the last 10 response_sites_values [0 or 1].
    #                       left: 1, right: 0
    #                       if stored in a boolean array please convert to numerical using e.g.: np.astype()

    # calc S-O measure
    n_opposite_responses = np.sum(np.abs(np.subtract(stimulus_site_record[1:], stimulus_site_record[:-1])))
    n_same_responses = 9 - n_opposite_responses

    # clac L-R measure
    n_left_responses = np.sum(stimulus_site_record[1:])
    n_right_responses = 9 - n_left_responses

    bias_correction_mode_original = np.abs(n_same_responses - n_opposite_responses) - np.abs(n_left_responses - n_right_responses)

    # ## simplified calculation ## #
    # calc S-O measure
    n_opposite_responses = np.sum(np.abs(np.subtract(stimulus_site_record[1:], stimulus_site_record[:-1])))
    # clac L-R measure
    n_left_responses = np.sum(stimulus_site_record[1:])
    bias_correction_mode = 2*(np.abs(n_opposite_responses - 4.5) - np.abs(n_left_responses - 4.5))

    # if bias_correction_mode != bias_correction_mode_original:
    #     print('NOT EQUAL!!!')
    # #

    previous_site = stimulus_site_record[-1]
    # I now need to implement a LEFT vs. RIGHT correction part

    #

    if bias_correction_mode < 0:  # more L-R bias
        # print('More _L-R')
        if n_left_responses > 4:
            # more left responses - so right next
            # print('Too left opposite: ' + str(n_left_responses))
            next_stimulus_left = 0
        else:
            # more right responses - so switch from last
            # print('Too many same: ' + str(n_left_responses))
            next_stimulus_left = 1
        #
    elif bias_correction_mode == 0:
        # This doesn't mean that there is no bias.
        # But there is no clear way to correct which ever one it is, so wait until the next trial.
        # print('equal: '+str(n_opposite_responses)+', '+str(n_left_responses))
        # I had the issue that if the mouse really exclusively answered on one side than both biases were always equal
        # next_stimulus_left = np.random.rand() > 0.5
        next_stimulus_left = 1 - previous_site
    else:
        # print('More _S-O')
        if n_opposite_responses > 4:
            # more opposite responses - so repeat the last side
            # print('Too many opposite: '+str(n_opposite_responses))
            next_stimulus_left = previous_site
        # elif n_opposite_responses == 5:
        #     # This doesn't mean that there is no bias.
        #     # But there is no clear way to correct which ever one it is, so wait until the next trial.
        #     print('equal: '+str(n_opposite_responses))
        #     next_stimulus_left = np.random.rand() > 0.5
        else:
            # more same responses - so switch from last
            # print('Too many same: '+str(n_opposite_responses))
            next_stimulus_left = 1 - previous_site
        #
    #

    return next_stimulus_left
#


def bias_correction(stimulus_site_record, n_no_responses):
    stimulus_site_record = np.array(stimulus_site_record)
    if stimulus_site_record.shape[0] < 10 or n_no_responses > 5:
        if stimulus_site_record.shape[0] > 1:
            if stimulus_site_record[-1] == stimulus_site_record[-2]:
                if stimulus_site_record[-1] == 0:
                    next_stimulus_left = True
                else:
                    next_stimulus_left = False
                #
            else:
                next_stimulus_left = np.random.rand() > 0.5
            #
        else:
            next_stimulus_left = np.random.rand() > 0.5
        #
    else:
        # last_ten_trials = stimulus_site_record[trial_id - 10:trial_id].astype(np.int8)
        last_ten_trials = stimulus_site_record[-10:].astype(np.int8)
        next_stimulus_left = same_opposite_correction(last_ten_trials)
    #

    return next_stimulus_left
#
