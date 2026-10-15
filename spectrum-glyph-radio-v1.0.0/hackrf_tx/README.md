# HackRF One 发射

使用 GNU Radio + SoapyHackRF，将文字、内置汉字或图片映射为子载波并循环发射。

## 启动

在已激活的 GNU Radio 3.10 环境中，进入本目录：

```shell
python sendData_gnuradio_ui.py
```

或打开 `sendData_gnuradio.grc` 并点击 Run。它会调用同目录 UI；生成的 `sendData_gnuradio.py` 不是此界面的启动入口。

**窗口加载完成即开始发射。** 当前默认值为 435 MHz、2 MS/s、FFT 512、模拟滤波带宽 1.75 MHz、TX VGA 47 dB、RF AMP 开启。默认增益较高，启动前安排好负载或衰减。

默认文字模式读取 `transmit.txt` 全文，支持多行编辑或导入；内置字模读取 `hanzi.m`，无需 MATLAB；图片模式默认读取 `RandomMan.jpg`。本目录与 Pluto 发射目录具有相同的配套文件结构，可单独复制使用。

程序通过 Soapy 自动枚举 HackRF；需要指定设备时查看 UI 顶部 `HACKRF_DEVICE_ARGS`。发射采用复数 8 位 IQ（CS8）；采样率预设和滤波带宽联动，实际支持档位仍取决于设备与驱动。

占用子载波选择值默认 2048，但会限制到小于 FFT 的最大偶数；FFT 512 时实际为 510。用另一台 Pluto 接收本端默认信号，可在项目根目录运行：

```shell
python pluto_rx/receiveData_gnuradio.py --sample-rate 2000000 --fft-len 512
```

HackRF 是半双工设备，观察空口需要另一台 SDR。设备打开失败先正常关闭其他占用程序，再检查 USB 驱动；退出发射时使用窗口关闭按钮，以便正常释放设备。

参见 [项目首页](../README.md)、[环境配置](../docs/environment.md) 和 [维护说明](../docs/maintenance.md)。
