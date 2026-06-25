"""8-bit 合成音效引擎：纯 Python wave 模块，零外部依赖。

所有音效即时合成到内存，通过 PyQt5 QSoundEffect 播放。
"""
from __future__ import annotations
import io
import struct
import math
import random
from PyQt5 import QtCore, QtMultimedia

_SAMPLE_RATE = 8000


def _make_wav(samples: list[float]) -> io.BytesIO:
    """将 [-1,1] 浮点采样数组写入 WAV bytestream。"""
    buf = io.BytesIO()
    n = len(samples)
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + n * 2))
    buf.write(b"WAVE")
    buf.write(b"fmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, _SAMPLE_RATE,
                           _SAMPLE_RATE * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", n * 2))
    for s in samples:
        val = max(-32767, min(32767, int(s * 32767)))
        buf.write(struct.pack("<h", val))
    buf.seek(0)
    return buf


def _square(phase: float) -> float:
    return 1.0 if (phase % 1.0) < 0.5 else -1.0


def _play_raw(samples: list[float]):
    """播放采样数组。"""
    buf = _make_wav(samples)
    data = QtCore.QByteArray(buf.read())
    qbuf = QtCore.QBuffer(data)
    qbuf.open(QtCore.QIODevice.ReadOnly)

    # 保存引用防止被 GC
    if not hasattr(_play_raw, "_refs"):
        _play_raw._refs = []
    _play_raw._refs.append(qbuf)

    player = QtMultimedia.QSoundEffect()
    player.setSource(QtCore.QUrl.fromLocalFile(""))
    player.setVolume(0.3)
    # 用 QMediaPlayer 播放内存 WAV
    from PyQt5 import QtCore as QC
    mplayer = QtMultimedia.QMediaPlayer()
    mplayer.setMedia(QtMultimedia.QMediaContent(), qbuf)
    mplayer.setVolume(40)
    mplayer.play()


class ChipSounds:
    """街机音效集合。"""

    def __init__(self):
        self._last_player = None

    def coin(self):
        """硬币投入声：方波滑音。"""
        samples = []
        for i in range(1600):
            t = i / _SAMPLE_RATE
            freq = 800 + t * 600
            phase = freq * t
            samp = _square(phase) * (1.0 - t / 0.2) * 0.6
            samples.append(max(-0.9, min(0.9, samp)))
        self._play(samples)

    def tick(self):
        """电子哔声（倒计时每跳）。"""
        samples = []
        for i in range(400):
            t = i / _SAMPLE_RATE
            samp = _square(1200 * t) * (1.0 - t / 0.05) * 0.4
            samples.append(samp)
        self._play(samples)

    def go(self):
        """GO! 爆破音。"""
        samples = []
        for i in range(800):
            t = i / _SAMPLE_RATE
            freq = 600 + i * 3
            noise = random.uniform(-0.3, 0.3)
            samp = (_square(freq * t) * 0.5 + noise) * (1.0 - t / 0.1)
            samples.append(max(-0.9, min(0.9, samp)))
        self._play(samples)

    def victory(self):
        """胜利短旋律：哆咪嗦哆。"""
        notes = [523, 659, 784, 1047]
        samples = []
        for note in notes:
            for i in range(1500):
                t = i / _SAMPLE_RATE
                env = max(0, 1.0 - t / 0.18)
                samples.append(_square(note * t) * env * 0.5)
            for i in range(300):
                samples.append(0.0)
        self._play(samples)

    def super_victory(self):
        """新纪录长版旋律 + 滑音。"""
        notes = [523, 659, 784, 1047, 1047, 1175, 1319, 1568]
        samples = []
        for idx, note in enumerate(notes):
            dur = 1200 if idx < 4 else 800
            for i in range(dur):
                t = i / _SAMPLE_RATE
                freq = note + (i * 2 if idx >= 4 else 0)
                env = max(0, 1.0 - t / 0.14)
                samples.append(_square(freq * t) * env * 0.5)
            for i in range(200):
                samples.append(0.0)
        self._play(samples)

    def click(self):
        """极短点击声。"""
        samples = []
        for i in range(40):
            t = i / _SAMPLE_RATE
            samples.append(_square(2000 * t) * 0.3 * (1.0 - t / 0.005))
        self._play(samples)

    def _play(self, samples: list[float]):
        """用 QMediaPlayer 播放 WAV 字节流。"""
        buf = _make_wav(samples)
        data = buf.read()
        qbuf = QtCore.QBuffer()
        qbuf.setData(QtCore.QByteArray(data))
        qbuf.open(QtCore.QIODevice.ReadOnly)

        self._last_player = QtMultimedia.QMediaPlayer()
        self._last_player.setMedia(QtMultimedia.QMediaContent(), qbuf)
        self._last_player.setVolume(55)
        self._last_player.play()
