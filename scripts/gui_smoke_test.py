"""GUI smoke test：在 offscreen 平台启动主窗口，模拟一次评估调用，
验证组件构建和工作线程信号链路无异常。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PyQt5 import QtCore, QtWidgets  # noqa: E402

from vqa.gui.main_window import MainWindow  # noqa: E402

SAMPLES = ROOT / "samples"


def main() -> int:
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()

    # 模拟点击 SSIM
    win.preview_ref._set_path(str(SAMPLES / "ref.png"))
    win.preview_dis._set_path(str(SAMPLES / "dis_blur.png"))
    win.mode_combo.setCurrentIndex(0)  # FR
    idx = win.algo_combo.findText("SSIM")
    win.algo_combo.setCurrentIndex(idx)
    win.max_spin.setValue(0)  # 全部 (图片只有 1 帧)

    done = {"ok": False, "score": None}

    def _on_finished(result):
        done["ok"] = True
        done["score"] = result["score"]
        app.quit()

    def _on_failed(msg):
        print(f"FAILED: {msg}")
        app.quit()

    # 替换槽函数顺序：在 worker 完成后我们再退出
    win._on_run()
    # MainWindow 内部已 connect 了 _on_finished；我们再补一个监听用于退出
    QtCore.QTimer.singleShot(8000, app.quit)  # 安全超时

    # 我们要在 worker 跑完后退出 app
    def hook_finished(result):
        _on_finished(result)
    # 通过定时器轮询 last_result
    poll = QtCore.QTimer()
    def _check():
        if win._last_result is not None:
            done["ok"] = True
            done["score"] = win._last_result["score"]
            app.quit()
    poll.timeout.connect(_check)
    poll.start(50)

    app.exec_()
    if not done["ok"]:
        print("smoke-test: 未能在 8s 内拿到结果")
        return 1
    print(f"smoke-test OK, SSIM(blur vs ref) = {done['score']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
