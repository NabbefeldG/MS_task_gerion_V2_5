import numpy as np
# import keyboard
from time import sleep


def press(value):
    global x
    x = value
#


def wait_for_response():
    while True:
        global x

        if x is not None:
            temp = x
            x = None
            return temp
        #
        sleep(0.1)
    #
#


def generate_stimuli():
    l = ([(0, 0)] + [(0, 1)] +
         [(1, 0)] + [(1, 1)] +
         [(2, 0)] + [(2, 1)] +
         [(3, 0)] + [(3, 1)])
    stimuli = []
    [stimuli.extend(np.random.permutation(2*l)) for _ in range(100)]

    return stimuli
#


class SpoutBiasCorrection:
    def __init__(self, left_in, right_in):
        self.left_in = left_in
        self.left_out = self.left_in - 80
        self.left_current = self.left_in

        self.right_in = right_in
        self.right_out = self.right_in - 80
        self.right_current = self.right_in

        self.left_trial_response_history = list()
        self.right_trial_response_history = list()
    #

    def single_spout_trial_check(self, both_spouts, next_stimulus_side_left):
        # if the last 3 responses in both the left and right trials were on the same side (very strong side-bias)
        # use a single spout trial to "remind" the mouse that there is another spout available
        if len(self.left_trial_response_history) > 3 and len(self.right_trial_response_history) > 3:
            if np.all(np.array(self.left_trial_response_history[-3:]) ==
                      (1 - np.array(self.right_trial_response_history[-3:]))):
                # if next_stim is "left" & the last left-response was false, then don't use both_spouts
                if next_stimulus_side_left != self.left_trial_response_history[-1]:
                    # this becomes false
                    both_spouts = 0
                #
            #
        #

        return both_spouts
    #

    def apply_spout_position_bias_correction(self, stimulus_side_left, response_left, left_in, right_in,
                                             left_out, right_out, factors=(1, 2, 5), thresholds=(0.05, 0.15, 0.30)):
        # update in case the user changes the inner positions
        if self.left_in != left_in:
            self.left_in = left_in
            self.left_current = left_in
        #
        if self.right_in != right_in:
            self.right_in = right_in
            self.right_current = right_in
        #

        if self.left_out != left_out:
            self.left_out = left_out
            if self.left_current < left_out:
                self.left_current = left_out
            #
        #
        if self.right_out != right_out:
            self.right_out = right_out
            if self.right_current < right_out:
                self.right_current = right_out
            #
        #

        # update response histories
        if stimulus_side_left == 1:
            self.left_trial_response_history.append(1 * (response_left == stimulus_side_left))
            if len(self.left_trial_response_history) > 10:
                self.left_trial_response_history = self.left_trial_response_history[-10:]
            #
        else:
            self.right_trial_response_history.append(1 * (response_left == stimulus_side_left))
            if len(self.right_trial_response_history) > 10:
                self.right_trial_response_history = self.right_trial_response_history[-10:]
            #
        #

        if True:  # stimulus_side_left != response_left:
            try:
                # check bias
                if len(self.left_trial_response_history) > 0:
                    performance_left = np.array(self.left_trial_response_history).mean()
                else:
                    performance_left = 0.5
                #
                if len(self.right_trial_response_history) > 0:
                    performance_right = np.array(self.right_trial_response_history).mean()
                else:
                    performance_right = 0.5
                #

                perf_diff = abs(performance_left - performance_right)
                if perf_diff > thresholds[0]:
                    correction_factor = factors[0]
                else:
                    correction_factor = 0
                if perf_diff > thresholds[1]:
                    correction_factor = factors[1]
                if perf_diff > thresholds[2]:
                    correction_factor = factors[2]
                #
            except:
                performance_left = 0
                performance_right = 0
                correction_factor = 0
            #
        #

        # In case of errors, compute the performances side-wise and the apply the correction factors
        if stimulus_side_left != response_left:
            # now apply the correction_factor
            if len(self.left_trial_response_history) == 10 and len(self.right_trial_response_history) == 10:
                if performance_left - performance_right < 0:
                    # left is worse -> mouse has a right-bias

                    # e.g.:
                    # l: 0.7, r: 0.9
                    # current: left_side, response: right
                    # if response_left is 0: wrong right response -> change
                    # if response_left is 1: don't do anything
                    if response_left == 0:
                        if self.left_current < self.left_in:
                            # left can be moved further in
                            self.left_current += correction_factor
                            if self.left_current > self.left_in:
                                self.left_current = self.left_in
                            #
                        else:
                            # left can't be moved further in
                            self.right_current -= correction_factor
                            if self.right_current < self.right_out:
                                self.right_current = self.right_out
                            #
                        #
                    #
                else:
                    # left_bias
                    if response_left == 1:
                        if self.right_current < self.right_in:
                            # right can be moved further in
                            self.right_current += correction_factor
                            if self.right_current > self.right_in:
                                self.right_current = self.right_in
                            #
                        else:
                            # right can't be moved further in
                            self.left_current -= correction_factor
                            if self.left_current < self.left_out:
                                self.left_current = self.left_out
                            #
                        #
                    #
                #
            #
        #

        print('left_current: ', self.left_current,
              'right_current: ', self.right_current,
              'left_in: ', self.left_in,
              'right_in: ', self.right_in,
              'left_out: ', self.left_out,
              'right_out: ', self.right_out,
              'left: ', performance_left,
              'right: ', performance_right)
        #

        return self.left_current, self.right_current
    #
#


if __name__ == '__main__':
    x = None
    keyboard.add_hotkey('left', lambda: press(1))
    keyboard.add_hotkey('right', lambda: press(0))

    stimuli = generate_stimuli()
    print(stimuli)

    bias = SpoutBiasCorrection(left_in=80, right_in=80)

    for i in range(len(stimuli)):
        stimulus_side_left = stimuli[i][1]
        both_spouts = 1

        print('both_spouts: ', bias.single_spout_trail_check(both_spouts, stimulus_side_left))
        if stimulus_side_left == 1:
            print('L')
        else:
            print('R')
        #
        response = wait_for_response()

        bias.apply_spout_position_bias_correction(stimulus_side_left=stimulus_side_left, response_left=response,
                                                  left_in=80, right_in=80)
    #
#
