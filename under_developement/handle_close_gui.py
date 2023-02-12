import sys
from PyQt5.QtWidgets import *


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        QPushButton("Open Sub Window", self)

    def closeEvent(self, event):
        QApplication.topLevelWidgets()
        print('close')
        event.ignore()
    #
#


app = QApplication(sys.argv)
mainWin = MainWindow()
mainWin.show()
sys.exit(app.exec_())
