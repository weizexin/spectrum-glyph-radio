#!/usr/bin/env python3
"""One-shot builder: emits receiveData_gnuradio.grc.

The flowgraph is a Qt-GUI flowgraph: running it (Run in GRC, or
`python receiveData_gnuradio.py`) opens

  * the GNU Radio main window with the spectrum (QT GUI Frequency Sink),
    a centre-frequency box, an RX-gain slider and the **unified bandwidth
    slider** (it changes the real sample rate, so spectrum, waterfall and
    hardware all follow the same control), and
  * the top-down scrolling waterfall window owned by the embedded python
    block (GNU Radio's own waterfall sink can only scroll bottom-up).

    Soapy Source ─┬─> QT GUI Frequency Sink        (频谱, 主窗口内, 不滚动)
                  └─> StreamToVector -> FFT -> Mag² -> EPY block
                                                     (自绘瀑布, 自上而下滚动)

The generated flowgraph is a pure spectrum / waterfall monitor and does
not save captures or decode image frames.

The values the companion scripts override at start-up (sample rate, FFT
length, driver, URI, ...) stay "parameter" blocks so the generated top block
keeps accepting them as constructor keywords.
"""
import yaml
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / "receiveData_gnuradio_epy_block_0.py").read_text(encoding="utf-8")

FREQ_NAME = '"Received baseband — visual OFDM (DC centred, DC nulled)"'


def states(coordinate, state="enabled"):
    return {
        "bus_sink": False, "bus_source": False, "bus_structure": None,
        "coordinate": list(coordinate), "rotation": 0, "state": state,
    }


def block(name, bid, params, coordinate, state="enabled"):
    return {
        "name": name,
        "id": bid,
        "parameters": {
            **params,
            "affinity": "",
            "alias": "",
            "comment": "",
        },
        "states": states(coordinate, state),
    }


def variable(name, value, coordinate):
    # variable 块定义只有 value（+comment）；它会随其他变量求值，所以
    # `subcarriers = fft_len-2` 这类表达式只能写成 variable（parameter 块
    # 是逐个独立求值的，引用别的参数会报 NameError）。
    return {
        "name": name,
        "id": "variable",
        "parameters": {"value": value, "comment": ""},
        "states": states(coordinate),
    }


def parameter(name, label, ptype, value, coordinate):
    # parameter 块定义只有 label/type/value/short_id/hide（无 affinity/alias）；
    # 它的作用是把值变成生成代码里顶层函数的构造关键字参数。
    return {
        "name": name,
        "id": "parameter",
        "parameters": {
            "label": repr(label),
            "type": ptype,
            "value": value,
            "short_id": "",
            "hide": "none",
        },
        "states": states(coordinate),
    }


def qtgui_range(name, label, range_type, value, start, stop, step, gui_hint,
                coordinate):
    return {
        "name": name,
        "id": "variable_qtgui_range",
        "parameters": {
            "comment": "",
            "gui_hint": gui_hint,
            "label": repr(label),
            "min_len": "200",
            "orient": "QtCore.Qt.Horizontal",
            "rangeType": range_type,
            "start": str(start),
            "step": str(step),
            "stop": str(stop),
            "value": str(value),
            "widget": "counter_slider",
        },
        "states": states(coordinate),
    }


def qtgui_entry(name, label, entry_type, value, gui_hint, coordinate):
    return {
        "name": name,
        "id": "variable_qtgui_entry",
        "parameters": {
            "comment": "",
            "entry_signal": "editingFinished",
            "gui_hint": gui_hint,
            "label": repr(label),
            "type": entry_type,
            "value": str(value),
        },
        "states": states(coordinate),
    }


def freq_sink(coordinate):
    params = {
        "affinity": "",
        "alias": "",
        "comment": "Spectrum of the received baseband; the transmitted picture "
                   "sits centred at DC with the DC bin nulled.  Bandwidth "
                   "follows the unified slider.",
        "autoscale": "True",
        "average": "0.2",
        "axislabels": "True",
        "bw": "bandwidth",
        "ctrlpanel": "False",
        "fc": "0",
        "fftsize": "fft_len",
        "freqhalf": "True",
        "grid": "True",
        "gui_hint": "0,0,1,2",
        "label": "Relative amplitude",
        "legend": "True",
        "name": FREQ_NAME,
        "nconnections": "1",
        "norm_window": "False",
        "showports": "False",
        "tr_chan": "0",
        "tr_level": "0.0",
        "tr_mode": "qtgui.TRIG_MODE_FREE",
        "tr_tag": '""',
        "type": "complex",
        "units": "dB",
        "update_time": "0.10",
        "wintype": "window.WIN_BLACKMAN_hARRIS",
        "ymax": "10",
        "ymin": "-140",
    }
    for index in range(1, 11):
        params["label%d" % index] = repr("Received baseband") if index == 1 \
            else "''"
        params["width%d" % index] = "1"
        params["color%d" % index] = '"blue"' if index == 1 else '"red"'
        params["alpha%d" % index] = "1.0"
    return {"name": "qtgui_freq_sink_x_0", "id": "qtgui_freq_sink_x",
            "parameters": params, "states": states(coordinate)}


