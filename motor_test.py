# from PyQt5.QtWidgets import *
from PyQt5.QtWidgets import QApplication, QMainWindow, QLineEdit, QLabel, QPushButton, QGroupBox, \
                            QVBoxLayout, QGridLayout, QCheckBox, QWidget, QComboBox
from PyQt5.QtGui import *
from PyQt5 import QtCore
import sys
from time import time, sleep
from PyQt5.QtCore import QTimer, Qt
from datetime import timedelta
from modules.Session import Session
from modules.VisualStimulusServer import VisualStimulusServer
import subprocess
from os import path, getcwd
from modules.Serial_functions import search_for_teensy_module, send_data_until_confirmation
import numpy as np
import pyqtgraph as pg
# from pyqtgraph import PlotWidget, plot
import configparser


# Commands to Teensy
ADJUST_SPOUTES = 71
ADJUST_SPOUTSPEED = 73
ADJUST_TOUCHLEVEL = 75

FLUSH_VALVE_LEFT = 104  # flush valves outside of the experiment using this command
FLUSH_VALVE_RIGHT = 105  # flush valves outside of the experiment using this command

CALIBRATE_PHOTODIODE = 110  # calibrate photodiode just lick the lick sensors for 2sec

TOUCH_THRESHOLD_LEFT_UP = 111
TOUCH_THRESHOLD_LEFT_DOWN = 112
TOUCH_THRESHOLD_RIGHT_UP = 113
TOUCH_THRESHOLD_RIGHT_DOWN = 114


# OG Bytes
LED_INTENSITY = 126  # sends two values defining og0.intensity and og1.intensity
SWITCH_CW_OFF_OG0 = 128  # Switches CW mode off again. To normal state.
SWITCH_CW_OFF_OG1 = 130  # Switches CW mode off again. To normal state.


#
serial_obj = search_for_teensy_module(name='MS_task_V2_5')
send_data_until_confirmation(serial_obj=serial_obj, header_byte=ADJUST_SPOUTSPEED, data=[8])

while 1:
    send_data_until_confirmation(serial_obj, header_byte=ADJUST_SPOUTES, data=[0, 0])
    sleep(0.5)
    send_data_until_confirmation(serial_obj, header_byte=ADJUST_SPOUTES,
                                 data=[190, 280])
    sleep(0.5)
#

