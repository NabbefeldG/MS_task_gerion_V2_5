from time import time, sleep
from modules.Serial_functions import open_serial, send_data_until_confirmation, wait_for_signal_byte, _send_dec_values

import winsound
frequency = 2500  # Set Frequency To 2500 Hertz
duration = 200  # Set Duration To 1000 ms == 1 second

START_TRIAL = 70
ADJUST_SPOUTES = 71
ADJUST_SPOUTSPEED = 73

SPOUTS_IN = 101  # serial command to move the spouts in
LEFT_SPOUT_OUT = 102  # serial command to move the left spout out
RIGHT_SPOUT_OUT = 103  # serial command to move the right spout out

if __name__ == '__main__':
    serial_obj = open_serial(COM_port='COM4', baudrate=9600)

    send_data_until_confirmation(serial_obj=serial_obj, header_byte=ADJUST_SPOUTSPEED,
                                 data=[100])
    sleep(0.01)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=ADJUST_SPOUTES,
                                 data=[0, 0])
    sleep(0.5)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=SPOUTS_IN)
    sleep(0.5)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=LEFT_SPOUT_OUT)
    sleep(0.1)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=SPOUTS_IN)
    sleep(0.1)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=LEFT_SPOUT_OUT)
    sleep(0.1)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=SPOUTS_IN)
    sleep(0.5)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=RIGHT_SPOUT_OUT)
    sleep(0.1)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=SPOUTS_IN)
    sleep(0.1)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=RIGHT_SPOUT_OUT)
    sleep(0.1)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=SPOUTS_IN)
    sleep(0.5)
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=ADJUST_SPOUTES,
                                 data=[0, 0])
#
