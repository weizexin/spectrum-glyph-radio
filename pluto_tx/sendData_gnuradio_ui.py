"""Compact Qt control window for the visual-OFDM Pluto transmitter.

This file is started by sendData_gnuradio.grc.  It intentionally owns the
controls instead of using GRC's variable-toolbars: Qt's stacked pages allow
text controls and image controls to appear only in their applicable mode.
"""

from pathlib import Path
import re
import sys
import threading

import numpy as np
# PyQt must be loaded before GNU Radio's Qt-dependent modules.  GRC-generated
# programs use this order too; reversing it mixes the Pothos Qt DLLs with this
# Python installation's PyQt platform plugin and prevents the "windows" plugin
# from starting.
from PyQt5 import Qt
import sip
from PyQt5.QtCore import Qt as QtCoreQt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QImage, QPainter
from gnuradio import blocks, gr, qtgui, soapy
from gnuradio.fft import window


HERE = Path(__file__).resolve().parent
HANZI_FILE = HERE / "hanzi.m"
DEFAULT_IMAGE = HERE / "RandomMan.jpg"
DEFAULT_TEXT_FILE = HERE / "transmit.txt"
AMPLITUDE = 7.0
# Blank picture rows are kept as exact digital zeros on purpose.  The RF output
# then falls to the leakage floor there, so the gaps between text lines are
# genuinely silent and never light up in a receive waterfall.  Measured on this
# Pluto: a stream that alternates lit and all-zero rows keeps transmitting
# indefinitely, so silence between rows is safe -- it is not what used to stop
# the transmitter (that was a zero TX gain, see the notes in README).
# Let SoapyPlutoSDR select the enumerated device.  This avoids pinning the
# package to an IP endpoint when the same Pluto is currently attached by USB.
PLUTO_URI = ""


def hanzi_payload():
    source = HANZI_FILE.read_text(encoding="utf-8")
    groups = re.findall(r"B[1-6]\s*=\s*\[(.*?)\];", source, flags=re.DOTALL)
    if len(groups) != 6:
        raise RuntimeError("Cannot read B1...B6 from " + str(HANZI_FILE))
    glyphs = []
    for group in groups:
        values = [int(x, 16) for x in re.findall(r"0x[0-9a-fA-F]{2}", group)]
        glyphs.append(np.unpackbits(np.asarray(values, dtype=np.uint8)).reshape(32, 32))
    text = np.hstack(glyphs).astype(np.float32)
    canvas = np.zeros((32, 256), dtype=np.float32)
    canvas[:, 32:224] = text
    return np.pad(canvas, ((16, 16), (0, 0)))


def qimage_array(image):
    image = image.convertToFormat(QImage.Format_Grayscale8)
    pointer = image.bits()
    pointer.setsize(image.byteCount())
    rows = np.frombuffer(pointer, dtype=np.uint8).reshape(image.height(), image.bytesPerLine())
    return rows[:, :image.width()].astype(np.float32) / 255.0


