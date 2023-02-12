from modules.DAQ import DO
from time import time, sleep
from modules.Serial_functions import search_for_teensy_module, send_data_until_confirmation


START_TRIAL = 70


if __name__ == '__main__':
    serial_obj = search_for_teensy_module(name='MS_task_V2_5')

    while 1:
        send_data_until_confirmation(serial_obj=serial_obj, header_byte=START_TRIAL,
                                     data=[81,
                                           81,
                                           81 - 80,
                                           81 - 80,
                                           int(1),
                                           int(0),
                                           int(0),
                                           int(0),
                                           int(0),
                                           int(1000),
                                           int(1000),
                                           int(0),  # aud
                                           int(1),  # # int(self.target_site == 'left'),  # left_photodiode
                                           int(0),  # i think this is enable spouts
                                           int(0),  # use response based next trial delay
                                           int(0),
                                           int(0),
                                           int(6),
                                           int(6)] + \
                                          list([0, 500, 1000, 1500, 2000, 2500]) + \
                                          list([0, 500, 1000, 1500, 2000, 2500]) + \
                                          [250, 3250, 3500, 3750, 4000])
        sleep(4.5)
    #

    # air_puff_l = DO(object_name='air_puff_l', line='Dev1/port1/line4, Dev1/port2/line1', duration=0.04)
    # air_puff_r = DO(object_name='air_puff_r', line='Dev1/port1/line5, Dev1/port2/line3', duration=0.04)
    #
    # t1 = time()
    # while True:
    #     t2 = time()
    #     if time() - t1 > 0.5:
    #         air_puff_l.send_trigger()
    #         air_puff_r.send_trigger()
    #         t1 = t2
    #     else:
    #         sleep(0.05)
    # #
    #
    # # air_puff_l.close()
    # # air_puff_r.close()
#
