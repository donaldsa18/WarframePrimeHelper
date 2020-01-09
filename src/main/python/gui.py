from PyQt5.QtWidgets import QTableWidget, QWidget, QVBoxLayout, QLabel, QAbstractItemView, QHBoxLayout, \
    QSlider, QGridLayout, QGroupBox, QCheckBox, QHeaderView, QPushButton, QProgressBar, QTableWidgetItem, QDialog, QDialogButtonBox
from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtCore import Qt, QThread, QTimer, QSettings
#from PyQt5 import QtSvg
import qdarkstyle
from functools import partial
from ocr import OCR
from api import APIReader
from market_api import MarketReader
import time
import threading
from threading import Lock
from datetime import datetime
from fbs_runtime.application_context.PyQt5 import ApplicationContext


class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__()

        self.icon_path = 'resources\\warframe.ico'
        self.app_title = 'Warframe Prime Helper'
        self.company_name = 'Warframe Tools'

        self.settings = QSettings(self.company_name, self.app_title)
        self.setWindowTitle(self.app_title)

        self.market_api = None

        self.image_label = None
        self.image_label2 = None

        self.warframe_height = 1080
        self.warframe_width = 1920

        self.table = None
        self.mission_table = None

        self.slider_names = None
        self.sliders = None
        self.slider_labels = None
        self.slider_default_values = None
        self.slider_orig_values = None
        self.slider_values = None
        self.is_slider_max_set = False

        #self.plat_check_box = QCheckBox("Prefer platinum")
        #self.plat_check_box.setChecked(True)

        self.update_prices_button = None
        self.update_ducats_button = None
        self.update_prices_progress = None
        self.update_ducats_progress = None
        self.last_updated_prices_value = None
        self.last_updated_ducats_value = None
        self.num_parts_value = None
        self.latest_item_value = None

        self.move_to_top_check_box = None
        self.pause_button = None
        self.is_paused = False

        self.hide_crop_check_box = None
        self.hide_filter_check_box = None
        self.hide_fissure_check_box = None

        self.relics = None
        self.hide_relics = {}
        self.hidden_relics = set()

        self.hide_missions = {}
        self.hidden_missions = set()
        self.hide_missions_box = None

        self.crop_img = None
        self.filter_img = None

        self.dialog = None
        self.layout = None

        self.filled_rows = 0
        self.max = -1
        self.max_row = -1

        self.ocr = None
        self.old_screenshot_shape = 0
        self.old_filtered_shape = 0

        self.missions = []

        self.num_primes = 100
        self.api = None

        self.prices_progress_lock = Lock()
        self.ducats_progress_lock = Lock()

        self.ducats_thread = None
        self.prices_thread = None

        self.timer = None

        self.init_image_labels()
        self.init_tables()
        self.init_sliders()
        self.init_dialog()
        self.set_layout()
        self.init_timer()

        self.show()

        #measured correct values
        self.setFixedSize(978, 617)

    def init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_mission_table_time)
        self.timer.start(1000)

    def init_image_labels(self):
        self.image_label = QLabel()
        image = QPixmap('temp\\crop_27.bmp')
        self.image_label.setPixmap(image)

        self.image_label2 = QLabel()
        self.image_label2.setPixmap(image)

    def set_layout(self):
        settings_button_box = self.make_settings_button_box()
        self.init_imgs()
        bot_box = self.make_bot_box()

        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.addSpacing(-12)
        self.layout.addLayout(settings_button_box)
        self.layout.addWidget(self.crop_img)
        self.layout.addWidget(self.filter_img)
        self.layout.addWidget(bot_box)
        self.setLayout(self.layout)

    def make_settings_button_box(self):
        settings_button = QPushButton()
        # Gear icon is from: https://iconscout.com/icon/gear-222
        style_sheet = """
        QPushButton {
            qproperty-icon: url(" ");
            qproperty-iconSize: 15px 15px;
            border-image: url("resources/Gear.svg");
            background-color: rgba(255, 255, 255, 0);
        }
        
        QPushButton:hover {
            border-image: url("resources/SelectedGear.svg");
        }"""
        settings_button.setStyleSheet(style_sheet)
        #settings_button.setStyleSheet("background-color: rgba(0, 0, 0, 255); font-size: 23px;")
        settings_button.clicked.connect(self.show_preferences)
        settings_button.setFixedWidth(30)
        settings_button.setFixedHeight(30)

        settings_button_hb = QHBoxLayout()
        settings_button_hb.setAlignment(Qt.AlignRight)
        settings_button_hb.addWidget(settings_button)
        settings_button_hb.addSpacing(-11)
        return settings_button_hb

    def make_bot_box(self):
        bot_layout = QHBoxLayout()
        bot_layout.addWidget(self.table)
        bot_layout.addWidget(self.mission_table)

        bot_box = QGroupBox()
        bot_box.setLayout(bot_layout)
        bot_box.setFixedHeight(287)
        return bot_box

    def init_dialog(self):
        crop_box = self.make_crop_box()
        filter_box = self.make_filter_box()
        other_box = self.make_other_box()

        settings_layout_1 = QVBoxLayout()
        settings_layout_1.addWidget(crop_box)
        settings_layout_1.addWidget(filter_box)
        settings_layout_1.addWidget(other_box)

        update_box = self.make_update_box()
        rate_box = self.make_rate_box()

        settings_layout_2 = QVBoxLayout()
        settings_layout_2.addWidget(update_box)
        settings_layout_2.addWidget(rate_box)

        hide_box = self.make_hide_box()
        hide_relics_box = self.make_hide_relics_box()
        button_box = self.make_button_box()

        settings_layout_3 = QVBoxLayout()
        settings_layout_3.addWidget(hide_box)
        settings_layout_3.addWidget(hide_relics_box)

        hide_missions_box = self.make_hide_missions_box()
        settings_layout_4 = QVBoxLayout()
        settings_layout_4.addWidget(hide_missions_box)
        settings_layout_4.addWidget(button_box)

        settings_layout = QHBoxLayout()
        settings_layout.addLayout(settings_layout_1)
        settings_layout.addLayout(settings_layout_2)
        settings_layout.addLayout(settings_layout_3)
        settings_layout.addLayout(settings_layout_4)

        self.dialog = QDialog()
        self.dialog.setWindowTitle("Preferences")
        self.dialog.setWindowModality(Qt.ApplicationModal)
        self.dialog.setLayout(settings_layout)

    def make_button_box(self):
        button_box = QDialogButtonBox()
        button_box.setOrientation(Qt.Horizontal)
        button_box.setStandardButtons(QDialogButtonBox.Cancel | QDialogButtonBox.Ok)
        button_box.accepted.connect(self.save_settings)
        button_box.rejected.connect(self.load_settings)
        return button_box

    def load_settings(self):
        slider_orig_values = {'x': 521, 'y': 400, 'w': 908, 'h': 70, 'v1': 197, 'v2': 180, 'd': 4,
                              'Screencap (hz)': 1, 'Fissure (s)': 30, 'API Threads': 4}
        self.slider_default_values = {}
        slider_default_max = {'x': self.warframe_width/2,
                              'y': self.warframe_height/2,
                              'w': self.warframe_width,
                              'h': self.warframe_height,
                              'v1': 255,
                              'v2': 255,
                              'd': 40}

        for slider_name in self.slider_names:
            self.slider_default_values[slider_name] = self.settings.value(slider_name,defaultValue=slider_orig_values[slider_name])
            if len(slider_name) <= 2:
                max_val = self.settings.value("{}_max".format(slider_name), defaultValue=slider_default_max[slider_name], type=int)
                self.sliders[slider_name].setMaximum(max_val)
            self.sliders[slider_name].setValue(self.slider_default_values[slider_name])

        prices = self.settings.value("last_updated_prices_value", defaultValue="Never", type=str)
        ducats = self.settings.value("last_updated_ducats_value", defaultValue="Never", type=str)
        num_parts = self.settings.value("num_parts_value", defaultValue=350, type=int)
        latest_item = self.settings.value("latest_item_value", defaultValue="", type=str)

        self.last_updated_prices_value.setText(prices)
        self.last_updated_ducats_value.setText(ducats)
        self.num_parts_value.setNum(num_parts)
        self.latest_item_value.setText(latest_item)

        for relic in self.relics:
            checked = self.settings.value("hide_{}".format(relic), defaultValue=False,type=bool)
            self.hide_relics[relic].setChecked(checked)
            if checked:
                self.set_hidden_relic(relic)

        if self.settings.value("toggle_fissure_table", defaultValue=False, type=bool):
            self.hide_fissure_check_box.setChecked(True)
            self.toggle_fissure_table()

        if self.settings.value("toggle_move_to_top", defaultValue=False, type=bool):
            self.move_to_top_check_box.setChecked(True)
            self.toggle_move_to_top()

        if self.settings.value("toggle_cropped_img", defaultValue=False, type=bool):
            self.hide_crop_check_box.setChecked(True)
            self.toggle_cropped_img()

        if self.settings.value("toggle_filtered_img", defaultValue=False, type=bool):
            self.hide_filter_check_box.setChecked(True)
            self.toggle_filtered_img()
        self.dialog.close()

    def save_settings(self):
        for slider_name in self.slider_names:
            self.settings.setValue(slider_name, self.sliders[slider_name].value())

        for relic in self.relics:
            self.settings.setValue("hide_{}".format(relic), self.hide_relics[relic].isChecked())

        self.settings.setValue("toggle_fissure_table", self.hide_fissure_check_box.isChecked())
        self.settings.setValue("toggle_move_to_top", self.move_to_top_check_box.isChecked())
        self.settings.setValue("toggle_cropped_img", self.hide_crop_check_box.isChecked())
        self.settings.setValue("toggle_filtered_img", self.hide_filter_check_box.isChecked())
        self.dialog.close()

    def init_imgs(self):
        self.crop_img = QGroupBox("Crop")
        crop_img_layout = QVBoxLayout()
        crop_img_layout.addWidget(self.image_label)
        self.crop_img.setLayout(crop_img_layout)

        self.filter_img = QGroupBox("Filtered")
        filter_img_layout = QVBoxLayout()
        filter_img_layout.addWidget(self.image_label2)
        self.filter_img.setLayout(filter_img_layout)

    def make_hide_missions_box(self, missions=None):
        if self.hide_missions_box is None:
            self.hide_missions_box = QGroupBox("Hide Missions")
        if missions is not None:
            hide_missions_layout = QGridLayout()
            hide_missions_layout.setColumnStretch(2, 2)
            hide_missions_layout.setAlignment(Qt.AlignTop)
            hide_missions_layout.setContentsMargins(0, 0, 0, 0)

            skip_missions = ["MT_SECTOR", "MT_PVP", "MT_LANDSCAPE", "MT_EVACUATION", "MT_ASSASSINATION", "MT_ARENA"]
            seen_missions = set()
            i = 0
            for mission in missions:
                if mission not in skip_missions and mission not in seen_missions:
                    mission_name = missions[mission]['value']
                    self.hide_missions[mission_name] = QCheckBox(mission_name)
                    self.hide_missions[mission_name].setChecked(False)
                    self.hide_missions[mission_name].stateChanged.connect(partial(self.set_hidden_mission, mission_name))
                    hide_missions_layout.addWidget(self.hide_missions[mission_name], int(i/2),i % 2)
                    i += 1
                    seen_missions.add(mission_name)
            self.hide_missions_box.setLayout(hide_missions_layout)
        return self.hide_missions_box

    def set_hidden_mission(self, mission):
        if self.hide_missions[mission].isChecked():
            self.hidden_missions.add(mission)
        else:
            self.hidden_missions.remove(mission)
        self.update_mission_table_hidden()

    def make_hide_relics_box(self):
        hide_relics_layout = QVBoxLayout()
        hide_relics_layout.setAlignment(Qt.AlignTop)
        hide_relics_layout.setContentsMargins(0, 0, 0, 0)
        self.relics = ["Axi", "Neo", "Meso", "Lith", "Requiem"]

        for relic in self.relics:
            self.hide_relics[relic] = QCheckBox(relic)
            self.hide_relics[relic].setChecked(False)
            self.hide_relics[relic].stateChanged.connect(partial(self.set_hidden_relic, relic))
            hide_relics_layout.addWidget(self.hide_relics[relic])

        hide_relics_box = QGroupBox("Hide Relics")
        hide_relics_box.setLayout(hide_relics_layout)
        return hide_relics_box

    def make_hide_box(self):
        hide_layout = QVBoxLayout()
        hide_layout.setAlignment(Qt.AlignTop)
        hide_layout.setContentsMargins(0, 0, 0, 0)

        self.hide_crop_check_box = QCheckBox("Hide Crop")
        self.hide_crop_check_box.setChecked(False)
        self.hide_crop_check_box.stateChanged.connect(self.toggle_cropped_img)
        hide_layout.addWidget(self.hide_crop_check_box)

        self.hide_filter_check_box = QCheckBox("Hide Filtered")
        self.hide_filter_check_box.setChecked(False)
        self.hide_filter_check_box.stateChanged.connect(self.toggle_filtered_img)
        hide_layout.addWidget(self.hide_filter_check_box)

        self.hide_fissure_check_box = QCheckBox("Hide Fissure Table")
        self.hide_fissure_check_box.setChecked(False)
        self.hide_fissure_check_box.stateChanged.connect(self.toggle_fissure_table)
        hide_layout.addWidget(self.hide_fissure_check_box)

        hide_box = QGroupBox("Hide UI")
        hide_box.setLayout(hide_layout)
        return hide_box

    def make_rate_box(self):
        rate_grid = QGridLayout()
        rate_grid.setColumnStretch(3, 3)
        rate_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            slider_name = self.slider_names[i + 7]
            rate_grid.addWidget(self.slider_labels[slider_name], i, 0)
            rate_grid.addWidget(self.slider_values[slider_name], i, 1)
            rate_grid.addWidget(self.sliders[slider_name], i, 2)

        rate_box = QGroupBox("Rates")
        rate_box.setLayout(rate_grid)
        return rate_box

    def make_other_box(self):
        self.move_to_top_check_box = QCheckBox("Bring to front")
        self.move_to_top_check_box.setChecked(True)
        self.move_to_top_check_box.stateChanged.connect(self.toggle_move_to_top)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.toggle_button)
        self.is_paused = False
        other_layout = QVBoxLayout()
        other_layout.setAlignment(Qt.AlignTop)
        other_layout.setContentsMargins(0, 0, 0, 0)
        other_layout.addWidget(self.move_to_top_check_box)
        other_layout.addWidget(self.pause_button)

        other_box = QGroupBox("Other")
        other_box.setLayout(other_layout)
        return other_box

    def make_filter_box(self):
        filter_grid = QGridLayout()
        filter_grid.setColumnStretch(3, 3)
        filter_grid.setAlignment(Qt.AlignTop)
        filter_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(3):
            slider_name = self.slider_names[i + 4]
            filter_grid.addWidget(self.slider_labels[slider_name], i, 0)
            filter_grid.addWidget(self.slider_values[slider_name], i, 1)
            filter_grid.addWidget(self.sliders[slider_name], i, 2)

        filter_box = QGroupBox("Filter Parameters")
        filter_box.setLayout(filter_grid)
        return filter_box

    def make_crop_box(self):
        crop_grid = QGridLayout()
        crop_grid.setColumnStretch(3, 4)
        crop_grid.setAlignment(Qt.AlignTop)
        crop_grid.setContentsMargins(0, 0, 0, 0)
        for i in range(4):
            slider_name = self.slider_names[i]
            crop_grid.addWidget(self.slider_labels[slider_name], i, 0)
            crop_grid.addWidget(self.slider_values[slider_name], i, 1)
            crop_grid.addWidget(self.sliders[slider_name], i, 2)

        crop_box = QGroupBox("Crop Parameters")
        crop_box.setLayout(crop_grid)
        return crop_box

    def make_update_box(self):
        update_layout = QGridLayout()
        update_layout.setColumnStretch(4, 2)
        update_layout.setAlignment(Qt.AlignTop)
        update_layout.setContentsMargins(0, 0, 0, 0)
        self.update_prices_button = QPushButton("Update Prices")
        self.update_prices_button.clicked.connect(self.update_prices)
        self.update_prices_progress = QProgressBar()
        self.update_prices_progress.setFixedWidth(110)
        self.update_prices_progress.setRange(0, 100)
        update_layout.addWidget(self.update_prices_button, 0, 0)
        update_layout.addWidget(self.update_prices_progress, 0, 1)

        self.update_ducats_button = QPushButton("Update Ducats")
        self.update_ducats_button.clicked.connect(self.update_ducats)
        self.update_ducats_progress = QProgressBar()
        self.update_ducats_progress.setFixedWidth(110)
        self.update_ducats_progress.setRange(0, 100)
        update_layout.addWidget(self.update_ducats_button, 1, 0)
        update_layout.addWidget(self.update_ducats_progress, 1, 1)

        last_updated_prices_label = QLabel("Prices Updated")

        prices = self.settings.value("last_updated_prices_value", defaultValue="Never", type=str)
        ducats = self.settings.value("last_updated_ducats_value", defaultValue="Never", type=str)
        num_parts = self.settings.value("num_parts_value", defaultValue=350, type=str)
        latest_item = self.settings.value("latest_item_value", defaultValue="", type=str)

        self.last_updated_prices_value = QLabel(prices)
        self.last_updated_ducats_value = QLabel(ducats)
        self.num_parts_value = QLabel(num_parts)
        self.latest_item_value = QLabel(latest_item)

        update_layout.addWidget(last_updated_prices_label, 2, 0)
        update_layout.addWidget(self.last_updated_prices_value, 2, 1)

        last_updated_ducats_label = QLabel("Ducats Updated")
        update_layout.addWidget(last_updated_ducats_label, 3, 0)
        update_layout.addWidget(self.last_updated_ducats_value, 3, 1)

        num_parts_label = QLabel("Prime Parts")
        update_layout.addWidget(num_parts_label, 4, 0)
        update_layout.addWidget(self.num_parts_value, 4, 1)

        latest_item_label = QLabel("Latest Prime")
        update_layout.addWidget(latest_item_label, 5, 0)
        update_layout.addWidget(self.latest_item_value, 5, 1)

        update_box = QGroupBox("Updates")
        update_box.setLayout(update_layout)
        return update_box

    def init_sliders(self):
        self.slider_names = ['x', 'y', 'w', 'h', 'v1', 'v2', 'd', 'Screencap (hz)', 'Fissure (s)', 'API Threads']
        self.sliders = {x: QSlider(Qt.Horizontal) for x in self.slider_names}
        self.slider_labels = {x: QLabel(x) for x in self.slider_names}
        self.slider_default_values = {}
        self.slider_orig_values = {'x': 521, 'y': 400, 'w': 908, 'h': 70, 'v1': 197, 'v2': 180, 'd': 4,
                                   'Screencap (hz)': 1, 'Fissure (s)': 30, 'API Threads': 4}
        for slider_name in self.slider_names:
            self.slider_default_values[slider_name] = self.settings.value(slider_name, defaultValue=self.slider_orig_values[slider_name])
        self.slider_values = {x: QLabel(str(self.slider_default_values[x])) for x in self.slider_names}
        self.slider_values['Screencap (hz)'].setNum(self.slider_default_values['Screencap (hz)']/4)
        self.slider_values['d'].setNum(self.slider_default_values['d'] / 4)

        self.slider_labels['d'].setText('\u0394')

        self.sliders['x'].setMaximum(int(self.warframe_width / 2))
        self.sliders['y'].setMaximum(int(self.warframe_height / 2))
        self.sliders['w'].setMaximum(self.warframe_width)
        self.sliders['h'].setMaximum(self.warframe_height)
        self.sliders['v1'].setMaximum(255)
        self.sliders['v2'].setMaximum(255)
        self.sliders['d'].setMaximum(40)
        self.sliders['Screencap (hz)'].setMaximum(20)
        self.sliders['Screencap (hz)'].setMinimum(1)
        self.sliders['Fissure (s)'].setMaximum(60)
        self.sliders['Fissure (s)'].setMinimum(10)
        self.sliders['API Threads'].setMaximum(10)
        self.sliders['API Threads'].setMinimum(2)
        for slider_name in self.slider_names:
            if len(slider_name) <= 2:
                self.sliders[slider_name].setMinimum(0)
            self.sliders[slider_name].setSingleStep(1)
            self.slider_values[slider_name].setFixedWidth(35)
            self.sliders[slider_name].setValue(self.slider_default_values[slider_name])

    def init_tables(self):
        self.table = QTableWidget(7, 3)
        self.table.setHorizontalHeaderLabels(['Prime Part', 'Plat', 'Ducats'])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.mission_table = QTableWidget(30, 4)
        self.mission_table.setHorizontalHeaderLabels(['Relic', 'Mission', 'Type', 'Time Left'])
        self.mission_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        mission_header = self.mission_table.horizontalHeader()

        for i in range(4):
            mission_header.setSectionResizeMode(i, QHeaderView.Interactive)
        mission_header.resizeSection(0, 55)
        mission_header.resizeSection(1, 150)
        mission_header.resizeSection(2, 90)
        mission_header.resizeSection(3, 60)
        self.mission_table.setFixedWidth(405)

    def update_prices(self):
        self.prices_thread = threading.Thread(name="prices_thread", target=self.market_api.update_prices)
        self.prices_thread.start()

        self.update_prices_button.setEnabled(False)
        self.update_ducats_button.setEnabled(False)

    def update_ducats(self):
        self.ducats_thread = threading.Thread(name="ducats_thread", target=self.market_api.update_ducats)
        self.ducats_thread.start()

        self.update_prices_button.setEnabled(False)
        self.update_ducats_button.setEnabled(False)

    def update_primes_info(self, num, latest):
        self.num_parts_value.setNum(num)
        self.latest_item_value.setText(latest)
        self.update_prices_progress.setMaximum(num)
        self.update_ducats_progress.setMaximum(num)
        self.num_primes = num

    def get_datetime(self):
        return datetime.now().strftime("%b %d %Y %H:%M:%S")

    def update_ducats_time(self):
        self.last_updated_ducats_value.setText(self.get_datetime())
        self.ducats_progress_lock.acquire()
        self.update_ducats_progress.setValue(self.num_primes)
        self.ducats_progress_lock.release()

        self.settings.setValue("last_updated_ducats_value", self.last_updated_ducats_value.text())
        self.settings.setValue("num_parts_value", self.num_parts_value.text())
        self.settings.setValue("latest_item_value", self.latest_item_value.text())

    def update_prices_time(self):
        self.last_updated_prices_value.setText(self.get_datetime())
        self.prices_progress_lock.acquire()
        self.update_prices_progress.setValue(self.num_primes)
        self.prices_progress_lock.release()

        self.settings.setValue("last_updated_prices_value", self.last_updated_prices_value.text())
        self.settings.setValue("num_parts_value", self.num_parts_value.text())
        self.settings.setValue("latest_item_value", self.latest_item_value.text())

    def set_update_prices_progress(self, val):
        if self.prices_progress_lock.acquire():
            self.update_prices_progress.setValue(val)
            self.prices_progress_lock.release()

    def set_update_ducats_progress(self, val):
        if self.ducats_progress_lock.acquire():
            self.update_ducats_progress.setValue(val)
            self.ducats_progress_lock.release()

    def finished_update_progress(self):
        self.update_prices_button.setEnabled(True)
        self.update_ducats_button.setEnabled(True)

    def show_preferences(self):
        self.dialog.exec_()
        self.load_settings()

    def toggle_fissure_table(self):
        if self.hide_fissure_check_box.isChecked():
            self.mission_table.hide()
        else:
            self.mission_table.show()
        self.setFixedSize(self.layout.sizeHint())

    def toggle_move_to_top(self):
        self.ocr.set_move_to_top(self.move_to_top_check_box.isChecked())

    def toggle_cropped_img(self):
        if self.hide_crop_check_box.isChecked():
            self.crop_img.hide()
        else:
            self.crop_img.show()
        self.setFixedSize(self.layout.sizeHint())

    def toggle_filtered_img(self):
        if self.hide_filter_check_box.isChecked():
            self.filter_img.hide()
        else:
            self.filter_img.show()
        self.setFixedSize(self.layout.sizeHint())
        #print("{}h,{}w".format(self.frameGeometry().height(),self.frameGeometry().width()))

    def set_sliders_range(self, x, y):
        max_values = {'x': int(x/2), 'y': int(y/2), 'w':x, 'h':y}
        for slider_name in max_values:
            self.sliders[slider_name].setMaximum(max_values[slider_name])
            self.sliders[slider_name].setValue(self.slider_default_values[slider_name])
            self.settings.setValue("{}_max", max_values[slider_name])

    def toggle_button(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_button.setText("Resume")
        else:
            self.pause_button.setText("Pause")
        if self.ocr is not None:
            if self.is_paused:
                self.ocr.save_screenshot()
                self.ocr.skip_screenshot = True
            else:
                self.ocr.skip_screenshot = False

    def clear_table(self):
        self.table.clearSelection()
        self.table.clearContents()
        self.filled_rows = 0
        #self.table.setRowCount(self.filled_rows)

    def is_plat_preferred(self):
        return self.plat_check_box.isChecked()

    def insert_table_row(self, row):
        for i in range(3):
            self.table.setItem(self.filled_rows, i, QTableWidgetItem(str(row[i])))

        self.filled_rows = self.filled_rows + 1
        #self.table.setRowCount(self.filled_rows)

    def update_mission_table(self, missions):
        self.missions = list(missions)
        cur_time = time.time()
        for i in range(len(missions)):
            for j in range(3):
                self.mission_table.setItem(i, j, QTableWidgetItem(str(self.missions[i][j])))

            self.mission_table.setItem(i, 3, QTableWidgetItem(self.get_duration_str(self.missions[i][3]-cur_time)))
            if self.missions[i][0] in self.hidden_relics:
                self.mission_table.setRowHidden(i, True)
            else:
                self.mission_table.setRowHidden(i, False)

        self.mission_table.setRowCount(len(self.missions)-1)

    def update_mission_table_time(self):
        cur_time = time.time()
        needs_update = False
        for i in range(len(self.missions)):
            self.mission_table.setItem(i, 3, QTableWidgetItem(self.get_duration_str(self.missions[i][3]-cur_time)))
            if self.missions[i][3]-cur_time < 0:
                needs_update = True
        if needs_update:
            self.api.filter_expired_missions()

    def update_mission_table_hidden(self):
        for i in range(len(self.missions)):
            if self.missions[i][0] in self.hidden_relics:
                self.mission_table.setRowHidden(i, True)
            elif self.missions[i][2] in self.hidden_missions:
                self.mission_table.setRowHidden(i, True)
            else:
                self.mission_table.setRowHidden(i, False)

    def get_duration_str(self, duration):
        m, s = divmod(int(duration), 60)
        h, m = divmod(m, 60)
        return '{:d}:{:02d}:{:02d}'.format(h, m, s)

    def set_ocr_connection(self, ocr):
        for slider_name in self.slider_names:
            self.sliders[slider_name].valueChanged.connect(partial(self.set_ocr_crop, ocr, slider_name))
        self.ocr = ocr
        self.market_api = MarketReader(ocr=self.ocr, gui=self)

    def set_api(self, wf_api):
        self.api = wf_api
        self.make_hide_missions_box(self.api.mission_types)

    def set_hidden_relic(self, relic):
        if self.hide_relics[relic].isChecked():
            self.hidden_relics.add(relic)
        else:
            self.hidden_relics.remove(relic)
        self.update_mission_table_hidden()

    def set_ocr_crop(self, ocr, dim, val):
        if dim == 'Screencap (hz)' or dim == 'd':
            val = val / 4
        self.slider_values[dim].setNum(val)
        if val < 0 or val > 100000 or val is None:
            return
        if dim == 'x':
            ocr.set_x_offset(val)
        if dim == 'y':
            ocr.set_y_offset(val)
        if dim == 'w':
            ocr.set_w(val)
        if dim == 'h':
            ocr.set_h(val)
        if dim == 'v1':
            ocr.set_v1(val)
        if dim == 'v2':
            ocr.set_v2(val)
        if dim == 'd':
            self.ocr.set_diff_threshold(val/4)
        if dim == 'Screencap (hz)':
            ocr.set_interval(1/val)
        if dim == 'Fissure (s)':
            self.api.set_rate(val)
        if dim == 'API Threads':
            self.market_api.set_num_threads(val)

    #def select_max(self):
    #    # TODO doesnt work
    #    self.table.clearSelection()
    #    self.table.selectRow(self.max_row)

    def update_filtered(self, filtered):
        filtered_shape = None
        if not self.hide_filter_check_box.isChecked():
            filtered_shape = filtered.shape
            h, w = filtered.shape
            bytes_per_line = w
            filtered_pix = QPixmap(QImage(filtered, w, h, bytes_per_line, QImage.Format_Grayscale8))
            filtered_pix = filtered_pix.scaled(908, 70, Qt.KeepAspectRatio)
            self.image_label2.setPixmap(filtered_pix)
        #self.update_window_size(None, filtered_shape)

    def update_screenshot(self, screenshot):
        screenshot_shape = None
        if not self.hide_crop_check_box.isChecked():
            screenshot_shape = screenshot.shape
            h, w, ch = screenshot.shape
            bytes_per_line = ch * w
            screenshot_pix = QPixmap(QImage(screenshot, w, h, bytes_per_line, QImage.Format_RGB888))
            screenshot_pix = screenshot_pix.scaled(908, 70, Qt.KeepAspectRatio)
            self.image_label.setPixmap(screenshot_pix)
        #self.update_window_size(screenshot_shape, None)

    def update_window_size(self, screenshot_shape, filtered_shape):
        should_update = False
        if screenshot_shape is not None and screenshot_shape == self.old_screenshot_shape:
            self.old_screenshot_shape = screenshot_shape
            should_update = True
        if filtered_shape is not None and filtered_shape == self.old_filtered_shape:
            self.old_filtered_shape = filtered_shape
            should_update = True
        if should_update:
            self.setFixedSize(self.layout.sizeHint())

    def __exit__(self):
        self.market_api.exit_now = True
        self.ocr.exit_now = True


class OCRThread(QThread):
    def __init__(self, gui):
        QThread.__init__(self)
        self.ocr = OCR(debug=False, gui=gui)
        self.ocr_thread = threading.Thread(name="ocr_thread", target=self.ocr.main)

    def __del__(self):
        self.ocr.exit_now = True
        self.ocr_thread.join()
        self.wait()

    def run(self):
        self.ocr_thread.start()


class APIThread(QThread):
    def __init__(self, gui):
        QThread.__init__(self)
        self.api = APIReader(gui=gui)

    def __del__(self):
        self.api.cancel_event()
        self.wait()

    def run(self):
        self.api.run(blocking=False)


class App():
    def __init__(self):
        self.ocr_thread = None
        self.market_api = None

    def run(self):
        app = ApplicationContext()
        window = Window()
        app.app.setWindowIcon(QIcon(window.icon_path))
        dark_stylesheet = qdarkstyle.load_stylesheet_pyqt5()
        app.app.setStyleSheet(dark_stylesheet)

        ocr_thread = OCRThread(window)
        window.set_ocr_connection(ocr_thread.ocr)
        ocr_thread.start()

        api = APIReader(gui=window)
        api_thread = APIThread(window)
        window.set_api(api)
        api_thread.start()

        market_api = window.market_api
        exit_code = app.app.exec_()
        ocr_thread.ocr.exit_now = True
        market_api.exit_now = True
        ocr_thread.terminate()
        api_thread.terminate()
        return exit_code


if __name__ == "__main__":
    app = App()
    app.run()
# use to figure out if any threads are keeping python open
    #time.sleep(1)
    #print(str({t.ident: t.name for t in threading.enumerate()}))