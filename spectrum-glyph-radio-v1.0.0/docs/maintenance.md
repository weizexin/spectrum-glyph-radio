# 维护说明

## 工程结构

| 目录 | 用途 |
| --- | --- |
| `pluto_tx` | ADALM-Pluto 发射，包含配套字模、图片与演示文字 |
| `hackrf_tx` | HackRF One 发射，包含配套字模、图片与演示文字 |
| `pluto_rx` | Pluto 的 GNU Radio 频谱 / 瀑布接收工程 |

两套发射目录可独立复制使用。目录内同名 Python 模块分别属于不同设备工程，运行时保持各自配套文件在一起。

## 修改入口

| 文件 | 维护方式 |
| --- | --- |
| `sendData_gnuradio_ui.py` | 实际发射界面、波形源与设备控制 |
| `sendData_gnuradio.grc` | 发射 GRC 入口，Run 调用同目录 UI |
| `sendData_gnuradio.py` | 发射 GRC 生成结果，重新生成会覆盖 |
| `sendData_gnuradio_epy_block_0.py` | 发射 GRC 内嵌块导出副本 |
| `receiveData_gnuradio.grc` | 接收流图，可通过 GRC 编辑 |
| `receiveData_gnuradio.py` | 接收 GRC 生成的顶层程序 |
| `receiveData_gnuradio_epy_block_0.py` | 接收瀑布显示、状态指标和采样率跟随 |
| `_build_grc.py` | 接收流图构造脚本，将内嵌块源码写入 `.grc` |

发射自定义 UI 与 GRC 内嵌源分别维护。修改 GRC 画布参数不会自动改变 UI 的默认设置；项目首页的参数表以 UI 为准。直接运行生成的发射 `.py` 也不会经过自定义 UI。

如果使用接收构造脚本维护流图，在 `pluto_rx` 目录执行：

```shell
python _build_grc.py
grcc -d . receiveData_gnuradio.grc
```

第一步会覆盖同目录 `.grc`，执行前保存需要保留的手动修改。第二步将流图重新生成为 Python。

## 版本与验证

当前发布版本为 **v1.0.0**，项目已由维护者验证可用。发布记录见 [CHANGELOG](../CHANGELOG.md)。

发布整理保持信号处理与硬件参数不变，并核对文件结构、文档路径、Python 与流图内嵌代码语法。环境、设备增益、USB 带宽和字体可用性会影响实际效果，移植时请按本机设备核对。

## 发布到 GitHub

将项目文件夹内的内容作为仓库根目录上传，GitHub 首页将显示 `README.md`。ZIP 压缩包包含一个顶层项目目录，解压后进入该目录上传内容即可。

使用 Git 时，在项目目录运行：

```shell
git init
git add .
git commit -m "Release v1.0.0"
```

之后按新建 GitHub 仓库页面的提示关联远程仓库并推送。版本发布可使用标签 `v1.0.0`；更新版本时同步维护首页版本号和 `CHANGELOG.md`。

## 许可证与素材

本项目中 BI1WJD 的原创内容采用 **CC BY-SA 4.0**，版权所有者署名为 **BI1WJD**，版权年份为 2026。完整协议见 [LICENSE](../LICENSE)，署名信息见 [NOTICE](../NOTICE)，中文协议摘要见 [Creative Commons 官网](https://creativecommons.org/licenses/by-sa/4.0/deed.zh)。

`RandomMan.jpg` 与 `hanzi.m` 沿用原工程素材。第三方素材如有单独授权条件，应按其原有许可使用；本项目的许可声明不改变第三方素材的权利归属。
