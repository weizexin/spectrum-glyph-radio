# ADALM-Pluto 发射

使用 GNU Radio + SoapyPlutoSDR，将文字、内置汉字或图片映射为子载波并循环发射。

## 启动

在已激活的 GNU Radio 3.10 环境中，进入本目录：

```shell
python sendData_gnuradio_ui.py
```

或打开 `sendData_gnuradio.grc` 并点击 Run。它会调用同目录 UI；生成的 `sendData_gnuradio.py` 不是此界面的启动入口。

**窗口加载完成即开始发射。** 当前默认值为 435 MHz、500 kS/s、FFT 512、Soapy TX gain 89。增益沿用原工程设置，应结合本机驱动确认含义，并在启动前安排好负载或衰减。

默认文字模式读取 `transmit.txt` 全文，可多行编辑或导入文本；内置汉字模式读取 `hanzi.m` 中 B1～B6 的十六进制字模，无需 MATLAB；图片模式默认读取 `RandomMan.jpg`。

## 文件

| 文件 | 用途 |
| --- | --- |
| `sendData_gnuradio.grc` | GRC 入口，Run 启动 UI |
| `sendData_gnuradio_ui.py` | 实际界面、波形源和硬件流图 |
| `sendData_gnuradio.py` | GRC 生成的顶层代码 |
| `sendData_gnuradio_epy_block_0.py` | GRC 内嵌波形源的导出副本 |
| `hanzi.m` | 字模数据 |
| `transmit.txt` | UTF-8 多行演示文字 |
| `RandomMan.jpg` | 默认图片 |

程序通过 Soapy 自动枚举 Pluto；需要固定设备时查看 UI 顶部 `PLUTO_URI`。发射采用复数 8 位 IQ（CS8）路径。配套资源按程序目录定位，建议始终从本目录启动 GRC。

占用子载波选择值默认 2048，但会限制到小于 FFT 的最大偶数；FFT 512 时实际为 510。接收端需匹配中心频率、采样率和 FFT。使用 HackRF 接收时，建议先将本端采样率设为 2 MS/s，再给接收端设置相同速率。

关闭时使用窗口关闭按钮。设备打开失败先检查是否被其他 SDR 程序占用；收不到信号时确认发射接 TX、接收接 RX，并核对双方参数。基带预览无法代替空口验证。

参见 [项目首页](../README.md)、[环境配置](../docs/environment.md) 和 [维护说明](../docs/maintenance.md)。
