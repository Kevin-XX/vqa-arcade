"""单元测试：跑 pytest 或直接运行均可。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from vqa.scorer import Scorer  # noqa: E402

SAMPLES = ROOT / "samples"


class TestAlgorithms(unittest.TestCase):
    def test_psnr_self_is_max(self):
        r = Scorer("PSNR").score(SAMPLES / "ref.png", SAMPLES / "ref.png")
        self.assertGreaterEqual(r["score"], 50.0)

    def test_ssim_self_is_one(self):
        r = Scorer("SSIM").score(SAMPLES / "ref.png", SAMPLES / "ref.png")
        self.assertAlmostEqual(r["score"], 1.0, places=5)

    def test_psnr_ranks_distortions(self):
        ref = SAMPLES / "ref.png"
        s_blur = Scorer("PSNR").score(SAMPLES / "dis_blur.png", ref)["score"]
        s_noise = Scorer("PSNR").score(SAMPLES / "dis_noise.png", ref)["score"]
        s_self = Scorer("PSNR").score(ref, ref)["score"]
        self.assertGreater(s_self, s_blur)
        self.assertGreater(s_self, s_noise)

    def test_ssim_blur_drops(self):
        ref = SAMPLES / "ref.png"
        s_blur = Scorer("SSIM").score(SAMPLES / "dis_blur.png", ref)["score"]
        s_noise = Scorer("SSIM").score(SAMPLES / "dis_noise.png", ref)["score"]
        self.assertLess(s_blur, 0.95)
        self.assertLess(s_noise, 0.95)

    def test_niqe_lite_blur_noise_higher_than_ref(self):
        s_ref = Scorer("NIQE-Lite").score(SAMPLES / "ref.png")["score"]
        s_blur = Scorer("NIQE-Lite").score(SAMPLES / "dis_blur.png")["score"]
        s_noise = Scorer("NIQE-Lite").score(SAMPLES / "dis_noise.png")["score"]
        self.assertGreater(s_blur, s_ref)
        self.assertGreater(s_noise, s_ref)

    def test_video_psnr_runs(self):
        r = Scorer("PSNR").score(SAMPLES / "dis_noise.mp4", SAMPLES / "ref.mp4",
                                  max_frames=10)
        self.assertEqual(len(r["per_frame"]), 10)


if __name__ == "__main__":
    unittest.main()
