# GNU Radio 频谱与瀑布接收

默认使用 Pluto，通过 Soapy Source 接收 IQ；一路显示 GNU Radio 频谱，另一路经 FFT、功率计算送入内嵌 Python 块，显示自上而下滚动的瀑布图。此工具不保存采集文件。

## 启动

在本目录打开 `receiveData_gnuradio.grc` 并点击 Run，或在激活的 GNU Radio 环境中运行：

```shell
python receiveData_gnuradio.py
```

默认 435 MHz、500 kS/s、FFT 512，与 Pluto 发射默认值相同。接收 HackRF 默认发射信号时：

```shell
python receiveData_gnuradio.py --sample-rate 2000000 --fft-len 512
```

若发射端修改了 FFT，命令中的 `--fft-len` 也需对应修改。GRC 中修改参数后需要重新生成并启动。

主窗口提供中心频率、RX 增益、统一带宽/采样率三个控件；带宽滑条同时影响硬件采样率、模拟带宽和频谱范围。瀑布窗口最新数据从顶部进入，历史向下滚动。终端会周期性打印信号对比度估计，该数值用于辅助观察，不能代替实际字形判断。

```shell
python receiveData_gnuradio.py --help
```

该接收工程主要面向 Pluto。`--driver` 虽保留 HackRF 选项，但增益控件按 Pluto 设计，未提供 HackRF 的 LNA/VGA/AMP 分级控制。

## 维护

`receiveData_gnuradio.py` 与 `receiveData_gnuradio_epy_block_0.py` 为 GRC 生成结果；`_build_grc.py` 可把内嵌块源码嵌回流图。修改方式与覆盖关系见 [维护说明](../docs/maintenance.md)。
