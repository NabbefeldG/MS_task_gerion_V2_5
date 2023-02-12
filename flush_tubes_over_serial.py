from time import sleep
from modules.Serial_functions import search_for_teensy_module, send_data_until_confirmation


if __name__ == '__main__':
    OPEN_VALVE_LEFT = 106  # Overwrite to just open the Valve to run water through the system, e.g.: to get bubbles out of the tubes or something
    OPEN_VALVE_RIGHT = 107  # Overwrite to just open the Valve to run water through the system, e.g.: to get bubbles out of the tubes or
    CLOSE_VALVE_LEFT = 108  # Overwrite to close the valve if they have been opend
    CLOSE_VALVE_RIGHT = 109  # Overwrite to close the valve if they have been opend

    #
    # serial_obj = open_serial(COM_port='COM3', baudrate=9600)
    serial_obj = search_for_teensy_module(name='MS_task_V2_5')

    for i in range(1):
        send_data_until_confirmation(serial_obj, header_byte=OPEN_VALVE_RIGHT)
        sleep(0.001)
        send_data_until_confirmation(serial_obj, header_byte=OPEN_VALVE_LEFT)
        sleep(15)

        send_data_until_confirmation(serial_obj, header_byte=CLOSE_VALVE_LEFT)
        sleep(0.001)
        send_data_until_confirmation(serial_obj, header_byte=CLOSE_VALVE_RIGHT)
        sleep(0.001)

        print(i)
    #
#
