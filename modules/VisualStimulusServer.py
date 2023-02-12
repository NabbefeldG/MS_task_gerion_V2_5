import socket
from time import time, sleep
import numpy as np


class VisualStimulusServer:
    def __init__(self):
        # create a socket object
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.settimeout(10)

        # get local machine name
        host = socket.gethostname()
        port = 57485

        # bind to the port
        self.serversocket.bind((host, port))

        # queue up to 5 requests
        self.serversocket.listen(5)

        # establish a connection
        self.clientsocket, addr = self.serversocket.accept()
        self.serversocket.settimeout(None)
        print("TCP Server connection from %s" % str(addr))
    #

    def send(self, data):
        # msg = str(int(n_cues_left)) + ',' + str(int(frame_id_left)) + ',' + \
        #       str(int(n_cues_right)) + ',' + str(int(frame_id_right)) + '\r\n'

        msg = ''
        for value in data[:-1]:
            msg = msg + str(int(value)) + ','
        #
        # msg = msg + str(int(data[-1])) + '\r\n'
        msg = msg + str("%0.2f" % (data[-1])) + '\r\n'
        self.clientsocket.send(msg.encode('ascii'))
    #

    def close(self):
        try:
            for i in range(100):
                msg = 'quit\r\n'
                self.clientsocket.send(msg.encode('ascii'))
            #
        except:
            pass
        #
        sleep(0.1)
        self.clientsocket.close()
    #
#


if __name__ == '__main__':
    visual_stimulus_server = VisualStimulusServer()

    rate = 60  # fps

    x = np.concatenate((np.arange(150), -1 * np.ones((120,)), np.arange(200))).astype('int32')
    st = time()
    stimulus_side = 'left'
    while True:
        stimulus_cues_left = 6 * (stimulus_side == 'left')
        stimulus_cues_right = 6 - stimulus_cues_left

        idx = round(rate * (time() - st))
        if idx < len(x):
            visual_stimulus_server.send(stimulus_cues_left, x[idx], stimulus_cues_right, x[idx])
            # print(idx)
        else:
            break
        #

        if idx == 160:
            stimulus_side = 'right'
        #
    #
    visual_stimulus_server.close()
#
