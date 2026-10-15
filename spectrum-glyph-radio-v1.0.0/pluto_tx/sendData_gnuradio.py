#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Visual OFDM — ADALM-PLUTO Transmitter
# Description: Visual OFDM Pluto transmitter; Run opens the compact dynamic-control UI.
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, pyqtSlot
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import soapy
import sendData_gnuradio_epy_block_0 as epy_block_0  # embedded python block
import sip
import threading



class sendData_gnuradio(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Visual OFDM — ADALM-PLUTO Transmitter", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Visual OFDM — ADALM-PLUTO Transmitter")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "sendData_gnuradio")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Variables
        ##################################################
        self.sample_rate = sample_rate = 500000
        self.fft_len = fft_len = 512
        self.active_subcarriers = active_subcarriers = 510
        self.tx_gain = tx_gain = 89.0
        self.text_message = text_message = '欢迎报考北京邮电大学'
        self.row_hold_ms = row_hold_ms = 6000
        self.pluto_uri = pluto_uri = ''
        self.pixel_size = pixel_size = 32
        self.payload_mode = payload_mode = 0
        self.occupied_bandwidth = occupied_bandwidth = (active_subcarriers*sample_rate/fft_len)
        self.image_path = image_path = 'RandomMan.jpg'
        self.font_family = font_family = 'Microsoft YaHei'
        self.center_frequency = center_frequency = 435e6
        self.amplitude = amplitude = 7.0

        ##################################################
        # Blocks
        ##################################################

        self._text_message_tool_bar = Qt.QToolBar(self)
        self._text_message_tool_bar.addWidget(Qt.QLabel("Text to transmit" + ": "))
        self._text_message_line_edit = Qt.QLineEdit(str(self.text_message))
        self._text_message_tool_bar.addWidget(self._text_message_line_edit)
        self._text_message_line_edit.editingFinished.connect(
            lambda: self.set_text_message(str(str(self._text_message_line_edit.text()))))
        self.top_grid_layout.addWidget(self._text_message_tool_bar, 4, 1, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._sample_rate_options = [65104.1666667, 125000, 250000, 500000, 1024000, 2048000, 4096000, 6144000, 8192000]
        # Create the labels list
        self._sample_rate_labels = ['65.104 kS/s - Pluto minimum', '125 kS/s', '250 kS/s', '500 kS/s', '1.024 MS/s', '2.048 MS/s', '4.096 MS/s', '6.144 MS/s', '8.192 MS/s']
        # Create the combo box
        self._sample_rate_tool_bar = Qt.QToolBar(self)
        self._sample_rate_tool_bar.addWidget(Qt.QLabel("Baseband sample rate (live)" + ": "))
        self._sample_rate_combo_box = Qt.QComboBox()
        self._sample_rate_tool_bar.addWidget(self._sample_rate_combo_box)
        for _label in self._sample_rate_labels: self._sample_rate_combo_box.addItem(_label)
        self._sample_rate_callback = lambda i: Qt.QMetaObject.invokeMethod(self._sample_rate_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._sample_rate_options.index(i)))
        self._sample_rate_callback(self.sample_rate)
        self._sample_rate_combo_box.currentIndexChanged.connect(
            lambda i: self.set_sample_rate(self._sample_rate_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._sample_rate_tool_bar, 0, 1, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._row_hold_ms_range = qtgui.Range(1000, 10000, 100, 6000, 200)
        self._row_hold_ms_win = qtgui.RangeWidget(self._row_hold_ms_range, self.set_row_hold_ms, "Transmit time per row (ms)", "counter_slider", int, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._row_hold_ms_win, 2, 1, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._pixel_size_options = [16, 32]
        # Create the labels list
        self._pixel_size_labels = ['16 × 16', '32 × 32']
        # Create the combo box
        self._pixel_size_tool_bar = Qt.QToolBar(self)
        self._pixel_size_tool_bar.addWidget(Qt.QLabel("Text pixel size" + ": "))
        self._pixel_size_combo_box = Qt.QComboBox()
        self._pixel_size_tool_bar.addWidget(self._pixel_size_combo_box)
        for _label in self._pixel_size_labels: self._pixel_size_combo_box.addItem(_label)
        self._pixel_size_callback = lambda i: Qt.QMetaObject.invokeMethod(self._pixel_size_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._pixel_size_options.index(i)))
        self._pixel_size_callback(self.pixel_size)
        self._pixel_size_combo_box.currentIndexChanged.connect(
            lambda i: self.set_pixel_size(self._pixel_size_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._pixel_size_tool_bar, 5, 1, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._payload_mode_options = [0, 1, 2]
        # Create the labels list
        self._payload_mode_labels = ['Built-in Hanzi', 'Text', 'Image file']
        # Create the combo box
        self._payload_mode_tool_bar = Qt.QToolBar(self)
        self._payload_mode_tool_bar.addWidget(Qt.QLabel("Payload mode" + ": "))
        self._payload_mode_combo_box = Qt.QComboBox()
        self._payload_mode_tool_bar.addWidget(self._payload_mode_combo_box)
        for _label in self._payload_mode_labels: self._payload_mode_combo_box.addItem(_label)
        self._payload_mode_callback = lambda i: Qt.QMetaObject.invokeMethod(self._payload_mode_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._payload_mode_options.index(i)))
        self._payload_mode_callback(self.payload_mode)
        self._payload_mode_combo_box.currentIndexChanged.connect(
            lambda i: self.set_payload_mode(self._payload_mode_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._payload_mode_tool_bar, 4, 0, 1, 1)
        for r in range(4, 5):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._image_path_tool_bar = Qt.QToolBar(self)
        self._image_path_tool_bar.addWidget(Qt.QLabel("Image path" + ": "))
        self._image_path_line_edit = Qt.QLineEdit(str(self.image_path))
        self._image_path_tool_bar.addWidget(self._image_path_line_edit)
        self._image_path_line_edit.editingFinished.connect(
            lambda: self.set_image_path(str(str(self._image_path_line_edit.text()))))
        self.top_grid_layout.addWidget(self._image_path_tool_bar, 6, 0, 1, 2)
        for r in range(6, 7):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._font_family_options = ['SimSun', 'Microsoft YaHei', 'KaiTi', 'FangSong']
        # Create the labels list
        self._font_family_labels = ['宋体', '微软雅黑', '楷体', '仿宋']
        # Create the combo box
        self._font_family_tool_bar = Qt.QToolBar(self)
        self._font_family_tool_bar.addWidget(Qt.QLabel("Font family" + ": "))
        self._font_family_combo_box = Qt.QComboBox()
        self._font_family_tool_bar.addWidget(self._font_family_combo_box)
        for _label in self._font_family_labels: self._font_family_combo_box.addItem(_label)
        self._font_family_callback = lambda i: Qt.QMetaObject.invokeMethod(self._font_family_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._font_family_options.index(i)))
        self._font_family_callback(self.font_family)
        self._font_family_combo_box.currentIndexChanged.connect(
            lambda i: self.set_font_family(self._font_family_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._font_family_tool_bar, 5, 0, 1, 1)
        for r in range(5, 6):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        # Create the options list
        self._fft_len_options = [512, 1024, 2048, 4096, 8192]
        # Create the labels list
        self._fft_len_labels = ['512', '1024', '2048', '4096', '8192']
        # Create the combo box
        self._fft_len_tool_bar = Qt.QToolBar(self)
        self._fft_len_tool_bar.addWidget(Qt.QLabel("OFDM FFT length" + ": "))
        self._fft_len_combo_box = Qt.QComboBox()
        self._fft_len_tool_bar.addWidget(self._fft_len_combo_box)
        for _label in self._fft_len_labels: self._fft_len_combo_box.addItem(_label)
        self._fft_len_callback = lambda i: Qt.QMetaObject.invokeMethod(self._fft_len_combo_box, "setCurrentIndex", Qt.Q_ARG("int", self._fft_len_options.index(i)))
        self._fft_len_callback(self.fft_len)
        self._fft_len_combo_box.currentIndexChanged.connect(
            lambda i: self.set_fft_len(self._fft_len_options[i]))
        # Create the radio buttons
        self.top_grid_layout.addWidget(self._fft_len_tool_bar, 1, 1, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._center_frequency_tool_bar = Qt.QToolBar(self)
        self._center_frequency_tool_bar.addWidget(Qt.QLabel("RF center frequency (Hz)" + ": "))
        self._center_frequency_line_edit = Qt.QLineEdit(str(self.center_frequency))
        self._center_frequency_tool_bar.addWidget(self._center_frequency_line_edit)
        self._center_frequency_line_edit.editingFinished.connect(
            lambda: self.set_center_frequency(eng_notation.str_to_num(str(self._center_frequency_line_edit.text()))))
        self.top_grid_layout.addWidget(self._center_frequency_tool_bar, 0, 0, 1, 1)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._amplitude_range = qtgui.Range(0.0, 7.0, 0.1, 7.0, 200)
        self._amplitude_win = qtgui.RangeWidget(self._amplitude_range, self.set_amplitude, "Active-subcarrier amplitude", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._amplitude_win, 2, 0, 1, 1)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._active_subcarriers_range = qtgui.Range(32, 510, 2, 510, 200)
        self._active_subcarriers_win = qtgui.RangeWidget(self._active_subcarriers_range, self.set_active_subcarriers, "Occupied subcarriers", "counter_slider", int, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._active_subcarriers_win, 3, 0, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._tx_gain_range = qtgui.Range(0.0, 89.0, 0.25, 89.0, 200)
        self._tx_gain_win = qtgui.RangeWidget(self._tx_gain_range, self.set_tx_gain, "Pluto TX gain (dB)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._tx_gain_win, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.soapy_plutosdr_sink_0 = None
        dev = 'driver=plutosdr'
        stream_args = ''
        tune_args = ['']
        settings = ['']

        self.soapy_plutosdr_sink_0 = soapy.sink(dev, "sc8", 1, pluto_uri,
                                  stream_args, tune_args, settings)
        self.soapy_plutosdr_sink_0.set_sample_rate(0, sample_rate)
        self.soapy_plutosdr_sink_0.set_bandwidth(0, 3.5e6)
        self.soapy_plutosdr_sink_0.set_frequency(0, center_frequency)
        self.soapy_plutosdr_sink_0.set_gain(0, min(max(89.0, 0.0), 89.0))
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            fft_len, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            sample_rate, #bw
            "Baseband spectrum — occupied band centred at DC (DC nulled)", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-90), (-30))
        self.qtgui_freq_sink_x_0.set_y_label('Relative amplitude', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(True)
        self.qtgui_freq_sink_x_0.set_fft_average(0.1)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ["OFDM baseband", '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_x_0_win, 7, 0, 1, 2)
        for r in range(7, 8):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._occupied_bandwidth_tool_bar = Qt.QToolBar(self)

        if lambda x: "Occupied band, centred at DC (DC nulled): {:.3f} kHz".format(x / 1e3):
            self._occupied_bandwidth_formatter = lambda x: "Occupied band, centred at DC (DC nulled): {:.3f} kHz".format(x / 1e3)
        else:
            self._occupied_bandwidth_formatter = lambda x: eng_notation.num_to_str(x)

        self._occupied_bandwidth_tool_bar.addWidget(Qt.QLabel("'occupied_bandwidth'"))
        self._occupied_bandwidth_label = Qt.QLabel(str(self._occupied_bandwidth_formatter(self.occupied_bandwidth)))
        self._occupied_bandwidth_tool_bar.addWidget(self._occupied_bandwidth_label)
        self.top_grid_layout.addWidget(self._occupied_bandwidth_tool_bar, 3, 1, 1, 1)
        for r in range(3, 4):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(1, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.epy_block_0 = epy_block_0.blk(fft_len=fft_len, amplitude=amplitude, row_hold_ms=row_hold_ms, active_subcarriers=active_subcarriers, payload_mode=payload_mode, text_message=text_message, font_family=font_family, pixel_size=pixel_size, image_path=image_path, sample_rate=sample_rate)
        self.blocks_complex_to_interleaved_char_0 = blocks.complex_to_interleaved_char(True, 127.0)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_interleaved_char_0, 0), (self.soapy_plutosdr_sink_0, 0))
        self.connect((self.epy_block_0, 0), (self.blocks_complex_to_interleaved_char_0, 0))
        self.connect((self.epy_block_0, 0), (self.qtgui_freq_sink_x_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "sendData_gnuradio")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sample_rate(self):
        return self.sample_rate

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate
        self.set_occupied_bandwidth((self.active_subcarriers*self.sample_rate/self.fft_len))
        self._sample_rate_callback(self.sample_rate)
        self.epy_block_0.sample_rate = self.sample_rate
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.sample_rate)
        self.soapy_plutosdr_sink_0.set_sample_rate(0, self.sample_rate)

    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len
        self._fft_len_callback(self.fft_len)
        self.set_occupied_bandwidth((self.active_subcarriers*self.sample_rate/self.fft_len))
        self.epy_block_0.fft_len = self.fft_len

    def get_active_subcarriers(self):
        return self.active_subcarriers

    def set_active_subcarriers(self, active_subcarriers):
        self.active_subcarriers = active_subcarriers
        self.set_occupied_bandwidth((self.active_subcarriers*self.sample_rate/self.fft_len))
        self.epy_block_0.active_subcarriers = self.active_subcarriers

    def get_tx_gain(self):
        return self.tx_gain

    def set_tx_gain(self, tx_gain):
        self.tx_gain = tx_gain

    def get_text_message(self):
        return self.text_message

    def set_text_message(self, text_message):
        self.text_message = text_message
        Qt.QMetaObject.invokeMethod(self._text_message_line_edit, "setText", Qt.Q_ARG("QString", str(self.text_message)))
        self.epy_block_0.text_message = self.text_message

    def get_row_hold_ms(self):
        return self.row_hold_ms

    def set_row_hold_ms(self, row_hold_ms):
        self.row_hold_ms = row_hold_ms
        self.epy_block_0.row_hold_ms = self.row_hold_ms

    def get_pluto_uri(self):
        return self.pluto_uri

    def set_pluto_uri(self, pluto_uri):
        self.pluto_uri = pluto_uri

    def get_pixel_size(self):
        return self.pixel_size

    def set_pixel_size(self, pixel_size):
        self.pixel_size = pixel_size
        self._pixel_size_callback(self.pixel_size)
        self.epy_block_0.pixel_size = self.pixel_size

    def get_payload_mode(self):
        return self.payload_mode

    def set_payload_mode(self, payload_mode):
        self.payload_mode = payload_mode
        self._payload_mode_callback(self.payload_mode)
        self.epy_block_0.payload_mode = self.payload_mode

    def get_occupied_bandwidth(self):
        return self.occupied_bandwidth

    def set_occupied_bandwidth(self, occupied_bandwidth):
        self.occupied_bandwidth = occupied_bandwidth
        Qt.QMetaObject.invokeMethod(self._occupied_bandwidth_label, "setText", Qt.Q_ARG("QString", str(self._occupied_bandwidth_formatter(self.occupied_bandwidth))))

    def get_image_path(self):
        return self.image_path

    def set_image_path(self, image_path):
        self.image_path = image_path
        Qt.QMetaObject.invokeMethod(self._image_path_line_edit, "setText", Qt.Q_ARG("QString", str(self.image_path)))
        self.epy_block_0.image_path = self.image_path

    def get_font_family(self):
        return self.font_family

    def set_font_family(self, font_family):
        self.font_family = font_family
        self._font_family_callback(self.font_family)
        self.epy_block_0.font_family = self.font_family

    def get_center_frequency(self):
        return self.center_frequency

    def set_center_frequency(self, center_frequency):
        self.center_frequency = center_frequency
        Qt.QMetaObject.invokeMethod(self._center_frequency_line_edit, "setText", Qt.Q_ARG("QString", eng_notation.num_to_str(self.center_frequency)))
        self.soapy_plutosdr_sink_0.set_frequency(0, self.center_frequency)

    def get_amplitude(self):
        return self.amplitude

    def set_amplitude(self, amplitude):
        self.amplitude = amplitude
        self.epy_block_0.amplitude = self.amplitude




def main(top_block_cls=sendData_gnuradio, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()
    tb.flowgraph_started.set()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
