import numpy as np
import matplotlib.pyplot as plt


class ConditionTracker:
    def __init__(self, probability):
        self.full_history = [list(), list()]  # the full history since last probability change
        # self.recent_history = list()  # the last two occurrences
        self.current_probability = probability
    #

    def update(self, target_side_left, probability):
        if not probability == self.current_probability:
            for side_id in range(2):
                if len(self.full_history[side_id]) > 2:
                    self.full_history[side_id] = self.full_history[side_id][-2:]
                else:
                    self.full_history[side_id] = []
                #
            #
            self.current_probability = probability
        #

        # print(len(self.full_history[0]) + len(self.full_history[1]))
        if len(self.full_history[target_side_left]) > 1:
            # present a both
            condition_active = int(np.mean(self.full_history[target_side_left]) < probability)
        else:
            condition_active = int(np.random.rand() < probability)
        #

        # update full history
        self.full_history[target_side_left].append([condition_active])

        return condition_active
    #

    # def update(self, target_side_left, probability):
    #     if not probability == self.current_probability:
    #         for side_id in range(2):
    #             if len(self.full_history[side_id]) > 2:
    #                 self.full_history[side_id] = self.full_history[side_id][-2:]
    #             else:
    #                 self.full_history[side_id] = []
    #             #
    #         #
    #     #
    #
    #     # print(len(self.full_history[0]) + len(self.full_history[1]))
    #     if len(self.full_history[target_side_left]) > 1:
    #         # print('diff', abs(np.sum(self.full_history[0]) - np.sum(self.full_history[1])))
    #         if False:  # abs(np.mean(self.full_history[target_side_left]) - p) > 0.1:
    #             # if abs(np.mean(self.full_history[target_side_left]) - np.mean(self.full_history[1 - target_side_left])) > 0.1:
    #             # there is an inbalance
    #             both_spouts = int(np.mean(self.full_history[target_side_left]) < p)
    #             print(0)
    #         else:
    #             # print(abs(np.mean(self.full_history[target_side_left]) - p))
    #             if abs(np.mean(self.full_history[target_side_left]) - p) > -0.01:
    #                 # the probability is outside of a range of +-2% of the target probability for this side.
    #                 both_spouts = int(np.mean(self.full_history[target_side_left]) < p)
    #                 print(1)
    #             else:
    #                 both_spouts = int(np.random.rand() < p)
    #                 print(2)
    #
    #                 # If it's drawn random then check that I don't keep presenting it on the same side over and over
    #                 if both_spouts:
    #                     if np.sum(np.array(self.recent_history) == target_side_left) > 1:
    #                         both_spouts = 0
    #                         print(3)
    #                     #
    #                 #
    #             #
    #         #
    #     else:
    #         print(4)
    #         both_spouts = int(np.random.rand() < p)
    #     #
    #
    #     # update full history
    #     self.full_history[target_side_left].append(both_spouts)
    #
    #     # update recent history to check for repetitions of the same condition
    #     if both_spouts:
    #         if len(self.recent_history) > 1:
    #             self.recent_history[:1] = [self.recent_history[1]]
    #             self.recent_history[1] = target_side_left
    #         else:
    #             self.recent_history.append(target_side_left)
    #         #
    #     #
    #
    #     return both_spouts
    # #
#


class ConditionTrackerConditionWise:
    def __init__(self, probability):
        # Conditions I'm considering: target_side, modality, target_distractor_difference
        # self.full_history = [list(), list()]  # the full history since last probability change
        self.full_history = np.empty([2, 3, 7], dtype=object)
        self.full_history.fill([])

        self.current_probability = probability
    #

    def update(self, target_side_left, modality, difference, probability):
        if not probability == self.current_probability:
            for side_id in range(2):
                for modality_id in range(3):
                    for difference_id in range(7):
                        if len(self.full_history[side_id, modality_id, difference_id]) > 2:
                            self.full_history[side_id, modality_id, difference_id] = self.full_history[side_id, modality_id, difference_id][-2:]
                        else:
                            self.full_history[side_id, modality_id, difference_id] = []
                        #
                    #
                #
            #
            self.current_probability = probability
        #

        if len(self.full_history[target_side_left, modality, difference]) > 1:
            # present a both
            condition_active = int(np.mean(self.full_history[target_side_left, modality, difference]) < probability)
        else:
            condition_active = int(np.random.rand() < probability)
        #

        # update full history
        self.full_history[target_side_left, modality, difference].append([condition_active])

        return condition_active
    #
#


if __name__ == '__main__':
    p = 0.33
    n = 200

    both_spouts_controller = ConditionTracker(probability=p)

    history = np.zeros((n, 4))
    both_spouts_tracker = [[list(), list()], [list(), list()]]
    for i in range(n):
        left = np.mod(i, 2)
        if i > 0 and np.random.rand() < 0.05:
            left = int(history[:i, 0].mean() < 0.5)
        else:
            left = int(np.random.rand() < 0.5)
        #
        both_spouts = both_spouts_controller.update(target_side_left=left, probability=p)

        history[i, :2] = [left, both_spouts]
        history[i, 2] = np.nan  # both_spouts
        history[i, 3] = np.nan  # both_spouts

        both_spouts_tracker[left][0].append(i)
        both_spouts_tracker[left][1].append(both_spouts)
    #

    history[1:, 0] = [history[:i, 0].mean() for i in range(1, history.shape[0])]
    history[1:, 1] = [history[:i, 1].mean() for i in range(1, history.shape[0])]
    history[1:, 2] = [history[:i, 2].mean() for i in range(1, history.shape[0])]
    history[1:, 3] = [history[:i, 3].mean() for i in range(1, history.shape[0])]

    history[1:len(both_spouts_tracker[0][1]), 2] = [np.mean(both_spouts_tracker[0][1][:i]) for i in range(1, len(both_spouts_tracker[0][1]))]
    history[1:len(both_spouts_tracker[1][1]), 3] = [np.mean(both_spouts_tracker[1][1][:i]) for i in range(1, len(both_spouts_tracker[1][1]))]

    plt.plot(history[:, :2])
    plt.plot(both_spouts_tracker[0][0], history[:len(both_spouts_tracker[0][0]), 2], '-')
    plt.plot(both_spouts_tracker[1][0], history[:len(both_spouts_tracker[1][0]), 3], '-')
    plt.plot(np.array(both_spouts_tracker[0][0])[np.array(both_spouts_tracker[0][1]) == 1], history[:len(both_spouts_tracker[0][0]), 2][np.array(both_spouts_tracker[0][1]) == 1], 'x')
    plt.plot(np.array(both_spouts_tracker[1][0])[np.array(both_spouts_tracker[1][1]) == 1], history[:len(both_spouts_tracker[1][0]), 3][np.array(both_spouts_tracker[1][1]) == 1], 'x')
    plt.legend(['1', '2', '3', '4'])
    plt.show()
#
