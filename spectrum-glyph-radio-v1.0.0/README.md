# Spectrum Glyph Radio · 频谱字形发射

使用 **ADALM-Pluto 或 HackRF One**，把文字、汉字字模或图片转换为多载波信号并循环发射，让另一台 SDR 在瀑布图中看到字形和图案。项目基于 GNU Radio 3.10，包含两套设备发射工程和一套 Pluto 频谱 / 瀑布接收工程，已验证可用。

**版本：v1.0.0** · [环境配置](docs/environment.md) · [维护说明](docs/maintenance.md) · [版本记录](CHANGELOG.md)

图像的水平方向对应频率，垂直方向对应发送时间：每行像素映射为子载波幅度，经 IFFT 生成时域 IQ；接收端用 FFT 观察各频点亮度。DC 子载波留空，空白图像行输出数字零。这是一种视觉 OFDM 实验，并非带同步、编码和纠错的通用数据通信协议。

## 项目结构

```text
spectrum-glyph-radio/
├── README.md
├── CHANGELOG.md
├── LICENSE                    # CC BY-SA 4.0 完整条款
├── NOTICE                     # BI1WJD 署名信息
├── .gitignore
├── .gitattributes
├── docs/
│   ├── environment.md          # 环境配置与依赖检查
│   └── maintenance.md          # 文件来源、维护与发布说明
├── pluto_tx/                  # ADALM-Pluto 发射（自包含）
├── hackrf_tx/                 # HackRF One 发射（自包含）
└── pluto_rx/                  # GNU Radio 频谱 + 向下滚动瀑布
```

两套发射目录各保留 `.grc`、界面脚本、生成的 Python、内嵌块及配套载荷，可以分别复制使用。接收工程提供频谱与瀑布监视。

## 环境

建议使用带 GNU Radio 3.10 的 Radioconda 环境。需要 GNU Radio 的 Soapy、Qt GUI 模块，SoapySDR 及对应硬件插件、NumPy、PyQt5；接收工具另需 Matplotlib，接收流图构造脚本另需 PyYAML。安装与检查方法见 [环境说明](docs/environment.md)。

以下命令均在已激活的 SDR 环境中、从项目根目录运行。

## 快速开始

### 1. 选择发射设备

Pluto：

```shell
cd pluto_tx
python sendData_gnuradio_ui.py
```

HackRF One：

```shell
cd hackrf_tx
python sendData_gnuradio_ui.py
```

也可以在对应目录中打开 `sendData_gnuradio.grc`，点击 **Run**。发射流图的运行命令会启动同目录的 `sendData_gnuradio_ui.py`；它是实际操作入口，界面加载后会自动开始发射。

默认进入文字模式，读取同目录 `transmit.txt` 的完整 UTF-8 内容，支持多行。界面可切换内置汉字或图片模式；默认图片为 `RandomMan.jpg`。可调整中心频率、采样率、FFT、占用子载波数、增益、字体和显示时长。

### 2. 匹配接收参数

| 参数 | Pluto 发射默认值 | HackRF 发射默认值 |
| --- | --- | --- |
| 中心频率 | 435 MHz | 435 MHz |
| 采样率 | 500 kS/s | 2 MS/s |
| FFT 长度 | 512 | 512 |
| 占用子载波选择值 | 2048 | 2048 |
| 实际占用子载波数 | 510（受 FFT 限制） | 510（受 FFT 限制） |
| 文字行显示时长设置 | 6000 ms | 6000 ms |
| 发射增益 | Soapy gain 89 | VGA 47 dB、RF AMP 开 |

表中为当前界面脚本的默认值。占用子载波数会限制到小于 FFT 的最大偶数。文字行显示时长按字体行高换算为像素行停留时间，最小为 100 ms；图片与内置字模的像素行停留时间为 100 ms。

### 3. 观察瀑布图

使用另一台 Pluto 接收 HackRF 的默认发射信号：

```shell
cd pluto_rx
python receiveData_gnuradio.py --sample-rate 2000000 --fft-len 512
```

打开频谱窗口和自上而下滚动的瀑布窗口。接收 Pluto 默认发射信号时，该接收程序的默认采样率与 FFT 已匹配。也可从接收 `.grc` 启动；改变 FFT 后应重新生成并启动流图。

接收程序用于实时频谱 / 瀑布监视，不保存采集文件。默认使用 Pluto 接收；中心频率和增益可在主窗口中调整。

## 使用要点

- 发射和接收的中心频率、采样率、FFT 应一致；近似占用带宽为 `K × Fs / NFFT`，其中 K 是实际占用子载波数。
- 发射界面显示的是本机基带波形；空口效果需要另一台 SDR 接收确认。HackRF 为半双工设备。
- `hanzi.m` 作为字模数据读取，不需要 MATLAB；所选中文字体需在操作系统中可用。
- CS8 发射路径和增益取值沿用原工程适配；不同驱动版本的支持情况应以本机枚举、读回和接收结果为准。
- 仅在获准频率与合适的屏蔽条件下实验；现有发射默认增益较高，启动前安排好假负载或衰减。设备端口之间有线连接必须加入足够衰减。

更多操作见 [Pluto 发射](pluto_tx/README.md)、[HackRF 发射](hackrf_tx/README.md) 与 [Pluto 接收](pluto_rx/README.md)。

## 项目状态

项目已由维护者验证可用。发布版保留已验证的信号处理与硬件参数；不同操作系统、驱动和 USB 连接条件下，仍需核对设备支持的采样率、增益及实际接收效果。

## 许可证与署名

Copyright © 2026 **BI1WJD**。

本项目中 BI1WJD 的原创内容采用 **[知识共享 署名—相同方式共享 4.0 国际许可协议（CC BY-SA 4.0）](https://creativecommons.org/licenses/by-sa/4.0/deed.zh)**。允许分享和改编，包括商业用途；使用时须注明 BI1WJD、提供许可链接并说明修改，发布改编内容时须遵循协议的相同方式共享要求。

完整条款见 [LICENSE](LICENSE)，署名信息见 [NOTICE](NOTICE)。第三方素材保留其各自的权利和许可条件，详见 [维护说明](docs/maintenance.md)。
