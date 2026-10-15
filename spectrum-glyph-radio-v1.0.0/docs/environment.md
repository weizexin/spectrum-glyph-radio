# 环境配置

## 推荐环境

使用包含 GNU Radio 3.10 的 Radioconda，在它提供的命令行环境内运行项目。原工程使用 GNU Radio 3.10.12 / Python 3.12；其他版本和平台需要自行验证驱动与 Qt 兼容性。不要使用系统中另一个 Python 启动这些脚本。

项目依赖包含原生库、硬件驱动及 Qt 插件，不能仅靠 `pip install` 完成部署，因此未提供声称可一键安装的 `requirements.txt`。

| 组件 | 用途 |
| --- | --- |
| GNU Radio 3.10，含 `gr-soapy`、`qtgui` | 发射和 GNU Radio 接收 |
| SoapySDR | 统一设备访问，供 GNU Radio Soapy 模块使用 |
| SoapyPlutoSDR、libiio 与 Pluto 驱动 | Pluto 设备访问 |
| SoapyHackRF、libhackrf 与 USB 驱动 | HackRF 设备访问 |
| NumPy、PyQt5、PyQt5 的 sip 模块 | 波形计算与界面 |
| Matplotlib | `pluto_rx` 自绘瀑布窗口 |
| PyYAML | 维护时运行 `_build_grc.py` |

仅使用一种设备时可只配置该设备对应的 Soapy 插件。确认 USB/网络连接与系统驱动正常后再运行流图。

## 检查当前环境

以下导入检查不启动发射：

```shell
python -c "import sys; print(sys.executable); from PyQt5 import Qt; import sip; import numpy; from gnuradio import gr, blocks, qtgui, soapy; print('GNU Radio / Qt / Soapy imports OK')"
python -c "import matplotlib, yaml; print('Receiver / builder imports OK')"
SoapySDRUtil --info
SoapySDRUtil --find="driver=plutosdr"
SoapySDRUtil --find="driver=hackrf"
```

只需枚举所用设备；设备正被其他程序占用时先正常关闭该程序。若找不到驱动模块，检查当前环境内是否已安装对应 Soapy 插件，而不只是 SoapySDR 核心库。

## 常见问题

- Qt 插件或 DLL 错误：使用同一个激活环境中的 Python、GNU Radio 和 PyQt5；避免混用另一套 SDR 软件附带的 Qt。
- 字体缺失：在发射界面选本机已有的中文字体；Linux 下的可用字体可能与 Windows 不同。
- 接收画面被拉伸或错位：先核对采样率和 FFT，再检查 USB 丢样；降低速率或分开 USB 控制器。
- 接收流图默认面向 Pluto。虽然保留 `--driver hackrf` 参数，但其增益控件未提供 HackRF 分级增益调整。
