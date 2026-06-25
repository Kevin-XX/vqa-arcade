"""命令行入口：python -m vqa.cli score ...

示例：
    python -m vqa.cli list
    python -m vqa.cli score samples/dis_blur.png --ref samples/ref.png --algo SSIM
    python -m vqa.cli score samples/dis_noise.png --algo NIQE-Lite
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from . import __version__
from .algos import ALGORITHMS
from .scorer import Scorer


def _add_score(sub):
    p = sub.add_parser("score", help="对单个图像/视频打分")
    p.add_argument("target", help="待评估的图像或视频")
    p.add_argument("--ref", help="参考输入（FR 算法必填）")
    p.add_argument("--algo", required=True, choices=list(ALGORITHMS),
                   help="算法名（PSNR/SSIM/NIQE-Lite）")
    p.add_argument("--stride", type=int, default=1, help="视频抽帧步长，默认 1")
    p.add_argument("--max-frames", type=int, default=None,
                   help="最多处理的帧数，None 为全量")
    p.add_argument("--json", dest="json_out", help="把详细结果输出到 JSON 文件")
    p.add_argument("--quiet", action="store_true", help="只输出分数")


def _add_list(sub):
    sub.add_parser("list", help="列出可用算法")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="vqa",
        description=f"视觉质量评估 CLI v{__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)
    _add_score(sub)
    _add_list(sub)
    args = parser.parse_args(argv)

    if args.cmd == "list":
        for name, spec in ALGORITHMS.items():
            print(f"- [{spec['kind']}] {name}: {spec['desc']}")
        return 0

    if args.cmd == "score":
        scorer = Scorer(args.algo)
        t0 = time.time()
        result = scorer.score(
            target=args.target,
            reference=args.ref,
            stride=args.stride,
            max_frames=args.max_frames,
        )
        dt = time.time() - t0
        result["elapsed_sec"] = round(dt, 3)
        if args.quiet:
            print(f"{result['score']:.6f}")
        else:
            agg = result["agg"]
            print(f"算法 {args.algo} ({result['kind']})  耗时 {dt:.2f}s")
            print(f"  目标: {result['target']}")
            if result.get("reference"):
                print(f"  参考: {result['reference']}")
            unit = result.get("unit", "")
            print(f"  分数: {result['score']:.6f} {unit}")
            print(f"  逐帧 N={agg['n']}  mean={agg['mean']:.4f}  std={agg['std']:.4f}  "
                  f"min={agg['min']:.4f}  max={agg['max']:.4f}")
        if args.json_out:
            Path(args.json_out).write_text(
                json.dumps(result, ensure_ascii=False, indent=2))
            if not args.quiet:
                print(f"  详情已写入: {args.json_out}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
