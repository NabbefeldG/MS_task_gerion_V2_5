import numpy as np
import keyboard
from time import sleep


x = None
keyboard.add_hotkey('left', lambda: press(1))
keyboard.add_hotkey('right', lambda: press(0))


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


if __name__ == '__main__':
    stimuli = generate_stimuli()
    print(stimuli)

    in_l, in_r = 30, 30
    out_l, out_r = 20, 20
    l = 30
    r = 30

    history_stimulus = list()
    history_responses = list()

    i = 0
    while True:
        i += 1
        if stimuli[i][1] == 1:
            print('L')
        else:
            print('R')
        #

        response = wait_for_response()
        history_stimulus.append(stimuli[i][1])
        history_responses.append(1 * (response == stimuli[i][1]))

        if len(history_stimulus) > 10:
            history_stimulus = history_stimulus[1:]
            history_responses = history_responses[1:]
        #

        try:
            # check bias
            performance_left = np.array(history_responses)[np.array(history_stimulus) == 1].mean()
            performance_right = np.array(history_responses)[np.array(history_stimulus) == 0].mean()

            perf_diff = abs(performance_left - performance_right)
            if perf_diff > 0.05:
                f = 1
            else:
                f = 0
            if perf_diff > 0.15:
                f = 2
            if perf_diff > 0.30:
                f = 3
            #
        except:
            performance_left = 0
            performance_right = 0
            f = 0
            print('asd')
        #

        if len(history_stimulus) >= 10:
            if performance_left - performance_right < 0:
                # left is better
                if l < in_l:
                    # left can be moved further in
                    l += f
                    if l > in_l:
                        l = in_l
                    #
                else:
                    # left can't be moved further in
                    r -= f
                    if r < out_r:
                        r = out_r
                    #
                #
            else:
                # right is better
                if r < in_r:
                    # left can be moved further in
                    r += f
                    if r > in_r:
                        r = in_r
                    #
                else:
                    # left can't be moved further in
                    l -= f
                    if l < out_l:
                        l = out_l
                    #
                #
            #
        #

        print('l: ', l,
              'r: ', r,
              'left: ', performance_left,
              'right: ', performance_right)
        #

        # if history_responses[-1]:
        #     print('correct', history_responses)
        # else:
        #     print('error', history_responses)
        # #
    #
#
