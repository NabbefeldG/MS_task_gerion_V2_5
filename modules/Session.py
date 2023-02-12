import numpy as np
from time import time
from modules.save_to_h5 import H5Object
from os import makedirs
from os import path
from datetime import datetime
from modules.Serial_functions import send_data_until_confirmation, wait_for_signal_byte
from modules.PseudoRandomTrialSequence import PseudoRandomTrialSequence
from modules.SpoutBiasCorrection import SpoutBiasCorrection
from modules.condition_tracker import ConditionTracker, ConditionTrackerConditionWise
import configparser
# from modules.LabView_tcp_client import LabViewTCPClient
from modules.Labcams import Labcams
import random


# ## Define communication BYTES
# Commands to Teensy
START_TRIAL = 70
ADJUST_SPOUTES = 71
ADJUST_SPOUTSPEED = 73

# Feedback from Teensy
NextTrialByte = 110
VisualStimulusByte = 111
ResponseLeftByte = 112
ResponseRightByte = 113
ResponseMissedByte = 114


class GuiVariables:
    def __init__(self):
        self.display_both_spouts_probability = 0
        self.display_both_spouts_tact_probability = 0
        # self.display_both_spouts = False
        self.display_auto_reward = True
        self.display_target_side = False
        self.display_lick_left = False
        self.display_lick_right = False
        self.display_visual_trial_probability = 1.0
        self.display_tactile_trial_probability = 0.0
        # self.present_visuotactile_trials = False

        self.display_valve_left_duration = 7000
        self.display_valve_right_duration = 7000

        self.target_cue_probability_visual = 1.
        self.distractor_cue_probability_visual = 0.
        self.target_cue_probability_tactile = 1.
        self.distractor_cue_probability_tactile = 0.

        self.discrimination_probability = 0.

        self.optogenetic_trial_probability = 0.0

        self.optogenetic_target = "None"
        self.optogenetic_trial_left = False
        self.optogenetic_trial_right = False
        self.optogenetic_power = 0.0

        # self.og_modality = 0
        self.og_modality = (-1, -1)
        self.og_type = 0

        self.airpuff_pressure = 0.3
    #
#


