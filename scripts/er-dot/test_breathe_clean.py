# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""숨쉬기(breathe.py) · 도트 정리(clean_dot.py) 확인

python3 -B -m unittest discover -s scripts/er-dot -p "test_*.py"
"""
import sys
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import breathe  # noqa: E402
import clean_dot  # noqa: E402


def figure() -> Image.Image:
    """80×80, 키 60 (y 18~77): 머리(어두운) · 몸(파랑) · 다리(빨강)"""
    im = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    for y in range(18, 78):
        c = (20, 20, 30, 255) if y < 30 else (40, 80, 200, 255) if y < 50 else (200, 40, 40, 255)
        for x in range(34, 46):
            im.putpixel((x, y), c)
    return im


class BreatheTest(unittest.TestCase):
    def test_frame_counts_and_feet(self):
        im = figure()
        for n in (2, 3, 4):
            fs = breathe.frames(im, n, 0.45, 0.25)
            self.assertEqual(len(fs), n)
            self.assertEqual(fs[0].tobytes(), im.tobytes())
            for f in fs:
                self.assertEqual(f.size, (80, 80))
                # 발(맨 아래 줄)은 그대로
                self.assertEqual(f.getpixel((40, 77)), im.getpixel((40, 77)))
        fs = breathe.frames(im, 4, 0.45, 0.25)
        self.assertEqual(fs[1].tobytes(), fs[3].tobytes())  # 0 → 1 → 2 → 1

    def test_upper_body_moves_down_one(self):
        im = figure()
        b = breathe.frames(im, 2, 0.45, 0.25)[1]
        self.assertEqual(b.getpixel((40, 18))[3], 0)  # 맨 위 줄은 비고
        self.assertEqual(b.getpixel((40, 19)), im.getpixel((40, 18)))  # 머리가 1px 아래로
        self.assertEqual(b.getpixel((40, 30)), im.getpixel((40, 29)))  # 머리와 몸 경계도 1px 아래로
        self.assertEqual(b.getpixel((40, 60)), im.getpixel((40, 60)))  # 허리 아래는 그대로


class CleanDotTest(unittest.TestCase):
    def test_outline_added_around(self):
        im = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        im.putpixel((1, 1), (200, 40, 40, 255))
        out = clean_dot.add_outline(im)
        self.assertEqual(out.size, (6, 6))
        self.assertEqual(out.getpixel((2, 2)), (200, 40, 40, 255))
        for p in ((1, 2), (3, 2), (2, 1), (2, 3)):
            self.assertEqual(out.getpixel(p), (*clean_dot.LOCK[0], 255))
        self.assertEqual(out.getpixel((1, 1))[3], 0)  # 대각선은 안 칠해요

    def test_background_removed_from_border_median(self):
        # 귀퉁이만 어둡게 번진 분홍 배경 + 가운데 파란 사각형
        im = Image.new("RGB", (40, 40), (230, 30, 220))
        for p in ((0, 0), (39, 0), (0, 39), (39, 39)):
            im.putpixel(p, (120, 40, 110))
        for y in range(10, 30):
            for x in range(15, 25):
                im.putpixel((x, y), (40, 80, 200))
        out = clean_dot.remove_background(im)
        self.assertEqual(out.getpixel((20, 5))[3], 0)
        self.assertEqual(out.getpixel((20, 20))[3], 255)

    def test_dark_lines_survive_when_half(self):
        # 칸(4×4) 안에 어두운 색이 절반이면 어두운 색, 1/4 이면 밝은 색
        half = Image.new("RGBA", (4, 4), (240, 200, 180, 255))
        quarter = half.copy()
        for x in range(4):
            for y in range(2):
                half.putpixel((x, y), (20, 20, 30, 255))
            quarter.putpixel((x, 0), (20, 20, 30, 255))
        self.assertEqual(clean_dot.downsample_mode(half, (1, 1)).getpixel((0, 0)), (20, 20, 30, 255))
        self.assertEqual(clean_dot.downsample_mode(quarter, (1, 1)).getpixel((0, 0)), (240, 200, 180, 255))


if __name__ == "__main__":
    unittest.main()
