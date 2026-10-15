"""Embedded Python block of the ADALM-PLUTO receiver flowgraph (monitor only).

Input : Mag^2 power rows with ``fft_len`` bins (DC centred, DC bin nulled).
Output: none.

What it does
------------
* keeps a small thread-safe ring of recent power rows and prints a one-line
  link-quality report to the console every 2 s (works headless);
* owns a Qt window that draws a waterfall scrolling **top-down**: the newest
  spectrum row enters at the top and older rows move down.  GNU Radio's own
  ``qtgui.waterfall_sink_x`` can only scroll bottom-up and has no direction
  switch, so this window is drawn in Python (matplotlib canvas inside the
  flowgraph's Qt application).  The spectrum curve meanwhile stays the stock
  QT GUI Frequency Sink in the main window and does not scroll;
* watches its own ``sample_rate`` attribute: the unified bandwidth slider in
  the main GRC window rewires it, and this block then retunes the Soapy
  device (``set_sample_rate``) so hardware, spectrum and waterfall all follow
  that one slider.  No images are ever written to disk.

The window is created on the main thread while the top block is constructed,
so the QApplication of the Qt-GUI flowgraph already exists; without a Qt
application the block degrades to console-only output.
"""

import collections
import threading
import time

import numpy as np
from gnuradio import gr

SCROLL_ROWS = 400          # displayed rows kept in the scrolling window
SCROLL_SECONDS = 15.0      # wall-clock span the window covers
DB_MIN, DB_MAX = -110.0, -35.0


def to_db(power):
    return 10.0 * np.log10(np.maximum(power, 1e-20))


def contrast_db(power):
    """Per-bin median baseline removal: LO leakage / noise floor flatten out."""
    db = to_db(power)
    return db - np.median(db, axis=0)[None, :]


def band_span(fft_len, subcarriers):
    """Occupied subcarrier count (the TX leaves DC empty, halves both sides)."""
    span = subcarriers if subcarriers > 0 else fft_len - 2
    return max(2, min(int(span), fft_len - 2))


def estimate_quality(power, average=16):
    """Contrast of the received rows in dB (>= 6 dB counts as "signal").

    A single FFT block has an exponentially distributed power spectrum, so a
    per-block p99.9-median contrast is ~10 dB even for pure noise.  Averaging
    a few blocks in time shrinks the noise fluctuation as 1/sqrt(K) while the
    deterministic picture rows stay put: ~3 dB on noise, > 20 dB on a real
    line-scan transmission.
    """
    if power.shape[0] == 0:
        return 0.0
    average = max(1, min(int(average), power.shape[0]))
    usable = power.shape[0] - power.shape[0] % average
    if usable == 0:
        return 0.0
    averaged = power[:usable].reshape(-1, average, power.shape[1]).mean(axis=1)
    return float(np.percentile(contrast_db(averaged), 99.9))


