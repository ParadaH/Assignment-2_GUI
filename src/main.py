import sys
import time

import serial.tools.list_ports
import serial
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QGroupBox, QHBoxLayout, QPushButton, \
    QVBoxLayout, QProgressBar, QMessageBox, QLabel, QTextEdit
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
            time.sleep(2) # Small delay for the system
            self.running = True

            # Set LED status to connected
            self.update_led_icon("green")

            while self.running:
                if self.arduino.in_waiting > 0:
                    data = self.arduino.readline().decode('utf-8').strip()
                    self.message_received.emit(data)
        except serial.SerialException as e:
            print(f"Error decoding data: {e}")

    def send_data(self, data):
        if self.arduino and self.arduino.is_open:
            self.arduino.write(data.encode())
            self.message_sent.emit(data)

    def stop(self):
        self.running = False
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
        self.quit()
        self.wait()

    def update_led_icon(self, param):
        pass


def get_state_name(value):
    container_state = {
        101: "EMPTY",
        102: "FULL",
        103: "OPEN",
        104: "CLOSE",
        105: "ALARM",
        106: "SLEEP",
        107: "IDLE"
    }
    return container_state.get(value, "UNKNOWN")


class SmartWasteDisposalWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.restore_button = None
        self.empty_container_button = None
        self.state_text_label = None
        self.log_monitor = None
        self.led_icon_label = None
        self.port = None
        self.central_widget = None
        self.smart_container_progress_bar = None
        self.led_icon = None

        self.init_gui()
        self.arduino_thread = None

    def init_gui(self):
        self.setWindowTitle("Operator dashboard - Smart Waste Disposal")
        self.setWindowIcon(QIcon("img/bin.png"))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.log_monitor = QTextEdit()
        self.smart_container_progress_bar = QProgressBar()

        # Setting layout
        main_layout = QGridLayout()
        self.central_widget.setLayout(main_layout)

        # Creating groupbox of each element
        instruction_groupbox = self.create_instruction_groupbox
        buttons_groupbox = self.create_button_groupbox()
        led_icon_groupbox = self.create_led_icon_groupbox()
        smart_container_groupbox = self.create_progressbar_groupbox()
        state_text_groupbox = self.create_state_text_groupbox()
        text_edit_groupbox = self.create_text_edit_groupbox()

        # Add groupbox widgets to main layout
        main_layout.addWidget(instruction_groupbox, 0, 0, 2, 2)
        main_layout.addWidget(buttons_groupbox, 2, 0, 1, 1)
        main_layout.addWidget(led_icon_groupbox, 2, 1, 1, 1)
        main_layout.addWidget(smart_container_groupbox, 3, 0, 1, 1)
        main_layout.addWidget(state_text_groupbox, 3, 1, 1, 1)
        main_layout.addWidget(text_edit_groupbox, 0, 2, 3, 2)

    @property
    def create_instruction_groupbox(self):
        instruction_groupbox = QGroupBox("How to use?")
        instruction_layout = QVBoxLayout()
        instruction_groupbox.setLayout(instruction_layout)

        instruction_label = QLabel()
        instruction_label.setText(
            '1. Click "Start connection" to connect with Smart Waste Disposal.\n'
            '2. Press "Empty container" to empty container.\n'
            '3. Press "Restore" to disable alarm.\n'
            '4. Press "Save" to save event log monitor to file.\n'
            '5. Monitor the storage fill level on the progress bar.\n'
            '6. LED changes color according to status:\n'
            '       - Green: Connection success.\n'
            '       - Red: Connection error or full storage.\n'
            '       - Yellow: Alarm!\n'
            '       - White: Initial state of the app.'
        )
        instruction_label.setWordWrap(True)
        instruction_layout.addWidget(instruction_label)

        return instruction_groupbox

    def create_button_groupbox(self):
        buttons_groupbox = QGroupBox("Operator Buttons")
        buttons_layout = QHBoxLayout()
        buttons_groupbox.setLayout(buttons_layout)

        start_connection_button = QPushButton("Start connection", self)
        start_connection_button.clicked.connect(self.start_arduino_communication)

        self.empty_container_button = QPushButton("Empty container", self)
        self.empty_container_button.setEnabled(False)
        self.empty_container_button.clicked.connect(self.send_empty_command)

        self.restore_button = QPushButton("Restore", self)
        self.restore_button.setEnabled(False)
        self.restore_button.clicked.connect(self.send_restore_command)

        buttons_layout.addWidget(start_connection_button)
        buttons_layout.addWidget(self.empty_container_button)
        buttons_layout.addWidget(self.restore_button)

        return buttons_groupbox

    def create_progressbar_groupbox(self):
        smart_container_groupbox = QGroupBox("Storage")
        smart_container_layout = QVBoxLayout()
        smart_container_groupbox.setLayout(smart_container_layout)

        self.smart_container_progress_bar.setOrientation(1)
        self.smart_container_progress_bar.setMinimum(0)
        self.smart_container_progress_bar.setMaximum(100)

        smart_container_layout.addWidget(self.smart_container_progress_bar)

        return smart_container_groupbox

    def update_progress_bar(self, value):
        if value >= 99:
            self.update_led_icon("red")
            self.smart_container_progress_bar.setValue(100)
        else:
            self.update_led_icon("green")
            self.smart_container_progress_bar.setValue(value)

    def create_led_icon_groupbox(self):
        led_icon_groupbox = QGroupBox("Status")
        led_icon_layout = QHBoxLayout()
        led_icon_groupbox.setLayout(led_icon_layout)

        self.led_icon_label = QLabel()
        self.led_icon = QPixmap('img/white_led.png')
        self.led_icon_label.setPixmap(self.led_icon)

        led_icon_layout.addWidget(self.led_icon_label)

        return led_icon_groupbox

    def update_led_icon(self, color):
        if color == "green":
            self.led_icon = QPixmap('img/green_led.png')
        elif color == "red":
            self.led_icon = QPixmap('img/red_led.png')
        elif color == "white":
            self.led_icon = QPixmap('img/white_led.png')
        elif color == "yellow":
            self.led_icon = QPixmap('img/yellow_led.png')

        self.led_icon_label.setPixmap(self.led_icon)

    def create_state_text_groupbox(self):
        state_text_groupbox = QGroupBox("State")
        state_text_layout = QHBoxLayout()
        state_text_groupbox.setLayout(state_text_layout)

        self.state_text_label = QLabel()
        self.state_text_label.setText("Not available")
        self.state_text_label.setWordWrap(True)
        state_text_layout.addWidget(self.state_text_label)

        return state_text_groupbox

    def create_text_edit_groupbox(self):
        text_edit_groupbox = QGroupBox("Event log monitor")
        text_edit_layout = QHBoxLayout()
        text_edit_groupbox.setLayout(text_edit_layout)

        text_edit_layout.addWidget(self.log_monitor)

        return text_edit_groupbox

    def update_text_edit(self, state):
        self.state_text_label.setText(state)

    def closeEvent(self, event):
        if self.arduino_thread is not None:
            self.arduino_thread.stop()
        event.accept()

    def start_arduino_communication(self):
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            if "Arduino" in port.description:
                self.port = port.device
                break
        else:
            # Set LED status to error
            self.update_led_icon("yellow")
            QMessageBox.warning(self, "Error", "Arduino not found")
            return

        try:
            self.arduino_thread = ArduinoThread(self.port)
            self.arduino_thread.message_received.connect(self.read_data)
            self.arduino_thread.start()

            self.empty_container_button.setEnabled(True)
            self.restore_button.setEnabled(True)

        except serial.SerialException as e:
            # Set LED status to error
            self.update_led_icon("yellow")
            print(f"Error: {e}")

    def read_data(self, message):
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            value = int(message)
            if 0 <= value <= 97:
                self.update_led_icon("green")
                self.update_progress_bar(value)
                self.log_monitor.append(f"Storage level: {message}")
            elif 97 < value <= 100:
                self.update_led_icon("red")
                self.update_progress_bar(value)
                self.log_monitor.append(f"Storage level: {message}")

            elif 101 <= value <= 107:
                state = get_state_name(value)
                self.update_text_edit(state)
                self.log_monitor.append(f"State: {state}")
                if value == 105:
                    self.update_led_icon("yellow")
                    QMessageBox.warning(self, "Alarm", "Alarm: check the waste container!")
            else:
                print(f"Invalid data received: {value}")

        except ValueError:
            print(f"Error: {message}")

    def send_empty_command(self):
        self.arduino_thread.send_data("101")
        self.update_led_icon("green")

    def send_restore_command(self):
        self.arduino_thread.send_data("107")
        self.update_led_icon("green")
        self.update_progress_bar(0)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SmartWasteDisposalWindow()
    window.show()
    sys.exit(app.exec_())
