import socket
from time import sleep


class LabViewTCPClient:
    def __init__(self, server_ip='134.130.63.54', server_port=8089):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_address = (server_ip, server_port)
        self.client.connect(self.server_address)
    #

    def send(self, message):
        if type(message) is str:
            message = message.encode()
        #

        # message = b'This is suppose to be a path'
        size = ("%04d" % len(message)).encode()
        self.client.sendall(size+message)
    #
#


if __name__ == '__main__':
    client = LabViewTCPClient(server_ip='134.130.63.54', server_port=8089)
    client.send("Maus2")
    client.send(r"E:\Data\test\test")
    sleep(5.)
    # client.send("Quit")
#
