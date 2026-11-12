# SPDX-FileCopyrightText: 2026 SG
# SPDX-License-Identifier: AGPL-3.0-only
"""도트 넣기 검사 규칙 확인

python3 -B -m unittest discover -s scripts/er-dot -p "test_*.py"
"""
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_dot  # noqa: E402

OUTLINE = (0x1A, 0x1C, 0x2C, 255)


def dot(path: Path, size=(80, 80), colors=3, semi=False, bottom=78) -> Path:
    """가운데에 세로 막대 (발끝 = bottom 줄)"""
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    w, h = size
    for i in range(colors):
        for y in range(max(0, bottom - 60), bottom + 1):
            im.putpixel((w // 2 - colors // 2 + i, y), OUTLINE if i == 0 else (40 + i * 10, 80, 120, 255))
    if semi:
        im.putpixel((1, 1), (255, 0, 0, 128))
    im.save(path)
    return path


class ImportDotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.names = import_dot.er_names()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_good_battle_dot(self) -> None:
        key, errors, notes = import_dot.check(dot(self.dir / "1_0.png"), self.names)
        self.assertEqual(key, (1, 0, False))
        self.assertEqual(errors, [])
        self.assertTrue(any("키 61px" in n for n in notes))

    def test_names(self) -> None:
        self.assertEqual(import_dot.check(dot(self.dir / "재키_2.png"), self.names)[0], (1, 2, False))
        self.assertEqual(import_dot.check(dot(self.dir / "Jackie_1_icon.png", (40, 30), bottom=28), self.names)[0], (1, 1, True))
        self.assertTrue(import_dot.check(dot(self.dir / "없는사람_0.png"), self.names)[1])
        self.assertTrue(import_dot.check(dot(self.dir / "jackie.png"), self.names)[1])

    def test_rules(self) -> None:
        def errs(name: str, **kw) -> str:
            return " ".join(import_dot.check(dot(self.dir / name, **kw), self.names)[1])

        self.assertIn("크기", errs("1_0.png", size=(96, 96)))
        self.assertIn("크기", errs("1_0_icon.png"))  # 아이콘인데 80×80
        self.assertIn("반투명", errs("1_0.png", semi=True))
        self.assertIn("색이 16개", errs("1_0.png", colors=16))
        self.assertEqual(errs("1_0.png", colors=15), "")

    def test_feet_note(self) -> None:
        notes = import_dot.check(dot(self.dir / "1_0.png", bottom=70), self.names)[2]
        self.assertTrue(any("발끝" in n for n in notes))

    def test_rebuild_manifest_and_icon_sheet(self) -> None:
        old = (import_dot.DOT_DIR, import_dot.ICON_SHEET, import_dot.MANIFEST)
        try:
            import_dot.DOT_DIR = self.dir / "dot"
            import_dot.ICON_SHEET = self.dir / "dot-icons.png"
            import_dot.MANIFEST = self.dir / "dot-manifest.ts"
            import_dot.DOT_DIR.mkdir()
            for name in ("1_0.png", "1_2.png", "30_0.png"):
                dot(import_dot.DOT_DIR / name)
            for name in ("1_0_icon.png", "30_0_icon.png"):
                dot(import_dot.DOT_DIR / name, (40, 30), bottom=28)
            self.assertEqual(import_dot.rebuild(), (3, 2))
            ts = import_dot.MANIFEST.read_text(encoding="utf-8")
            self.assertIn("1: [0, 2],", ts)
            self.assertIn("30: [0],", ts)
            self.assertIn("1: { 0: [0, 0] },", ts)
            self.assertIn("30: { 0: [40, 0] },", ts)
            with Image.open(import_dot.ICON_SHEET) as sheet:
                self.assertEqual(sheet.size, (80, 30))
        finally:
            import_dot.DOT_DIR, import_dot.ICON_SHEET, import_dot.MANIFEST = old


if __name__ == "__main__":
    unittest.main()