class _WaterfallWindow:
    """Qt window holding one waterfall that scrolls from top to bottom."""

    def __init__(self, block):
        from PyQt5 import QtCore, QtWidgets
        import matplotlib
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        from matplotlib.figure import Figure

        self._QtCore = QtCore
        self._block = block
        self.rate = float(block.sample_rate)
        self.fft_len = int(block.fft_len)
        self.display = np.full((SCROLL_ROWS, self.fft_len), DB_MIN,
                               dtype=np.float32)

        matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei",
                                                  "DejaVu Sans"]
        matplotlib.rcParams["axes.unicode_minus"] = False
        self.figure = Figure(figsize=(9.4, 5.6), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle("接收瀑布图 — 自上而下滚动 (GNU Radio)")
        self.window.resize(960, 620)
        self.window.setCentralWidget(self.canvas)

        self.axis = self.figure.add_subplot(1, 1, 1)
        self.image = self.axis.imshow(
            self.display, origin="upper", aspect="auto", cmap="turbo",
            vmin=DB_MIN, vmax=DB_MAX, interpolation="nearest",
            extent=self._extent())
        self.axis.set_xlabel("相对中心频率 (MHz)")
        self.axis.set_ylabel("时间（新数据在顶部，%d 行 ≈ %.0f s）"
                             % (SCROLL_ROWS, SCROLL_SECONDS))
        self.status = self.figure.suptitle("等待数据…", fontsize=10)
        self.figure.subplots_adjust(left=0.10, right=0.97, top=0.90,
                                    bottom=0.10)

        self.timer = QtCore.QTimer()
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.redraw)
        self.timer.start()

    def _extent(self):
        half = self.rate / 2.0 / 1e6
        return (-half, half, SCROLL_SECONDS, 0.0)

    def show(self):
        self.window.show()

    def redraw(self):
        """Timer callback - runs in the Qt main thread only."""
        rows = self._block.take_display_rows()
        if rows:
            # Rows arrive oldest-first; the newest one goes to the top.
            fresh = np.asarray(rows, dtype=np.float32)[::-1]
            self.display = np.concatenate((fresh, self.display),
                                          axis=0)[:SCROLL_ROWS]
            self.image.set_data(self.display)
        if abs(self.rate - float(self._block.sample_rate)) > 1.0:
            self.rate = float(self._block.sample_rate)
            self.image.set_extent(self._extent())
        self.status.set_text(self._block.status())
        self.canvas.draw_idle()

    def save_figure(self, path):
        """Test-driver helper only; the program itself never saves files."""
        self.canvas.draw()
        self.figure.savefig(path, dpi=110)

    def close(self):
        self.timer.stop()
        self.window.close()