def main():
    graph = {
        "options": {
            "parameters": {
                "author": "",
                "catch_exceptions": "True",
                "category": "Custom",
                "cmake_opt": "",
                "comment": "",
                "copyright": "",
                "description": "Visual OFDM monitor: Run opens the GNU Radio "
                               "spectrum window (with a unified bandwidth "
                               "slider that retunes the real sample rate) plus "
                               "a top-down scrolling waterfall window drawn by "
                               "the embedded python block.  No files written.",
                "gen_cmake": "On",
                "gen_linking": "dynamic",
                "generate_options": "qt_gui",
                "hier_block_src_path": ".:",
                "id": "receiveData_gnuradio",
                "max_nouts": "0",
                "output_language": "python",
                "placement": "(0,0)",
                "realtime_scheduling": "",
                "run": "True",
                "run_command": "{python} -u {filename}",
                "run_options": "prompt",
                "sizing_mode": "fixed",
                "thread_safe_setters": "",
                "title": "Visual OFDM \u2014 ADALM-PLUTO Receiver",
                "window_size": "(1000,1000)",
            },
            "states": states([0, 0]),
        },
        "blocks": [
            parameter("sample_rate", "Initial sample rate (S/s)",
                      "eng_float", "500000", [16, 12]),
            parameter("fft_len", "OFDM FFT length", "intx", "512", [16, 100]),
            variable("subcarriers", "fft_len-2", [16, 188]),
            parameter("driver", "Soapy driver (plutosdr/hackrf)",
                      "str", "'plutosdr'", [16, 276]),
            parameter("pluto_uri", "Soapy URI (empty = auto)",
                      "str", "''", [16, 364]),
            parameter("agc", "Use hardware AGC (Pluto only)", "intx", "0",
                      [16, 452]),
            parameter("max_rows", "Row ring size (console quality only)",
                      "intx", "4096", [16, 540]),
            parameter("console_report", "Print status every 2 s", "intx", "1",
                      [16, 628]),
            qtgui_entry("center_frequency", "RF center frequency (Hz)", "real",
                        "435e6", "1,0,1,1", [16, 716]),
            qtgui_range("rx_gain", "RX gain (PGA, dB)", "float", 35.0, 0.0,
                        73.0, 1.0, "1,1,1,1", [16, 804]),
            # 统一带宽：一个滑动条同时决定硬件采样率、频谱与瀑布的显示范围。
            # 初值用 sample_rate 表达式（GRC 允许），所以 --sample-rate 仍然有效。
            qtgui_range("bandwidth", "统一带宽 / 采样率 (S/s)", "float",
                        "sample_rate", "0.2e6", "4.0e6", "0.05e6",
                        "2,0,1,2", [16, 892]),
            block("soapy_custom_source_0", "soapy_custom_source", {
                "driver": "driver",
                "type": "fc32",
                "nchan": "1",
                "dev_args": "pluto_uri",
                "stream_args": "",
                "samp_rate": "bandwidth",
                "tune_args0": "",
                "settings0": "",
                # 模拟前端带宽也跟随同一条滑动条（标准 SDR 行为）
                "bandwidth0": "bandwidth",
                # 参数值原样插入生成代码，可写运行时表达式按驱动选天线
                "antenna0": "('A_BALANCED' if driver == 'plutosdr' "
                            "else 'TX/RX')",
                "center_freq0": "center_frequency",
                "freq_correction0": "0",
                "agc0": "agc",
                "gain0": "rx_gain",
                "dc_removal0": "False",
                "dc_offset0": "0",
                "iq_balance0": "0",
            }, [352, 400]),
            freq_sink([928, 12]),
            block("blocks_stream_to_vector_0", "blocks_stream_to_vector", {
                "type": "complex",
                "num_items": "fft_len",
                "vlen": "1",
            }, [352, 700]),
            block("fft_vxx_0", "fft_vxx", {
                "type": "complex",
                "fft_size": "fft_len",
                "forward": "True",
                "window": "window.hann(fft_len)",
                "shift": "True",
                "nthreads": "1",
            }, [608, 700]),
            block("blocks_complex_to_mag_squared_0",
                  "blocks_complex_to_mag_squared", {
                      "vlen": "fft_len",
                  }, [864, 700]),
            {
                "name": "epy_block_0",
                "id": "epy_block",
                "parameters": {
                    "_source_code": SOURCE,
                    "fft_len": "fft_len",
                    # GRC 会把这个变量接到本块的同名属性上，_follow_rate()
                    # 因此能实时看到滑动条的新值并去改硬件采样率。
                    "sample_rate": "bandwidth",
                    "subcarriers": "subcarriers",
                    "max_rows": "max_rows",
                    "console_report": "console_report",
                    "affinity": "",
                    "alias": "",
                    "comment": "Top-down scrolling waterfall window + console "
                               "quality report + sample-rate follow.",
                    "maxoutbuf": "0",
                    "minoutbuf": "0",
                },
                "states": states([1120, 700]),
            },
        ],
        "connections": [
            ["soapy_custom_source_0", "0", "qtgui_freq_sink_x_0", "0"],
            ["soapy_custom_source_0", "0", "blocks_stream_to_vector_0", "0"],
            ["blocks_stream_to_vector_0", "0", "fft_vxx_0", "0"],
            ["fft_vxx_0", "0", "blocks_complex_to_mag_squared_0", "0"],
            ["blocks_complex_to_mag_squared_0", "0", "epy_block_0", "0"],
        ],
        "metadata": {"file_format": 1, "grc_version": "3.10.12.0"},
    }
    out = HERE / "receiveData_gnuradio.grc"
    with out.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(graph, handle, sort_keys=False, default_flow_style=False,
                       allow_unicode=True, width=1000)
    print("written", out)


if __name__ == "__main__":
    main()
