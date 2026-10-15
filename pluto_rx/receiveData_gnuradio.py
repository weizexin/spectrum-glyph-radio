#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Visual OFDM — ADALM-PLUTO Receiver
# Description: Visual OFDM monitor: Run opens the GNU Radio spectrum window (with a unified bandwidth slider that retunes the real sample rate) plus a top-down scrolling waterfall window drawn by the embedded python block.  No files written.
# GNU Radio version: 3.10.12.0

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import fft
from gnuradio.fft import window
from gnuradio import gr
from gnuradio.filter import firdes
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import soapy
import receiveData_gnuradio_epy_block_0 as epy_block_0  # embedded python block
import sip
import threading



class receiveData_gnuradio(gr.top_block, Qt.QWidget):

    def __init__(self, sample_rate=500000, fft_len=512, driver='plutosdr', pluto_uri='', agc=0, max_rows=4096, console_report=1):
        gr.top_block.__init__(self, "Visual OFDM — ADALM-PLUTO Receiver", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Visual OFDM — ADALM-PLUTO Receiver")
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

        self.settings = Qt.QSettings("gnuradio/flowgraphs", "receiveData_gnuradio")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)
        self.flowgraph_started = threading.Event()

        ##################################################
        # Parameters
        ##################################################
        self.sample_rate = sample_rate
        self.fft_len = fft_len
        self.driver = driver
        self.pluto_uri = pluto_uri
        self.agc = agc
        self.max_rows = max_rows
        self.console_report = console_report

        ##################################################
        # Variables
        ##################################################
        self.subcarriers = subcarriers = fft_len-2
        self.rx_gain = rx_gain = 35.0
        self.center_frequency = center_frequency = 435e6
        self.bandwidth = bandwidth = sample_rate

        ##################################################
        # Blocks
        ##################################################

        self._rx_gain_range = qtgui.Range(0.0, 73.0, 1.0, 35.0, 200)
        self._rx_gain_win = qtgui.RangeWidget(self._rx_gain_range, self.set_rx_gain, "RX gain (PGA, dB)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._rx_gain_win, 1, 1, 1, 1)
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
        self.top_grid_layout.addWidget(self._center_frequency_tool_bar, 1, 0, 1, 1)
        for r in range(1, 2):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 1):
            self.top_grid_layout.setColumnStretch(c, 1)
        self._bandwidth_range = qtgui.Range(0.2e6, 4.0e6, 0.05e6, sample_rate, 200)
        self._bandwidth_win = qtgui.RangeWidget(self._bandwidth_range, self.set_bandwidth, "统一带宽 / 采样率 (S/s)", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_grid_layout.addWidget(self._bandwidth_win, 2, 0, 1, 2)
        for r in range(2, 3):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.soapy_custom_source_0 = None
        dev = 'driver=' + driver
        stream_args = ''
        tune_args = ['']
        settings = ['']
        self.soapy_custom_source_0 = soapy.source(dev, "fc32",
                                  1, pluto_uri,
                                  stream_args, tune_args, settings)
        self.soapy_custom_source_0.set_sample_rate(0, bandwidth)
        self.soapy_custom_source_0.set_bandwidth(0, bandwidth)
        self.soapy_custom_source_0.set_antenna(0, ('A_BALANCED' if driver == 'plutosdr' else 'TX/RX'))
        self.soapy_custom_source_0.set_frequency(0, center_frequency)
        self.soapy_custom_source_0.set_frequency_correction(0, 0)
        self.soapy_custom_source_0.set_gain_mode(0, agc)
        self.soapy_custom_source_0.set_gain(0, rx_gain)
        self.soapy_custom_source_0.set_dc_offset_mode(0, False)
        self.soapy_custom_source_0.set_dc_offset(0, 0)
        self.soapy_custom_source_0.set_iq_balance(0, 0)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            fft_len, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            bandwidth, #bw
            "Received baseband — visual OFDM (DC centred, DC nulled)", #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-140), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative amplitude', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(True)
        self.qtgui_freq_sink_x_0.enable_grid(True)
        self.qtgui_freq_sink_x_0.set_fft_average(0.2)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['Received baseband', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
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
        self.top_grid_layout.addWidget(self._qtgui_freq_sink_x_0_win, 0, 0, 1, 2)
        for r in range(0, 1):
            self.top_grid_layout.setRowStretch(r, 1)
        for c in range(0, 2):
            self.top_grid_layout.setColumnStretch(c, 1)
        self.fft_vxx_0 = fft.fft_vcc(fft_len, True, window.hann(fft_len), True, 1)
        self.epy_block_0 = epy_block_0.blk(fft_len=fft_len, sample_rate=bandwidth, subcarriers=subcarriers, max_rows=max_rows, console_report=console_report)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, fft_len)
        self.blocks_complex_to_mag_squared_0 = blocks.complex_to_mag_squared(fft_len)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_mag_squared_0, 0), (self.epy_block_0, 0))
        self.connect((self.blocks_stream_to_vector_0, 0), (self.fft_vxx_0, 0))
        self.connect((self.fft_vxx_0, 0), (self.blocks_complex_to_mag_squared_0, 0))
        self.connect((self.soapy_custom_source_0, 0), (self.blocks_stream_to_vector_0, 0))
        self.connect((self.soapy_custom_source_0, 0), (self.qtgui_freq_sink_x_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("gnuradio/flowgraphs", "receiveData_gnuradio")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sample_rate(self):
        return self.sample_rate

    def set_sample_rate(self, sample_rate):
        self.sample_rate = sample_rate
        self.set_bandwidth(self.sample_rate)

    def get_fft_len(self):
        return self.fft_len

    def set_fft_len(self, fft_len):
        self.fft_len = fft_len
        self.set_subcarriers(self.fft_len-2)
        self.fft_vxx_0.set_window(window.hann(self.fft_len))
        self.epy_block_0.fft_len = self.fft_len

    def get_driver(self):
        return self.driver

    def set_driver(self, driver):
        self.driver = driver
        self.soapy_custom_source_0.set_antenna(0, ('A_BALANCED' if self.driver == 'plutosdr' else 'TX/RX'))

    def get_pluto_uri(self):
        return self.pluto_uri

    def set_pluto_uri(self, pluto_uri):
        self.pluto_uri = pluto_uri

    def get_agc(self):
        return self.agc

    def set_agc(self, agc):
        self.agc = agc
        self.soapy_custom_source_0.set_gain_mode(0, self.agc)

    def get_max_rows(self):
        return self.max_rows

    def set_max_rows(self, max_rows):
        self.max_rows = max_rows
        self.epy_block_0.max_rows = self.max_rows

    def get_console_report(self):
        return self.console_report

    def set_console_report(self, console_report):
        self.console_report = console_report
        self.epy_block_0.console_report = self.console_report

    def get_subcarriers(self):
        return self.subcarriers

    def set_subcarriers(self, subcarriers):
        self.subcarriers = subcarriers
        self.epy_block_0.subcarriers = self.subcarriers

    def get_rx_gain(self):
        return self.rx_gain

    def set_rx_gain(self, rx_gain):
        self.rx_gain = rx_gain
        self.soapy_custom_source_0.set_gain(0, self.rx_gain)

    def get_center_frequency(self):
        return self.center_frequency

    def set_center_frequency(self, center_frequency):
        self.center_frequency = center_frequency
        Qt.QMetaObject.invokeMethod(self._center_frequency_line_edit, "setText", Qt.Q_ARG("QString", eng_notation.num_to_str(self.center_frequency)))
        self.soapy_custom_source_0.set_frequency(0, self.center_frequency)

    def get_bandwidth(self):
        return self.bandwidth

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth
        self.soapy_custom_source_0.set_bandwidth(0, self.bandwidth)
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.bandwidth)
        self.epy_block_0.sample_rate = self.bandwidth



def argument_parser():
    description = 'Visual OFDM monitor: Run opens the GNU Radio spectrum window (with a unified bandwidth slider that retunes the real sample rate) plus a top-down scrolling waterfall window drawn by the embedded python block.  No files written.'
    parser = ArgumentParser(description=description)
    parser.add_argument(
        "--sample-rate", dest="sample_rate", type=eng_float, default=eng_notation.num_to_str(float(500000)),
        help="Set Initial sample rate (S/s) [default=%(default)r]")
    parser.add_argument(
        "--fft-len", dest="fft_len", type=intx, default=512,
        help="Set OFDM FFT length [default=%(default)r]")
    parser.add_argument(
        "--driver", dest="driver", type=str, default='plutosdr',
        help="Set Soapy driver (plutosdr/hackrf) [default=%(default)r]")
    parser.add_argument(
        "--pluto-uri", dest="pluto_uri", type=str, default='',
        help="Set Soapy URI (empty = auto) [default=%(default)r]")
    parser.add_argument(
        "--agc", dest="agc", type=intx, default=0,
        help="Set Use hardware AGC (Pluto only) [default=%(default)r]")
    parser.add_argument(
        "--max-rows", dest="max_rows", type=intx, default=4096,
        help="Set Row ring size (console quality only) [default=%(default)r]")
    parser.add_argument(
        "--console-report", dest="console_report", type=intx, default=1,
        help="Set Print status every 2 s [default=%(default)r]")
    return parser


def main(top_block_cls=receiveData_gnuradio, options=None):
    if options is None:
        options = argument_parser().parse_args()

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls(sample_rate=options.sample_rate, fft_len=options.fft_len, driver=options.driver, pluto_uri=options.pluto_uri, agc=options.agc, max_rows=options.max_rows, console_report=options.console_report)

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
