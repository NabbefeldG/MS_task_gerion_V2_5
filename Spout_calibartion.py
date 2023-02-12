from time import sleep
# from modules.DAQ import DO
from modules.Serial_functions import search_for_teensy_module, send_data_until_confirmation
import configparser


def calculate_valve_duration(temp_value, side):
    config = configparser.ConfigParser()
    config.read(r'setup_config.ini')

    if side == 'left':
        temp_value = round((temp_value - float(config['Setup']['spout_duration_left_intercept'])) / float(config['Setup']['spout_duration_left_slope']))
    else:
        temp_value = round((temp_value - float(config['Setup']['spout_duration_right_intercept'])) / float(config['Setup']['spout_duration_right_slope']))
    #

    return temp_value
#


if __name__ == "__main__":
    # OPEN_VALVE_LEFT = 106  # Overwrite to just open the Valve to run water through the system, e.g.: to get bubbles out of the tubes or something
    # OPEN_VALVE_RIGHT = 107  # Overwrite to just open the Valve to run water through the system, e.g.: to get bubbles out of the tubes or
    # CLOSE_VALVE_LEFT = 108  # Overwrite to close the valve if they have been opend
    # CLOSE_VALVE_RIGHT = 109  # Overwrite to close the valve if they have been opend

    FLUSH_VALVE_LEFT = 104  # flush valves outside of the experiment using this command
    FLUSH_VALVE_RIGHT = 105  # flush valves outside of the experiment using this command

    dur_l = 40000
    dur_r = 35000

    left_valve = 0

    if 1:  # This is just to test the resent calibarion!!!
        dur_l = calculate_valve_duration(2, 'left')
        dur_r = calculate_valve_duration(2, 'right')

        print(dur_l)
        print(dur_r)

        serial_obj = search_for_teensy_module(name='MS_task_V2_5')

        # left_valve = 0

        rate = 10
        for i in range(100):
            if left_valve:
                send_data_until_confirmation(serial_obj, header_byte=FLUSH_VALVE_LEFT, data=[dur_l])
            else:
                send_data_until_confirmation(serial_obj, header_byte=FLUSH_VALVE_RIGHT, data=[dur_r])
                #
            sleep(1. / rate)
            print(i)
        #
    else:
        #
        serial_obj = search_for_teensy_module(name='MS_task_V2_5')

        rate = 10
        for i in range(100):
            if left_valve:
                send_data_until_confirmation(serial_obj, header_byte=FLUSH_VALVE_LEFT, data=[dur_l])
                # sleep(1. / rate)
                # send_data_until_confirmation(serial_obj, header_byte=FLUSH_VALVE_RIGHT, data=[dur_l])
            else:
                send_data_until_confirmation(serial_obj, header_byte=FLUSH_VALVE_RIGHT, data=[dur_r])
            #
            sleep(1. / rate)
            print(i)
        #
    #

    # # Old version:
    # left_valve = False
    #
    # valve_l = DO(object_name='valve_l', line='Dev1/port1/line6, Dev1/port2/line5', duration=0.01)  # 0.0069
    # valve_r = DO(object_name='valve_r', line='Dev1/port1/line7, Dev1/port2/line6', duration=0.01)  # 0.0095
    #
    # if False:
    #     for i in range(100):
    #         valve_l.write(True)
    #         valve_r.write(True)
    #         sleep(0.1)
    #         valve_l.write(False)
    #         valve_r.write(False)
    #         sleep(0.001)
    # else:
    #     for i in range(20):
    #         print(i)
    #         # left_valve = not left_valve
    #         if left_valve:
    #             valve_l.send_trigger()
    #         else:
    #             valve_r.send_trigger()
    #         #
    #
    #
    #         sleep(2)
    #     #
    # #
    #
    # valve_l.close()
    # valve_r.close()
#
