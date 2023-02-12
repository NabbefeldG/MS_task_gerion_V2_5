import numpy as np
import matplotlib.pyplot as plt
from time import time


def generate_pseudorandom_sequence(visual_probability=0.3333, tactile_probability=0.3333,
                                   discrimination_probability=0.2):
    visuotactile_probability = 1 - visual_probability - tactile_probability

    sequence = list()
    id_list = list()

    conditions = [(0, 0, 0), (0, 1, 0),
                  (1, 0, 0), (1, 1, 0),
                  (2, 0, 0), (2, 1, 0),
                  (0, 0, 1), (0, 1, 1),
                  (1, 0, 1), (1, 1, 1),
                  (2, 0, 1), (2, 1, 1)]
    condition_ids = np.arange(len(conditions))

    target_probs = np.array([visual_probability, visual_probability,
                             tactile_probability, tactile_probability,
                             visuotactile_probability, visuotactile_probability])

    # now compute the relative probability for detection and discrimination trials
    target_probs = np.array(list(target_probs * (1 - discrimination_probability)) +
                            list(target_probs * discrimination_probability))

    # normalize probabilities so they add to 1. This is important for the calculation of the target_occurences
    target_probs = target_probs / sum(target_probs)

    for i in range(1000):
        if len(id_list) < 3:
            # 3 are required for the comparrision if the same stimulus is presented too often in a row, before 3 this makes no sense
            next_id = np.random.choice(condition_ids, 1, p=target_probs)[0]
        else:
            while True:
                n_occurrences = np.array([(id_list == c).sum() for c in condition_ids])
                target_occurences = float(len(id_list)) * target_probs
                deviation_from_target_dist = n_occurrences - target_occurences
                # print(target_occurences, n_occurrences, deviation_from_even_dist, np.max(deviation_from_even_dist))

                if np.max(deviation_from_target_dist) + np.min(deviation_from_target_dist) > 0:
                    # one condition is occuring too often
                    if np.any(deviation_from_target_dist > 2):
                        # check if there is also a condition that is too underrepresented
                        possible_conditions = np.where(deviation_from_target_dist < 2)[0]
                        if len(possible_conditions) > 0:
                            # this means I have a condition that is too underrepresented as well. I'm picking this one then.
                            next_id = np.random.choice(possible_conditions, 1)[0]
                        else:
                            # randomly pick one of the conditions, that has fewer occurences
                            possible_conditions = np.where(deviation_from_target_dist < 0)[0]
                            if len(possible_conditions) < 1:
                                # I think this can not be the case ever, but I don't want to take any risks
                                next_id = np.random.choice(condition_ids, 1)[0]
                            else:
                                next_id = np.random.choice(possible_conditions, 1)[0]
                                # print(i, next_id)
                            #
                        #
                    else:
                        next_id = np.random.choice(condition_ids, 1)[0]
                    #
                else:
                    # one condition is not occurring often enough
                    if np.any(deviation_from_target_dist < -2):
                        # check if there is also a condition that is too overrepresented
                        possible_conditions = np.where(deviation_from_target_dist < -2)[0]
                        if len(possible_conditions) > 0:
                            # this means I have a condition that is too overrepresented as well. I'm picking this one then.
                            next_id = np.random.choice(possible_conditions, 1)[0]
                        else:
                            # randomly pick one of the conditions, that is underrepresented so far
                            possible_conditions = np.where(deviation_from_target_dist > 0)[0]
                            if len(possible_conditions) < 1:
                                # I think this can not be the case ever, but I don't want to take any risks
                                next_id = np.random.choice(condition_ids, 1)[0]
                            else:
                                next_id = np.random.choice(possible_conditions, 1)[0]
                            #
                        #
                    else:
                        next_id = np.random.choice(condition_ids, 1)[0]
                    #
                # END OF DETERMINE next_id section

                new_stim = False
                if target_probs[next_id] < 0.001:
                    # I had it while testing that stimuli occurred that souldn't have been presented that session.
                    # Likely due to rounding errors of the other probabilities, this should prohibit that.
                    new_stim = True
                #

                # same side repetitions ################################################################################
                if not new_stim:
                    # if np.all(np.array(sequence[-3:])[:, 1] == conditions[next_id][1]):
                    if np.all(np.mod(np.array(id_list[-3:]), 2) == np.mod(next_id, 2)):
                        # 50% chance to draw a new stimulus if the previous 2 trials were already shown on the same side
                        # print([id_list[-3:], next_id])
                        if np.random.rand() < 0.5:
                            new_stim = True
                        #
                    #
                #

                # if (0.2 <= discrimination_probability <= 0.8):
                #     if np.all(sequence[-1][2] == conditions[next_id][2]):
                #         # 50% chance to draw a new stimulus if the previous trial was the same detection/discrimination condition
                #         if np.random.rand() < 0.5:
                #             new_stim = True
                #         #
                #     #
                # #

                # try to correct detection/discrimination repetitions ##################################################
                if not new_stim:
                    if np.all(sequence[-1][2] == conditions[next_id][2]):
                        # check if the previous trial was the same detection/discrimination condition
                        if discrimination_probability < 0.2:
                            # if disc_prob is low, only check for repeated disc trials
                            if sequence[-1][2] == 1:
                                if np.random.rand() < 0.5:
                                    # 50% chance to draw a new stimulus
                                    new_stim = True
                                #
                            #
                        elif discrimination_probability > 0.8:
                            # if disc_prob is high, only check for repeated detection trials
                            if sequence[-1][2] == 0:
                                if np.random.rand() < 0.5:
                                    # 50% chance to draw a new stimulus
                                    new_stim = True
                                #
                            #
                        #
                        else:
                            # otherwise try to correct either repetition
                            if np.random.rand() < 0.5:
                                # 50% chance to draw a new stimulus
                                new_stim = True
                            #
                        #
                    #
                #

                # identical condition repetition #######################################################################
                if not new_stim:
                    if np.all(np.array(id_list[-1:]) == next_id):
                        # again 50% chance to draw a new stimulus if the exact same stimulus has been shown the previous 2 trials already
                        if np.random.rand() < 0.5:
                            new_stim = True
                        #
                    #
                #

                # ######################################################################################################
                if not new_stim:
                    break
                #
            #
        #

        # if next_id == 4 or next_id == 5 or next_id == 10 or next_id == 11:
        #     print('break')
        # #

        id_list.append(next_id)
        sequence.append(conditions[id_list[-1]])
    #

    return sequence, id_list