def text_payload(text, font_name, pixel_size, max_width):
    """Render every line in its own centred row.  Newlines are preserved."""
    text = text if text else " "
    font = QFont(font_name)
    font.setPixelSize(pixel_size)
    metrics = QFontMetrics(font)
    lines = text.splitlines() or [""]
    widths = [max(1, metrics.horizontalAdvance(line)) for line in lines]
    width = max(widths)
    if width > max_width:
        # The frequency payload cannot have more bins than the chosen FFT.
        width = max_width
    line_height = max(pixel_size, metrics.height())
    # QPainter does not reliably render onto 8-bit grayscale images on Windows;
    # paint on a 32-bit surface and convert to grayscale after drawing.
    image = QImage(width, line_height * len(lines), QImage.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    painter.setPen(QColor(255, 255, 255))
    painter.setFont(font)
    for index, line in enumerate(lines):
        x = max(0, (width - metrics.horizontalAdvance(line)) // 2)
        painter.drawText(x, (index + 1) * line_height - metrics.descent(), line)
    painter.end()
    return np.pad(qimage_array(image), ((2, 2), (0, 0)))


def image_payload(path):
    image = QImage(str(path))
    if image.isNull():
        raise RuntimeError("Cannot open image: " + str(path))
    # Image mode has a fixed 256-subcarrier horizontal raster by design.
    image = image.convertToFormat(QImage.Format_Grayscale8).scaledToWidth(256, QtCoreQt.SmoothTransformation)
    return np.pad(qimage_array(image), ((2, 2), (0, 0)))


class VisualOFDMSource(gr.sync_block):
    """Continuous source with a centred band and an unused DC carrier."""

    def __init__(self, fft_len=512, sample_rate=500000, row_hold_ms=6000,
                 active_subcarriers=510):
        gr.sync_block.__init__(self, name="Visual OFDM source", in_sig=None, out_sig=[np.complex64])
        self._lock = threading.RLock()
        self.fft_len = int(fft_len)
        self.sample_rate = float(sample_rate)
        self.row_hold_ms = float(row_hold_ms)
        self.active_subcarriers = int(active_subcarriers)
        self.mode = "hanzi"
        self.text = "你好，GNU Radio"
        self.font = "Microsoft YaHei"
        self.pixel_size = 32
        self.image_path = str(DEFAULT_IMAGE)
        self._symbols = np.zeros((1, self.fft_len), dtype=np.complex64)
        self._row_order = [0]
        self._row_index = self._repeat_index = self._sample_offset = 0
        self._rebuild()

    def configure(self, *, fft_len=None, sample_rate=None, row_hold_ms=None,
                  active_subcarriers=None,
                  mode=None, text=None, font=None, pixel_size=None, image_path=None):
        with self._lock:
            if fft_len is not None:
                self.fft_len = int(fft_len)
            if sample_rate is not None:
                self.sample_rate = float(sample_rate)
            if row_hold_ms is not None:
                self.row_hold_ms = float(row_hold_ms)
            if active_subcarriers is not None:
                self.active_subcarriers = int(active_subcarriers)
            if mode is not None:
                self.mode = str(mode)
            if text is not None:
                self.text = str(text)
            if font is not None:
                self.font = str(font)
            if pixel_size is not None:
                self.pixel_size = int(pixel_size)
            if image_path is not None:
                self.image_path = str(image_path)
            self._rebuild()

    def _rebuild(self):
        if self.fft_len < 512 or self.fft_len & (self.fft_len - 1):
            raise ValueError("FFT length must be a power of two and at least 512")
        if self.mode == "text":
            payload = text_payload(self.text, self.font, self.pixel_size, self.fft_len - 1)
        elif self.mode == "image":
            payload = image_payload(self.image_path)
        else:
            payload = hanzi_payload()
        self._row_dwell_ms = 100.0
        if self.mode == "text":
            font = QFont(self.font)
            font.setPixelSize(self.pixel_size)
            line_height = max(self.pixel_size, QFontMetrics(font).height())
            self._row_dwell_ms = max(100.0, self.row_hold_ms / line_height)
        width = min(max(2, self.active_subcarriers), self.fft_len - 1)
        width -= width % 2
        if payload.shape[1] != width:
            indices = np.rint(np.linspace(0, payload.shape[1] - 1, width)).astype(int)
            payload = payload[:, indices]
        left = width // 2
        right = width - left
        frequency = np.zeros((payload.shape[0], self.fft_len), dtype=np.float32)
        frequency[:, self.fft_len-left:] = payload[:, :left] * AMPLITUDE
        frequency[:, 1:1+right] = payload[:, left:] * AMPLITUDE
        # No carrier filler: blank rows stay exact zeros so the transmitter is
        # truly silent between the text lines.  Only the overall scale is
        # normalised, which keeps the Pluto's DAC inside full scale without
        # changing any row-to-row brightness ratio.
        self._symbols = np.fft.ifft(frequency.astype(np.complex64), axis=1).astype(np.complex64)
        peak = float(np.max(np.abs(self._symbols)))
        if peak > 0.5:
            self._symbols *= np.float32(0.5 / peak)
        # 峰值归一化会把稀疏文字/图像 OFDM 的平均功率压到 DAC 满量程以下约 30 dB
        # (峰均比)，空口链路因此收不到。这里把整体 RMS 提升到固定目标电平，再对
        # 极少数尖峰限幅(实测 <0.2% 样本)。整体乘同一增益: 行间亮度比例不变，
        # 空白行仍然是精确的数字零。
        rms = float(np.sqrt(np.mean(np.abs(self._symbols) ** 2)))
        if rms > 0:
            boost = min(0.10 / rms, 8.0)
            if boost > 1.0:
                self._symbols *= np.float32(boost)
                self._symbols.real = np.clip(self._symbols.real, -0.95, 0.95)
                self._symbols.imag = np.clip(self._symbols.imag, -0.95, 0.95)
        self._row_order = list(range(self._symbols.shape[0] - 1, -1, -1))
        self._row_index = self._repeat_index = self._sample_offset = 0

    def work(self, input_items, output_items):
        output = output_items[0]
        written = 0
        with self._lock:
            while written < len(output):
                symbol = self._symbols[self._row_order[self._row_index]]
                count = min(len(output) - written, self.fft_len - self._sample_offset)
                output[written:written + count] = symbol[self._sample_offset:self._sample_offset + count]
                written += count
                self._sample_offset += count
                if self._sample_offset == self.fft_len:
                    self._sample_offset = 0
                    self._repeat_index += 1
                    repetitions = max(1, round(self._row_dwell_ms * self.sample_rate / (1000 * self.fft_len)))
                    if self._repeat_index >= repetitions:
                        self._repeat_index = 0
                        self._row_index = (self._row_index + 1) % len(self._row_order)
        return written


class TransmitterWindow(Qt.QWidget):
    SAMPLE_RATES = (
        ("65.104 kS/s — Pluto minimum", 65104.1666667),
        ("125 kS/s", 125000), ("250 kS/s", 250000), ("500 kS/s", 500000),
        ("1.024 MS/s", 1024000), ("2.048 MS/s", 2048000),
        ("4.096 MS/s", 4096000), ("6.144 MS/s", 6144000), ("8.192 MS/s", 8192000),
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Visual OFDM — ADALM-PLUTO Transmitter")
        self.resize(1120, 1020)
        self._make_flowgraph()
        self._make_ui()
        self.mode.setCurrentIndex(1)
        self.apply_source()
        # Sync the radio to the widgets once before streaming, so the Pluto and
        # the on-screen values can never disagree at startup.
        self.apply_radio()
        self.flowgraph.start()
        # The GNU Radio waterfall defaults to putting new lines at the bottom.
        # Apply the reversed time axis only after the Qt plot is live so new
        # samples enter at the top and the history moves downward.
        self._tx_started = True
        Qt.QTimer.singleShot(250, self._set_waterfall_scroll_down)

    def _make_flowgraph(self):
        self.flowgraph = gr.top_block("Visual OFDM Pluto transmitter")
        self.source = VisualOFDMSource()
        self.tx_converter = blocks.complex_to_interleaved_char(True, 127.0)
        try:
            self.pluto = soapy.sink("driver=plutosdr", "sc8", 1, PLUTO_URI, "", [""], [""])
        except RuntimeError as error:
            # The Pluto is exclusive too; a second user makes the driver fail.
            raise RuntimeError(
                "无法打开 ADALM-Pluto（%s）。\n"
                "请关闭其它占用 Pluto 的程序（包括残留的 python.exe 进程）或拔插一次"
                " Pluto 的 USB 线，再重新启动。" % error)
        self.pluto.set_sample_rate(0, 500000)
        self.pluto.set_bandwidth(0, 700000)
        self.pluto.set_frequency(0, 435e6)
        self.pluto.set_gain(0, 89.0)
        self.spectrum = qtgui.freq_sink_c(512, window.WIN_BLACKMAN_hARRIS, 0, 500000,
                                           "Baseband spectrum — DC centred / DC nulled", 1, None)
        self.spectrum.set_update_time(0.10)
        # Autoscale cannot cope with this waveform: blank picture rows are exact
        # zeros, their FFT frames are -inf dB and they drag the auto range down to
        # about -390 dB, which draws the real band off-scale.  A fixed range keeps
        # the occupied band readable.
        self.spectrum.enable_autoscale(False)
        self.spectrum.enable_axis_labels(True)
        self.spectrum.enable_grid(True)
        self.spectrum.set_y_axis(-90.0, -60.0)
        self.spectrum.set_line_label(0, "OFDM baseband")
        self.waterfall = qtgui.waterfall_sink_c(
            512, window.WIN_BLACKMAN_hARRIS, 0, 500000,
            "Transmit waterfall (baseband)", 1, None)
        # One waterfall line per picture row keeps the glyphs undistorted: with
        # the default 100 ms update a 146 ms row is resampled at 0.68x, which
        # doubles and smears the text.  apply_source() refreshes this whenever
        # the row time or FFT length changes.
        self.waterfall.set_update_time(0.001)
        self.waterfall.enable_axis_labels(True)
        self.waterfall.enable_grid(False)
        # GNU Radio's Multi-Color palette is the familiar SDR waterfall theme
        # (dark blue -> cyan/green -> yellow/red) on a range
        # measured from the real baseband level: fully-lit subcarriers sit near
        # -64 dB and the anti-aliased glyph edges spread ~30 dB below that, so
        # the range has to cover them or the text breaks up into speckle.  This
        # is the darkest-backed colour map GNU Radio ships (Multi-Color's floor
        # is dark blue, so the text reads clearly like a normal SDR waterfall.
        self.waterfall.set_intensity_range(-94.0, -63.0)
        self.waterfall.set_color_map(0, qtgui.INTENSITY_COLOR_MAP_TYPE_MULTI_COLOR)
        self.waterfall.set_line_alpha(0, 1.0)
        self.waterfall.set_line_label(0, "OFDM baseband")
        self.waterfall.set_time_title("Time (newest at top; history downward)")
        self.flowgraph.connect(self.source, self.tx_converter, self.pluto)
        self.flowgraph.connect(self.source, self.spectrum)
        self.flowgraph.connect(self.source, self.waterfall)

    def _pluto_report(self):
        """Read the radio back: the Pluto keeps its settings between runs, so a
        stale low gain silently mutes the transmitter (0 in Soapy means maximum
        attenuation, not full power)."""
        try:
            gain = float(self.pluto.get_gain(0))
            rate = float(self.pluto.get_sample_rate(0))
            freq = float(self.pluto.get_frequency(0)) / 1e6
            return gain, rate, freq
        except Exception:
            return None

    def refresh_tx_status(self):
        report = self._pluto_report()
        if report is None:
            self.tx_status.setText("Pluto 状态: 读取失败")
            self.tx_status.setStyleSheet("color: #b3261e; font-weight: bold;")
            return
        gain, rate, freq = report
        if gain < 40.0:
            # 0-40 is nearly full attenuation on this driver: nothing radiates.
            self.tx_status.setText(
                "Pluto 状态: %.3f MHz, %.0f kS/s, TX gain %.1f dB — ⚠ 增益过低，几乎无输出（此驱动 89=满功率，0=静默）"
                % (freq, rate / 1e3, gain))
            self.tx_status.setStyleSheet("color: #b3261e; font-weight: bold;")
        else:
            self.tx_status.setText(
                "Pluto 状态: %.3f MHz, %.0f kS/s, TX gain %.1f dB — 正常发射中"
                % (freq, rate / 1e3, gain))
            self.tx_status.setStyleSheet("color: #1b7f3b;")

    @staticmethod
    def _spin(value, minimum, maximum, step, suffix=""):
        box = Qt.QDoubleSpinBox()
        box.setRange(minimum, maximum)
        box.setSingleStep(step)
        box.setValue(value)
        box.setDecimals(0 if step >= 1 else 2)
        box.setSuffix(suffix)
        return box

    def _make_ui(self):
        root = Qt.QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        radio = Qt.QGroupBox("Radio / OFDM")
        radio_form = Qt.QFormLayout(radio)
        radio_form.setLabelAlignment(QtCoreQt.AlignRight)
        radio_form.setHorizontalSpacing(12)
        radio_form.setVerticalSpacing(7)
        self.frequency = self._spin(435e6, 70e6, 6e9, 1e6, " Hz")
        self.sample_rate = Qt.QComboBox()
        for label, value in self.SAMPLE_RATES:
            self.sample_rate.addItem(label, value)
        self.sample_rate.setCurrentIndex(3)
        self.gain = self._spin(89, 0, 89, 0.25, " dB")
        self.active_subcarriers = Qt.QComboBox()
        for value in (256, 512, 1024, 2048):
            self.active_subcarriers.addItem(str(value), value)
        self.active_subcarriers.setCurrentText("2048")
        self.fft = Qt.QComboBox()
        for value in (512, 1024, 2048, 4096, 8192):
            self.fft.addItem(str(value), value)
        self.fft.setCurrentText("512")
        self.row_time = self._spin(6000, 1000, 10000, 100, " ms")
        radio_form.addRow("RF centre frequency", self.frequency)
        radio_form.addRow("Baseband sample rate", self.sample_rate)
        radio_form.addRow("Pluto TX gain", self.gain)
        radio_form.addRow("OFDM FFT length", self.fft)
        radio_form.addRow("Occupied subcarriers", self.active_subcarriers)
        radio_form.addRow("Text line display time", self.row_time)
        radio_form.addRow("TX / HackRF RX", Qt.QLabel(
            "Continuous loop | HackRF: match RF center, narrow span, raise RX gain gradually"))
        self.tx_status = Qt.QLabel("Pluto 状态: 初始化…")
        self.tx_status.setStyleSheet("color: #555;")
        radio_form.addRow("Transmit check", self.tx_status)
        root.addWidget(radio)

        payload_box = Qt.QGroupBox("Payload")
        payload_layout = Qt.QVBoxLayout(payload_box)
        mode_row = Qt.QHBoxLayout()
        mode_row.addWidget(Qt.QLabel("Transmit"))
        self.mode = Qt.QComboBox()
        self.mode.addItem("Built-in Hanzi", "hanzi")
        self.mode.addItem("Text", "text")
        self.mode.addItem("Image", "image")
        mode_row.addWidget(self.mode)
        mode_row.addStretch(1)
        payload_layout.addLayout(mode_row)
        self.pages = Qt.QStackedWidget()
        self.pages.addWidget(Qt.QLabel("Uses the original 6-character 32 × 32 Hanzi bitmap."))
        text_page = Qt.QWidget()
        text_form = Qt.QFormLayout(text_page)
        text_form.setLabelAlignment(QtCoreQt.AlignRight | QtCoreQt.AlignTop)
        self.text = Qt.QPlainTextEdit("你好，GNU Radio")
        self.text.setPlaceholderText("Enter text; Enter inserts a new line.")
        self.text.setMinimumHeight(110)
        if DEFAULT_TEXT_FILE.is_file():
            self.text.setPlainText(DEFAULT_TEXT_FILE.read_text(encoding="utf-8-sig"))
        self.font = Qt.QComboBox()
        for label, family in (("宋体", "SimSun"), ("微软雅黑", "Microsoft YaHei"), ("楷体", "KaiTi"), ("仿宋", "FangSong")):
            self.font.addItem(label, family)
        self.font.setCurrentIndex(1)
        self.pixel = Qt.QComboBox()
        self.pixel.addItem("16 × 16", 16)
        self.pixel.addItem("32 × 32", 32)
        self.pixel.setCurrentIndex(1)
        text_file_row = Qt.QHBoxLayout()
        self.text_file_label = Qt.QLabel(str(DEFAULT_TEXT_FILE))
        self.text_file_label.setTextInteractionFlags(QtCoreQt.TextSelectableByMouse)
        open_text = Qt.QPushButton("Open TXT")
        open_text.clicked.connect(self.open_text_file)
        save_text = Qt.QPushButton("Save TXT")
        save_text.clicked.connect(self.save_text_file)
        text_file_row.addWidget(self.text_file_label, 1)
        text_file_row.addWidget(open_text)
        text_file_row.addWidget(save_text)
        text_form.addRow("Text file", text_file_row)
        text_form.addRow("Text", self.text)
        text_form.addRow("Font", self.font)
        text_form.addRow("Glyph pixels", self.pixel)
        self.pages.addWidget(text_page)
        image_page = Qt.QWidget()
        image_row = Qt.QHBoxLayout(image_page)
        image_row.setContentsMargins(0, 0, 0, 0)
        self.image = Qt.QLineEdit(str(DEFAULT_IMAGE))
        self.image.setReadOnly(True)
        browse = Qt.QPushButton("Choose image…")
        browse.clicked.connect(self.choose_image)
        image_row.addWidget(self.image, 1)
        image_row.addWidget(browse)
        self.pages.addWidget(image_page)
        payload_layout.addWidget(self.pages)
        root.addWidget(payload_box)

        spectrum_widget = sip.wrapinstance(self.spectrum.qwidget(), Qt.QWidget)
        root.addWidget(spectrum_widget, 1)
        waterfall_widget = sip.wrapinstance(self.waterfall.qwidget(), Qt.QWidget)
        root.addWidget(waterfall_widget, 2)

        self._rebuild_timer = Qt.QTimer(self)
        self._rebuild_timer.setSingleShot(True)
        self._rebuild_timer.setInterval(250)
        self._rebuild_timer.timeout.connect(self.apply_source)
        self._status_timer = Qt.QTimer(self)
        self._status_timer.setInterval(1000)
        self._status_timer.timeout.connect(self.refresh_tx_status)
        self._status_timer.start()
        self.refresh_tx_status()
        self.frequency.valueChanged.connect(self.apply_radio)
        self.sample_rate.currentIndexChanged.connect(self.apply_radio)
        self.gain.valueChanged.connect(self.apply_radio)
        self.fft.currentIndexChanged.connect(self.schedule_source)
        self.active_subcarriers.currentIndexChanged.connect(self.schedule_source)
        self.row_time.valueChanged.connect(self.schedule_source)
        self.mode.currentIndexChanged.connect(self.on_mode_changed)
        self.text.textChanged.connect(self.schedule_source)
        self.font.currentIndexChanged.connect(self.schedule_source)
        self.pixel.currentIndexChanged.connect(self.schedule_source)

    def schedule_source(self):
        """Coalesce rapid payload edits into one waveform rebuild."""
        self._rebuild_timer.start()

    def choose_image(self):
        path, _ = Qt.QFileDialog.getOpenFileName(self, "Choose image", self.image.text(),
                                                   "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All files (*)")
        if path:
            self.image.setText(path)
            self.schedule_source()

    def open_text_file(self):
        path, _ = Qt.QFileDialog.getOpenFileName(
            self, "Open text file", self.text_file_label.text(), "Text files (*.txt);;All files (*)")
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError) as error:
            Qt.QMessageBox.warning(self, "Cannot open text file", str(error))
            return
        self.text_file_label.setText(path)
        self.text.setPlainText(content)
        self.mode.setCurrentIndex(1)
        self.on_mode_changed()

    def save_text_file(self):
        path, _ = Qt.QFileDialog.getSaveFileName(
            self, "Save text file", self.text_file_label.text(), "Text files (*.txt);;All files (*)")
        if not path:
            return
        if Path(path).suffix.lower() != ".txt":
            path += ".txt"
        try:
            Path(path).write_text(self.text.toPlainText(), encoding="utf-8", newline="")
        except OSError as error:
            Qt.QMessageBox.warning(self, "Cannot save text file", str(error))
            return
        self.text_file_label.setText(path)

    def on_mode_changed(self):
        self.pages.setCurrentIndex(self.mode.currentIndex())
        self.schedule_source()

    def apply_radio(self):
        rate = float(self.sample_rate.currentData())
        # Order matters on the Pluto: rate and bandwidth re-run the AD9361
        # filters, so apply them first and write frequency/gain last.
        self.pluto.set_sample_rate(0, rate)
        self.pluto.set_bandwidth(0, max(200000.0, min(3.5e6, rate)))
        self.pluto.set_frequency(0, self.frequency.value())
        self.pluto.set_gain(0, self.gain.value())
        self.spectrum.set_frequency_range(0, rate)
        self.waterfall.set_frequency_range(0, rate)
        if getattr(self, "_tx_started", False):
            Qt.QTimer.singleShot(0, self._set_waterfall_scroll_down)
        self.source.configure(sample_rate=rate)

    def _sync_waterfall_timing(self):
        """Keep the waterfall's line interval safely below one picture row so no
        row is ever skipped (skipped rows are what mottles the glyphs).  A line
        interval of half a row stretches the picture slightly but keeps every
        glyph edge sharp."""
        dwell = max(0.001, float(getattr(self.source, "_row_dwell_ms", 100.0)) / 1000.0)
        self.waterfall.set_update_time(dwell / 2.0)

    def _set_waterfall_scroll_down(self):
        """Put the newest line at the top and scroll history downward.  The slot
        signature is setYaxis(double,double) -- Q_ARG(float,...) invokes it
        with mismatched marshalling, which silently corrupts this plot's own
        frequency axis and wipes the frequency sink next to it."""
        form = sip.wrapinstance(self.waterfall.qwidget(), Qt.QWidget)
        plot = next(c for c in form.findChildren(Qt.QWidget)
                    if c.metaObject().className() == "WaterfallDisplayPlot")
        Qt.QMetaObject.invokeMethod(plot, "setYaxis", QtCoreQt.DirectConnection,
                                    Qt.Q_ARG("double", 200.0), Qt.Q_ARG("double", 0.0))

    def apply_source(self):
        try:
            self.source.configure(
                fft_len=int(self.fft.currentData()), row_hold_ms=self.row_time.value(),
                active_subcarriers=int(self.active_subcarriers.currentData()),
                mode=str(self.mode.currentData()), text=self.text.toPlainText(),
                font=str(self.font.currentData()), pixel_size=int(self.pixel.currentData()),
                image_path=self.image.text(), sample_rate=float(self.sample_rate.currentData()),
            )
            self._sync_waterfall_timing()
        except Exception as error:
            Qt.QMessageBox.warning(self, "Cannot update payload", str(error))

    def closeEvent(self, event):
        self.flowgraph.stop()
        self.flowgraph.wait()
        event.accept()


def main():
    app = Qt.QApplication(sys.argv)
    window = TransmitterWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
