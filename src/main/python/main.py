from fbs_runtime.application_context.PySide2 import ApplicationContext
from PySide2.QtWidgets import QMessageBox, QTextEdit, QMainWindow, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QComboBox, QFileDialog, QLabel
from PySide2.QtCore import QProcess
from PySide2.QtGui import QFontDatabase
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

    self.setWindowTitle('ESP32 Flasher - By @kapraran')

    self.running = False
    row_btn_width = 160

    self.ctx = ctx
    self.resize(800, 500)

    self.cb = self.createComboBox()

    fixedFont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    self.output = QTextEdit()
    self.output.setReadOnly(True)
    self.output.setFont(fixedFont)
    self.output.setStyleSheet("QTextEdit { background-color : #000; color: orange; }")

    mainWidget = QWidget()

    button1 = QPushButton("Επιλογή Αρχείου")
    button1.setFixedWidth(row_btn_width)
    button1.clicked.connect(self.openFile)

    self.btn_upload = QPushButton("Μεταφόρτωση")
    self.btn_upload.clicked.connect(self.extractZip)
    self.btn_upload.setFixedHeight(60)

    self.selectedDir = QLabel("-")
    self.selectedDir.setStyleSheet("QLabel { background-color : #cccccc; padding: 0 4px; }")

    self.btn_refresh = QPushButton("Ανανέωση")
    self.btn_refresh.setFixedWidth(row_btn_width)
    self.btn_refresh.clicked.connect(self.refresh_comports)

    row1 = QWidget()

    row1_layout = QHBoxLayout()
    row1_layout.setMargin(0)
    row1_layout.addWidget(self.cb)
    row1_layout.addWidget(self.btn_refresh)

    row1.setLayout(row1_layout)

    row2 = QWidget()
    row2_layout = QHBoxLayout()
    row2_layout.setMargin(0)
    row2_layout.addWidget(self.selectedDir)
    row2_layout.addWidget(button1)
    row2.setLayout(row2_layout)

    layout = QVBoxLayout()
    # layout.addWidget(self.cb)
    layout.addWidget(row1)
    # layout.addWidget(self.selectedDir)
    # layout.addWidget(button1)
    layout.addWidget(row2)
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

  def alert(self, message):
    QMessageBox.critical(self, 'Σφάλμα', message)

  def refresh_comports(self):
    if self.running:
      return

    self.btn_refresh.setEnabled(False)
    self.cb.clear()
    self.cb.addItems(get_usb_ports())
    self.btn_refresh.setEnabled(True)

  def onprocFinished(self):
    self.output.append('\n ** ΤΕΛΟΣ **')

    # move scrollbar to the bottom
    maximum = self.output.verticalScrollBar().maximum()
    self.output.verticalScrollBar().setValue(maximum)

    self.running = False
    self.btn_upload.setEnabled(True)

  def openFile(self):
    if self.running:
      return

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
    self.running = True
    self.btn_upload.setEnabled(False)
    self.output.clear()

    comport = self.cb.currentText()
    filepath = self.selectedDir.text()

    if comport.strip() == '':
      self.alert('Δεν επιλέχθηκε port')
      self.endRunning()
      return

    if filepath.strip() == '-':
      self.alert('Δεν επιλέχθηκε κάποιο αρχείο')
      self.endRunning()
      return

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
        '--port', comport,
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

  def endRunning(self):
    self.running = False
    self.btn_upload.setEnabled(True)


if __name__ == '__main__':
    appctxt = ApplicationContext()

    window = Main(appctxt)
    window.show()

    exit_code = appctxt.app.exec_()
    sys.exit(exit_code)
