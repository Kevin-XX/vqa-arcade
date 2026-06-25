"""支持拖拽的预览框：图片直接显示，视频显示首帧 + 标签。"""
from __future__ import annotations

import os
from pathlib import Path

from PyQt5 import QtCore, QtGui, QtWidgets

import cv2


class DropPreview(QtWidgets.QFrame):
    fileDropped = QtCore.pyqtSignal(str)

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet(
            "DropPreview { background: #0f172a; border: 1px dashed #334155; border-radius: 8px; }"
        )
        self._path = ""
        self._title = label
        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)

        self._label = QtWidgets.QLabel(f"{label}：拖拽文件到此  或  点击下方按钮选择")
        self._label.setAlignment(QtCore.Qt.AlignCenter)
        self._label.setStyleSheet("color: #94a3b8; font-size: 13px;")

        self._image = QtWidgets.QLabel()
        self._image.setAlignment(QtCore.Qt.AlignCenter)
        self._image.setMinimumHeight(200)
        self._image.setStyleSheet("background: transparent;")

        self._meta = QtWidgets.QLabel("")
        self._meta.setAlignment(QtCore.Qt.AlignCenter)
        self._meta.setStyleSheet("color: #cbd5e1; font-size: 12px;")

        self._btn = QtWidgets.QPushButton("选择文件…")
        self._btn.clicked.connect(self._pick)
        self._btn.setStyleSheet(
            "QPushButton { padding: 6px 12px; background: #1e293b; color: #e2e8f0;"
            " border: 1px solid #334155; border-radius: 6px; }"
            "QPushButton:hover { background: #334155; }"
        )

        self._layout.addWidget(self._label)
        self._layout.addWidget(self._image, 1)
        self._layout.addWidget(self._meta)
        self._layout.addWidget(self._btn, 0, QtCore.Qt.AlignCenter)

    def path(self) -> str:
        return self._path

    def clear(self):
        self._path = ""
        self._image.clear()
        self._meta.setText("")

    def _pick(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, f"选择{self._title}",
            os.path.expanduser("~"),
            "媒体文件 (*.png *.jpg *.jpeg *.bmp *.webp *.tif *.mp4 *.mov *.avi *.mkv *.webm)")
        if path:
            self._set_path(path)

    def _set_path(self, path: str):
        self._path = path
        suffix = Path(path).suffix.lower()
        if suffix in {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}:
            cap = cv2.VideoCapture(path)
            ok, frame = cap.read()
            cap.release()
            if ok:
                self._show_bgr(frame)
                self._meta.setText(f"📹 视频：{Path(path).name}")
            else:
                self._meta.setText(f"⚠️ 视频读取失败：{Path(path).name}")
        else:
            pix = QtGui.QPixmap(path)
            if not pix.isNull():
                self._image.setPixmap(pix.scaled(
                    self._image.size(), QtCore.Qt.KeepAspectRatio,
                    QtCore.Qt.SmoothTransformation))
                self._meta.setText(f"🖼️ 图片：{Path(path).name}")
            else:
                self._meta.setText(f"⚠️ 无法显示：{Path(path).name}")
        self.fileDropped.emit(path)

    def _show_bgr(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = rgb.shape
        qimg = QtGui.QImage(rgb.data, w, h, w * c, QtGui.QImage.Format_RGB888).copy()
        pix = QtGui.QPixmap.fromImage(qimg)
        self._image.setPixmap(pix.scaled(
            self._image.size(), QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation))

    # ---- drag & drop ----
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if p:
                self._set_path(p)
                break
