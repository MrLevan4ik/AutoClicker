import sys
import os
import json
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QRadioButton, QButtonGroup
from PyQt5.QtCore import QThread, pyqtSignal
import keyboard
import mouse
import time
from translations import translations

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
        self.lang = 'en'  # default language
        self.initUI()
        self.clicker_thread = ClickerThread()
        self.clicker_thread.finished.connect(self.on_clicking_finished)
        self.load_config()

    def initUI(self):
        layout = QVBoxLayout()

        # language selection
        lang_layout = QHBoxLayout()
        self.lang_label = QLabel("Language:")
        lang_layout.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['English', 'Русский'])
        self.lang_combo.currentIndexChanged.connect(self.change_language)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        hotkey_layout = QHBoxLayout()
        self.hotkey_label = QLabel("Hotkey:")
        hotkey_layout.addWidget(self.hotkey_label)
        self.hotkey_input = QLineEdit("W+S")  # default hotkey
        hotkey_layout.addWidget(self.hotkey_input)
        self.set_hotkey_button = QPushButton("Set")
        self.set_hotkey_button.clicked.connect(self.set_hotkey)
        hotkey_layout.addWidget(self.set_hotkey_button)
        layout.addLayout(hotkey_layout)

        delay_layout = QHBoxLayout()
        self.delay_label = QLabel("Delay (sec):")
        delay_layout.addWidget(self.delay_label)
        self.delay_input = QLineEdit("0.01")
        delay_layout.addWidget(self.delay_input)
        self.set_delay_button = QPushButton("Set")
        self.set_delay_button.clicked.connect(self.update_delay)
        delay_layout.addWidget(self.set_delay_button)
        layout.addLayout(delay_layout)

        mouse_button_layout = QHBoxLayout()
        self.mouse_button_label = QLabel("Mouse Button:")
        mouse_button_layout.addWidget(self.mouse_button_label)
        self.mouse_button_combo = QComboBox()
        self.mouse_button_combo.addItems(['left', 'right', 'middle'])
        mouse_button_layout.addWidget(self.mouse_button_combo)
        layout.addLayout(mouse_button_layout)

        click_mode_layout = QVBoxLayout()
        self.click_mode_label = QLabel("Click Mode:")
        click_mode_layout.addWidget(self.click_mode_label)
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

        self.retranslateUi()
        self.show()

    def tr(self, text):
        return translations[self.lang][text]

    def set_hotkey(self):
        hotkey = self.hotkey_input.text().strip()
        if hotkey:
            try:
                keyboard.add_hotkey(hotkey, self.toggle_clicker)
                self.set_hotkey_button.setText(f"{self.tr('set')}: {hotkey}")
                self.save_config()
            except ValueError as e:
                QMessageBox.warning(self, self.tr('invalid_hotkey'), str(e))
        else:
            QMessageBox.warning(self, self.tr('invalid_hotkey'), self.tr('enter_valid_hotkey'))

    def update_delay(self):
        try:
            self.clicker_thread.delay = float(self.delay_input.text())
            self.set_delay_button.setText(self.tr('set'))
        except ValueError:
            QMessageBox.warning(self, self.tr('invalid_delay'), self.tr('enter_valid_delay'))

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
                    QMessageBox.warning(self, self.tr('invalid_click_count'), self.tr('enter_valid_click_count'))
                    return
            elif self.duration_radio.isChecked():
                try:
                    self.clicker_thread.duration = float(self.duration_input.text())
                    self.clicker_thread.click_mode = 'duration'
                except ValueError:
                    QMessageBox.warning(self, self.tr('invalid_duration'), self.tr('enter_valid_duration'))
                    return
            self.clicker_thread.clicking = True
            self.clicker_thread.start()
            self.status_label.setText(self.tr('status_enabled'))
            self.toggle_button.setText(self.tr('stop'))
        else:
            self.clicker_thread.clicking = False
            self.status_label.setText(self.tr('status_disabled'))
            self.toggle_button.setText(self.tr('start'))

    def on_clicking_finished(self):
        self.status_label.setText(self.tr('status_disabled'))
        self.toggle_button.setText(self.tr('start'))

    def save_config(self):
        temp_dir = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'AutoClicker')
        os.makedirs(temp_dir, exist_ok=True)
        config_file = os.path.join(temp_dir, 'config.json')
        with open(config_file, 'w') as f:
            json.dump({'hotkey': self.hotkey_input.text(), 'lang': self.lang}, f)

    def load_config(self):
        temp_dir = os.path.join(os.environ.get('TEMP', os.path.expanduser('~')), 'AutoClicker')
        config_file = os.path.join(temp_dir, 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                self.hotkey_input.setText(config.get('hotkey', 'W+S'))
                self.lang = config.get('lang', 'en')
                self.lang_combo.setCurrentIndex(0 if self.lang == 'en' else 1)
        self.set_hotkey()
        self.retranslateUi()

    def retranslateUi(self):
        self.setWindowTitle(self.tr("AutoClicker"))
        self.hotkey_label.setText(self.tr('hotkey'))
        self.set_hotkey_button.setText(self.tr('set'))
        self.delay_label.setText(self.tr('delay'))
        self.set_delay_button.setText(self.tr('set'))
        self.mouse_button_label.setText(self.tr('mouse_button'))
        self.click_mode_label.setText(self.tr('click_mode'))
        self.infinite_radio.setText(self.tr('infinite'))
        self.count_radio.setText(self.tr('click_count'))
        self.duration_radio.setText(self.tr('duration'))
        self.click_count_input.setPlaceholderText(self.tr('enter_click_count'))
        self.duration_input.setPlaceholderText(self.tr('enter_duration'))
        self.status_label.setText(self.tr('status_disabled'))
        self.toggle_button.setText(self.tr('start'))
        self.lang_label.setText(self.tr('language'))

    def change_language(self, index):
        self.lang = 'en' if index == 0 else 'ru'
        self.retranslateUi()
        self.save_config()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutoClicker()
    sys.exit(app.exec_())
