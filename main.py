import json
import os
import sys
import time

import keyboard
import mouse
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from translations import translations

CONFIG_DIR_NAME = "AutoClicker"
CONFIG_FILE_NAME = "config.json"
DEFAULT_HOTKEY = "W+S"


def get_config_path():
    base_dir = os.getenv("APPDATA") or os.getenv("XDG_CONFIG_HOME") or os.path.expanduser("~")
    config_dir = os.path.join(base_dir, CONFIG_DIR_NAME)
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, CONFIG_FILE_NAME)

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
        self.theme = 'dark'
        self.hotkey_id = None
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

        theme_layout = QHBoxLayout()
        self.theme_label = QLabel("Theme:")
        theme_layout.addWidget(self.theme_label)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)

        hotkey_layout = QHBoxLayout()
        self.hotkey_label = QLabel("Hotkey:")
        hotkey_layout.addWidget(self.hotkey_label)
        self.hotkey_input = QLineEdit(DEFAULT_HOTKEY)  # default hotkey
        hotkey_layout.addWidget(self.hotkey_input)
        self.set_hotkey_button = QPushButton("Set")
        self.set_hotkey_button.clicked.connect(self.set_hotkey)
        hotkey_layout.addWidget(self.set_hotkey_button)
        layout.addLayout(hotkey_layout)

        delay_layout = QHBoxLayout()
        self.delay_label = QLabel("Delay (sec):")
        delay_layout.addWidget(self.delay_label)
        self.delay_input = QLineEdit("0.01")
        delay_validator = QDoubleValidator(0.001, 3600.0, 3, self)
        delay_validator.setNotation(QDoubleValidator.StandardNotation)
        self.delay_input.setValidator(delay_validator)
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
        self.click_count_input.setValidator(QIntValidator(1, 1000000000, self))
        self.click_count_input.setPlaceholderText("Enter click count")
        self.duration_input = QLineEdit()
        self.duration_input.setValidator(QDoubleValidator(0.1, 3600.0, 2, self))
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
        self.apply_theme()
        self.retranslateUi()
        self.show()

    def tr(self, text):
        return translations[self.lang][text]

    def apply_theme(self):
        if self.theme == 'light':
            stylesheet = """
                QWidget {
                    background-color: #ECEFF4;
                    color: #2E3440;
                    font-family: Arial;
                    font-size: 14px;
                }
                QLineEdit, QPushButton, QComboBox {
                    background-color: #FFFFFF;
                    border: 1px solid #4C566A;
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #D8DEE9;
                }
                QPushButton:pressed {
                    background-color: #B0BEC5;
                }
                QLabel {
                    font-weight: bold;
                }
            """
        else:
            stylesheet = """
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
            """
        self.setStyleSheet(stylesheet)

    def set_hotkey(self):
        hotkey = self.hotkey_input.text().strip()
        if hotkey:
            try:
                if self.hotkey_id is not None:
                    keyboard.remove_hotkey(self.hotkey_id)
                self.hotkey_id = keyboard.add_hotkey(hotkey, self.toggle_clicker)
                self.set_hotkey_button.setText(f"{self.tr('set')}: {hotkey}")
                self.save_config()
            except ValueError as e:
                QMessageBox.warning(self, self.tr('invalid_hotkey'), str(e))
        else:
            QMessageBox.warning(self, self.tr('invalid_hotkey'), self.tr('enter_valid_hotkey'))

    def update_delay(self):
        value = self.delay_input.text().strip()
        try:
            delay = float(value)
        except ValueError:
            QMessageBox.warning(self, self.tr('invalid_delay'), self.tr('enter_valid_delay'))
            return
        if delay <= 0:
            QMessageBox.warning(self, self.tr('invalid_delay'), self.tr('enter_valid_delay'))
            return
        self.clicker_thread.delay = delay
        self.set_delay_button.setText(self.tr('set'))
        self.save_config()

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
        self.save_config()

    def on_clicking_finished(self):
        self.status_label.setText(self.tr('status_disabled'))
        self.toggle_button.setText(self.tr('start'))

    def save_config(self):
        config_file = get_config_path()
        config = {
            'hotkey': self.hotkey_input.text(),
            'lang': self.lang,
            'theme': self.theme,
            'delay': self.delay_input.text(),
            'mouse_button': self.mouse_button_combo.currentText(),
            'click_mode': self.get_click_mode(),
            'click_count': self.click_count_input.text(),
            'duration': self.duration_input.text(),
        }
        with open(config_file, 'w') as f:
            json.dump(config, f)

    def load_config(self):
        config_file = get_config_path()
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            self.hotkey_input.setText(config.get('hotkey', DEFAULT_HOTKEY))
            self.lang = config.get('lang', 'en')
            self.theme = config.get('theme', 'dark')
            self.delay_input.setText(config.get('delay', '0.01'))
            self.mouse_button_combo.setCurrentText(config.get('mouse_button', 'left'))
            self.click_count_input.setText(config.get('click_count', ''))
            self.duration_input.setText(config.get('duration', ''))
            click_mode = config.get('click_mode', 'infinite')
            self.set_click_mode(click_mode)
            self.lang_combo.setCurrentIndex(0 if self.lang == 'en' else 1)
            self.theme_combo.setCurrentIndex(0 if self.theme == 'dark' else 1)
        self.apply_theme()
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
        self.theme_label.setText(self.tr('theme'))
        self.theme_combo.setItemText(0, self.tr('dark'))
        self.theme_combo.setItemText(1, self.tr('light'))

    def change_language(self, index):
        self.lang = 'en' if index == 0 else 'ru'
        self.retranslateUi()
        self.save_config()

    def change_theme(self, index):
        self.theme = 'dark' if index == 0 else 'light'
        self.apply_theme()
        self.save_config()

    def get_click_mode(self):
        if self.infinite_radio.isChecked():
            return 'infinite'
        if self.count_radio.isChecked():
            return 'count'
        if self.duration_radio.isChecked():
            return 'duration'
        return 'infinite'

    def set_click_mode(self, mode):
        if mode == 'count':
            self.count_radio.setChecked(True)
        elif mode == 'duration':
            self.duration_radio.setChecked(True)
        else:
            self.infinite_radio.setChecked(True)

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    ex = AutoClicker()
    sys.exit(app.exec_())
