# Here I'm collect the low-level hardware objects and modules
import nidaqmx
from nidaqmx.constants import AcquisitionType, LineGrouping, EncoderType, AngleUnits
import numpy as np
from time import time, sleep
import _thread
import matplotlib.pyplot as plt


class DIBuffered:
    def __init__(self, lines, sample_rate_in_hz):
        self._task = nidaqmx.Task()
        self._task.di_channels.add_di_chan(lines=lines, name_to_assign_to_lines='DI',
                                           line_grouping=LineGrouping.CHAN_PER_LINE)
        self._task.timing.cfg_samp_clk_timing(sample_rate_in_hz, source='', sample_mode=AcquisitionType.CONTINUOUS,
                                              samps_per_chan=100000)

    def start(self):
        self._task.start()

    def read(self):
        return np.array(self._task.read(-1))

    def close(self):
        # then stop the wheel
        try:
            if hasattr(self, '_task'):
                self._task.stop()
        except Exception as e:
            print(e)
        #
        if hasattr(self, '_task'):
            self._task.close()
            del self._task
    #

    def __del__(self):
        try:
            if hasattr(self, '_task'):
                self.close()
        except ResourceWarning:
            pass
        except Exception as e:
            print(e)
        #
    #
#


class DO:
    def __init__(self, object_name='default', line='', duration=1.):
        self.object_name = object_name
        self.duration = duration
        self.line = line

        self._task = nidaqmx.Task()
        self._task.do_channels.add_do_chan(self.line, name_to_assign_to_lines='DO',
                                           line_grouping=LineGrouping.CHAN_PER_LINE)
        self._task.start()

        # Finally, just for safety set the lines to False
        number_of_channels = self._task.number_of_channels
        if number_of_channels == 1:
            self._task.write([False], auto_start=True)
        elif number_of_channels == 2:
            self._task.write([False, False], auto_start=True)
        #
    #

    def _digital_trigger_function(self):
        try:
            number_of_channels = self._task.number_of_channels
            if number_of_channels == 1:
                self._task.write([True], auto_start=True)
                sleep(self.duration)
                self._task.write([False], auto_start=True)
            elif number_of_channels == 2:
                self._task.write([True, True], auto_start=True)
                sleep(self.duration)
                self._task.write([False, False], auto_start=True)
            #

            # self._task.write([True], auto_start=True)
            # sleep(self.duration)
            # self._task.write([False], auto_start=True)
        except Exception as e:
            print(e)
            raise e
        #
    #

    def send_trigger(self, exit_even_if_not_send=False):
        while True:
            try:
                # self._digital_trigger_function()
                _thread.start_new_thread(self._digital_trigger_function, ())
                # print('Trigger Send on line: %s' % line)
                trigger_send = True
                break
            except Exception as e:
                trigger_send = False
                print(e)
                if exit_even_if_not_send:
                    break
            #
        #
        return trigger_send
    #

    def write(self, value):
        try:
            # self._task.write([value], auto_start=True)
            number_of_channels = self._task.number_of_channels
            if number_of_channels == 1:
                self._task.write([value], auto_start=True)
            elif number_of_channels == 2:
                self._task.write([value, value], auto_start=True)
                #
        except Exception as e:
            print(e)
        #
    #

    def set_duration(self, duration):
        self.duration = duration
    #

    def close(self):
        try:
            # TODO: I should check if the started threads are done yet!
            if hasattr(self, '_task'):
                sleep(self.duration + 0.05)
                # RODO: make thuis n_channel dependent
                # self._task.write([False], auto_start=True)
                self.write(False)
                sleep(0.01)
                self._task.stop()
        except Exception as e:
            print(e)
        #
        if hasattr(self, '_task'):
            try:
                self._task.close()
                del self._task
            except:
                pass
            #
    #

    def __del__(self):
        # print('DO deleted')
        try:
            self.close()
        except ResourceWarning:
            pass
        except Exception as e:
            print(e)
        #
    #
#


class Wheel:
    def __init__(self, wheel_ctr, circumference_in_cm=45., pulses_per_rev=360):
        self.pulses_per_rev = int(pulses_per_rev)
        self.circumference_in_cm = circumference_in_cm
        self.reference_position = 0.
        self.current_position_in_cm = [0.]
        self._position_record = list()

        # Start the wheel_task
        # self._task = nidaqmx.Task(new_task_name='wheel')
        self._task = nidaqmx.Task()
        self._task.ci_channels.add_ci_ang_encoder_chan(name_to_assign_to_channel='wheel',
                                                       counter=wheel_ctr,
                                                       decoding_type=EncoderType.X_1,
                                                       units=AngleUnits.TICKS,
                                                       initial_angle=int(2147483647),  # to center the encoder: 2^32 / 2
                                                       pulses_per_rev=int(self.pulses_per_rev))
        self._task.start()
        self.reset()
    #

    def read_position(self):
        # read current number of ticks and scale to wheel circumference
        # first read current relative position, then convert to revolutions and then scale by circumference
        try:
            temp_positions = (np.array(self._task.read(1)) - self.reference_position) \
                                          * self.circumference_in_cm / self.pulses_per_rev
            if temp_positions.shape[0] > 0:
                self.current_position_in_cm = temp_positions
                self._position_record.extend(list(self.current_position_in_cm))
                return self.current_position_in_cm[-1]
            else:
                return self.current_position_in_cm[-1]
        except Exception as e:
            raise e
        #
    #

    def reset(self):
        self.reference_position = self._task.read(1)

    def close(self):
        # then stop the wheel
        try:
            if hasattr(self, '_task'):
                self._task.stop()
        except Exception as e:
            print(e)
        #
        if hasattr(self, '_task'):
            self._task.close()
            del self._task
    #

    def __del__(self):
        # print('wheel deleted')
        try:
            if hasattr(self, '_task'):
                self.close()
        except ResourceWarning:
            pass
        except Exception as e:
            print(e)
        #
    #
