import socket
from datetime import datetime


class Labcams:
    def __init__(self, save_path, ip="134.130.63.118", port=9998):
        # self.ip = "134.130.63.118"
        # self.port = 9998
        self.ip = ip
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(2.)
        self.send("ping")
        self.send("softtrigger=0")
        self.send(r"expname=" + save_path)
        self.send("softtrigger=1")
        self.send("manualsave=1")
    #

    def send(self, msg):
        self.socket.sendto(msg.encode(), (self.ip, self.port))
        return self.socket.recv(1024)
    #

    def close(self):
        self.send("manualsave=0")
        self.send("softtrigger=0")
        self.send("softtrigger=1")
        self.send(r"expname=" + "default_" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    #
#
