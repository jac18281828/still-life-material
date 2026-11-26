# SPDX-License-Identifier: MIT
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TexScale(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        shutil.copy(ROOT / "Makefile", cls.work / "Makefile")

    def scale(self, width, *args):
        shot = self.work / "shots" / "probe"
        shot.mkdir(parents=True, exist_ok=True)
        (shot / "shot.rib").write_text(f"## probe\nFormat {width} 1200 1\nPixelSamples 2 2\n")
        result = subprocess.run(
            ["make", "-s", "texscale", "shot=probe", *args],
            cwd=self.work,
            check=True,
            capture_output=True,
            text=True,
        )
        return int(result.stdout)

    def test_a_shot_up_to_1920_wide_keeps_scale_1(self):
        self.assertEqual(self.scale(640), 1)
        self.assertEqual(self.scale(1920), 1)

    def test_each_further_1920_pixels_adds_one(self):
        self.assertEqual(self.scale(1921), 2)
        self.assertEqual(self.scale(3840), 2)
        self.assertEqual(self.scale(3841), 3)
        self.assertEqual(self.scale(7680), 4)

    def test_no_shot_gives_scale_1(self):
        result = subprocess.run(["make", "-s", "texscale"], cwd=self.work, check=True, capture_output=True, text=True)
        self.assertEqual(int(result.stdout), 1)

    def test_a_shot_without_a_format_gives_scale_1(self):
        result = subprocess.run(
            ["make", "-s", "texscale", "shot=missing"], cwd=self.work, check=True, capture_output=True, text=True
        )
        self.assertEqual(int(result.stdout), 1)

    def test_texscale_on_the_command_line_wins(self):
        self.assertEqual(self.scale(640, "TEXSCALE=3"), 3)

    def test_the_shipped_shots_stay_at_scale_1(self):
        for shot in ("preview", "hq"):
            result = subprocess.run(
                ["make", "-s", "texscale", f"shot={shot}"], cwd=ROOT, check=True, capture_output=True, text=True
            )
            self.assertEqual(int(result.stdout), 1, shot)


if __name__ == "__main__":
    unittest.main()