class blk(gr.sync_block):
    """Monitor block: row ring + top-down waterfall + sample-rate follow."""

    def __init__(self, fft_len=512, sample_rate=500000, subcarriers=510,
                 max_rows=4096, console_report=1):
        gr.sync_block.__init__(
            self, name="Waterfall display (top-down)",
            in_sig=[(np.float32, int(fft_len))], out_sig=None)
        self.fft_len = int(fft_len)
        self.sample_rate = float(sample_rate)
        self.subcarriers = int(subcarriers)
        self.max_rows = max(64, int(max_rows))
        self.console_report = int(console_report)
        self._source = None
        # Match the FFT window used in the flowgraph (periodic Hann).
        window = np.hanning(self.fft_len + 1)[:-1].astype(np.float32)
        self._normalization = float(np.sum(window ** 2)) * self.fft_len

        self._ring = np.zeros((self.max_rows, self.fft_len), dtype=np.float32)
        self._ring_fill = 0
        self._ring_total = 0
        self._lock = threading.Lock()
        self._display_rows = collections.deque()
        self._status = "等待数据…"
        self._applied_rate = float(sample_rate)
        self._next_rate_apply = 0.0
        self._next_report = time.time() + 2.0
        self._acc = np.zeros(self.fft_len, dtype=np.float32)
        self._acc_count = 0

        self.window = None
        try:
            from PyQt5 import QtWidgets
            if QtWidgets.QApplication.instance() is not None:
                self.window = _WaterfallWindow(self)
                self.window.show()
                print("[*] 瀑布窗口已打开：新行从顶部进入、向下滚动"
                      "（原生 Qt 瀑布只能从下往上，这里自己画）", flush=True)
            else:
                print("[!] 没有 QApplication：瀑布窗口未开，只做控制台输出",
                      flush=True)
        except Exception as error:                      # pragma: no cover
            print("[!] 创建瀑布窗口失败：%s" % error, flush=True)
            self.window = None

    # ------------------------------------------------------------------ work
    def rows_per_display(self):
        """How many raw FFT rows are averaged into one displayed row."""
        rows_per_second = max(1e-6, float(self.sample_rate) / self.fft_len)
        return max(1, int(round(rows_per_second * SCROLL_SECONDS / SCROLL_ROWS)))

    def work(self, input_items, output_items):
        block = input_items[0]
        if block.size:
            # Undo the FFT window scaling once, here, for everybody else.
            block = block / self._normalization
            with self._lock:
                for row in block:
                    self._ring[self._ring_fill] = row
                    self._ring_fill = (self._ring_fill + 1) % self.max_rows
                    self._ring_total += 1
            self._acc += block.sum(axis=0)
            self._acc_count += block.shape[0]
            need = self.rows_per_display()
            if self._acc_count >= need:
                display_row = to_db(self._acc / self._acc_count)
                self._acc = np.zeros(self.fft_len, dtype=np.float32)
                self._acc_count = 0
                with self._lock:
                    self._display_rows.append(display_row)
                    while len(self._display_rows) > 4 * SCROLL_ROWS:
                        self._display_rows.popleft()
        if time.time() >= self._next_report:
            self._report()
        self._follow_rate()
        return len(block)

    # ------------------------------------------------------------ cross-thread
    def take_display_rows(self):
        with self._lock:
            rows = list(self._display_rows)
            self._display_rows.clear()
        return rows

    def status(self):
        return self._status

    def _recent_rows(self):
        with self._lock:
            total = self._ring_total
            fill = self._ring_fill
            if total < self.max_rows:
                return self._ring[:total].copy()
            return np.concatenate((self._ring[fill:], self._ring[:fill]),
                                  axis=0)

    # ---------------------------------------------------------------- helpers
    def _find_source(self):
        """Locate the Soapy source instance of this flowgraph.

        GRC evaluates every python-block parameter in the *variable*
        namespace, so a block reference cannot be passed in as a parameter
        ("name 'self' is not defined").  The Qt-GUI flowgraph itself, however,
        is a QWidget created before its blocks, and GRC stores each block on
        it as an attribute - so walk the Qt widget list, which the block can
        reach from any thread, and pick the one carrying the source.
        """
        try:
            from PyQt5 import QtWidgets
        except Exception:                                # pragma: no cover
            return None
        application = QtWidgets.QApplication.instance()
        if application is None:
            return None
        seen = []
        for widget in list(application.topLevelWidgets()) + \
                list(application.allWidgets()):
            if widget in seen:
                continue
            seen.append(widget)
            source = getattr(widget, "soapy_custom_source_0", None)
            if source is not None:
                return source
        return None

    def _report(self):
        self._next_report = time.time() + 2.0
        rows = self._recent_rows()
        if rows.shape[0] < 8:
            self._status = "采样率 %.3f MS/s — 等待数据" % (self.sample_rate / 1e6)
        else:
            contrast = estimate_quality(rows)
            verdict = "收到信号" if contrast >= 6.0 else "未见信号"
            self._status = ("采样率 %.3f MS/s · 对比度 p99.9 = %.1f dB · %s"
                            % (self.sample_rate / 1e6, contrast, verdict))
        if self.console_report:
            print("[*] " + self._status, flush=True)

    def _follow_rate(self):
        """Retune the hardware after the unified bandwidth slider moves."""
        target = float(self.sample_rate)
        if abs(target - self._applied_rate) < 1.0:
            return
        now = time.time()
        if now < self._next_rate_apply:            # debounce while dragging
            return
        self._next_rate_apply = now + 0.5
        if self._source is None:
            self._source = self._find_source()
            if self._source is None:
                print("[!] 找不到 Soapy 源：滑动条只改显示范围，硬件采样率不变",
                      flush=True)
        try:
            if self._source is not None:
                self._source.set_sample_rate(0, target)
            self._applied_rate = target
            print("[*] 统一带宽 -> %.3f MS/s（硬件采样率已跟随）"
                  % (target / 1e6), flush=True)
        except Exception as error:                       # pragma: no cover
            print("[!] 设置采样率失败：%s" % error, flush=True)
