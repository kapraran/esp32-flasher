from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget, QComboBox, QFileDialog, QLabel

import sys
import serial.tools.list_ports

class Main(QMainWindow):
  def __init__(self):
    super().__init__()

    self.resize(250, 150)

    # ports = serial.tools.list_ports.comports()
    # for port, desc, hwid in sorted(ports):
    #   print("{}: {} [{}]".format(port, desc, hwid))

    self.cb = self.createComboBox()


    mainWidget = QWidget()

    button1 = QPushButton("Επιλογή Φακέλου")
    button1.clicked.connect(self.openFile)

    self.selectedDir = QLabel("-")

    layout = QVBoxLayout()
    layout.addWidget(self.cb)
    layout.addWidget(self.selectedDir)
    layout.addWidget(button1)
    layout.addStretch()

    self.dlg = QFileDialog()
    self.dlg.setFileMode(QFileDialog.Directory)

    mainWidget.setLayout(layout)

    self.setCentralWidget(mainWidget)

  def openFile(self):
    if self.dlg.exec_():
      self.selectedDir.setText(self.dlg.selectedFiles()[0]) 

  def createComboBox(self):
    cb = QComboBox()

    ports = serial.tools.list_ports.comports()
    portNames = list(map(lambda item: item.device, sorted(ports)))
    cb.addItems(portNames)

    return cb


if __name__ == '__main__':
    appctxt = ApplicationContext()

    window = Main()
    window.show()

    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
