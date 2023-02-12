from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton
import sys
from time import time
from PyQt5.QtCore import QTimer, Qt
from datetime import timedelta


class MSTaskGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # GUI
        self.setWindowTitle('test')  # set the title
        self.setGeometry(100, 100, 300, 100)  # setting  the geometry of window
        self.setStyleSheet("background-color: white")

        self.session_time = self.add_label(text='Time: ', pos=[10, 10])
        self.session_start = time()
        self.session_time.setText('Time: %s' % str(timedelta(seconds=0)))

        self.start_button = QPushButton('Run', self)
        self.start_button.move(10, 50)
        self.start_button.clicked.connect(self.start_callback)

        self.stop_button = QPushButton('Run', self)
        self.stop_button.move(150, 50)
        self.stop_button.setGeometry(150, 50, 100, 40)
        self.stop_button.clicked.connect(self.stop_callback)
        self.stop_button.setVisible(False)

        # make QTimer
        self.qTimer = QTimer()
        self.qTimer.setInterval(0)  # in ms: 1000 ms = 1 s
        self.qTimer.timeout.connect(self.update_gui)  # connect timeout signal to signal handler
        self.qTimer.start()

        # draw GUI
        self.show()
    #

    def add_label(self, text='Lick Left', pos=None):
        if pos is None:
            pos = []
        obj = QLabel(text, self)
        obj.setAlignment(Qt.AlignCenter)
        if len(pos) > 1:
            obj.move(pos[0], pos[1])  # moving position
        #
        # set_label_bg_color(obj, False)  # set background color

        return obj
    #

    def update_gui(self):
        # update time
        self.session_time.setText('Time: %s' % str(timedelta(seconds=round(time()-self.session_start))))
    #

    def start_callback(self):
        self.stop_button.setVisible(True)

        self.start_button.deleteLater()
        self.start_button = None
        del self.start_button

        self.update()
        self.show()
    #

    def stop_callback(self):
        # self.stop_button.deleteLater()
        # self.stop_button = None
        # del self.stop_button
        self.close()
    #
#


if __name__ == "__main__":
    App = QApplication(sys.argv)  # create pyqt5 app
    # save into variable so GC doesnt delete the gui immediately!
    gui = MSTaskGUI()  # create the instance of our Window
    sys.exit(App.exec())  # start the app
#
