import sys
import time

import serial.tools.list_ports
import serial
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QGroupBox, QHBoxLayout, QPushButton, \
    QVBoxLayout, QProgressBar, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal


class ArduinoThread(QThread):
    message_received = pyqtSignal(str)
    message_sent = pyqtSignal(str)

    def __init__(self, port, baudrate=9600):
        super().__init__()
        self.arduino = None
        self.port = port
        self.baudrate = baudrate
        self.running = False

    def run(self):
        try:
            self.arduino = serial.Serial(self.port, self.baudrate, timeout=1)
            time.sleep(3)
            self.running = True

            while self.running:
                pass
        except serial.SerialException as e:
            print(e)

    def send_data(self, data):
        self.arduino.write(data.encode())

    def stop(self):
        self.running = False

class SmartWasteDisposalWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.port = None
        self.central_widget = None
        self.smart_container_progress_bar = None

        self.init_gui()
        self.arduino_thread = None

    def init_gui(self):
        self.setWindowTitle("Smart Waste Disposal")
        self.setGeometry(300, 150, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.smart_container_progress_bar = QProgressBar()

        # Setting layout
        main_layout = QGridLayout()
        self.central_widget.setLayout(main_layout)

        # Creating buttons and progress bar
        buttons_groupbox = self.create_button_groupbox()
        smart_container_groupbox = self.create_progressbar_groupbox()

        main_layout.addWidget(buttons_groupbox, 0, 0, 1, 1)
        main_layout.addWidget(smart_container_groupbox, 1, 0, 1, 1)

    def create_button_groupbox(self):
        buttons_groupbox = QGroupBox("Operator Buttons")
        buttons_layout = QHBoxLayout()
        buttons_groupbox.setLayout(buttons_layout)

        start_connection_button = QPushButton("Start connection", self)
        start_connection_button.clicked.connect(self.start_arduino_communication)

        empty_container_button = QPushButton("Empty container", self)
        empty_container_button.clicked.connect(self.send_empty_command)

        restore_button = QPushButton("Restore", self)
        # restore_button.clicked.connect()

        buttons_layout.addWidget(start_connection_button)
        buttons_layout.addWidget(empty_container_button)
        buttons_layout.addWidget(restore_button)

        return buttons_groupbox

    def create_progressbar_groupbox(self):
        smart_container_groupbox = QGroupBox("Smart Container Storage")
        smart_container_layout = QVBoxLayout()
        smart_container_groupbox.setLayout(smart_container_layout)

        self.smart_container_progress_bar.setOrientation(1)
        self.smart_container_progress_bar.setMinimum(0)
        self.smart_container_progress_bar.setMaximum(100)
        self.smart_container_progress_bar.setValue(10) #just an example

        smart_container_layout.addWidget(self.smart_container_progress_bar)

        return smart_container_groupbox

    def send_restore_command(self):
        if self.serial_port:
            try:
                self.serial_port.write(b'123')
                data = self.serial_port.readline()
                print(f"{data}")

            except serial.SerialException as e:
                    print("Error:", e)
            else:
                print("No connection with serial port.")

    def closeEvent(self, event):
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        event.accept()

    def start_arduino_communication(self):
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "Arduino" in port.description:
                self.port = port.device
                break
            else:
                QMessageBox.warning(self, "Error", "Arduino not found")
                return
        try:
            self.arduino_thread = ArduinoThread(self.port)
            self.arduino_thread.start()
        except serial.SerialException as e:
            print(f"Error: {e}")

    def send_empty_command(self):
        self.arduino_thread.send_data("0")


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = SmartWasteDisposalWindow()
    window.show()
    sys.exit(app.exec_())