#


class PseudoRandomTrialSequence:
    def __init__(self):
        # self.visual_probability = visual_probability
        # self.tactile_probability = tactile_probability
        # self.discrimination_probability = discrimination_probability
        self.visual_probability = None
        self.tactile_probability = None
        self.discrimination_probability = None

        self.sequence_id = -1
        self.sequence = []
        self.id_list = []
        # self.sequence, self.id_list = \
        #     generate_pseudorandom_sequence(visual_probability=self.visual_probability,
        #                                    tactile_probability=self.tactile_probability,
        #                                    discrimination_probability=self.discrimination_probability)
    #

    def get_next_trial(self, visual_probability, tactile_probability, discrimination_probability):
        if (self.visual_probability == visual_probability and
                self.tactile_probability == tactile_probability and
                self.discrimination_probability == discrimination_probability and
                len(self.sequence) > self.sequence_id + 1):

            self.sequence_id += 1
        else:
            self.visual_probability = visual_probability
            self.tactile_probability = tactile_probability
            self.discrimination_probability = discrimination_probability

            print(self.sequence_id)

            self.sequence_id = 0
            self.sequence, self.id_list = \
                generate_pseudorandom_sequence(visual_probability=self.visual_probability,
                                               tactile_probability=self.tactile_probability,
                                               discrimination_probability=self.discrimination_probability)
        #

        return self.sequence[self.sequence_id], self.id_list[self.sequence_id]
    #
#


if __name__ == '__main__':
    st = time()

    visual_probability = 0.3333
    tactile_probability = 0.3333
    discrimination_probability = 0.0

    seq = PseudoRandomTrialSequence(visual_probability=visual_probability,
                                    tactile_probability=tactile_probability,
                                    discrimination_probability=discrimination_probability)
    # sequence, id_list = generate_pseudorandom_sequence()

    sequence = []
    id_list = []
    for i in range(1000):
        s, id = seq.get_next_trial(visual_probability=visual_probability,
                                   tactile_probability=tactile_probability,
                                   discrimination_probability=discrimination_probability)
        print("modality: %d, side: %d, discrimination: %d" % (s[0], s[1], s[2]))
        sequence.extend([s])
        id_list.extend([id])
    #
    print(time() - st)

    plt.plot([np.mod(id_list[:i], 2).mean() for i in range(len(id_list))])
    plt.show()

    plt.plot([np.mod(id_list[i-20:i], 2).mean() for i in range(len(id_list))])
    plt.show()

    # print([(np.array(id_list) == i).mean() for i in range(12)])
    # print(target_probs)

    # plt.plot(id_list)
    # plt.show()
    # plt.close()
    #-
    # plt.hist(id_list, 12)
    # plt.show()
    # plt.close()

    # [plt.hist(np.diff(np.where(np.array(id_list)==i)[0]), bins=range(0, 100, 5), range=(0, 100), alpha=0.4, density=True, cumulative=False) for i in [0, 1, 10, 11]]
    for i in range(12):
        h, b = np.histogram(np.diff(np.where(np.array(id_list) == i)[0]), bins=25, normed=True)
        plt.plot(b[1:], np.cumsum(h) * (b[1] - b[0]))
    #
    plt.show()


    # [plt.hist(np.diff(np.where(np.array(id_list)==i)[0]), bins=range(0, 100, 5), range=(0, 100), alpha=0.4, density=True, cumulative=False) for i in [0, 1, 10, 11]]
    for i in range(2):
        plt.hist(np.diff(np.where(np.mod(np.array(id_list), 2) == i))[0], bins=range(10), alpha=0.4, density=True)
        # h, b = np.histogram(np.diff(np.where(np.mod(np.array(id_list), 2) == i)), bins=10, normed=True)
        # plt.plot(b[1:], np.cumsum(h) * (b[1] - b[0]))
    #
    plt.show()
#