class Session:
    def __init__(self, config, mouse_id, spout_positions, serial_obj, DAQ_disabled=False, optogenetic_target="None",
                 optogenetic_power=2.0, og_modality=(0, 0), og_type=0, visual_contrast_control=0, airpuff_pressure_control=0,
                 optogenetics_in_detection_conditions=False, optogenetics_bilateral=True):
        # define control experiments
        self.visual_contrast_control = visual_contrast_control
        self.airpuff_pressure_control = airpuff_pressure_control

        self.optogenetics_in_detection_conditions = optogenetics_in_detection_conditions
        self.optogenetics_bilateral = optogenetics_bilateral

        # Default Name if no control experiment
        experiment_name = 'MS_task_V2_5'

        if self.visual_contrast_control:
            experiment_name = 'MS_task_V2_5_visual_contrast_control'
            # # self.contrast_sequence = [0.0625, 0.125, 0.25, 0.5, 1.0] * 200
            # self.contrast_sequence = [0.33, 0.66, 1.0] * 350
            # np.random.shuffle(self.contrast_sequence)

            contrast_list = [0.15, 0.30, 1.0] * 2
            self.contrast_sequence = list()
            [self.contrast_sequence.extend(random.sample(contrast_list, k=len(contrast_list))) for _ in range(200)]
            print('Contrast Length: ' + str(len(self.contrast_sequence)))
        else:
            # self.contrast_sequence = [0.5] * 1000
            # if mouse_id == '2253':
            #     self.contrast_sequence = [0.3] * 1000
            # elif mouse_id == '2254':
            #     self.contrast_sequence = [0.5] * 1000
            # elif mouse_id == '2255':
            #     self.contrast_sequence = [0.3] * 1000
            # elif mouse_id == '2257':
            #     self.contrast_sequence = [0.5] * 1000
            # elif mouse_id == '2258':
            #     self.contrast_sequence = [0.5] * 1000
            # elif mouse_id == '2263':
            #     self.contrast_sequence = [0.5] * 1000
            # elif mouse_id == '2265':
            #     self.contrast_sequence = [0.5] * 1000
            # elif mouse_id == '2274':
            #     self.contrast_sequence = [0.4] * 1000
            # else:
            #     self.contrast_sequence = [0.5] * 1000
            #     [print("WARNING! NOT CONTRAST SETTING FOR MOUSE FOUND, USING DEFAULT CONTRAST OF 50%") for _ in range(100)]
            self.contrast_sequence = [1.0] * 1000
        #

        if self.airpuff_pressure_control:
            experiment_name = 'MS_task_V2_5_tactile_pressure_control'
        #

        DAQ_device = config['Setup']['ni_daq_devide']
        self.left_lick_DI_id = int(config['Setup']['left_lick_DI_id'])
        self.right_lick_DI_id = int(config['Setup']['right_lick_DI_id'])
        self.use_left_photodiode = int(config['Setup']['use_left_photodiode']) > 0
        self.use_right_photodiode = int(config['Setup']['use_right_photodiode']) > 0

        if not (self.use_left_photodiode or self.use_right_photodiode):
            raise Exception('No Photodiode configured')
        #

        self.mouse_id = mouse_id
        self.DAQ_disabled = DAQ_disabled

        try:
            raise(Exception('Dont Do This!'))
            # if False:
            # We decided to restart everything if the file is too old. Instead just save under a generated path

            # Try to fetch the Save_path from the imaging-software
            try:
                file = open(r'F:\transfer\experimentaol_config_MS_task_WF.txt', 'r')
            except:
                file = open(r'\\Fileserver\AG Kampa\transfer\experimentaol_config_MS_task_WF.txt', 'r')
            #
            self.save_path = file.read()
            self.save_path = 'C' + self.save_path[1:]
            try:
                makedirs(self.save_path)
            except FileExistsError:
                # likely already exists
                pass
            except FileNotFoundError as e:
                # if there is no configs folder, e.g.: for testing
                print(e)
            except Exception as e:
                print(e)
            #
            file.close()
            print('Save_path loaded from Imaging-software: ', self.save_path)

            temp_dir, temp_file = path.split(self.save_path)
            temp_dir, self.time_stamp = path.split(temp_dir)
            temp_dir, self.mouse_id = path.split(temp_dir)
            temp_dir, experiment_name = path.split(temp_dir)

            dt = datetime.now()
            dt2 = datetime(year=int(self.time_stamp[:4]), month=int(self.time_stamp[5:7]), day=int(self.time_stamp[8:10]),
                           hour=int(self.time_stamp[11:13]), minute=int(self.time_stamp[14:16]))
            # (dt - dt2)
            # print(dt, '\r\n', dt2)
            if (dt - dt2).seconds > 600:
                # this checks if more than 10 min ago
                raise Exception('Took too long! More than 10 min since imaging start.')

            # Don't think I need this!
            # self.time_stamp = self.save_path[-29:-10]
            self.file_base = path.join(self.save_path, experiment_name + '_' + self.mouse_id + '_' + self.time_stamp)
        except:
            # self.time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            # self.save_path = path.join(r'C:\data', experiment_name, self.mouse_id, self.time_stamp, 'task_data')
            # behavior_video_path = path.join(r'E:\data', experiment_name, self.mouse_id, self.time_stamp,
            #                                 'behavior_recordings')
            # makedirs(self.save_path)
            #
            # # self.file_base = path.join('MS_task_V1_3_' + self.mouse_id + '_' + self.time_stamp)
            # self.file_base = path.join(self.save_path, experiment_name+'_' + self.mouse_id + '_' + self.time_stamp)
            # print('Unable to load Save_path from Imaging-software. Using generate Path: ', self.save_path)
            #
            # self.LabView_client = LabViewTCPClient(server_ip='134.130.63.54', server_port=8089)
            # self.LabView_client.send(self.mouse_id)
            # self.LabView_client.send(behavior_video_path)
            self.time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            self.save_path = path.join(r'C:\data', experiment_name, self.mouse_id, self.time_stamp, 'task_data')
            makedirs(self.save_path)

            # self.file_base = path.join('MS_task_V1_3_' + self.mouse_id + '_' + self.time_stamp)
            self.file_base = path.join(self.save_path, experiment_name + '_' + self.mouse_id + '_' + self.time_stamp)
            print('Unable to load Save_path from Imaging-software. Using generate Path: ', self.save_path)

            # Insert to use labcams
            if 1:
                self.labcams_udp = Labcams(save_path=path.join(experiment_name, self.mouse_id, self.time_stamp,
                                                               "behavior_recordings_mp4", mouse_id),
                                           ip="134.130.63.186", port=9999)
                # self.labcams_udp = Labcams(save_path=path.join(experiment_name, self.mouse_id, self.time_stamp,
                #                                                "behavior_recordings_mp4", mouse_id),
                #                            ip="134.130.63.80", port=9999)
            else:
                self.labcams_udp = None
            #
        #

        # DAQ
        self.DIBuffered_object = None
        self.wheel = None
        self.AIs = None
        self.og0 = None
        self.og1 = None

        # Disable DAQ. During development there is not always a DAQ-Device available
        if not self.DAQ_disabled:
            # from modules.DAQ import DIBuffered, Wheel, Photodiode
            self.configure_daq(DAQ_devide=DAQ_device)
        else:
            for i in range(100):
                print('WARNING DAQ DISABLED!!!!')
            #
        #

        # # Trial variables
        self.h5f = None
        self.trial_id = -1
        self.modality = -1
        self.target_site = None
        self.both_spouts_probability = 0.2
        self.trial_sequence = PseudoRandomTrialSequence()
        self.spout_bias_correction = SpoutBiasCorrection(spout_positions[0], spout_positions[1])

        self.reward_probability = 1.
        self.enable_reward = 1

        # THIS IS JUST INITIALIZATION:
        self.response_delay = 0  # in ms

        # Trial variables make a separate class at some point
        self.stimulus_start_time = -1

        # Define stimuli and visual stimulus server parameters
        self.visual_stimulus_server_data = []

        self.cues_left_visual = [0, 0, 0, 0, 0, 0]
        self.cues_right_visual = [0, 0, 0, 0, 0, 0]
        self.cues_left_tactile = [0, 0, 0, 0, 0, 0]
        self.cues_right_tactile = [0, 0, 0, 0, 0, 0]
        self.reward_both_sides = False

        # Reward
        self.response_history = list()  # tracks responses for side-bias correction
        self.n_no_responses = 0  # indicator to track motivation of the animal

        # container for the gui to write values into at runtime without interfering with current trial
        # update trial parameters at trial_init from here then.
        self.gui_variables = GuiVariables()
        self.gui_variables.optogenetic_target = optogenetic_target
        self.gui_variables.optogenetic_power = optogenetic_power
        self.gui_variables.og_modality = og_modality
        self.gui_variables.og_type = og_type

        # Those controllers ensure the both spout trials are equally distributed over left and right trials
        # and closely adhere to the target probability over short-time windows (pseudo-random)
        self.both_spouts_controller = ConditionTracker(probability=self.both_spouts_probability)
        self.optogenetic_trial_controller = ConditionTrackerConditionWise(probability=self.gui_variables.optogenetic_trial_probability)
        print('INIT OG: ', self.gui_variables.optogenetic_trial_probability)

        # State-variables
        self.both_spouts = True
        self.auto_reward = True
        self.lick_response = None

        self.valve_left_duration = 7000
        self.valve_right_duration = 7000

        self.valve_left_water_amount = 3
        self.valve_right_water_amount = 3

        self.visual_contrast = 1.0

        # THIS IS NEEDED IN THE GUI TO DETERMINE WHEN TO PAUSE AND WHEN TO CLOSE THE SESSION.
        self.trial_finished = True

        # Performance trackers for side-bias-correction, modality-bias-correction and display
        self.target_distractor_difference = 0
        self.performance = np.zeros((7, 3, 3))
        self.performance_by_side = np.zeros((7, 3, 3, 2))
        self.total_number_of_trials_presented = np.zeros((2, 3))

        self.modality_and_performance_record = list()
        # self.max_modality_imbalance_factor = 4

        # Insert for V2_0:
        # Start Serial
        self.serial_obj = serial_obj

        self.spout_left_in_position = spout_positions[0]
        self.spout_right_in_position = spout_positions[1]
        self.spout_left_out_position = spout_positions[2]
        self.spout_right_out_position = spout_positions[3]
        self.spout_left_current_position = self.spout_left_in_position
        self.spout_right_current_position = self.spout_right_in_position

        # trial_phase == 0: waiting for Trial_Start_BYTE
        # trial_phase == 1: waiting for Stimulus_Start_BYTE
        # trial_phase == 2: waiting for RESPONSE_BYTE
        self.trial_phase = 0  # if False: Waiting for RESPONSE_BYTE, and once I have Received that, the trial is over

        if not self.DAQ_disabled:
            # now start the DAQ. Do this last
            self.DIBuffered_object.start()
        #
    #

    def determine_stimulus_cues(self, discrimination_trial):
        # for now I'm assuming that if I present stimuli in both modalities that I always present them together
        # this might change however

        # draw random values here once, so that the visual and tactile have the same values
        # target_cues = np.random.rand(6)
        # distractor_cues = np.random.rand(6)
        # if discrimination_trial and self.modality > 0:  # Removed the additional condition for the setup switch 2021-11-27
        if discrimination_trial:
            # print('DISCRIMINATION TRIAL: ', self.gui_variables.target_cue_probability_visual, self.gui_variables.distractor_cue_probability_visual)
            if 1:  # This is the older but already modified version to only present 3, 4 difference discriminations
                if 0:  # self.mouse_id in ['2258', '2263', '2274']:
                    while True:
                        # Just moved this here. 2021-10-20 - surprised that that never made issues in the past!!!
                        target_cues = np.random.rand(6)
                        distractor_cues = np.random.rand(6)

                        # threshold her and sort later
                        if self.modality == 0 or self.modality == 2:
                            # visual condition
                            target_visual = np.uint8(target_cues < self.gui_variables.target_cue_probability_visual)
                            distractor_visual = np.uint8(
                                distractor_cues < self.gui_variables.distractor_cue_probability_visual)
                        else:
                            target_visual = [0, 0, 0, 0, 0, 0]
                            distractor_visual = [0, 0, 0, 0, 0, 0]
                        if self.modality > 0:
                            # tactile condition
                            target_tactile = np.uint8(target_cues < self.gui_variables.target_cue_probability_tactile)
                            distractor_tactile = np.uint8(
                                distractor_cues < self.gui_variables.distractor_cue_probability_tactile)
                        else:
                            target_tactile = [0, 0, 0, 0, 0, 0]
                            distractor_tactile = [0, 0, 0, 0, 0, 0]
                        #

                        # check if there are more distractors than targets by random chance and fix it
                        if sum(target_visual) < sum(distractor_visual):
                            temp = target_visual
                            target_visual = distractor_visual
                            distractor_visual = temp
                        #
                        if sum(target_tactile) < sum(distractor_tactile):
                            temp = target_tactile
                            target_tactile = distractor_tactile
                            distractor_tactile = temp
                        #

                        if sum(target_visual) > 0 or sum(target_tactile) > 0:
                            # IMPORTANT: I'M ADDING THIS CONDITION FOR THE OG BATCH NOW.
                            # TO ONLY PRESENT STIMULI WITH A DIFFERENCE OF 3 OR 4
                            # temp = max([abs(sum(target_visual) - sum(distractor_visual)),
                            #             abs(sum(target_tactile) - sum(distractor_tactile))])
                            temp2 = max([sum(distractor_visual), sum(distractor_tactile)])
                            if temp2 > 0:
                                break
                            #

                            # if ((temp == 3) or (temp == 4)) and temp2 > 0:
                            #     print(temp, temp2)
                            #     break
                        #
                    #
                else:  # Now all
                    # here I'm drawing the difficuilty only once, so that they are evenly distributed
                    # difference = np.random.randint(2, 5)  # This ggives the 1 and the 2 a 50%-50% chance
                    # differences_to_present = [3, 5]  # Until 2022-09-20, but only one session used for the Deep-SC batch
                    if self.modality == 0:
                        differences_to_present = [4]
                    else:
                        differences_to_present = [2]
                    #
                    # differences_to_present = [1, 2, 3]
                    difference = np.random.choice(differences_to_present, 1)[0]
                    while True:
                        # Just moved this here. 2021-10-20 - surprised that that never made issues in the past!!!
                        target_cues = np.random.rand(6)
                        # distractor_cues = np.random.rand(6)
                        # difference = np.random.randint(3, 5)  # This ggives the 1 and the 2 a 50%-50% chance

                        # threshold her and sort later
                        if self.modality == 0 or self.modality == 2:
                            # visual condition
                            target_visual = np.uint8(target_cues < self.gui_variables.target_cue_probability_visual)
                            if sum(target_visual) < 3:
                                continue
                            #
                            distractor_visual = np.array([0, 0, 0, 0, 0, 0])
                            distractor_visual[np.random.permutation(range(6))[:sum(target_visual) - difference]] = 1
                            distractor_visual = list(distractor_visual)
                        else:
                            target_visual = [0, 0, 0, 0, 0, 0]
                            distractor_visual = [0, 0, 0, 0, 0, 0]
                        if self.modality == 1:
                            # tactile condition
                            target_tactile = np.uint8(target_cues < self.gui_variables.target_cue_probability_tactile)
                            if sum(target_tactile) < 3:
                                continue
                            #
                            distractor_tactile = np.array([0, 0, 0, 0, 0, 0])
                            distractor_tactile[np.random.permutation(range(6))[:sum(target_tactile) - difference]] = 1
                            distractor_tactile = list(distractor_tactile)
                        elif self.modality == 2:
                            target_tactile = target_visual
                            distractor_tactile = distractor_visual
                        else:
                            target_tactile = [0, 0, 0, 0, 0, 0]
                            distractor_tactile = [0, 0, 0, 0, 0, 0]
                        #

                        # check if there are more distractors than targets by random chance and fix it
                        if sum(target_visual) < sum(distractor_visual):
                            temp = target_visual
                            target_visual = distractor_visual
                            distractor_visual = temp
                        #
                        if sum(target_tactile) < sum(distractor_tactile):
                            temp = target_tactile
                            target_tactile = distractor_tactile
                            distractor_tactile = temp
                        #

                        if sum(target_visual) > 0 or sum(target_tactile) > 0:
                            # IMPORTANT: I'M ADDING THIS CONDITION FOR THE OG BATCH NOW.
                            # TO ONLY PRESENT STIMULI WITH A DIFFERENCE OF 3 OR 4
                            temp = max([abs(sum(target_visual) - sum(distractor_visual)),
                                        abs(sum(target_tactile) - sum(distractor_tactile))])
                            temp2 = max([sum(distractor_visual), sum(distractor_tactile)])
                            if (temp == difference) and temp2 > 0:  # The modality thing should never be the case but I wanted to make super sure!!!
                                # if temp2 > 0:  # The modality thing should never be the case but I wanted to make super sure!!!
                                #                             print(temp, temp2)
                                break
                            #
                        #
                    #
                #
            else:
                while True:
                    # Just moved this here. 2021-10-20 - surprised that that never made issues in the past!!!
                    target_cues = np.random.rand(6)
                    # distractor_cues = np.random.rand(6)
                    difference = np.random.randint(1, 3)  # This ggives the 1 and the 2 a 50%-50% chance

                    # threshold her and sort later
                    if self.modality == 0 or self.modality == 2:
                        # visual condition
                        target_visual = np.uint8(target_cues < self.gui_variables.target_cue_probability_visual)
                        if sum(target_visual) < 3:
                            continue
                        #
                        distractor_visual = np.array([0, 0, 0, 0, 0, 0])
                        distractor_visual[np.random.permutation(range(6))[:sum(target_visual)-difference]] = 1
                        distractor_visual = list(distractor_visual)
                    else:
                        target_visual = [0, 0, 0, 0, 0, 0]
                        distractor_visual = [0, 0, 0, 0, 0, 0]
                    if self.modality > 0:
                        # tactile condition
                        target_tactile = np.uint8(target_cues < self.gui_variables.target_cue_probability_tactile)
                        if sum(target_tactile) < 3:
                            continue
                        #
                        distractor_tactile = np.array([0, 0, 0, 0, 0, 0])
                        distractor_tactile[np.random.permutation(range(6))[:sum(target_tactile)-difference]] = 1
                        distractor_tactile = list(distractor_tactile)
                    else:
                        target_tactile = [0, 0, 0, 0, 0, 0]
                        distractor_tactile = [0, 0, 0, 0, 0, 0]
                    #

                    # check if there are more distractors than targets by random chance and fix it
                    if sum(target_visual) < sum(distractor_visual):
                        temp = target_visual
                        target_visual = distractor_visual
                        distractor_visual = temp
                    #
                    if sum(target_tactile) < sum(distractor_tactile):
                        temp = target_tactile
                        target_tactile = distractor_tactile
                        distractor_tactile = temp
                    #

                    if sum(target_visual) > 0 or sum(target_tactile) > 0:
                        # IMPORTANT: I'M ADDING THIS CONDITION FOR THE OG BATCH NOW.
                        # TO ONLY PRESENT STIMULI WITH A DIFFERENCE OF 3 OR 4
                        temp = max([abs(sum(target_visual) - sum(distractor_visual)),
                                    abs(sum(target_tactile) - sum(distractor_tactile))])
                        temp2 = max([sum(distractor_visual), sum(distractor_tactile)])
                        if (((temp == 1) or (temp == 2)) and temp2 > 0) or self.modality == 0:  # The modality thing should never be the case but I wanted to make super sure!!!
                            print(temp, temp2)
                            break
                    #
                #
            #
        else:
            # TODO: If I decide to do this, I would edit the detection condition here to also draw the targets
            #  probability based
            if self.modality == 0 or self.modality == 2:
                # target_visual = np.uint8(target_cues < self.gui_variables.target_cue_probability_visual)
                target_visual = [1, 1, 1, 1, 1, 1]
            else:
                target_visual = [0, 0, 0, 0, 0, 0]
            #

            if self.modality > 0:
                # target_tactile = np.uint8(target_cues < self.gui_variables.target_cue_probability_tactile)
                target_tactile = [1, 1, 1, 1, 1, 1]
            else:
                target_tactile = [0, 0, 0, 0, 0, 0]
            #

            distractor_visual = [0, 0, 0, 0, 0, 0]
            distractor_tactile = [0, 0, 0, 0, 0, 0]
        #

        # target_tactile = [1, 1, 1, 1, 1, 1]
        # distractor_tactile = [1, 1, 1, 1, 1, 1]

        #
        if self.target_site == 'left':
            self.cues_left_visual = list(target_visual)
            self.cues_right_visual = list(distractor_visual)
            self.cues_left_tactile = list(target_tactile)
            self.cues_right_tactile = list(distractor_tactile)
        else:
            self.cues_left_visual = list(distractor_visual)
            self.cues_right_visual = list(target_visual)
            self.cues_left_tactile = list(distractor_tactile)
            self.cues_right_tactile = list(target_tactile)
        #

        # target-distractor difference, the abs() is obsolete, but I like to be super sure
        target_distractor_difference = max([abs(sum(target_visual) - sum(distractor_visual)), abs(sum(target_tactile) - sum(distractor_tactile))])

        self.reward_both_sides = target_distractor_difference == 0

        return target_distractor_difference
    #

    def generate_tactile_cue_times(self):
        temp_cues = np.array(self.cues_left_tactile)
        left_tactile_times = np.array(6*[0])
        n_left_tactile_cues = sum(temp_cues)
        left_tactile_times[:n_left_tactile_cues] = (np.arange(0, 3000, 500) * temp_cues)[temp_cues > 0]

        temp_cues = np.array(self.cues_right_tactile)
        right_tactile_times = np.array(6*[0])
        n_right_tactile_cues = sum(temp_cues > 0)
        right_tactile_times[:n_right_tactile_cues] = (np.arange(0, 3000, 500) * temp_cues)[temp_cues > 0]

        return n_left_tactile_cues, n_right_tactile_cues, left_tactile_times, right_tactile_times
    #

    def init_trial(self, bias_threshold, bias_factors):
        # this is just for testing phase
        self.bias_threshold = bias_threshold
        self.bias_factors = bias_factors

        #

        print('')
        # print('TRIAL_INIT')
        self.trial_id += 1
        self.trial_phase = 0
        self.stimulus_start_time = -1

        # if self.trial_id == 0:
        #     print('Settings:')
        #     print(self.gui_variables.display_visual_trial_probability)
        #     print(self.gui_variables.display_tactile_trial_probability)
        #     print(self.gui_variables.discrimination_probability)
        # #

        self.visual_contrast = self.contrast_sequence[self.trial_id]

        # I might want to replace this at some point with a completely random routine
        # next_trial_settings, _ = \
        #     self.trial_sequence.get_next_trial(visual_probability=self.gui_variables.display_visual_trial_probability,
        #                                        tactile_probability=self.gui_variables.display_tactile_trial_probability,
        #                                        discrimination_probability=self.gui_variables.discrimination_probability)

        # self.modality = next_trial_settings[0]
        # stimulus_left = next_trial_settings[1]
        # discrimination_trial = next_trial_settings[2]

        # if self.trial_id == 0:
        #     print('Sequence:')
        #     print(self.trial_sequence.sequence)
        # #

        # Check that vis/tact trial probabilities make sense
        temp_vis_prob = self.gui_variables.display_visual_trial_probability
        temp_tact_prob = self.gui_variables.display_tactile_trial_probability
        if temp_vis_prob < 0:
            temp_vis_prob = 0
        elif temp_vis_prob > 1:
            temp_vis_prob = 1

        if temp_tact_prob < 0:
            temp_tact_prob = 0
        elif temp_tact_prob > 1:
            temp_tact_prob = 1

        # Check and correct if the sum of vis-prob and tact_prob is already adding up to more than 100%
        if temp_vis_prob + temp_tact_prob > 1:
            temp_prob_sum = temp_vis_prob + temp_tact_prob
            temp_vis_prob = temp_vis_prob / temp_prob_sum
            temp_tact_prob = temp_tact_prob / temp_prob_sum
        #

        temp_rand_val = np.random.rand()
        if temp_rand_val < temp_vis_prob:
            self.modality = 0
        elif temp_rand_val < temp_vis_prob + temp_tact_prob:
            self.modality = 1
        else:
            self.modality = 2
        #

        stimulus_left = int(np.random.rand() < 0.5)
        discrimination_trial = int(np.random.rand() < self.gui_variables.discrimination_probability)

        # Define next stimulus
        if stimulus_left:
            self.target_site = 'left'
        else:
            self.target_site = 'right'
        #

        # This determines the next number of distractors in a pseudo-random manner
        self.target_distractor_difference = self.determine_stimulus_cues(discrimination_trial=discrimination_trial)

        # # Here I'm updating everything that depends on the GUI settings
        # Make the both-spouts in probability based
        # update the probability based on GUI value
        if self.modality == 1:
            self.both_spouts_probability = self.gui_variables.display_both_spouts_tact_probability
        else:
            self.both_spouts_probability = self.gui_variables.display_both_spouts_probability
        #

        # if self.gui_variables.display_both_spouts:
        #     # self.both_spouts = np.random.rand() < self.both_spouts_probability
        #     self.both_spouts = self.both_spouts_controller.update(target_side_left=stimulus_left,
        #                                                           probability=self.both_spouts_probability)
        #
        #     # check if the mouse has answered the last 3 left and last 3 right and give single spout in opposing trials
        #     self.both_spouts = self.spout_bias_correction.single_spout_trial_check(self.both_spouts, stimulus_left)
        #
        #     # this overwrites both_spouts this has to be accounted for in the controller
        #     self.both_spouts_controller.full_history[stimulus_left][-1] = self.both_spouts
        # else:
        #     self.both_spouts = False
        # #

        self.both_spouts = np.random.rand() < self.both_spouts_probability

        #
        # optogenetic_trial = self.optogenetic_trial_controller.update(target_side_left=stimulus_left,
        #                                                              modality=self.modality,
        #                                                              difference=abs(self.target_distractor_difference),
        #                                                              probability=self.gui_variables.optogenetic_trial_probability)

        if self.both_spouts:
            optogenetic_trial = np.random.rand() < self.gui_variables.optogenetic_trial_probability
        else:
            optogenetic_trial = False
        #


        # # I'm not sure yet if I like it, but with this I ensure, that if it's a > 90% visual session I use og in
        # # visual trials. This is meant to rule out accidentally disabling of optogentics by selecting the
        # # wrong og_modality (especially leaving it at "None")
        # if self.gui_variables.display_visual_trial_probability > 0.9:
        #     if self.modality != 0:
        #         optogenetic_trial = False
        #     #
        # elif self.gui_variables.display_tactile_trial_probability > 0.9:
        #     # same here as above but for tactile
        #     if self.modality != 1:
        #         optogenetic_trial = False
        #     #
        # else:
        #     # if self.modality not in self.gui_variables.og_modality:
        #
        #     # Changed this 2021-11-27 for the setup switch of the two og batches
        #     if 0:  # only 1 modality
        #         if self.modality != self.gui_variables.og_modality[0]:
        #             optogenetic_trial = False
        #         #
        #     else:
        #         if self.gui_variables.optogenetic_target == 'SC':
        #             if self.modality != self.gui_variables.og_modality[0]:
        #                 optogenetic_trial = False
        #             #
        #         else:
        #             if self.modality not in self.gui_variables.og_modality:
        #                 optogenetic_trial = False
        #             #
        #     #
        # #

        # print('OG: ', self.gui_variables.optogenetic_trial_probability)

        # Edit Gerion 2022-09-22: Were doing it in all modalities now!
        # # EDIT GERION 2022-08-26: Before opto didn't consider modality. With this we limit opto to only one modality per
        # # session, which would allow us to up the prob. to up to 50%
        # if (self.modality != self.gui_variables.og_modality[0]) and (self.modality != self.gui_variables.og_modality[1]):
        #     optogenetic_trial = False
        # #

        if (self.gui_variables.optogenetic_trial_left > 0) or (self.gui_variables.optogenetic_trial_right > 0):  # Check if last trial was already an og trial
            # don't show two OG trials in a row
            optogenetic_trial = False
        #

        if self.trial_id < 3:
            # dont show OG in the first trial
            optogenetic_trial = False
        #

        if not self.optogenetics_in_detection_conditions:
            # This prevents og trials in detection cases
            if self.gui_variables.discrimination_probability > 0:
                # This case is new. 2022-09-21: We moved on the discrimination for al but one mouse
                # However we still want to do detection in this last mouse. This is our fix for this now.
                if self.target_distractor_difference == 6:
                    # don't show OG in the first trial
                    optogenetic_trial = False
                #
            #
        #

        # # Moved this block down here 2021-10-25 - I needed to konw the distractor number to only present in discrimination trials
        # self.optogenetic_trial_controller.full_history[stimulus_left][-1] = optogenetic_trial

        # This is new the 2 -> stimulus inhibition, 1 full stimulus an 3 choice
        # gui object to control and
        # 2022-12-04: We added a new mode now (Random Stimulus/Choice: 4)
        # if 4 is selected we want to randomly use either stimulus or choice
        if self.gui_variables.og_type == 4:
            # This is the new behavior with random but mixed Stimulus/Choice within a  single session
            if np.random.rand() < 0.5:
                temp_og_mode = 2  # Stimulus
            else:
                temp_og_mode = 3  # Choice
            #
        else:
            # This is the regulat behavior we used previously [0 1 2 3]
            temp_og_mode = self.gui_variables.og_type
        #

        if self.optogenetics_bilateral:
            self.gui_variables.optogenetic_trial_left = optogenetic_trial * temp_og_mode  # I always use bilateral stimulation
            self.gui_variables.optogenetic_trial_right = optogenetic_trial * temp_og_mode  # I always use bilateral stimulation
        else:  # Alternating Unilateral inhibition
            if np.random.rand() < 0.5:
                self.gui_variables.optogenetic_trial_left = 0  # This is now unilateral
                self.gui_variables.optogenetic_trial_right = optogenetic_trial * temp_og_mode
            else:
                self.gui_variables.optogenetic_trial_left = optogenetic_trial * temp_og_mode
                self.gui_variables.optogenetic_trial_right = 0  # This is now unilateral
            #
        #

        if optogenetic_trial:
            print('')
            print('OG Trial!!! - L:', self.gui_variables.optogenetic_trial_left, '; R:', self.gui_variables.optogenetic_trial_right, '; ', self.gui_variables.optogenetic_power, ' mW')
            print('')
        #

        self.auto_reward = self.gui_variables.display_auto_reward
        # ######

        self.reward_probability = 1.
        if self.auto_reward:
            self.enable_reward = int(1.)  # for this trial
        else:
            self.enable_reward = int(np.random.rand() < self.reward_probability)  # for this trial
        #

        self.valve_left_duration = self.gui_variables.display_valve_left_duration
        self.valve_right_duration = self.gui_variables.display_valve_right_duration
        self.valve_left_water_amount = self.gui_variables.display_valve_left_water_amount
        self.valve_right_water_amount = self.gui_variables.display_valve_right_water_amount

        self.response_delay = 500  # in ms
        # self.response_delay = 1000  # in ms
        # self.response_delay = 2000  # in ms

        # update user:
        print('Stimulus side: %s, target-distractor difference: %d, auto-reward: %d, both-spouts: %d' %
              (self.target_site, self.target_distractor_difference, int(self.auto_reward), int(self.both_spouts)))

        n_left_tactile_cues, n_right_tactile_cues, left_tactile_times, right_tactile_times = self.generate_tactile_cue_times()
        print(left_tactile_times, right_tactile_times)

        # # The way I'm currently handling the spout OUT-positions, I need IN-Positions >= 15 setps
        if self.spout_left_current_position < 80:
            self.spout_left_current_position = 80
        if self.spout_right_current_position < 80:
            self.spout_right_current_position = 80
        #

        # determine which photodiode to use
        photodiode_to_use = int(self.target_site == 'left')
        if not self.use_left_photodiode:
            photodiode_to_use = 0  # use the right photodiode
        #
        if not self.use_right_photodiode:
            photodiode_to_use = 1  # use the left photodiode
        #

        # # ## SERIAL COM.
        # # Send 0's as n_distractor left/right so the teensy showns no tactile stimuli
        send_data_until_confirmation(serial_obj=self.serial_obj, header_byte=START_TRIAL,
                                     data=[self.spout_left_current_position,
                                           self.spout_right_current_position,
                                           self.spout_left_current_position - 80,
                                           self.spout_right_current_position - 80,
                                           int(self.target_site == 'left'),
                                           int(self.auto_reward),
                                           int(self.both_spouts),
                                           int(self.reward_both_sides),
                                           int(self.enable_reward),
                                           int(self.valve_left_duration),
                                           int(self.valve_right_duration),
                                           int(0),  # aud
                                           int(photodiode_to_use),  # # int(self.target_site == 'left'),  # left_photodiode
                                           int(1),  # i think this is enable spouts
                                           int(1),  # use response based next trial delay
                                           int(self.gui_variables.optogenetic_trial_left),
                                           int(self.gui_variables.optogenetic_trial_right),
                                           int(n_left_tactile_cues),
                                           int(n_right_tactile_cues)] + \
                                          list(left_tactile_times) + \
                                          list(right_tactile_times) + \
                                          [1000, 4000, 4500, 6500, 7000])
        self.total_number_of_trials_presented[1-int(self.target_distractor_difference == 6), self.modality] += 1
        print('Total number Trials presented:')
        print(self.total_number_of_trials_presented)
    #

    def create_new_h5file(self):
        # Stop writing data and wheel to the previous h5-file and create the new one
        try:
            self.h5f.close()
        except:
            pass
        #

        # create_trial_data_file
        self.h5f = H5Object('%s_%06d.h5' % (self.file_base, self.trial_id),
                            channel_names=['DI', 'wheel', 'photodiode', 'optogenetic_signal_0', 'optogenetic_signal_1',
                                           'n_DI_samples_since_last_wheel_update',
                                           'auto_reward', 'Response_left', 'target_side_left', 'modality',
                                           'both_spouts_probability',
                                           'both_spouts', 'visual_trial_probability',
                                           'discrimination_probability',
                                           'cues_left_visual', 'cues_right_visual', 'cues_left_tactile',
                                           'cues_right_tactile',
                                           'target_cue_probability_visual', 'distractor_cue_probability_visual',
                                           'target_cue_probability_tactile', 'distractor_cue_probability_tactile',
                                           'reward_probability', 'enable_reward',  # 'response_delay',
                                           'valve_left_duration', 'valve_right_duration',
                                           'water_amount_left_ul', 'water_amount_right_ul',
                                           'current_spout_position_left', 'current_spout_position_right',
                                           'optogenetic_target', 'optogenetic_trial_left', 'optogenetic_trial_right',
                                           'optogenetic_power', 'visual_contrast', 'airpuff_pressure'],
                            n_dimensions=[2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])


        # save all the trial data that is saved once per trial
        # in this part all of the trial parameters except for the Response are written down.
        self.h5f.add_data('auto_reward', data=[self.auto_reward])
        self.h5f.add_data('modality', data=[self.modality])
        self.h5f.add_data('target_side_left', data=[int(self.target_site == 'left')])
        self.h5f.add_data('both_spouts_probability', data=[float(self.both_spouts_probability)])
        self.h5f.add_data('both_spouts', data=[int(self.both_spouts)])
        self.h5f.add_data('visual_trial_probability', data=[int(self.gui_variables.display_visual_trial_probability)])

        self.h5f.add_data('discrimination_probability', data=[self.gui_variables.discrimination_probability])
        self.h5f.add_data('cues_left_visual', data=self.cues_left_visual)
        self.h5f.add_data('cues_right_visual', data=self.cues_right_visual)
        self.h5f.add_data('cues_left_tactile', data=self.cues_left_tactile)
        self.h5f.add_data('cues_right_tactile', data=self.cues_right_tactile)
        self.h5f.add_data('target_cue_probability_visual', data=[self.gui_variables.target_cue_probability_visual])
        self.h5f.add_data('distractor_cue_probability_visual',
                          data=[self.gui_variables.distractor_cue_probability_visual])
        self.h5f.add_data('target_cue_probability_tactile', data=[self.gui_variables.target_cue_probability_tactile])
        self.h5f.add_data('distractor_cue_probability_tactile',
                          data=[self.gui_variables.distractor_cue_probability_tactile])

        self.h5f.add_data('reward_probability', data=[self.reward_probability])
        self.h5f.add_data('enable_reward', data=[self.enable_reward])
        # self.h5f.add_data('response_delay', data=[self.response_delay])

        self.h5f.add_data('valve_left_duration', data=[self.valve_left_duration])
        self.h5f.add_data('valve_right_duration', data=[self.valve_right_duration])

        self.h5f.add_data('water_amount_left_ul', data=[self.valve_left_water_amount])
        self.h5f.add_data('water_amount_right_ul', data=[self.valve_right_water_amount])

        self.h5f.add_data('current_spout_position_left', data=[self.spout_left_current_position])
        self.h5f.add_data('current_spout_position_right', data=[self.spout_right_current_position])

        # self.h5f.add_data('optogenetic_target', data=[self.gui_variables.optogenetic_target.encode()])
        self.h5f.add_data('optogenetic_trial_left', data=[self.gui_variables.optogenetic_trial_left])
        self.h5f.add_data('optogenetic_trial_right', data=[self.gui_variables.optogenetic_trial_right])
        print('SAVED OG: ', self.gui_variables.optogenetic_trial_left, self.gui_variables.optogenetic_trial_right)

        self.h5f._file.attrs['optogenetic_target'] = self.gui_variables.optogenetic_target
        self.h5f.add_data('optogenetic_target', data=[int(c) for c in self.gui_variables.optogenetic_target.encode('utf-8')])

        self.h5f.add_data('optogenetic_power', data=[self.gui_variables.optogenetic_power])

        self.h5f.add_data('visual_contrast', data=[self.visual_contrast])

        # self.h5f.add_data('airpuff_pressure', data=[0.3])
        self.h5f.add_data('airpuff_pressure', data=[self.gui_variables.airpuff_pressure])
        # print('Saved: ', self.gui_variables.airpuff_pressure)
    #

    def trial_loop(self):
        # reset the server data so that the function can return something outside the stimulus interval
        # [1: stimulus_phase, 6: left_cues, 6: right_cues] all values as [0, 1] for [True, False]
        self.visual_stimulus_server_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

        # read_inputs from buffered DI channels
        if not self.DAQ_disabled:
            try:
                data = self.DIBuffered_object.read()
                pos = self.wheel.read_position()  # read current wheel position
                temp_ai_data = self.AIs.read()
                photodiode_value = temp_ai_data[0]
                # og0_value = temp_ai_data[1]  # self.og0.read()
                # og1_value = temp_ai_data[2]  # self.og1.read()

                self.gui_variables.display_lick_left = np.any(data[self.left_lick_DI_id])
                self.gui_variables.display_lick_right = np.any(data[self.right_lick_DI_id])
                # self.gui_variables.display_lick_left = np.any(data[6])
                # self.gui_variables.display_lick_right = np.any(data[7])
            except:
                print("DAQ Error!!!")
                self.trial_finished = True
            #
        #

        # Those are the trial phases
        if self.trial_phase == 0:
            # Waiting for the Start of the next-trial
            # Initialize the next trial once the Trial_Start_BYTE has been received
            # close the previous h5-file and open a new one here, to stay as close to having the data of a single trial
            input_raw, received = wait_for_signal_byte(serial_obj=self.serial_obj, target_bytes=[NextTrialByte])

            if received and (input_raw == NextTrialByte):
                # this also saves all the settings for the next trial, such as the target_side, modality, ...
                self.create_new_h5file()

                # Ugly here but if I do it at init_trial, then its never visible
                self.gui_variables.display_target_side = self.target_site
                self.lick_response = None

                #
                self.trial_phase = 1
            #
        if self.trial_phase == 1:
            # Waiting for the Start of the Stimulus
            input_raw, received = wait_for_signal_byte(serial_obj=self.serial_obj, target_bytes=[VisualStimulusByte])

            if received and input_raw == VisualStimulusByte:
                # print('Received: ' + str(input_raw))

                # log this down in labcams
                if self.labcams_udp is not None:
                    self.labcams_udp.send("log=Stimulus_start")
                #

                self.trial_phase = 2
                self.stimulus_start_time = time()
            #
        #

        if self.trial_phase == 2:
            # 1. I'm setting "visual_stimulus_server_data" to trigger the client
            # 2. I'm waiting for the Response_BYTE

            # # Now the visual stimulus
            # This is an ugly solution! I had it once or twice that the client missed the signal,
            # by sending it repeatedly, I avoid that the stimulus is not presented at all.
            if time() - self.stimulus_start_time < 0.5:  # send this for half the duration
                self.visual_stimulus_server_data = [1] + list(self.cues_left_visual) + list(self.cues_right_visual) + [self.visual_contrast]
            #

            # Wait for Response_BYTE
            input_raw, received = wait_for_signal_byte(serial_obj=self.serial_obj,
                                                       target_bytes=[ResponseLeftByte,
                                                                     ResponseRightByte,
                                                                     ResponseMissedByte], timeout=0)

            if received and (input_raw in [ResponseLeftByte, ResponseRightByte, ResponseMissedByte]):
                if input_raw == ResponseMissedByte:
                    self.lick_response = "missed"
                if input_raw == ResponseLeftByte:
                    self.lick_response = "left"
                if input_raw == ResponseRightByte:
                    self.lick_response = "right"
                #

                # log this down in labcams
                if self.labcams_udp is not None:
                    self.labcams_udp.send("log=Received_respose_"+self.lick_response)
                #

                print('Received: ' + str(self.lick_response))

                # now the response and response_history
                if len(self.response_history) >= 10:
                    self.response_history = self.response_history[-9:]
                #

                if self.lick_response != "missed":
                    # use spout_side_bias_correction once I got the response of the animal to the current trial
                    # this then affects the next trial spout positions
                    self.spout_left_current_position, self.spout_right_current_position = \
                        self.spout_bias_correction.apply_spout_position_bias_correction(
                            stimulus_side_left=int(self.target_site == 'left'),
                            response_left=int(self.lick_response == 'left'),
                            left_in=self.spout_left_in_position,
                            right_in=self.spout_right_in_position,
                            left_out=self.spout_left_out_position,
                            right_out=self.spout_right_out_position,
                            factors=self.bias_factors,
                            thresholds=self.bias_threshold
                        )
                else:
                    self.spout_left_current_position, self.spout_right_current_position = \
                        self.spout_bias_correction.apply_spout_position_bias_correction(
                            stimulus_side_left=int(self.target_site == 'left'),
                            response_left=int(self.target_site != 'left'),
                            left_in=self.spout_left_in_position,
                            right_in=self.spout_right_in_position,
                            left_out=self.spout_left_out_position,
                            right_out=self.spout_right_out_position,
                            factors=[0, 0, 0],
                            thresholds=[1, 1, 1]
                        )
                #

                if self.auto_reward:
                    # auto-reward trial
                    self.n_no_responses = 0

                    self.h5f.add_data('Response_left', data=[int(self.target_site == 'left')])
                    # print('Response_left (auto_reward): %d' % (int(self.target_site == 'left')))
                    self.response_history.append(int(self.target_site == 'left'))
                else:
                    if self.lick_response == "missed":
                        # missed trial
                        self.n_no_responses += 1

                        self.h5f.add_data('Response_left', data=[-1])
                        # print('Response_left: %d' % -1)

                        # append to the performance list to display in GUI
                        # [target_distractor_difference][vis, tact, vis-tack][correct, error, missed]
                        self.performance[self.target_distractor_difference, self.modality, 2] += 1
                        self.performance_by_side[self.target_distractor_difference, self.modality, 2, int(not (self.target_site == 'left'))] += 1
                    else:
                        if self.both_spouts:
                            # Mouse Answered and not auto-reward
                            if self.target_distractor_difference == 0:
                                self.n_no_responses = 0
                                correct_response = int(1)
                            else:
                                if self.lick_response == "left":
                                    # left response trial
                                    self.n_no_responses = 0
                                    correct_response = int(self.target_site == 'left')
                                else:  # right
                                    # right response trial
                                    self.n_no_responses = 0
                                    correct_response = int(self.target_site == 'right')
                                #
                            #

                            # append to the performance list to display in GUI
                            # [target_distractor_difference][vis, tact, vis-tack][correct, error, missed]
                            self.performance[self.target_distractor_difference, self.modality, int(not correct_response)] += 1
                            self.performance_by_side[self.target_distractor_difference, self.modality, int(not correct_response), int(not (self.lick_response == 'left'))] += 1

                            # print('Response_left: %d' % int(self.lick_response == 'left'))
                            self.response_history.append(int(self.lick_response == 'left'))

                            # append here the current modality and if the mouse responded correctly for the modality
                            # bias-correction only account for non-auto_reward trials, also ignore missed trials
                            self.modality_and_performance_record.append([self.modality, correct_response])
                        #

                        self.h5f.add_data('Response_left', data=[int(self.lick_response == 'left')])
                    #
                #

                self.trial_finished = True
            #
        #

        # ## CALL THIS EVERY ITERATION ## #
        if not self.DAQ_disabled:
            # save data to file
            if self.h5f is not None:
                try:
                    self.h5f.add_data('DI', data=data)
                    self.h5f.add_data('wheel', data=[pos])
                    self.h5f.add_data('photodiode', data=photodiode_value)
                    # self.h5f.add_data('optogenetic_signal_0', data=og0_value)
                    # self.h5f.add_data('optogenetic_signal_1', data=og1_value)
                    self.h5f.add_data('n_DI_samples_since_last_wheel_update', data=[len(data[0])])
                except Exception as e:
                    print(e)
                    self.trial_finished = True
                #
            #
        #

        return self.visual_stimulus_server_data
    #

    def end_session(self):
        # self.LabView_client.send("Quit")

        # send a message to stop acquiring behavior videos using labcams
        if self.labcams_udp is not None:
            self.labcams_udp.close()
        #

        try:
            self.h5f.close()
        except:
            pass
        #

        # clean_up modules
        if not self.DAQ_disabled:
            self.clean_up_daq()
        #
    #

    def configure_daq(self, DAQ_devide='PXI1Slot4'):
        from modules.DAQ import DIBuffered, Wheel, AI_object
        # _dev = 'Dev1'
        # DAQ_devide = 'PXI1Slot4'
        if not self.DAQ_disabled:
            # DI 0.0: lick_left
            # DI 0.1: lick_right
            self.DIBuffered_object = DIBuffered(lines=DAQ_devide+'/port0/line0:7', sample_rate_in_hz=10000)

            # create wheel_task
            # 2.0 & 2.2 are used by the wheel
            self.wheel = Wheel(wheel_ctr=DAQ_devide+'/ctr0', circumference_in_cm=45., pulses_per_rev=360)

            # create the AI Task used to read the voltage signal from the photodiode on the right monitor
            # self.photodiode = AI_object(DAQ_devide+'/ai0')
            self.AIs = AI_object(DAQ_devide+'/ai0,'+
                                 DAQ_devide+'/ai2,'+
                                 DAQ_devide+'/ai3')

            # self.og0 = AI_object(DAQ_devide + '/ai2')
            # self.og1 = AI_object(DAQ_devide + '/ai3')
        #
    #

    def clean_up_daq(self):
        self.DIBuffered_object.close()
        self.wheel.close()
        try:
            self.AIs.close()
        except:
            pass
        #
    #
#


if __name__ == '__main__':
    mouse_id = 'test'
    session = Session(mouse_id=mouse_id)
    session.init_trial()

    session_started = False
    # while True:
    while session.trial_id < 10:
        session.auto_reward = False
        if session.trial_finished:
            session.init_trial()
        session.trial_loop()
    #

    session.end_session()
#
