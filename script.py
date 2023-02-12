##
#
import configparser


config = configparser.ConfigParser()
config.read(r'setup_config.ini')
ni_daq_devide = config['Setup']['ni_daq_devide']
left_monitor_id = int(config['Setup']['left_monitor_id'])
right_monitor_id = int(config['Setup']['right_monitor_id'])
left_lick_DI_id = int(config['Setup']['left_lick_DI_id'])
right_lick_DI_id = int(config['Setup']['right_lick_DI_id'])
use_left_photodiode = int(config['Setup']['use_left_photodiode']) > 0
use_right_photodiode = int(config['Setup']['use_right_photodiode']) > 0

print(ni_daq_devide, left_monitor_id, right_monitor_id, left_lick_DI_id, right_lick_DI_id, use_left_photodiode, use_right_photodiode)
