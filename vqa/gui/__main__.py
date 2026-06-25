"""使 `python -m vqa.gui` 启动街机主窗口。"""
from .arcade_main import ArcadeMain
from PyQt5 import QtWidgets
import sys

def main():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    win = ArcadeMain()
    win.show()
    sys.exit(app.exec_())

main()
