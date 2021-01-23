from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2.QtWidgets import QTextEdit, QMainWindow, QPushButton, QVBoxLayout, QWidget, QComboBox, QFileDialog, QLabel
from PySide2.QtCore import QProcess
import tempfile
import zipfile
import os
import sys
import serial.tools.list_ports

def get_usb_ports():
  ports = serial.tools.list_ports.comports()
  ports = filter(lambda port: port.pid != None, ports)
  return list(map(lambda item: item.device, sorted(ports)))

class Main(QMainWindow):
  def __init__(self, ctx):
    super().__init__()

    self.ctx = ctx
    self.resize(800, 500)

    self.cb = self.createComboBox()

    self.output = QTextEdit()
    self.output.setReadOnly(True)

    mainWidget = QWidget()

    button1 = QPushButton("Επιλογή Αρχείου")
    button1.clicked.connect(self.openFile)

    self.btn_upload = QPushButton("Μεταφόρτωση")
    self.btn_upload.clicked.connect(self.extractZip)
    self.btn_upload.setFixedHeight(60)

    self.selectedDir = QLabel("-")

    layout = QVBoxLayout()
    layout.addWidget(self.cb)
    layout.addWidget(self.selectedDir)
    layout.addWidget(button1)
    layout.addWidget(self.output)
    layout.addWidget(self.btn_upload)

    self.dlg = QFileDialog()
    self.dlg.setFileMode(QFileDialog.ExistingFiles)
    self.dlg.setNameFilter("esbin (*.esbin)")

    self.process = QProcess(self)
    self.process.readyRead.connect(self.dataReady)
    self.process.finished.connect(self.onprocFinished)

    mainWidget.setLayout(layout)

    self.setCentralWidget(mainWidget)

  def onprocFinished(self):
    self.btn_upload.setEnabled(True)
    self.output.append('\n ** ΤΕΛΟΣ **')

  def openFile(self):
    if self.dlg.exec_():
      self.selectedDir.setText(self.dlg.selectedFiles()[0])

  def dataReady(self):
    cursor = self.output.textCursor()
    cursor.movePosition(cursor.End)
    cursor.insertText(str(self.process.readAll().data().decode('utf-8', 'ignore')))
    self.output.ensureCursorVisible()

  def get_sketch_bin_paths(self, tmp_dir):
    path_InoBin = None
    path_InoPartitionsBin = None

    for file in os.listdir(tmp_dir):
      if file.endswith('.ino.bin'):
        path_InoBin = os.path.join(tmp_dir, file)
      elif file.endswith('.ino.partitions.bin'):
        path_InoPartitionsBin = os.path.join(tmp_dir, file)

    if path_InoBin is None or path_InoPartitionsBin is None:
      return None
    else:
      return (path_InoBin, path_InoPartitionsBin)

  def extractZip(self):
    self.btn_upload.setEnabled(False)
    self.output.clear()

    filepath = self.selectedDir.text()
    self.tmp_dir = tempfile.TemporaryDirectory()

    # extract files
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
      zip_ref.extractall(self.tmp_dir.name)

    # get tools paths
    path_EspTool = self.ctx.get_resource('esptool.exe')
    path_BootApp0 = self.ctx.get_resource('boot_app0.bin')
    path_BootloaderQio80m = self.ctx.get_resource('bootloader_qio_80m.bin')

    result = self.get_sketch_bin_paths(self.tmp_dir.name)

    if not result is None:
      path_InoBin, path_InoPartitionsBin = result

      self.process.start(path_EspTool, [
        '--chip', 'esp32',
        '--port', self.cb.currentText(),
        '--baud', '921600',
        '--before', 'default_reset',
        '--after', 'hard_reset', 'write_flash',
        '-z',
        '--flash_mode', 'dio',
        '--flash_freq', '80m',
        '--flash_size', 'detect',
        '0xe000', path_BootApp0,
        '0x1000', path_BootloaderQio80m,
        '0x10000', path_InoBin,
        '0x8000', path_InoPartitionsBin,
      ])

    # self.tmp_dir.cleanup()

  def createComboBox(self):
    cb = QComboBox()

    # ports = serial.tools.list_ports.comports()
    portNames = get_usb_ports()
    cb.addItems(portNames)

    return cb


if __name__ == '__main__':
    appctxt = ApplicationContext()

    window = Main(appctxt)
    window.show()

    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
