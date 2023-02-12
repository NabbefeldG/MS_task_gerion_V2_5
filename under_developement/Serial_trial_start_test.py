from time import time, sleep
from Serial_functions import open_serial, send_data_until_confirmation, wait_for_signal_byte
import winsound

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

if __name__ == '__main__':
    serial_obj = open_serial(COM_port='COM4', baudrate=9600)

    send_data_until_confirmation(serial_obj=serial_obj, header_byte=ADJUST_SPOUTSPEED,
                                 data=[100])
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=ADJUST_SPOUTES,
                                 data=[1, 1])
    send_data_until_confirmation(serial_obj=serial_obj, header_byte=ADJUST_SPOUTES,
                                 data=[0, 0])

    sleep(2)

    st = time()
    while True:
        while serial_obj.in_waiting:
            print(serial_obj.readline().decode('ascii'))
        #

        # Start Trial
        spout_left_out_position = 80
        spout_right_out_position = 80
        spout_left_in_position = 50
        spout_right_in_position = 50
        target_left_side = 1
        n_cues_left = 6
        n_cues_right = 3
        auto_reward = 0
        send_data_until_confirmation(serial_obj=serial_obj, header_byte=START_TRIAL,
                                     data=[spout_left_out_position,
                                           spout_right_out_position,
                                           spout_left_in_position,
                                           spout_right_in_position,
                                           target_left_side,
                                           n_cues_left,
                                           n_cues_right,
                                           auto_reward])

        timeout = -1

        input_raw, received = wait_for_signal_byte(serial_obj=serial_obj, target_bytes=[NextTrialByte], timeout=timeout)
        print(time() - st)
        st = time()
        # print(input_raw, 0)

        # while True:
        #     if serial_obj.in_waiting:
        #         sig = serial_obj.read(size=1)
        #         print(sig)
        #         if sig == b'r':
        #             break
        #     #
        # #
        #
        # print('----------------------------------------------')

        input_raw, received = wait_for_signal_byte(serial_obj=serial_obj, target_bytes=[VisualStimulusByte], timeout=timeout)
        print(input_raw, time() - st)

        if received:
            winsound.Beep(frequency=2500, duration=200)
        #

        input_raw, received = wait_for_signal_byte(serial_obj=serial_obj, target_bytes=[ResponseLeftByte, ResponseRightByte, ResponseMissedByte], timeout=timeout)
        print(input_raw, time() - st)

        dt = time() - st
        if dt < timeout:
            sleep(timeout - dt)
        #
    #
#