#


class AI_object:
    def __init__(self, ai_terminal):
        # Start the ai_task
        self._task = nidaqmx.Task()
        self._task.ai_channels.add_ai_voltage_chan(name_to_assign_to_channel='AIs',
                                                   physical_channel=ai_terminal)
        self._task.start()
    #

    def read(self):
        # read current ai-value
        try:
            return np.array(self._task.read(1))
        except Exception as e:
            raise e
        #
    #

    def close(self):
        # then stop the wheel
        try:
            if hasattr(self, '_task'):
                self._task.stop()
        except Exception as e:
            print(e)
        #
        if hasattr(self, '_task'):
            self._task.close()
            del self._task
    #

    def __del__(self):
        # print('wheel deleted')
        try:
            if hasattr(self, '_task'):
                self.close()
        except ResourceWarning:
            pass
        except Exception as e:
            print(e)
        #
    #
#


# if __name__ == '__main__':
#     DIBuffered_object = DIBuffered(lines='Dev1/port0/line0:7', sample_rate_in_hz=10000)
#     # DOBuffered_object_2 = DOBuffered(lines='Dev1/port0/line4', duration=duration, clock_terminal=sample_clock_PFI)
#
#     # 1.0: lick_l
#     # 1.1: lick_r
#     task_feedback = DO(object_name='task_feedback', line='Dev1/port1/line2')
#     camera_trigger = DO(object_name='camera_trigger', line='Dev1/port1/line3', duration=0.2)
#
#     air_puff_l = DO(object_name='air_puff_l', line='Dev1/port1/line4', duration=0.1)
#     air_puff_r = DO(object_name='air_puff_r', line='Dev1/port2/line1, Dev1/port1/line5', duration=0.5)
#
#     valve_l = DO(object_name='valve_l', line='Dev1/port1/line6', duration=0.005)
#     valve_r = DO(object_name='valve_r', line='Dev1/port1/line7', duration=0.005)
#
#     # create wheel_task
#     wheel_ctr_terminal = 'Dev1/ctr0'
#     wheel = Wheel(wheel_ctr=wheel_ctr_terminal, circumference_in_cm=45., pulses_per_rev=360)
#
#     side_l = True
#     record = list()
#
#     # start DI_task
#     print('starting now')
#     DIBuffered_object.start()
#
#     #
#     for i in range(1):
#         st = time()
#         last_update = -1
#         reward_given = False
#
#         camera_trigger.send_trigger()
#         while True:
#             sleep(1./30.)
#             current_time = time() - st
#
#             pos = wheel.read_position()
#
#             if current_time < 1.:
#                 task_feedback.write(False)
#             elif current_time < 2.:
#                 task_feedback.write(True)
#
#                 if current_time - last_update > 0.4:
#                     # air_puff_l.send_trigger()
#                     air_puff_r.send_trigger()
#                     last_update = current_time
#
#             elif current_time < 3.:
#                 task_feedback.write(False)
#             elif current_time < 4.:
#                 task_feedback.write(True)
#
#                 if not reward_given:
#                     valve_l.send_trigger()
#                     valve_r.send_trigger()
#                 #
#             else:
#                 task_feedback.write(False)
#             #
#
#             data = DIBuffered_object.read()
#             # print((pos, len(data[0]), data))
#
#             record.append([pos, np.array(data)])
#
#             if time() - st > 5.:
#                 break
#             #
#         #
#     #
#
#     # clean_up modules
#     DIBuffered_object.close()
#     wheel.close()
#     camera_trigger.close()
#     task_feedback.close()
#     air_puff_l.close()
#     air_puff_r.close()
#     valve_l.close()
#     valve_r.close()
#
#     # Post-processing/visualization
#     data = record[0][1]
#
#     for i in range(1, len(record)):
#         data = np.concatenate((data, record[i][1]), axis=1)
#     #
#
#     ax = plt.imshow(data, aspect='auto', interpolation='nearest')
#     plt.show()
# #

# if __name__ == '__main__':
#     # _dev = 'Dev1'
#     _dev = 'PXI1Slot4'
#     photodiode = Photodiode(_dev+'/ai0')
#     while True:
#         print(photodiode.read())
#         sleep(0.2)
#     #
# #
