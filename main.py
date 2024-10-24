import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QRadioButton, QButtonGroup
from PyQt5.QtCore import QThread, pyqtSignal
import keyboard
import mouse
import time

class ClickerThread(QThread):
    finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.clicking = False
        self.delay = 0.01
        self.button = 'left'
        self.click_count = 0
        self.duration = 0
        self.click_mode = 'infinite'

    def run(self):
        start_time = time.time()
        clicks_performed = 0
        while self.clicking:
            if self.click_mode == 'count' and clicks_performed >= self.click_count:
                break
            if self.click_mode == 'duration' and time.time() - start_time >= self.duration:
                break
            mouse.click(button=self.button)
            clicks_performed += 1
            time.sleep(self.delay)
        self.clicking = False
        self.finished.emit()

class AutoClicker(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.clicker_thread = ClickerThread()
        self.clicker_thread.finished.connect(self.on_clicking_finished)
        self.load_hotkey()

    def initUI(self):
        layout = QVBoxLayout()

        hotkey_layout = QHBoxLayout()
        hotkey_layout.addWidget(QLabel("Hotkey:"))
        self.hotkey_input = QLineEdit("W+S")  # default hotkey
        hotkey_layout.addWidget(self.hotkey_input)
        self.set_hotkey_button = QPushButton("Set")
        self.set_hotkey_button.clicked.connect(self.set_hotkey)
        hotkey_layout.addWidget(self.set_hotkey_button)
        layout.addLayout(hotkey_layout)

        delay_layout = QHBoxLayout()
        delay_layout.addWidget(QLabel("Delay (sec):"))
        self.delay_input = QLineEdit("0.01")
        delay_layout.addWidget(self.delay_input)
        self.set_delay_button = QPushButton("Set")
        self.set_delay_button.clicked.connect(self.update_delay)
        delay_layout.addWidget(self.set_delay_button)
        layout.addLayout(delay_layout)

        mouse_button_layout = QHBoxLayout()
        mouse_button_layout.addWidget(QLabel("Mouse Button:"))
        self.mouse_button_combo = QComboBox()
        self.mouse_button_combo.addItems(['left', 'right', 'middle'])
        mouse_button_layout.addWidget(self.mouse_button_combo)
        layout.addLayout(mouse_button_layout)

        click_mode_layout = QVBoxLayout()
        click_mode_layout.addWidget(QLabel("Click Mode:"))
        self.click_mode_group = QButtonGroup()
        self.infinite_radio = QRadioButton("Infinite")
        self.count_radio = QRadioButton("Click Count")
        self.duration_radio = QRadioButton("Duration (sec)")
        self.click_mode_group.addButton(self.infinite_radio)
        self.click_mode_group.addButton(self.count_radio)
        self.click_mode_group.addButton(self.duration_radio)
        click_mode_layout.addWidget(self.infinite_radio)
        click_mode_layout.addWidget(self.count_radio)
        click_mode_layout.addWidget(self.duration_radio)
        self.click_count_input = QLineEdit()
        self.click_count_input.setPlaceholderText("Enter click count")
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("Enter duration in seconds")
        click_mode_layout.addWidget(self.click_count_input)
        click_mode_layout.addWidget(self.duration_input)
        layout.addLayout(click_mode_layout)

        self.status_label = QLabel("Status: Disabled")
        layout.addWidget(self.status_label)

        self.toggle_button = QPushButton("Start/Stop")
        self.toggle_button.clicked.connect(self.toggle_clicker)
        layout.addWidget(self.toggle_button)

        self.setLayout(layout)
        self.setWindowTitle("AutoClicker")

        # Apply styles
        self.setStyleSheet("""
            QWidget {
                background-color: #2E3440;
                color: #D8DEE9;
                font-family: Arial;
                font-size: 14px;
            }
            QLineEdit, QPushButton, QComboBox {
                background-color: #4C566A;
                border: 1px solid #D8DEE9;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #5E81AC;
            }
            QPushButton:pressed {
                background-color: #88C0D0;
            }
            QLabel {
                font-weight: bold;
            }
        """)

        self.show()

    def set_hotkey(self):
        hotkey = self.hotkey_input.text().strip()
        if hotkey:
            try:
                keyboard.add_hotkey(hotkey, self.toggle_clicker)
                self.set_hotkey_button.setText(f"Set: {hotkey}")
                self.save_hotkey(hotkey)
            except ValueError as e:
                QMessageBox.warning(self, "Invalid Hotkey", str(e))
        else:
            QMessageBox.warning(self, "Invalid Hotkey", "Please enter a valid hotkey.")

    def update_delay(self):
        try:
            self.clicker_thread.delay = float(self.delay_input.text())
            self.set_delay_button.setText("Set")
        except ValueError:
            QMessageBox.warning(self, "Invalid Delay", "Please enter a valid number for delay.")

    def toggle_clicker(self):
        if not self.clicker_thread.clicking:
            self.clicker_thread.button = self.mouse_button_combo.currentText()
            if self.infinite_radio.isChecked():
                self.clicker_thread.click_mode = 'infinite'
            elif self.count_radio.isChecked():
                try:
                    self.clicker_thread.click_count = int(self.click_count_input.text())
                    self.clicker_thread.click_mode = 'count'
                except ValueError:
                    QMessageBox.warning(self, "Invalid Click Count", "Please enter a valid number for click count.")
                    return
            elif self.duration_radio.isChecked():
                try:
                    self.clicker_thread.duration = float(self.duration_input.text())
                    self.clicker_thread.click_mode = 'duration'
                except ValueError:
                    QMessageBox.warning(self, "Invalid Duration", "Please enter a valid number for duration.")
                    return
            self.clicker_thread.clicking = True
            self.clicker_thread.start()
            self.status_label.setText("Status: Enabled")
            self.toggle_button.setText("Stop")
        else:
            self.clicker_thread.clicking = False
            self.status_label.setText("Status: Disabled")
            self.toggle_button.setText("Start")

    def on_clicking_finished(self):
        self.status_label.setText("Status: Disabled")
        self.toggle_button.setText("Start")

    def save_hotkey(self, hotkey):
        temp_dir = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'AutoClicker')
        os.makedirs(temp_dir, exist_ok=True)
        config_file = os.path.join(temp_dir, 'config.json')
        with open(config_file, 'w') as f:
            json.dump({'hotkey': hotkey}, f)

    def load_hotkey(self):
        temp_dir = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'AutoClicker')
        config_file = os.path.join(temp_dir, 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                hotkey = config.get('hotkey')
                if hotkey:
                    self.hotkey_input.setText(hotkey)
        self.set_hotkey()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutoClicker()
    sys.exit(app.exec_())
