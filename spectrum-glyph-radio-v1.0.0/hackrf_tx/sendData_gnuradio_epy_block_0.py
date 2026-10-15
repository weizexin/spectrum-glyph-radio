"""Self-contained source for the active Hanzi MATLAB Function branch."""
from pathlib import Path
import re
import sys
import numpy as np
from gnuradio import gr
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QImage, QPainter

PROJECT_DIR = Path(globals().get("__file__", Path.cwd() / "_")).resolve().parent
class blk(gr.sync_block):
    """Visual OFDM source with a DC-null, centred occupied band."""

    def __init__(self, fft_len=4096, amplitude=7.0, row_hold_ms=15,
                 active_subcarriers=256, payload_mode=0,
                 text_message='你好，GNU Radio', font_family='Microsoft YaHei',
                 pixel_size=32, image_path='', sample_rate=4096000):
        gr.sync_block.__init__(self, name="Visual OFDM source", in_sig=None, out_sig=[np.complex64])
        self._ready = False
        self.fft_len = int(fft_len)
        self.amplitude = float(amplitude)
        self.row_hold_ms = float(row_hold_ms)
        self.active_subcarriers = int(active_subcarriers)
        self.payload_mode = int(payload_mode)
        self.text_message = str(text_message)
        self.font_family = str(font_family)
        self.pixel_size = int(pixel_size)
        self.image_path = str(image_path)
        self.sample_rate = float(sample_rate)
        self._row_index = 0
        self._repeat_index = 0
        self._sample_offset = 0
        self._ready = True
        self._rebuild()

    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)
        if name in ('fft_len', 'amplitude', 'row_hold_ms', 'active_subcarriers',
                    'payload_mode', 'text_message', 'font_family', 'pixel_size',
                    'image_path', 'sample_rate') and getattr(self, '_ready', False):
            self._rebuild()

    def _payload(self):
        candidates = (Path.cwd() / "hanzi.m",
                      Path(sys.argv[0]).resolve().parent / "hanzi.m",
                      PROJECT_DIR / "hanzi.m")
        hanzi_file = next((path for path in candidates if path.is_file()), candidates[-1])
        source = hanzi_file.read_text(encoding="utf-8")
        groups = re.findall(r"B[1-6]\s*=\s*\[(.*?)\];", source, flags=re.DOTALL)
        if len(groups) != 6:
            raise RuntimeError("Cannot read B1...B6 from " + str(hanzi_file))
        glyphs = []
        for group in groups:
            packed = np.asarray([int(x, 16) for x in re.findall(r"0x[0-9a-fA-F]{2}", group)], dtype=np.uint8)
            glyphs.append(np.unpackbits(packed).reshape(32, 32).astype(np.float32))
        text = np.hstack(glyphs)
        padded = np.zeros((32, 256), dtype=np.float32)
        padded[:, 32:224] = text
        return np.vstack((np.zeros((16, 256), dtype=np.float32), padded))

    @staticmethod
    def _array_from_qimage(image):
        image = image.convertToFormat(QImage.Format_Grayscale8)
        ptr = image.bits()
        ptr.setsize(image.byteCount())
        rows = np.frombuffer(ptr, dtype=np.uint8).reshape(image.height(), image.bytesPerLine())
        return rows[:, :image.width()].astype(np.float32) / 255.0

    @staticmethod
    def _fit_width(image, width):
        if image.shape[1] == width:
            return image
        column_map = np.rint(np.linspace(0, image.shape[1] - 1, width)).astype(int)
        return image[:, column_map]

    def _text_payload(self, width):
        height = int(self.pixel_size)
        image = QImage(width, height, QImage.Format_ARGB32)
        image.fill(0)
        painter = QPainter(image)
        painter.setPen(QColor(255, 255, 255))
        font = QFont(str(self.font_family))
        font.setPixelSize(max(1, height - 2))
        painter.setFont(font)
        painter.drawText(0, height - 2, str(self.text_message))
        painter.end()
        return np.pad(self._array_from_qimage(image), ((2, 2), (0, 0)))

    def _image_payload(self, width):
        image_path = Path(self.image_path)
        if not image_path.is_absolute():
            image_path = Path(sys.argv[0]).resolve().parent / image_path
        image = QImage(str(image_path))
        if image.isNull():
            raise RuntimeError('Cannot open image: ' + str(self.image_path))
        image = image.convertToFormat(QImage.Format_Grayscale8)
        image = image.scaledToWidth(width, Qt.SmoothTransformation)
        return np.pad(self._array_from_qimage(image), ((2, 2), (0, 0)))

    def _rebuild(self):
        fft_len = int(self.fft_len)
        if fft_len < 512 or fft_len & (fft_len - 1):
            raise ValueError('FFT length must be a power of two and at least 512')
        width = int(self.active_subcarriers)
        if width < 2 or width > fft_len - 1:
            raise ValueError('Occupied subcarrier count does not fit in this FFT length')
        width -= width % 2  # Equal negative/positive halves; DC remains unused.
        if int(self.payload_mode) == 1:
            payload = self._text_payload(width)
        elif int(self.payload_mode) == 2:
            payload = self._image_payload(width)
        else:
            payload = self._fit_width(self._payload(), width)
        frequency_rows = np.zeros((payload.shape[0], fft_len), dtype=np.float32)
        left = width // 2
        right = width - left
        # Native IFFT ordering: [DC, +f ... -f].  Split the picture
        # about DC instead of wrapping it across index zero.  A receiver
        # that displays fftshift(fft(x)) sees one centred, contiguous image.
        frequency_rows[:, fft_len-left:fft_len] = payload[:, :left] * float(self.amplitude)
        frequency_rows[:, 1:1+right] = payload[:, left:] * float(self.amplitude)
        # Blank picture rows stay exact digital zeros: the RF output drops
        # to the leakage floor there, so the gaps between picture lines are
        # silent and stay dark in a receive waterfall.  Only the overall
        # scale is normalised, which preserves every row-to-row ratio.
        self._symbols = np.fft.ifft(frequency_rows.astype(np.complex64),
                                    axis=1).astype(np.complex64)
        peak = float(np.max(np.abs(self._symbols)))
        if peak > 0.9:
            self._symbols *= np.float32(0.9 / peak)
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
        self._row_order = list(range(self._symbols.shape[0] - 1, 0, -1))
        self._row_index = self._repeat_index = self._sample_offset = 0

    def work(self, input_items, output_items):
        output = output_items[0]
        written = 0
        while written < len(output):
            symbol = self._symbols[self._row_order[self._row_index]]
            count = min(len(output) - written, int(self.fft_len) - self._sample_offset)
            output[written:written + count] = symbol[self._sample_offset:self._sample_offset + count]
            written += count
            self._sample_offset += count
            if self._sample_offset == int(self.fft_len):
                self._sample_offset = 0
                self._repeat_index += 1
                repeats = max(1, int(round(self.row_hold_ms * self.sample_rate / (1000.0 * self.fft_len))))
                if self._repeat_index == repeats:
                    self._repeat_index = 0
                    self._row_index = (self._row_index + 1) % len(self._row_order)
        return written