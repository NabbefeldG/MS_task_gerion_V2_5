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


# ## Define communication BYTES
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


class GUIObjects:
    def __init__(self):
        # Session group
        self.mouse_id_label = None
        self.mouse_id = None
        self.modality = None
        self.trial_id = None
        self.session_time = None

        # Trial group
        self.target_cue_probability = None
        self.distractor_cue_probability = None
        self.target_cue_probability_label = None
        self.distractor_cue_probability_label = None

        # behavior group
        self.cue_indicator_l = None
        self.cue_indicator_r = None
        self.target_side_l = None
        self.target_side_r = None
        self.lick_response_l = None  # the one that is counted as performance
        self.lick_response_r = None  # the one that is counted as performance
        self.lick_l = None
        self.lick_r = None

        self.start_button = None
        self.auto_reward_button = None
        # self.both_spouts_button = None
        self.both_spouts_probability_label = None
        self.both_spouts_probability = None
        self.both_spouts_tactile_probability_label = None
        self.both_spouts_tactile_probability = None
        self.stop_button = None
        self.pause_button = None

        self.valve_left_duration_label = None
        self.valve_left_duration = None
        self.valve_right_duration_label = None
        self.valve_right_duration = None

        self.flush_left = None
        self.flush_right = None

        self.serial_spouts_IN = None
        self.serial_spouts_OUT = None

        self.test_visual_stimulus_button = None

        self.performance_indicator = [[[None for _ in range(3)] for _ in range(3)] for _ in range(2)]

        self.visual_trial_probability_label = None
        self.visual_trial_probability = None
        self.tactile_trial_probability_label = None
        self.tactile_trial_probability = None

        self.DAQ_disabled_box = None

        self.optogenetic_target = None
        self.og_probability_label = None
        self.og_probability = None

        self.og_type_comboBox = None
        self.og_modality_comboBox = None
        self.og_power_comboBox = None
        self.og_bilateral_comboBox = None
    #
#


class GUIVars:
    def __init__(self):
        self.mouse_id = None
        self.pause = False
        self.session_start = None
        self.trial_id = -1
        self.stimulus_side = 'left'
        self.lick_l = False
        self.lick_r = False
        self.auto_reward = False
        self.both_spouts = True
        self.counter = 0
        self.end_session = False
        self.modality_keys = ['Visual', 'Tactile', 'Visuotactile']

        # self.og_modality = -1
        self.og_modality = (-1, -1)
        self.og_type = 0
    #
#


def set_label_bg_color(obj, value=False):
    if value:
        obj.setStyleSheet("background-color: lightgreen")
    else:
        obj.setStyleSheet("background-color: white")
    #
#


