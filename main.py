import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QThread
import keyboard
import mouse
import time

class ClickerThread(QThread):
    def __init__(self):
        super().__init__()
        self.clicking = False
        self.delay = 0.01

    def run(self):
        while True:
            if self.clicking:
                mouse.click(button='left')
                time.sleep(self.delay)
            else:
                time.sleep(0.1)

class AutoClicker(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.clicker_thread = ClickerThread()
        self.clicker_thread.start()
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
            QLineEdit, QPushButton {
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
        self.clicker_thread.clicking = not self.clicker_thread.clicking
        status = "Enabled" if self.clicker_thread.clicking else "Disabled"
        self.status_label.setText(f"Status: {status}")

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
