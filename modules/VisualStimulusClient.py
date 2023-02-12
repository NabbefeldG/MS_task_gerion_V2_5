import socket
try:
    from modules.VisualStimulus import VisualStimulus
except:
    from VisualStimulus import VisualStimulus
#
from time import time, sleep
import sys
from os import path
from glob import glob
import itertools
import configparser


class MyClient:
    def __init__(self):
        sleep(0.5)  # wait for the server to be online

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(30)

        # get local machine name
        self.host = socket.gethostname()

        self.port = 57485

        # connection to hostname on the port.
        self.s.connect((self.host, self.port))
        # self.s.settimeout(None)
        self.s.settimeout(30)
        print('Connected to: ', self.host, ', port: ', self.port)

    #

    def read(self):
        # print('reading...')
        while True:
            # Receive no more than 1024 bytes
            msg = self.s.recv(10240)
            try:
                msg_string = msg.decode('ascii')
                msg_list = msg_string.split('\r\n')
                # if len(msg_list) > 0:
                #     if msg_list[-1] != '':
                #         print(msg_list)
                if msg_list[-1] == '':
                    if len(msg_list) > 2:
                        msg_parts = msg_list[-3].split(',')
                        if msg_parts[-1] == 'quit':
                            print('Closing Connection')
                            self.close()
                        # return int(msg_parts[0]), int(msg_parts[1]), int(msg_parts[2]), int(msg_parts[3])
                        return msg_parts[0:14]
                    elif len(msg_list) > 1:
                        msg_parts = msg_list[-2].split(',')
                        if msg_parts[-1] == 'quit':
                            print('Closing Connection')
                            self.close()
                        # return int(msg_parts[0]), int(msg_parts[1]), int(msg_parts[2]), int(msg_parts[3])
                        return msg_parts[0:14]
                    #
                else:
                    msg_parts = msg_list[-1].split(',')
                    # print(msg_parts)
                    if msg_parts[-1] == 'quit':
                        print('Closing Connection')
                        self.close()
                    # return int(msg_parts[0]), int(msg_parts[1]), int(msg_parts[2]), int(msg_parts[3])
                    return msg_parts[0:14]
                #
            except Exception as e:
                try:
                    print(e)
                    print(msg)
                    print(msg_string)
                    print(msg_list)
                    print(msg_parts)
                    print('ERROR while reading TCP')
                except:
                    pass
                #
            #
            # print(msg.decode('ascii'))
        #

    #

    def close(self):
        self.s.close()
        sleep(1.)
        sys.exit(0)
        # raise SystemExit()
        # raise SystemError()
    #


#


def generate_binary_str(data):
    s = ''
    for b in data:
        s += str(b)
    #
    return s
#


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(r'setup_config.ini')
    left_monitor_id = int(config['Setup']['left_monitor_id'])
    right_monitor_id = int(config['Setup']['right_monitor_id'])

    # start TCP-client
    client = MyClient()

    Stimulus_path = r'C:\Shared_Software\MS_task_stimuli\MS_task_V2_2_Stimulus_frames\Stimulus_frames'

    # I'm giving it two different gray images cause I don't want psychopy to have trouble when trying to excess the same
    # file twice or something, who knows.
    gray_path_l = path.join(Stimulus_path, 'gray_l.png')
    gray_path_r = path.join(Stimulus_path, 'gray_r.png')

    # Added this extra frame that is displayed during the stimulus period so I can record the stimulus with the
    # photo-diode
    gray_path_r_stimulus = path.join(Stimulus_path, 'gray_r_stimulus.png')

    all_cue_combinations = list(map(list, itertools.product([0, 1], repeat=6)))

    frame_paths_left = dict()
    frame_paths_right = dict()
    for condition in all_cue_combinations:
        s = ''
        bin_str = generate_binary_str(condition)
        folder = 'left_'+bin_str
        frame_paths_left[folder] = glob(path.join(Stimulus_path, folder, '*.png'))
        folder = 'right_'+bin_str
        frame_paths_right[folder] = glob(path.join(Stimulus_path, folder, '*.png'))
    #

    n_frames_l = 181  # len(frame_paths_l[1])
    n_frames_r = 181  # len(frame_paths_r[1])

    # open the windows
    vis_stim_l = VisualStimulus(screen=left_monitor_id, screen_size=(1920, 1080), wait_blanking=False, fullscr=True)
    vis_stim_r = VisualStimulus(screen=right_monitor_id, screen_size=(1920, 1080), wait_blanking=True, fullscr=True)

    vis_stim_l.change_image(gray_path_l)
    vis_stim_r.change_image(gray_path_r)
    vis_stim_l.draw()
    vis_stim_r.draw()
    vis_stim_l.flip()
    vis_stim_r.flip()

    while True:
        vis_stim_l.change_image(gray_path_l)
        vis_stim_r.change_image(gray_path_r)

        vis_stim_l.draw()
        vis_stim_r.draw()
        vis_stim_l.flip()
        vis_stim_r.flip()
        #

        ref_time = time()
        # n_cues_left, frame_id_left, n_cues_right, frame_id_right = client.read()
        msg = client.read()
        contrast = float(msg[13])
        # print('Client - contrast:', contrast)
        vis_stim_l.change_contrast(contrast)
        vis_stim_r.change_contrast(contrast)

        msg = [int(val) for val in msg[:-1]]
        left_condition_key = 'left_' + generate_binary_str(msg[1:7])
        right_condition_key = 'right_' + generate_binary_str(msg[7:13])

        if time() - ref_time > 9.9:
            print(['CLIENT TIMEOUT'])
            SystemError('Took to long! Stimulus Client is shutting down!')
        # print(n_cues_left, frame_id_left, n_cues_right, frame_id_right)

        if int(msg[0]) > 0:
            st = time()
            while True:
                frame_id = round((time() - st) * 60)  # 60 Hz
                if frame_id <= 180:
                    vis_stim_l.change_image(frame_paths_left[left_condition_key][frame_id])
                    vis_stim_r.change_image(frame_paths_right[right_condition_key][frame_id])

                    vis_stim_l.draw()
                    vis_stim_r.draw()
                    vis_stim_l.flip()
                    vis_stim_r.flip()
                else:
                    break
                #
            #
        #
    #
#