class MSTaskGUI(QMainWindow):
    def __init__(self, default_discrimination_probability, default_spout_positions, default_both_spouts_probability,
                 use_visual_stimulus_client, screen, default_water_amount=2.):
        super().__init__()
        self.screen = screen

        self.optogenetics_in_detection_conditions = True

        # Read setup configs
        self.config = configparser.ConfigParser()
        self.config.read(r'setup_config.ini')

        if use_visual_stimulus_client:
            self.visual_stimulus_client = subprocess.Popen(path.join(getcwd(), 'modules', 'MS_task_visual_stimulus_client.bat'))
        #

        self.discrimination_probability = default_discrimination_probability

        # [left_IN, right_IN, left_OUT, right_OUT]
        self.spout_positions = default_spout_positions

        self.both_spouts_probability_value = default_both_spouts_probability
        self.both_spouts_tactile_probability_value = default_both_spouts_probability

        self.left_valve_duration = default_water_amount  # default in ul / trial
        self.right_valve_duration = default_water_amount  # default in ul / trial

        if use_visual_stimulus_client:
            self.visual_stimulus_server = VisualStimulusServer()
            self.last_visual_server_update = time()
        #

        # Session
        self.session = None

        # Start the Serial
        if True:
            self.og_teensy = search_for_teensy_module(name='OG_LED_Module')
            # Just to make sure switch off any possible CW-Modes and set intensity to 0 for now.
            # Don't forget to send the actual intensity that's supposed to be used at session start!!!
            # send_data_until_confirmation(serial_obj=self.og_teensy, header_byte=LED_INTENSITY, data=[0, 0])
            send_data_until_confirmation(serial_obj=self.og_teensy, header_byte=SWITCH_CW_OFF_OG0)
            send_data_until_confirmation(serial_obj=self.og_teensy, header_byte=SWITCH_CW_OFF_OG1)

            # self.optogenetic_power = 2.35
            # self.optogenetic_power = 9.5
            # self.optogenetic_power = 2.0
            self.optogenetic_power = 3.0
            optogenetic_relative_power_og0, optogenetic_relative_power_og1 = \
                self.calculate_relative_optogenetic_power(self.optogenetic_power)
            # # self.optogenetic_relative_power_left, self.optogenetic_relative_power_right = some_calibration_function(self.optogenetic_power)
            # self.optogenetic_relative_power_left, self.optogenetic_relative_power_right = 1., 1.
            send_data_until_confirmation(serial_obj=self.og_teensy, header_byte=LED_INTENSITY, data=[
                optogenetic_relative_power_og0, optogenetic_relative_power_og1])

            if use_visual_stimulus_client:
                self.visual_stimulus_server.send([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
            #

            self.serial_obj = search_for_teensy_module(name='MS_task_V2_5')
            send_data_until_confirmation(serial_obj=self.serial_obj, header_byte=ADJUST_SPOUTSPEED, data=[8])
            self.call_spouts_calibrate()
            self.call_spouts_IN()
            if use_visual_stimulus_client:
                self.visual_stimulus_server.send([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
            #
            sleep(0.5)  # wait a bit to make sure, that the spouts are at the IN position
            self.call_calibrate_licks()
            if use_visual_stimulus_client:
                for _ in range(8):
                    self.visual_stimulus_server.send([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
                    sleep(0.5)
                #
            #
            print('CALIBRATE_PHOTODIODE Started ...')
            send_data_until_confirmation(serial_obj=self.serial_obj, header_byte=CALIBRATE_PHOTODIODE)
            if use_visual_stimulus_client:
                for _ in range(4):
                    self.visual_stimulus_server.send([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
                    sleep(0.5)
            #
            print('CALIBRATE_PHOTODIODE Done ...')
            for _ in range(2):
                self.flush_valves('left')
                sleep(0.05)
                self.flush_valves('right')
                sleep(0.05)
                if use_visual_stimulus_client:
                    self.visual_stimulus_server.send([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
            #
        else:
            self.serial_obj = None
            [print('WARNING NO TEENSY!!!') for _ in range(100)]
        #

        # variables that I want to use inside the callbacks and send out
        self.vars = GUIVars()
        # self.vars.end_session = True

        # build GUI
        self.objs = GUIObjects()
        self.build_gui()

        # make QTimer
        self.qTimer = QTimer()
        self.qTimer.setInterval(0)  # in ms: 1000 ms = 1 s
        self.qTimer.timeout.connect(self.run)  # connect timeout signal to signal handler
        self.qTimer.start()

        self.update_gui()
        # draw GUI
        self.show()
    #

    def create_session_group(self):
        # Objects
        self.objs.modality = self.add_label(text='Modality.: ')
        self.objs.mouse_id_label = self.add_label(text='Mouse ID: ')
        self.objs.mouse_id = QLineEdit(self)
        self.objs.mouse_id.resize(150, 30)

        # creating the labels
        self.objs.trial_id = self.add_label(text='Trial Nr.: ')
        self.objs.trial_id.setVisible(False)

        self.objs.session_time = self.add_label(text='Time: ')
        self.objs.session_time.setVisible(False)

        # present multisensory checkBox
        self.objs.DAQ_disabled_box = QCheckBox('Disable DAQ?', self)
        self.objs.DAQ_disabled_box.resize(200, 30)
        self.objs.DAQ_disabled_box.setChecked(False)

        if 1:
            # DropDownMenu defining the broad session conditions
            # self.paradigm_selected = "visual only"
            self.objs.comboBox = QComboBox(self)
            self.objs.comboBox.addItems(["Detection - visual only",
                                         "Detection - visual + tactile",
                                         "Detection - tactile only",
                                         "Detection - all modalities",
                                         "Discrimination - all modalities"])
            # self.objs.comboBox.addItems(["Detection - visual only",
            #                              "Detection - tactile only",
            #                              "Detection - visual + tactile",
            #                              "Detection - all modalities",
            #                              "Discrimination - only visual",
            #                              "Discrimination - all modalities",
            #                              "Visual_contrast_control",
            #                              "Airpuff_pressure_control"])
            # "Discrimination - all modalities"])
            self.objs.comboBox.currentIndexChanged[str].connect(self.select_session_configuration)
            self.objs.comboBox.setStyleSheet("font-size: 16px; font-weight: bold;")
        #
        #

        # Optogenetic target area
        self.objs.optogenetic_target = QComboBox(self)
        # self.objs.optogenetic_target.addItems(["None", "V1", "S1", "RL", "Frontal", "SC"])
        # self.objs.optogenetic_target.addItems(["None", "NB", "HDB"])
        # self.objs.optogenetic_target.addItems(["None", "SC-deep"])
        self.objs.optogenetic_target.addItems(["None", "ALM"])
        self.objs.optogenetic_target.currentIndexChanged[str].connect(self.select_optogenetic_target)
        self.objs.optogenetic_target.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.objs.optogenetic_target.currentText()

        # # Select when to inhibit
        # self.objs.og_type_comboBox = QComboBox(self)
        # # self.objs.og_type_comboBox.addItems(["No Optogenetic",
        # #                                      "Full trial",
        # #                                      "Stimulus only",
        # #                                      "Choice only",
        # #                                      "Random Stimulus/Choice"])
        # self.objs.og_type_comboBox.addItems(["No Optogenetic",
        #                                      "Random Stimulus/Choice"])
        # # self.objs.og_type_comboBox.addItems(["No Optogenetic",
        # #                                      "Full trial",
        # #                                      "Stimulus only",
        # #                                      "Choice only"])
        # self.objs.og_type_comboBox.currentIndexChanged[str].connect(self.select_og_type)
        # self.objs.og_type_comboBox.setStyleSheet("font-size: 16px; font-weight: bold;")

        # At the moment there is only one mode we want to use:  Remove this overwrite if that changes again!
        self.vars.og_type = 4  # "Random Stimulus/Choice"


        # # Select when to inhibit
        # self.objs.og_modality_comboBox = QComboBox(self)
        # self.objs.og_modality_comboBox.addItems(["None",
        #                                          "Visual",
        #                                          "Tactile",
        #                                          "Vistact"])
        # self.objs.og_modality_comboBox.currentIndexChanged[str].connect(self.select_og_modality)
        # self.objs.og_modality_comboBox.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Select Optogenetics power
        self.objs.og_power_comboBox = QComboBox(self)
        # self.objs.og_power_comboBox.addItems(["0.5",
        #                                       "1.0",
        #                                       "1.5",
        #                                       "2.0"])
        self.objs.og_power_comboBox.addItems(["3.0",
                                              "2.0",
                                              "1.5",
                                              "1.0",
                                              "0.5"])
        self.objs.og_power_comboBox.currentIndexChanged[str].connect(self.select_optogenetics_power)
        self.objs.og_power_comboBox.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Select between bilateral and alternating unilateral
        self.objs.og_bilateral_comboBox = QComboBox(self)
        self.objs.og_bilateral_comboBox.addItems(["bilateral", "unilateral"])
        self.objs.og_bilateral_comboBox.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Run
        self.objs.start_button = QPushButton('Run', self)
        self.objs.start_button.move(10, 370)
        self.objs.start_button.clicked.connect(self.start_session)

        # Stop Button - replaces Start button during runtime
        self.objs.stop_button = QPushButton('Stop', self)
        self.objs.stop_button.move(10, 370)
        self.objs.stop_button.clicked.connect(self.stop_session)
        self.objs.stop_button.setVisible(False)

        self.objs.pause_button = QPushButton('Pause Experiment', self)
        self.objs.pause_button.setGeometry(10, 330, 100, 35)
        self.objs.pause_button.clicked.connect(self.call_pause)
        self.objs.pause_button.setVisible(False)

        self.objs.airpuff_pressure = QLineEdit(self)
        self.objs.airpuff_pressure.setText('0.3')
        self.objs.airpuff_pressure_label = self.add_label(text='Airpuff Pressure in bar e.g.: 0.1')

        # add modality first to its behind the mouse_id QLineEdit
        layout = QGridLayout()

        layout.addWidget(self.objs.airpuff_pressure_label, 2, 2)
        layout.addWidget(self.objs.airpuff_pressure, 3, 2)

        layout.addWidget(self.objs.modality, 0, 1)
        layout.addWidget(self.objs.mouse_id_label, 0, 0)
        layout.addWidget(self.objs.mouse_id, 0, 1)

        layout.addWidget(self.objs.trial_id, 1, 0)
        layout.addWidget(self.objs.session_time, 1, 1)

        if 1:
            temp = self.add_label(text='Session Configuration:')
            temp.setAlignment(QtCore.Qt.AlignLeft)
            layout.addWidget(temp, 2, 0, 1, 2)
            layout.addWidget(self.objs.comboBox, 3, 0, 1, 2)
        #

        temp = self.add_label(text='Optogenetic target-area:')
        temp.setAlignment(QtCore.Qt.AlignLeft)
        layout.addWidget(temp, 4, 0, 1, 3)
        layout.addWidget(self.objs.optogenetic_target, 5, 0, 1, 2)

        # Session.py ignores modality at the moment. This is obsolete now, if that changes change this again!!!
        # temp = self.add_label(text='Modality to Optogenetic inhibit:')
        # temp.setAlignment(QtCore.Qt.AlignLeft)
        # layout.addWidget(temp, 6, 0)
        # layout.addWidget(self.objs.og_modality_comboBox, 7, 0)

        # temp = self.add_label(text='Type of Inhibition:')
        # temp.setAlignment(QtCore.Qt.AlignLeft)
        # layout.addWidget(temp, 6, 1)
        # layout.addWidget(self.objs.og_type_comboBox, 7, 1)

        temp = self.add_label(text='Optogenetics Power in mW:')
        temp.setAlignment(QtCore.Qt.AlignLeft)
        layout.addWidget(temp, 8, 0)
        layout.addWidget(self.objs.og_power_comboBox, 9, 0)

        temp = self.add_label(text='Bilateral or Unilateral optogenetics:')
        temp.setAlignment(QtCore.Qt.AlignLeft)
        layout.addWidget(temp, 8, 1)
        layout.addWidget(self.objs.og_bilateral_comboBox, 9, 1)

        #
        layout.addWidget(self.objs.DAQ_disabled_box, 10, 0, 1, 2)

        layout.addWidget(self.objs.pause_button, 11, 0, 1, 2)
        layout.addWidget(self.objs.start_button, 12, 0, 1, 2)
        layout.addWidget(self.objs.stop_button, 12, 0, 1, 2)

        #
        self.GroupBox_session = QGroupBox("Session Settings")
        self.GroupBox_session.setLayout(layout)
    #

    def create_behavior_indicator_group(self):
        self.objs.cue_indicator_l = self.add_label(text='left cues:')
        self.objs.cue_indicator_r = self.add_label(text='right cues:')

        # Define objects
        self.objs.target_side_l = self.add_label(text='Target Left')
        self.objs.target_side_r = self.add_label(text='Target Right')

        self.objs.lick_l = self.add_label(text='Lick Left')
        self.objs.lick_r = self.add_label(text='Lick Right')

        self.objs.lick_response_l = self.add_label(text='Response Left')
        self.objs.lick_response_r = self.add_label(text='Response Right')

        # add objects to layout
        self.GroupBox_behavior_indicators = QGroupBox("Behavior indicators")
        layout = QGridLayout()
        layout.addWidget(self.objs.cue_indicator_l, 0, 0)
        layout.addWidget(self.objs.cue_indicator_r, 0, 1)

        layout.addWidget(self.objs.target_side_l, 1, 0)
        layout.addWidget(self.objs.target_side_r, 1, 1)

        layout.addWidget(self.objs.lick_l, 2, 0)
        layout.addWidget(self.objs.lick_r, 2, 1)

        layout.addWidget(self.objs.lick_response_l, 3, 0)
        layout.addWidget(self.objs.lick_response_r, 3, 1)

        self.GroupBox_behavior_indicators.setLayout(layout)
    #

    def create_plot_group(self):
        # Define objects
        self.PerformancePlot = pg.PlotWidget(background='w')
        self.ResponsePlot = pg.PlotWidget(background='w')

        self.Response_plots = {
            'correct_plot': self.ResponsePlot.plot([0], [0], pen=None, symbol='o', symbolBrush=(50, 255, 50)),
            'error_plot': self.ResponsePlot.plot([0], [0], pen=None, symbol='o', symbolBrush=(255, 50, 50)),
            'missed_plot': self.ResponsePlot.plot([0], [0], pen=None, symbol='o', symbolBrush=(50, 50, 255)),
            'invalid_plot': self.ResponsePlot.plot([0], [0], pen=None, symbol='o', symbolBrush=(127, 127, 127)),
            'trial_tracker': list()}

        self.PerformancePlot.showGrid(x=True, y=True)
        self.PerformancePlot.addLegend()
        self.Performance_plots = {
            'left_performance': self.PerformancePlot.plot([0], [0], pen=pg.mkPen(color=(50, 255, 50), style=None),
                                                          symbol='o', symbolBrush=(50, 255, 50), name='left'),
            'right_performance': self.PerformancePlot.plot([0], [0], pen=pg.mkPen(color=(255, 50, 50), style=None),
                                                           symbol='o', symbolBrush=(255, 50, 50), name='right'),
            'average_performance': self.PerformancePlot.plot([0], [0], pen=pg.mkPen(color=(50, 50, 50), style=None),
                                                             symbol='o', symbolBrush=(50, 50, 50), name='overall')}

        # add objects to layout
        layout = QGridLayout()
        layout.addWidget(self.ResponsePlot, 0, 0, 1, 1)
        layout.addWidget(self.PerformancePlot, 1, 0, 1, 3)

        self.GroupBox_plots = QGroupBox("Behavior Plots")
        self.GroupBox_plots.setLayout(layout)
    #

    def create_serial_group(self):
        # flush
        self.objs.flush_left = QPushButton("Flush left", self)
        # self.objs.flush_left.setGeometry(10, 330, 100, 35)
        self.objs.flush_left.clicked.connect(lambda: self.flush_valves('left'))

        self.objs.flush_right = QPushButton("Flush Right", self)
        # self.objs.flush_right.setGeometry(150, 330, 100, 35)
        self.objs.flush_right.clicked.connect(lambda: self.flush_valves('right'))

        # Spout Stepper Motors
        # Spout IN positions
        self.objs.spout_position_left_in_label = self.add_label(text='Left Spout IN: ')
        self.objs.spout_position_left_in_label.adjustSize()
        self.objs.spout_position_left_in_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.spout_position_right_in_label = self.add_label(text='Right Spout IN: ')
        self.objs.spout_position_right_in_label.adjustSize()
        self.objs.spout_position_right_in_label.setAlignment(QtCore.Qt.AlignLeft)

        # Current Spout positions
        self.objs.spout_position_left_current_label = self.add_label(text='Left Spout Current: ')
        self.objs.spout_position_left_current_label.adjustSize()
        self.objs.spout_position_left_current_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.spout_position_right_current_label = self.add_label(text='Right Spout Current: ')
        self.objs.spout_position_right_current_label.adjustSize()
        self.objs.spout_position_right_current_label.setAlignment(QtCore.Qt.AlignLeft)

        # Spout Stepper Motors
        self.objs.spout_position_left_out_label = self.add_label(text='Left Spout OUT: ')
        self.objs.spout_position_left_out_label.adjustSize()
        self.objs.spout_position_left_out_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.spout_position_right_out_label = self.add_label(text='Right Spout OUT: ')
        self.objs.spout_position_right_out_label.adjustSize()
        self.objs.spout_position_right_out_label.setAlignment(QtCore.Qt.AlignLeft)

        #
        self.objs.spout_position_left_in = QLineEdit(self)
        self.objs.spout_position_left_in.setText(str(self.spout_positions[0]))
        self.objs.spout_position_left_in.textChanged[str].connect(self.update_spout_position_left_in)

        self.objs.spout_position_right_in = QLineEdit(self)
        self.objs.spout_position_right_in.setText(str(self.spout_positions[1]))
        self.objs.spout_position_right_in.textChanged[str].connect(self.update_spout_position_right_in)

        self.objs.spout_position_left_current = QLineEdit(self)
        self.objs.spout_position_left_current.setText(str(self.spout_positions[0]))
        self.objs.spout_position_left_current.setReadOnly(True)
        # self.objs.spout_position_left_current.setEnabled(False)
        self.objs.spout_position_left_current.setStyleSheet("background-color: rgb(200, 200, 200); color: rgb(0, 0, 0); font-weight: bold;")

        self.objs.spout_position_right_current = QLineEdit(self)
        self.objs.spout_position_right_current.setText(str(self.spout_positions[1]))
        self.objs.spout_position_right_current.setReadOnly(True)
        # self.objs.spout_position_right_current.setEnabled(False)
        self.objs.spout_position_right_current.setStyleSheet("background-color: rgb(200, 200, 200); color: rgb(0, 0, 0); font-weight: bold;")

        self.objs.spout_position_left_out = QLineEdit(self)
        self.objs.spout_position_left_out.setText(str(self.spout_positions[2]))
        self.objs.spout_position_left_out.textChanged[str].connect(self.update_spout_position_left_out)

        self.objs.spout_position_right_out = QLineEdit(self)
        self.objs.spout_position_right_out.setText(str(self.spout_positions[3]))
        self.objs.spout_position_right_out.textChanged[str].connect(self.update_spout_position_right_out)

        # Serial Command Buttons
        self.objs.serial_spouts_IN = QPushButton("SPOUTS IN", self)
        self.objs.serial_spouts_IN.clicked.connect(self.call_spouts_IN)

        self.objs.serial_spouts_OUT = QPushButton("SPOUTS OUT", self)
        self.objs.serial_spouts_OUT.clicked.connect(self.call_spouts_OUT)

        self.objs.serial_spouts_calibrate = QPushButton("CALIBRATE SPOUT POSITIONS", self)
        self.objs.serial_spouts_calibrate.clicked.connect(self.call_spouts_calibrate)

        self.objs.serial_calibrate_licks = QPushButton("CALIBRATE LICK DETECTION", self)
        self.objs.serial_calibrate_licks.clicked.connect(self.call_calibrate_licks)

        self.objs.spouts_std = QLineEdit(self)
        self.objs.spouts_std.setText(str(3))

        self.objs.left_lick_threshold_up = QPushButton("left_lick_threshold_up", self)
        self.objs.left_lick_threshold_up.clicked.connect(lambda: self.change_touch_thresholds('left_up'))

        self.objs.left_lick_threshold_down = QPushButton("left_lick_threshold_down", self)
        self.objs.left_lick_threshold_down.clicked.connect(lambda: self.change_touch_thresholds('left_down'))

        self.objs.right_lick_threshold_up = QPushButton("right_lick_threshold_up", self)
        self.objs.right_lick_threshold_up.clicked.connect(lambda: self.change_touch_thresholds('right_up'))

        self.objs.right_lick_threshold_down = QPushButton("right_lick_threshold_down", self)
        self.objs.right_lick_threshold_down.clicked.connect(lambda: self.change_touch_thresholds('right_down'))

        # add objects to layout
        self.GroupBox_serial = QGroupBox("Serial Communiation")
        layout = QGridLayout()

        layout.addWidget(self.objs.flush_left, 0, 0)
        layout.addWidget(self.objs.flush_right, 0, 1)

        layout.addWidget(self.objs.spout_position_left_in_label, 1, 0)
        layout.addWidget(self.objs.spout_position_right_in_label, 1, 1)
        layout.addWidget(self.objs.spout_position_left_in, 2, 0)
        layout.addWidget(self.objs.spout_position_right_in, 2, 1)

        layout.addWidget(self.objs.spout_position_left_current_label, 3, 0)
        layout.addWidget(self.objs.spout_position_right_current_label, 3, 1)
        layout.addWidget(self.objs.spout_position_left_current, 4, 0)
        layout.addWidget(self.objs.spout_position_right_current, 4, 1)

        layout.addWidget(self.objs.spout_position_left_out_label, 5, 0)
        layout.addWidget(self.objs.spout_position_right_out_label, 5, 1)
        layout.addWidget(self.objs.spout_position_left_out, 6, 0)
        layout.addWidget(self.objs.spout_position_right_out, 6, 1)

        layout.addWidget(self.objs.serial_spouts_IN, 1, 2, 2, 1)
        layout.addWidget(self.objs.serial_spouts_OUT, 5, 2, 2, 1)
        layout.addWidget(self.objs.serial_spouts_calibrate, 7, 0, 1, 3)
        layout.addWidget(self.objs.serial_calibrate_licks, 8, 0, 1, 3)

        # layout.addWidget(self.objs.spouts_std, 9, 0, 1, 1)

        layout.addWidget(self.objs.left_lick_threshold_up, 10, 0)
        layout.addWidget(self.objs.left_lick_threshold_down, 11, 0)
        layout.addWidget(self.objs.right_lick_threshold_up, 10, 2)
        layout.addWidget(self.objs.right_lick_threshold_down, 11, 2)

        self.GroupBox_serial.setLayout(layout)
    #

    def create_trial_parameter_group(self):
        #
        self.objs.discrimination_probability_label = self.add_label(text='discrimination prob.: ')
        self.objs.discrimination_probability_label.resize(140, 30)
        self.objs.discrimination_probability_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.discrimination_probability = QLineEdit(self)
        self.objs.discrimination_probability.move(300, 65)
        self.objs.discrimination_probability.resize(100, 25)
        self.objs.discrimination_probability.setText(str(self.discrimination_probability))

        #
        self.objs.target_cue_probability_label = self.add_label(text='target cue prob.: ')
        self.objs.target_cue_probability_label.resize(140, 30)
        self.objs.target_cue_probability_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.target_cue_probability = QLineEdit(self)
        self.objs.target_cue_probability.move(300, 115)
        self.objs.target_cue_probability.resize(100, 25)
        self.objs.target_cue_probability.setText(str(0.7))
        self.objs.target_cue_probability.setEnabled(False)

        #
        self.objs.distractor_cue_probability_label = self.add_label(text='distractor cue prob.: ')
        self.objs.distractor_cue_probability_label.resize(140, 30)
        self.objs.distractor_cue_probability_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.distractor_cue_probability = QLineEdit(self)
        self.objs.distractor_cue_probability.move(300, 165)
        self.objs.distractor_cue_probability.resize(100, 25)
        self.objs.distractor_cue_probability.setText(str(0.3))
        self.objs.distractor_cue_probability.setEnabled(False)

        #

        # Visual trial probability
        self.objs.visual_trial_probability_label = self.add_label(text='visual trial prob.: ')
        self.objs.visual_trial_probability_label.resize(200, 30)
        self.objs.visual_trial_probability_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.visual_trial_probability = QLineEdit(self)
        self.objs.visual_trial_probability.move(10, 690)
        self.objs.visual_trial_probability.resize(75, 25)
        self.objs.visual_trial_probability.setText('0.3333')

        # Tactile trial probability
        self.objs.tactile_trial_probability_label = self.add_label(text='tactile trial prob.: ')
        self.objs.tactile_trial_probability_label.resize(200, 30)
        self.objs.tactile_trial_probability_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.tactile_trial_probability = QLineEdit(self)
        self.objs.tactile_trial_probability.move(10, 690)
        self.objs.tactile_trial_probability.resize(75, 25)
        self.objs.tactile_trial_probability.setText('0.3333')

        #

        # Auto-reward
        self.objs.auto_reward_button = QCheckBox('Auto-reward', self)
        self.objs.auto_reward_button.move(10, 110)
        self.objs.auto_reward_button.stateChanged.connect(self.auto_reward_callback)
        self.objs.auto_reward_button.setChecked(True)
        # self.objs.auto_reward_button.setChecked(False)

        # # Both-spouts
        # self.objs.both_spouts_button = QCheckBox('Move both spouts in?', self)
        # self.objs.both_spouts_button.move(10, 135)
        # self.objs.both_spouts_button.stateChanged.connect(self.both_spouts_callback)
        # self.objs.both_spouts_button.setChecked(False)

        self.objs.both_spouts_probability_label = self.add_label(text='Both-spouts IN prob. vis: ')
        self.objs.both_spouts_probability_label.resize(200, 30)
        self.objs.both_spouts_probability_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.both_spouts_probability = QLineEdit(self)
        self.objs.both_spouts_probability.move(300, 280)
        self.objs.both_spouts_probability.resize(75, 25)
        self.objs.both_spouts_probability.setText(str(self.both_spouts_probability_value))
        # self.objs.both_spouts_probability.textChanged[str].connect(self.update_spout_position_left_out)

        # Tactile case
        self.objs.both_spouts_tactile_probability_label = self.add_label(text='Both-spouts IN prob. tact: ')
        self.objs.both_spouts_tactile_probability_label.resize(200, 30)
        self.objs.both_spouts_tactile_probability_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.both_spouts_tactile_probability = QLineEdit(self)
        self.objs.both_spouts_tactile_probability.move(300, 330)
        self.objs.both_spouts_tactile_probability.resize(75, 25)
        self.objs.both_spouts_tactile_probability.setText(str(self.both_spouts_tactile_probability_value))
        #

        # OG_prob.
        self.objs.og_probability_label = self.add_label(text='Optogenetic trial prob.: ')
        self.objs.og_probability_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.og_probability = QLineEdit(self)
        self.objs.og_probability.setText('0.0')
        #

        #

        # Valve open durations
        self.objs.valve_left_duration_label = self.add_label(text='Left valve duration.: ')
        self.objs.valve_left_duration_label.resize(200, 30)
        self.objs.valve_left_duration_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.valve_left_duration = QLineEdit(self)
        self.objs.valve_left_duration.move(300, 280)
        self.objs.valve_left_duration.resize(75, 25)
        self.objs.valve_left_duration.setText(str(self.left_valve_duration))

        # Tactile case
        self.objs.valve_right_duration_label = self.add_label(text='Right valve duration.: ')
        self.objs.valve_right_duration_label.resize(200, 30)
        self.objs.valve_right_duration_label.setAlignment(QtCore.Qt.AlignLeft)

        self.objs.valve_right_duration = QLineEdit(self)
        self.objs.valve_right_duration.move(300, 330)
        self.objs.valve_right_duration.resize(75, 25)
        self.objs.valve_right_duration.setText(str(self.right_valve_duration))

        # bias thresholds
        self.objs.bias_threshold_0 = QLineEdit(self)
        self.objs.bias_threshold_0.resize(75, 25)
        self.objs.bias_threshold_0.setText('0.05')

        self.objs.bias_threshold_1 = QLineEdit(self)
        self.objs.bias_threshold_1.resize(75, 25)
        self.objs.bias_threshold_1.setText('0.15')

        self.objs.bias_threshold_2 = QLineEdit(self)
        self.objs.bias_threshold_2.resize(75, 25)
        self.objs.bias_threshold_2.setText('0.3')

        # bias factors
        self.objs.bias_factor_0 = QLineEdit(self)
        self.objs.bias_factor_0.resize(75, 25)
        self.objs.bias_factor_0.setText('1')

        self.objs.bias_factor_1 = QLineEdit(self)
        self.objs.bias_factor_1.resize(75, 25)
        self.objs.bias_factor_1.setText('2')

        self.objs.bias_factor_2 = QLineEdit(self)
        self.objs.bias_factor_2.resize(75, 25)
        self.objs.bias_factor_2.setText('5')

        #

        # add objects to layout
        layout = QGridLayout()

        layout.addWidget(self.objs.discrimination_probability_label, 0, 0)
        layout.addWidget(self.objs.discrimination_probability, 1, 0)

        layout.addWidget(self.objs.target_cue_probability_label, 0, 1)
        layout.addWidget(self.objs.distractor_cue_probability_label, 0, 2)
        layout.addWidget(self.objs.target_cue_probability, 1, 1)
        layout.addWidget(self.objs.distractor_cue_probability, 1, 2)

        #
        layout.addWidget(self.objs.auto_reward_button, 2, 0)
        # layout.addWidget(self.objs.both_spouts_button, 3, 0)

        #
        layout.addWidget(self.objs.visual_trial_probability_label, 2, 1)
        layout.addWidget(self.objs.visual_trial_probability, 3, 1)

        layout.addWidget(self.objs.tactile_trial_probability_label, 2, 2)
        layout.addWidget(self.objs.tactile_trial_probability, 3, 2)

        layout.addWidget(self.objs.both_spouts_probability_label, 4, 0)
        layout.addWidget(self.objs.both_spouts_probability, 5, 0)
        layout.addWidget(self.objs.both_spouts_tactile_probability_label, 4, 1)
        layout.addWidget(self.objs.both_spouts_tactile_probability, 5, 1)

        layout.addWidget(self.objs.og_probability_label, 4, 2)
        layout.addWidget(self.objs.og_probability, 5, 2)

        # Valve
        layout.addWidget(self.objs.valve_left_duration_label, 6, 0)
        layout.addWidget(self.objs.valve_left_duration, 7, 0)
        layout.addWidget(self.objs.valve_right_duration_label, 6, 1)
        layout.addWidget(self.objs.valve_right_duration, 7, 1)

        #
        # layout.addWidget(self.objs.bias_threshold_0, 8, 0)
        # layout.addWidget(self.objs.bias_threshold_1, 8, 1)
        # layout.addWidget(self.objs.bias_threshold_2, 8, 2)
        #
        # layout.addWidget(self.objs.bias_factor_0, 9, 0)
        # layout.addWidget(self.objs.bias_factor_1, 9, 1)
        # layout.addWidget(self.objs.bias_factor_2, 9, 2)

        #
        self.GroupBox_trial = QGroupBox("Trial Parameters")
        self.GroupBox_trial.setLayout(layout)
    #

    def create_performance_group(self, group_id):
        layout = QGridLayout()
        column_labels = ['correct', 'error', 'missed']
        row_labels = ['visual', 'tactile', 'visuotactile']
        for i in range(3):
            layout.addWidget(QLabel(column_labels[i]), 0, i + 1)
            layout.addWidget(QLabel(row_labels[i]), i + 1, 0)
            for j in range(3):
                self.objs.performance_indicator[group_id][i][j] = self.add_label(text='0 (0, 0); 0%')
                layout.addWidget(self.objs.performance_indicator[group_id][i][j], i+1, j+1)
            #
        #

        # add objects to layout
        if group_id == 0:
            self.GroupBox_performance[group_id] = QGroupBox("Detection Performance - [ L+R (L, R); ratio[%] ]")
        else:
            self.GroupBox_performance[group_id] = QGroupBox("Discrimination Performance - [ L+R (L, R); ratio[%] ]")
        #
        self.GroupBox_performance[group_id].setLayout(layout)
    #

    def build_gui(self):
        # Defines the GUI
        self.setWindowTitle('MS_task')  # set the title
        # self.setGeometry(-3800, 100, 300, 630)  # setting  the geometry of window
        self.setGeometry(20, 100, 1700, 850)  # setting  the geometry of window
        self.setStyleSheet("background-color: white")

        # create all GroupBoxes
        self.create_session_group()
        self.create_behavior_indicator_group()
        self.create_serial_group()
        self.create_trial_parameter_group()
        self.create_plot_group()

        self.GroupBox_performance = [None, None]
        self.create_performance_group(0)
        self.create_performance_group(1)

        # After adding all gui elements initialize with the first session conditions
        self.select_session_configuration("Detection - visual only")
        # self.select_session_configuration("Detection - all modalities")
        # self.select_session_configuration("Discrimination - all modalities")

        # Central Widget to add everything else to
        windowLayout = QGridLayout()
        windowLayout.addWidget(self.GroupBox_session, 0, 0)
        windowLayout.addWidget(self.GroupBox_trial, 0, 1)
        windowLayout.addWidget(self.GroupBox_behavior_indicators, 1, 0)
        windowLayout.addWidget(self.GroupBox_serial, 1, 1)
        windowLayout.addWidget(self.GroupBox_performance[0], 2, 0)
        windowLayout.addWidget(self.GroupBox_performance[1], 2, 1)
        windowLayout.addWidget(self.GroupBox_plots, 0, 2, 3, 1)

        windowLayout.setColumnStretch(0, 1)
        windowLayout.setRowStretch(2, 1)

        self.MainWidget = QWidget()
        self.MainWidget.setLayout(windowLayout)
        self.setCentralWidget(self.MainWidget)
    #

    #################################
    # ## build_gui() - FUNCTIONS ## #
    #################################
    def add_label(self, text='Lick Left'):
        obj = QLabel(text, self)
        obj.setAlignment(Qt.AlignCenter)
        set_label_bg_color(obj, False)  # set background color
        return obj
    #

    def start_session(self):
        optogenetic_target = self.objs.optogenetic_target.currentText()
        self.objs.optogenetic_target.setEnabled(False)
        # self.objs.og_type_comboBox.setEnabled(False)
        # self.objs.og_modality_comboBox.setEnabled(False)
        self.objs.og_power_comboBox.setEnabled(False)
        bilateral_og = self.objs.og_bilateral_comboBox.currentText() == 'bilateral'
        self.objs.og_bilateral_comboBox.setEnabled(False)

        print("Bilateral Optogenetics: %d" % bilateral_og)
        print("optogenetic_target: %s" % optogenetic_target)

        # also delete the buttons!
        self.objs.flush_left.deleteLater()
        self.objs.flush_right.deleteLater()

        self.objs.serial_spouts_IN.deleteLater()
        self.objs.serial_spouts_OUT.deleteLater()

        del self.objs.flush_left
        del self.objs.flush_right

        del self.objs.serial_spouts_IN
        del self.objs.serial_spouts_OUT

        self.vars.mouse_id = self.objs.mouse_id.text()

        # if self.vars.mouse_id == '2436':
        #     self.optogenetic_power = 4.0
        #     rel_power = 0.189
        # elif self.vars.mouse_id == '2435':
        #     self.optogenetic_power = 4.0
        #     rel_power = 0.108
        # elif self.vars.mouse_id == '2374':
        #     self.optogenetic_power = 4.0
        #     rel_power = 0.100
        # elif self.vars.mouse_id == '2375':
        #     self.optogenetic_power = 4.0
        #     rel_power = 0.112
        # else:
        #     print('WARNING: using default settings non of the once defined per mouse !!!')
        #     self.optogenetic_power = 2.0
        #     rel_power = 0.102
        # #
        # send_data_until_confirmation(serial_obj=self.og_teensy, header_byte=LED_INTENSITY, data=[rel_power, rel_power])
        # print('Optogenetic Power Used: ' + str(rel_power))

        # start the session
        self.session = Session(config=self.config, mouse_id=self.vars.mouse_id, spout_positions=self.spout_positions,
                               serial_obj=self.serial_obj, DAQ_disabled=self.objs.DAQ_disabled_box.isChecked(),
                               optogenetic_target=optogenetic_target, optogenetic_power=self.optogenetic_power,
                               og_type=self.vars.og_type, og_modality=self.vars.og_modality,
                               visual_contrast_control=self.visual_contrast_control,
                               airpuff_pressure_control=self.airpuff_pressure_control,
                               optogenetics_in_detection_conditions=self.optogenetics_in_detection_conditions,
                               optogenetics_bilateral=bilateral_og
        )

        self.objs.DAQ_disabled_box.setEnabled(False)

        # Clean-up the GUI
        self.objs.mouse_id.deleteLater()
        self.objs.mouse_id = None
        del self.objs.mouse_id
        self.objs.mouse_id_label.setText('Mouse ID: %s' % self.vars.mouse_id)

        # They are covered by the distractor min/max indicators. Now they can be set visible.
        self.objs.trial_id.setVisible(True)
        self.objs.session_time.setVisible(True)

        # set GUI session start time
        self.vars.session_start = time()

        # delete the start_button
        self.objs.start_button.deleteLater()
        del self.objs.start_button

        # add stop button
        self.objs.stop_button.setVisible(True)
        self.objs.pause_button.setVisible(True)
        self.show()

        self.update_gui()
    #

    # #####################################
    # CALLBACKS ###########################
    # #####################################
    def select_session_configuration(self, text):
        # Default was False
        # When moving to discrimination, we should disable this again!
        self.optogenetics_in_detection_conditions = True
        if text == "Detection - visual only":
            self.objs.visual_trial_probability.setText("1.0")
            self.objs.tactile_trial_probability.setText("0.0")
            self.objs.discrimination_probability.setText("0.0")
            self.visual_contrast_control = 0
            self.airpuff_pressure_control = 0
        elif text == "Detection - tactile only":
            self.objs.visual_trial_probability.setText("0.0")
            self.objs.tactile_trial_probability.setText("1.0")
            self.objs.discrimination_probability.setText("0.0")
            self.visual_contrast_control = 0
            self.airpuff_pressure_control = 0
        elif text == "Detection - visual + tactile":
            self.objs.visual_trial_probability.setText("0.5")
            self.objs.tactile_trial_probability.setText("0.5")
            self.objs.discrimination_probability.setText("0.0")
            self.visual_contrast_control = 0
            self.airpuff_pressure_control = 0
        elif text == "Detection - all modalities":
            self.objs.visual_trial_probability.setText("0.3333")
            self.objs.tactile_trial_probability.setText("0.3333")
            self.objs.discrimination_probability.setText("0.0")
            self.visual_contrast_control = 0
            self.airpuff_pressure_control = 0
        elif text == "Discrimination - all modalities":
            self.objs.visual_trial_probability.setText("0.3333")
            self.objs.tactile_trial_probability.setText("0.3333")
            self.objs.discrimination_probability.setText("0.5")
            self.visual_contrast_control = 0
            self.airpuff_pressure_control = 0
        elif text == "Discrimination - only visual":
            self.objs.visual_trial_probability.setText("1.0")
            self.objs.tactile_trial_probability.setText("0.0")
            self.objs.discrimination_probability.setText("0.666")
            self.visual_contrast_control = 0
            self.airpuff_pressure_control = 0
        elif text == "Visual_contrast_control":
            self.objs.visual_trial_probability.setText("1.0")
            self.objs.tactile_trial_probability.setText("0.0")
            self.objs.discrimination_probability.setText("0.0")
            self.visual_contrast_control = 1
            self.airpuff_pressure_control = 0
            self.optogenetics_in_detection_conditions = True
        elif text == "Airpuff_pressure_control":
            self.objs.visual_trial_probability.setText("0.0")
            self.objs.tactile_trial_probability.setText("1.0")
            self.objs.discrimination_probability.setText("0.0")
            self.visual_contrast_control = 0
            self.airpuff_pressure_control = 1
        #
    #

    def select_og_type(self, text):
        if text == "No Optogenetic":
            self.vars.og_type = 0
        elif text == "Full trial":
            self.vars.og_type = 1
        elif text == "Stimulus only":
            self.vars.og_type = 2
        elif text == "Choice only":
            self.vars.og_type = 3
        elif text == "Random Stimulus/Choice":
            self.vars.og_type = 4
        #
        print(self.vars.og_type)
    #

    def select_og_modality(self, text):
        # if text == "None":
        #     self.vars.og_modality = -1
        # elif text == "Visual":
        #     self.vars.og_modality = 0
        # elif text == "Tactile":
        #     self.vars.og_modality = 1
        # elif text == "Vistact":
        #     self.vars.og_modality = 2
        # #

        if text == "None":
            self.vars.og_modality = (-1, -1)
        elif text == "Visual":
            self.vars.og_modality = (0, 1)
        elif text == "Tactile":
            self.vars.og_modality = (1, 2)
        elif text == "Vistact":
            self.vars.og_modality = (2, 0)
        #
        print(self.vars.og_modality)
    #

    def select_optogenetic_target(self, text):
        if text != "None":
            # self.objs.og_probability.setText('0.15')
            self.objs.og_probability.setText('0.5')
        #

        if (text == "SC"):  # or (text == "SC-deep"):
            self.objs.og_probability.setText('0.15')
            # self.objs.og_probability.setText('0.30')
        #
    #

    def select_optogenetics_power(self, text):
        self.optogenetic_power = float(text)
        optogenetic_relative_power_og0, optogenetic_relative_power_og1 = \
            self.calculate_relative_optogenetic_power(self.optogenetic_power)
        # # self.optogenetic_relative_power_left, self.optogenetic_relative_power_right = some_calibration_function(self.optogenetic_power)
        # self.optogenetic_relative_power_left, self.optogenetic_relative_power_right = 1., 1.
        send_data_until_confirmation(serial_obj=self.og_teensy, header_byte=LED_INTENSITY, data=[
            optogenetic_relative_power_og0, optogenetic_relative_power_og1])
        #
        print('CHANGED OG POWER: ', [self.optogenetic_power,
            optogenetic_relative_power_og0, optogenetic_relative_power_og1])
    #

    def auto_reward_callback(self, state):
        try:
            self.session.gui_variables.display_auto_reward = (state == Qt.Checked)
        except:
            pass
        #
    #

    def both_spouts_callback(self, state):
        try:
            self.session.gui_variables.display_both_spouts = (state == Qt.Checked)
        except:
            pass
        #
    #

    def update_spout_position_left_in(self, text):
        try:
            if self.session is None:
                # change the default positions before starting the session
                self.spout_positions[0] = int(text)
                # self.spout_positions[2] = self.spout_positions[0] - 20
            else:
                # If the session has been started already set the variables there directly
                self.session.spout_left_in_position = int(text)
            #
        except:
            pass
        #
    #

    def update_spout_position_right_in(self, text):
        try:
            if self.session is None:
                # change the default positions before starting the session
                self.spout_positions[1] = int(text)
                # self.spout_positions[3] = self.spout_positions[1] - 20
            else:
                # If the session has been started already set the variables there directly
                self.session.spout_right_in_position = int(text)
            #
        except:
            pass
        #
    #

    def update_spout_position_left_out(self, text):
        try:
            if self.session is None:
                # change the default positions before starting the session
                self.spout_positions[2] = int(text)
            else:
                # If the session has been started already set the variables there directly
                self.session.spout_left_out_position = int(text)
            #
        except:
            pass
        #
    #

    def update_spout_position_right_out(self, text):
        try:
            if self.session is None:
                # change the default positions before starting the session
                self.spout_positions[3] = int(text)
            else:
                # If the session has been started already set the variables there directly
                self.session.spout_right_out_position = int(text)
            #
        except:
            pass
        #
    #

    def calculate_relative_optogenetic_power(self, temp_value):
        # WF_setup - LEDs
        # rel_power_og0 = (temp_value - 0.1354) / 2.2186  # calibrated 2021-06-03
        # rel_power_og1 = (temp_value - 0.1397) / 2.325  # calibrated 2021-06-03

        if temp_value == 9.5:
            # Laser
            rel_power_og0 = (temp_value - float(self.config['Setup']['rel_power_og0_intercept'])) / float(self.config['Setup']['rel_power_og0_slope'])
            rel_power_og1 = (temp_value - float(self.config['Setup']['rel_power_og1_intercept'])) / float(self.config['Setup']['rel_power_og1_slope'])
            print('OG_power 9.5mW: ', rel_power_og0, ', ', rel_power_og1)

            rel_power_og0 = 0.38  # Never used, I'm just putting this one in from memory. Don't trust this value if it looks weird!
            rel_power_og1 = 0.38  # Never used, I'm just putting this one in from memory. Don't trust this value if it looks weird!
        elif temp_value == 3.0:
            rel_power_og0 = 0.90  # Added this option LEDs 2023-01-23
            rel_power_og1 = 0.65  # Added this option 2023-01-23
            print('OG_power ', temp_value, 'mW: ', rel_power_og0, ', ', rel_power_og1)
            # print('OG_power 2mW: ', rel_power_og0, ', ', rel_power_og1)
        elif temp_value == 2.0:
            # # # rel_power_og0 = 0.1  # This I calibrated 2021-08-09 - 2mW
            # # # rel_power_og1 = 0.1  # This I calibrated 2021-08-09 - 2mW
            # # rel_power_og0 = 0.13  # This I calibrated 2021-08-09 (set to 5.6mW)
            # # rel_power_og1 = 0.13  # This I calibrated 2021-08-09
            # rel_power_og0 = 0.096  # Recalibrated at some point for Maria
            # rel_power_og1 = 0.096  # Recalibrated at some point for Maria
            # rel_power_og0 = 0.45  # Switched from Laser to LEDs 2022-08-30
            # rel_power_og1 = 0.365  # Switched from Laser to LEDs 2022-08-30
            rel_power_og0 = 0.51  # Updated LEDs 2023-01-23
            rel_power_og1 = 0.395  # Updated LEDs 2023-01-23
            print('OG_power ', temp_value, 'mW: ', rel_power_og0, ', ', rel_power_og1)
            # print('OG_power 2mW: ', rel_power_og0, ', ', rel_power_og1)
        elif temp_value == 1.5:
            # rel_power_og0 = 0.075  # Recalibrated at some point for Maria
            # rel_power_og1 = 0.075  # Recalibrated at some point for Maria
            # rel_power_og0 = 0.317  # Switched from Laser to LEDs 2022-08-30
            # rel_power_og1 = 0.263  # Switched from Laser to LEDs 2022-08-30
            rel_power_og0 = 0.375  # Updated LEDs 2023-01-23
            rel_power_og1 = 0.28  # Updated LEDs 2023-01-23
            print('OG_power ', temp_value, 'mW: ', rel_power_og0, ', ', rel_power_og1)
        elif temp_value == 1.0:
            # rel_power_og0 = 0.055  # Recalibrated at some point for Maria
            # rel_power_og1 = 0.055  # Recalibrated at some point for Maria
            # rel_power_og0 = 0.205  # Switched from Laser to LEDs 2022-08-30
            # rel_power_og1 = 0.175  # Switched from Laser to LEDs 2022-08-30
            rel_power_og0 = 0.235  # Updated LEDs 2023-01-23
            rel_power_og1 = 0.19  # Updated LEDs 2023-01-23
            print('OG_power ', temp_value, 'mW: ', rel_power_og0, ', ', rel_power_og1)
        elif temp_value == 0.5:
            # rel_power_og0 = 0.035  # Recalibrated at some point for Maria
            # rel_power_og1 = 0.035  # Recalibrated at some point for Maria
            # rel_power_og0 = 0.104  # Switched from Laser to LEDs 2022-08-30
            # rel_power_og1 = 0.092  # Switched from Laser to LEDs 2022-08-30
            rel_power_og0 = 0.12  # Updated LEDs 2023-01-23
            rel_power_og1 = 0.092  # Updated LEDs 2023-01-23
            print('OG_power ', temp_value, 'mW: ', rel_power_og0, ', ', rel_power_og1)
        else:
            [print('INVALIDE OPTOGENETICS POWER!!!') for _ in range(100)]
            raise Exception('Invalide Optogenetics Power !!!')
        #

        return rel_power_og0, rel_power_og1
    #

    def calculate_valve_duration(self, temp_value, side):
        # if side == 'left':
        #     # temp_value = round((temp_value - 0.41488095238095200000) / 0.00009559523809523810)  # calibrated 2021-03-17 - WF
        #     # temp_value = round((temp_value - 0.02495238095238100000) / 0.00008297142857142860)  # calibrated 2021-04-06 - e-phys
        #     # temp_value = round((temp_value + 0.12178571428571400000) / 0.00008721428571428570)  # calibrated 2021-04-15 - e-phys
        #     # 2021-04-19 - changed the tubing in the e-phys setup:
        #     temp_value = round((temp_value - 0.20928571428571700000) / 0.000051)  # calibrated 2021-04-19 - e-phys
        # else:
        #     # temp_value = round((temp_value - 0.48457142857142900000) / 0.00009528571428571430)  # calibrated 2021-03-17 - WF
        #     # temp_value = round((temp_value + 0.08285714285714290000) / 0.00009828571428571430)  # calibrated 2021-04-06 - e-phys
        #     # temp_value = round((temp_value + 0.18714285700000000000) / 0.00009628571428571430)  # calibrated 2021-04-15 - e-phys
        #     # 2021-04-19 - changed the tubing in the e-phys setup:
        #     temp_value = round((temp_value - 0.06285714285714290000) / 0.00005742857142857140)  # calibrated 2021-04-19 - e-phys
        # #

        if side == 'left':
            temp_value = round((temp_value - float(self.config['Setup']['spout_duration_left_intercept'])) / float(self.config['Setup']['spout_duration_left_slope']))
        else:
            temp_value = round((temp_value - float(self.config['Setup']['spout_duration_right_intercept'])) / float(self.config['Setup']['spout_duration_right_slope']))
        #

        return temp_value
    #

    def flush_valves(self, side):
        try:
            # if self.objs.flush_left.isChecked():
            for i in range(1):
                if side == 'left':
                    send_data_until_confirmation(self.serial_obj, header_byte=FLUSH_VALVE_LEFT,
                                                 data=[self.calculate_valve_duration(self.left_valve_duration, 'left')])
                    print('left: ', self.calculate_valve_duration(self.left_valve_duration, 'left'))
                else:  # right
                    send_data_until_confirmation(self.serial_obj, header_byte=FLUSH_VALVE_RIGHT,
                                                 data=[self.calculate_valve_duration(self.right_valve_duration, 'right')])
                    print('right: ', self.calculate_valve_duration(self.right_valve_duration, 'right'))
                #
                if use_visual_stimulus_client:
                    self.visual_stimulus_server.send([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
                sleep(0.1)
            #
            self.objs.flush_left.clicked = False
            #
        except:
            pass
        #
    #

    def call_spouts_calibrate(self):
        send_data_until_confirmation(self.serial_obj, header_byte=ADJUST_SPOUTES, data=[1, 1])
        sleep(0.01)
        send_data_until_confirmation(self.serial_obj, header_byte=ADJUST_SPOUTES, data=[0, 0])
        sleep(0.01)
    #

    def call_calibrate_licks(self):
        # 5 standard deviations as threshold
        try:
            temp = int(self.objs.spouts_std.text())
        except:  # Exception as e:
            # print('Spouts: ', 10)
            temp = 10
        #
        send_data_until_confirmation(self.serial_obj, header_byte=ADJUST_TOUCHLEVEL, data=[temp])
    #

    def call_spouts_IN(self):
        if self.session is None:
            # Session not started yet
            temp_left_position = self.spout_positions[0]
            temp_right_position = self.spout_positions[1]
        else:
            temp_left_position = self.session.spout_left_in_position
            temp_right_position = self.session.spout_right_in_position
        #
        send_data_until_confirmation(self.serial_obj, header_byte=ADJUST_SPOUTES,
                                     data=[temp_left_position, temp_right_position])
    #

    def call_spouts_OUT(self):
        if self.session is None:
            # Session not started yet
            temp_left_position = self.spout_positions[0] - 80
            temp_right_position = self.spout_positions[1] - 80
        else:
            temp_left_position = self.session.spout_left_out_position
            temp_right_position = self.session.spout_right_out_position
        #
        send_data_until_confirmation(self.serial_obj, header_byte=ADJUST_SPOUTES,
                                     data=[temp_left_position, temp_right_position])
    #

    def change_touch_thresholds(self, text):
        if text == 'left_up':
            send_data_until_confirmation(self.serial_obj, header_byte=TOUCH_THRESHOLD_LEFT_UP)
        elif text == 'left_down':
            send_data_until_confirmation(self.serial_obj, header_byte=TOUCH_THRESHOLD_LEFT_DOWN)
        elif text == 'right_up':
            send_data_until_confirmation(self.serial_obj, header_byte=TOUCH_THRESHOLD_RIGHT_UP)
        elif text == 'right_down':
            send_data_until_confirmation(self.serial_obj, header_byte=TOUCH_THRESHOLD_RIGHT_DOWN)
        #
    #

    # ##########################################
    # RUN SESSIONS #############################
    # ##########################################
    def run(self):
        if self.session is not None:
            # ##     ## #
            # TASK LOOP #
            # ##     ## #
            # self.session.display_auto_reward = self.vars.auto_reward
            if self.session.trial_finished:
                if self.vars.end_session:
                    self.visual_stimulus_server.close()
                    print('Server CLOSED!')

                    # This closes the window!
                    self.session.end_session()
                    self.close()
                    return
                else:
                    if not self.vars.pause:
                        try:
                            bias_thresholds = [float(self.objs.bias_threshold_0.text()),
                                               float(self.objs.bias_threshold_1.text()),
                                               float(self.objs.bias_threshold_2.text())]
                        except:
                            print('Overwrote bias_threshold with [0.05, 0.15, 0.30] !!!')
                            bias_thresholds = [0.05, 0.15, 0.30]
                        #

                        try:
                            bias_factors = [int(self.objs.bias_factor_0.text()),
                                            int(self.objs.bias_factor_1.text()),
                                            int(self.objs.bias_factor_2.text())]
                        except:
                            print('Overwrote bias_factors with [1, 2, 5] !!!')
                            bias_factors = [1, 2, 5]
                        #

                        self.update_performance_plots()

                        self.session.init_trial(bias_threshold=bias_thresholds, bias_factors=bias_factors)
                        self.session.trial_finished = False

                        # Update GUI Objects that change trial wise
                        self.objs.spout_position_left_current.setText(str(self.session.spout_left_current_position))
                        self.objs.spout_position_right_current.setText(str(self.session.spout_right_current_position))
                    #
                #
            visual_server_data = self.session.trial_loop()
            if use_visual_stimulus_client:
                if visual_server_data[0] == 0:
                    if time() - self.last_visual_server_update > 0.5:
                        self.visual_stimulus_server.send([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
                        self.last_visual_server_update = time()
                    #
                else:
                    if time() - self.last_visual_server_update > 0.01:
                        if len(visual_server_data) == 14:
                            self.visual_stimulus_server.send(visual_server_data)
                            self.last_visual_server_update = time()
                        #
                    #
                #
            #
            # ##                              ## #
            # END OF TASK LOOP! Now updating GUI #
            # ##                              ## #
        else:
            try:
                # If now regularly updated, the Psychopy Windows are identified as unresponsive by Windows -_-
                # Therefore, periodically send the client the gray-screen command
                if time() - self.last_visual_server_update > 0.5:
                    self.visual_stimulus_server.send([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1])
                    self.last_visual_server_update = time()
                #
            except:
                pass
            #
        #

        self.update_gui()
    #

    def update_gui(self):
        # TODO: make all this value_change based at some point to not always update everything!

        # Update label texts
        if self.session is not None:
            # send to session
            # self.session.display_auto_reward = self.objs.auto_reward_button.isChecked()
            # self.session.both_spouts = self.objs.both_spouts_button.isChecked()
            # self.vars.auto_reward = self.objs.auto_reward_button.isChecked()

            self.objs.cue_indicator_l.setText('left cues: ' + ''.join([str(i) for i in np.array(self.session.cues_left_visual) + np.array(self.session.cues_left_tactile)]))
            self.objs.cue_indicator_r.setText('right cues: ' + ''.join([str(i) for i in np.array(self.session.cues_right_visual) + np.array(self.session.cues_right_tactile)]))

            self.session.gui_variables.display_auto_reward = self.objs.auto_reward_button.checkState() == Qt.Checked
            # self.session.gui_variables.display_both_spouts = self.objs.both_spouts_button.checkState() == Qt.Checked

            try:
                temp_value = float(self.objs.both_spouts_probability.text())
                if temp_value < 0:
                    temp_value = 0
                if temp_value > 1:
                    temp_value = 1
                self.session.gui_variables.display_both_spouts_probability = temp_value
                self.objs.both_spouts_probability_label.setText('Both-spouts IN prob. vis: '+('%0.2f' % temp_value))
            except:
                pass
            #

            try:
                # tact both spouts
                temp_value = float(self.objs.both_spouts_tactile_probability.text())
                if temp_value < 0:
                    temp_value = 0
                if temp_value > 1:
                    temp_value = 1
                self.session.gui_variables.display_both_spouts_tact_probability = temp_value
                self.objs.both_spouts_tactile_probability_label.setText(
                    'Both-spouts IN prob. tact: ' + ('%0.2f' % temp_value))
            except:
                pass
            #

            try:
                # og
                temp_value = float(self.objs.og_probability.text())
                if temp_value < 0:
                    temp_value = 0
                if temp_value > 1:
                    temp_value = 1
                self.session.gui_variables.optogenetic_trial_probability = temp_value
                self.objs.og_probability_label.setText(
                    'Optogenetic trial prob.: ' + ('%0.2f' % temp_value))
            except:
                pass
            #

            try:
                temp_value = float(self.objs.valve_left_duration.text())
                if temp_value < 0:
                    temp_value = 0
                self.session.gui_variables.display_valve_left_water_amount = temp_value
                temp_value = self.calculate_valve_duration(temp_value, 'left')
                # temp_value = (temp_value - 0.41488095238095200000) / 0.00009559523809523810  # calibrated 2021-03-17
                self.session.gui_variables.display_valve_left_duration = temp_value
                self.objs.valve_left_duration_label.setText('Left valve duration: '+('%0.2f' % temp_value))

                # tact both spouts
                temp_value = float(self.objs.valve_right_duration.text())
                if temp_value < 0:
                    temp_value = 0
                # temp_value = (temp_value - 0.48457142857142900000) / 0.00009528571428571430  # calibrated 2021-03-17
                self.session.gui_variables.display_valve_right_water_amount = temp_value
                temp_value = self.calculate_valve_duration(temp_value, 'right')
                self.session.gui_variables.display_valve_right_duration = temp_value
                self.objs.valve_right_duration_label.setText('Right valve duration: '+('%0.2f' % temp_value))
            except:
                pass
            #
            try:
                temp_value = float(self.objs.visual_trial_probability.text())
                if temp_value < 0:
                    temp_value = 0
                if temp_value > 1:
                    temp_value = 1
                self.session.gui_variables.display_visual_trial_probability = temp_value
                self.objs.visual_trial_probability_label.setText('visual trial prob.: '+('%0.2f' % temp_value))
            except:
                pass
            #
            try:
                temp_value = float(self.objs.tactile_trial_probability.text())
                if temp_value < 0:
                    temp_value = 0
                if temp_value > 1:
                    temp_value = 1
                self.session.gui_variables.display_tactile_trial_probability = temp_value
                self.objs.tactile_trial_probability_label.setText('tactile trial prob.: '+('%0.2f' % temp_value))
            except:
                pass
            #

            try:
                temp_value = float(self.objs.discrimination_probability.text())
                if temp_value < 0:
                    temp_value = 0
                if temp_value > 1:
                    temp_value = 1
                self.session.gui_variables.discrimination_probability = temp_value
                self.objs.discrimination_probability_label.setText('discrimination prob.: '+('%0.2f' % temp_value))
            except:
                pass
            #

            try:
                temp_value = float(self.objs.target_cue_probability.text())
                if temp_value < 0:
                    temp_value = 0
                if temp_value > 1:
                    temp_value = 1
                self.session.gui_variables.target_cue_probability_visual = temp_value
                self.session.gui_variables.target_cue_probability_tactile = temp_value
                self.objs.target_cue_probability_label.setText('target cue prob.: '+('%0.2f' % temp_value))
            except:
                pass
            #

            try:
                temp_value = float(self.objs.distractor_cue_probability.text())
                if temp_value < 0:
                    temp_value = 0
                if temp_value > 1:
                    temp_value = 1
                self.session.gui_variables.distractor_cue_probability_visual = temp_value
                self.session.gui_variables.distractor_cue_probability_tactile = temp_value
                self.objs.distractor_cue_probability_label.setText('distractor cue prob.: '+('%0.2f' % temp_value))
            except:
                pass
            #

            try:
                temp_value = float(self.objs.airpuff_pressure.text())
                self.session.gui_variables.airpuff_pressure = temp_value
                self.objs.airpuff_pressure_label.setText('Airpuff pressure in bar: '+('%0.3f' % temp_value))
            except:
                pass
            #

            if self.session.trial_id > self.vars.trial_id:
                self.vars.trial_id = self.session.trial_id
                self.objs.trial_id.setText('Trial Nr.: %d' % self.session.trial_id)
                self.objs.modality.setText('Modality.: %s' % self.vars.modality_keys[self.session.modality])
                self.update_performance_indicators()
            #

            if self.session.gui_variables.display_target_side is not None:
                set_label_bg_color(self.objs.target_side_l, self.session.gui_variables.display_target_side == 'left')
                set_label_bg_color(self.objs.target_side_r, self.session.gui_variables.display_target_side == 'right')
            #

            # Update licks
            # TODO: figure out a way to display the licks online
            set_label_bg_color(self.objs.lick_l, self.session.gui_variables.display_lick_left)
            set_label_bg_color(self.objs.lick_r, self.session.gui_variables.display_lick_right)

            # Update Response
            if self.session.lick_response is None:
                set_label_bg_color(self.objs.lick_response_l, False)
                set_label_bg_color(self.objs.lick_response_r, False)
            else:
                set_label_bg_color(self.objs.lick_response_l, self.session.lick_response == 'left')
                set_label_bg_color(self.objs.lick_response_r, self.session.lick_response == 'right')
            #

            # update time
            self.objs.session_time.setText('Time: %s' % str(timedelta(seconds=round(time() - self.vars.session_start))))
        else:
            # self.objs.trial_id.setText('Trial Nr.: %d' % self.vars.trial_id)
            self.objs.trial_id.setText('Session not started')
        #
    #

    def call_pause(self):
        self.vars.pause = not self.vars.pause
        if self.vars.pause:
            self.objs.pause_button.setText('Resume Experiment')
        else:
            self.objs.pause_button.setText('Pause Experiment')
        #
    #

    def stop_session(self):
        self.save_screenshot()

        self.vars.end_session = True

        self.objs.stop_button.deleteLater()
        del self.objs.stop_button

        # sleep(11.)
        # self.visual_stimulus_client.kill()
    #

    def save_screenshot(self):
        screenshot = self.screen.grabWindow(self.MainWidget.winId())
        folder = path.split(path.split(self.session.file_base)[0])[0]
        file_base = path.split(self.session.file_base)[1]
        screenshot.save(path.join(folder, file_base+'_screenshot.png'))
    #

    def update_performance_indicators(self):
        for group_id in range(2):
            try:
                if group_id == 0:
                    # detection case
                    distractor_id = 6  # difference between targets and distractors
                    temp_performance = self.session.performance[6, :, :]
                    temp_performance_by_side = self.session.performance_by_side[6, :, :, :]
                else:
                    # discrimination case
                    distractor_id = 6  # difference between targets and distractors
                    temp_performance = self.session.performance[:6, :, :].sum(axis=0)
                    temp_performance_by_side = self.session.performance_by_side[:6, :, :, :].sum(axis=0)
                #

                for mod_id in range(3):
                    n_answered_trials = temp_performance[mod_id, :2].sum()
                    if n_answered_trials == 0:
                        n_answered_trials = 1
                    for condition_id in range(3):
                        if condition_id < 2:
                            self.objs.performance_indicator[group_id][mod_id][condition_id].setText(
                                '%d (%d, %d); %0.1f %%' % (
                                int(temp_performance[mod_id, condition_id]),  # total number
                                temp_performance_by_side[mod_id, condition_id, 0],  # left
                                temp_performance_by_side[mod_id, condition_id, 1],  # right
                                100. * temp_performance[mod_id, condition_id] / n_answered_trials))  # performance
                        else:
                            self.objs.performance_indicator[group_id][mod_id][condition_id].setText(
                                str(int(temp_performance[mod_id, condition_id])))
                        #
                    #
                #
            except Exception as e:
                pass
            #
        #
    #

    def update_performance_plots(self):
        if (not self.session.auto_reward) and self.session.both_spouts:
            if self.session.lick_response == 'left':
                # left response
                temp = 0
            elif self.session.lick_response == 'right':
                # right response
                temp = 1
            else:
                # missed trial
                temp = 2
            #
        else:
            # invalid trial, because its either auto-rewarded or a single spout trial
            temp = 4
        #

        # Only display the last 60 Trials
        if len(self.Response_plots['trial_tracker']) > 60:
            self.Response_plots['trial_tracker'] = self.Response_plots['trial_tracker'][-60:]
        #

        self.Response_plots['trial_tracker'].append((self.session.trial_id, 1-int(self.session.target_site == 'left'), temp))
        # print('THIS HERE: ', self.session.trial_id, 1-int(self.session.target_site == 'left'), self.session.lick_response)

        temp = np.array(self.Response_plots['trial_tracker'])
        correct_ids = temp[:, 1] == temp[:, 2]
        error_ids = 1-temp[:, 1] == temp[:, 2]
        missed_ids = temp[:, 2] == 2
        invalid_ids = temp[:, 2] == 4

        self.Response_plots['correct_plot'].setData(temp[correct_ids, 0], temp[correct_ids, 1])
        self.Response_plots['error_plot'].setData(temp[error_ids, 0], temp[error_ids, 1])
        self.Response_plots['missed_plot'].setData(temp[missed_ids, 0], temp[missed_ids, 1])
        self.Response_plots['invalid_plot'].setData(temp[invalid_ids, 0], temp[invalid_ids, 1])

        self.ResponsePlot.setYRange(0, 1, padding=0.2)
        # self.ResponsePlot.getAxis('left').setTicks([[0, 'left'], [1, 'right']])
        self.ResponsePlot.getAxis('left').setTicks([[(0, 'left')], [(1, 'right')]])
        self.ResponsePlot.getAxis('bottom').setLabel('Trial ID')

        # Performance plot
        try:
            left_performance = np.empty((7,))
            right_performance = np.empty((7,))
            average_performance = np.empty((7,))
            for target_distractor_difference in range(7):
                # n_answered_trials = self.session.performance_by_side[target_distractor_difference, :, :2, 1].sum()
                n_answered_trials = (self.session.performance_by_side[target_distractor_difference, :, 0, 0].sum() +  # correct left response
                                     self.session.performance_by_side[target_distractor_difference, :, 1, 1].sum())  # false right response
                if n_answered_trials > 0:
                    left_performance[target_distractor_difference] = \
                        self.session.performance_by_side[target_distractor_difference, :, 0, 0].sum() / n_answered_trials
                else:
                    left_performance[target_distractor_difference] = np.nan

                # n_answered_trials = self.session.performance_by_side[target_distractor_difference, :, :2, 0].sum()
                n_answered_trials = (self.session.performance_by_side[target_distractor_difference, :, 0, 1].sum() +  # correct right response
                                     self.session.performance_by_side[target_distractor_difference, :, 1, 0].sum())  # false left response

                if n_answered_trials > 0:
                    right_performance[target_distractor_difference] = \
                        self.session.performance_by_side[target_distractor_difference, :, 0, 1].sum() / n_answered_trials
                else:
                    right_performance[target_distractor_difference] = np.nan

                n_answered_trials = self.session.performance_by_side[target_distractor_difference, :, :2, :2].sum()
                if n_answered_trials > 0:
                    average_performance[target_distractor_difference] = \
                        self.session.performance_by_side[target_distractor_difference, :, 0, :2].sum() / n_answered_trials
                else:
                    average_performance[target_distractor_difference] = np.nan

            #

            if not np.isnan(left_performance).all():
                self.Performance_plots['left_performance'].setData(x=range(7), y=100*left_performance)
            if not np.isnan(right_performance).all():
                self.Performance_plots['right_performance'].setData(x=range(7), y=100*right_performance)
            if not np.isnan(average_performance).all():
                self.Performance_plots['average_performance'].setData(x=range(7), y=100*average_performance)
            #

            self.PerformancePlot.getAxis('left').setLabel('Performance in %')
            self.PerformancePlot.getAxis('bottom').setLabel('Target Distractor Difference')

            self.PerformancePlot.setYRange(0, 100, padding=0.05)
        except Exception as e:
            print(e)
        #
    #
#


if __name__ == "__main__":
    default_discrimination_probability = 0.
    default_both_spouts_probability = 1.0

    # Spout Positions [LEFT_IN, RIGHT_IN, LEFT_OUT, RIGHT_OUT]
    default_spout_positions = [215, 244]
    default_spout_positions.extend([default_spout_positions[0]-30, default_spout_positions[1]-30])

    use_visual_stimulus_client = True
    #
    app = QApplication(sys.argv)  # create pyqt5 app
    # save into variable so GC doesnt delete the gui immediately!
    gui = MSTaskGUI(default_discrimination_probability=default_discrimination_probability,
                    default_spout_positions=default_spout_positions,
                    default_both_spouts_probability=default_both_spouts_probability,
                    use_visual_stimulus_client=use_visual_stimulus_client,
                    screen=app.primaryScreen(),
                    default_water_amount=2.0)
    sys.exit(app.exec())  # start the app
#
