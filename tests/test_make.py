# SPDX-License-Identifier: MIT
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = (
    "marble.tif",
    "marblenormal.tif",
    "cactus.tif",
    "cactusnormal.tif",
    "cactus.rib",
    "foil.tif",
    "foilnormal.tif",
)
STUB = """#!/bin/sh
script=$(basename "$1"); shift
case $script in
  cactus.py) outs="$1 $2 $4"; scale=$5 ;;
  *) outs="$1 $2"; scale=$3 ;;
esac
echo "$script $scale" >> stub.log
for out in $outs; do echo "$scale" > "$out"; done
"""


def make(cwd, *args):
    result = subprocess.run(["make", "-s", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return result.stdout


class Work(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.work = Path(cls.tmp.name)
        shutil.copy(ROOT / "Makefile", cls.work / "Makefile")


class TexScale(Work):
    def scale(self, *args, width=None, shot="probe"):
        if width is not None:
            (self.work / "shots" / shot).mkdir(parents=True, exist_ok=True)
            (self.work / "shots" / shot / "shot.rib").write_text(f"## probe\nFormat {width} 1200 1\nPixelSamples 2 2\n")
        return int(make(self.work, "texscale", *args))

    def test_a_shot_up_to_1920_wide_keeps_scale_1(self):
        self.assertEqual(self.scale("shot=probe", width=640), 1)
        self.assertEqual(self.scale("shot=probe", width=1920), 1)

    def test_each_further_1920_pixels_adds_one(self):
        for width, expected in ((1921, 2), (3840, 2), (3841, 3), (7680, 4)):
            self.assertEqual(self.scale("shot=probe", width=width), expected, width)

    def test_no_shot_gives_scale_1(self):
        self.assertEqual(self.scale(), 1)

    def test_a_shot_without_a_format_gives_scale_1(self):
        self.assertEqual(self.scale("shot=missing"), 1)

    def test_texscale_on_the_command_line_wins(self):
        self.assertEqual(self.scale("shot=probe", "TEXSCALE=3", width=640), 3)

    def test_the_shipped_shots_stay_at_scale_1(self):
        for shot in ("preview", "hq"):
            self.assertEqual(int(make(ROOT, "texscale", f"shot={shot}")), 1, shot)


class Stamp(Work):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        (cls.work / "tools").mkdir()
        for name in ("foil.py", "marble.py", "cactus.py", "tiff16.py"):
            (cls.work / "tools" / name).write_text("")
        stub = cls.work / "stub.sh"
        stub.write_text(STUB)
        stub.chmod(0o755)

    def assets(self, *args):
        make(self.work, "-j4", "assets", f"PYTHON={self.work / 'stub.sh'}", *args)

    def built_at(self):
        return {name: (self.work / "build" / name).read_text().strip() for name in ASSETS}

    def test_a_changed_scale_rebuilds_every_texture_at_once(self):
        shutil.rmtree(self.work / "build", ignore_errors=True)
        self.assets()
        self.assertEqual(set(self.built_at().values()), {"1"})
        self.assets("TEXSCALE=2")
        self.assertEqual(set(self.built_at().values()), {"2"})
        self.assets()
        self.assertEqual(set(self.built_at().values()), {"1"})

    def test_an_unknown_shot_builds_nothing(self):
        shutil.rmtree(self.work / "build", ignore_errors=True)
        for args in (("shot=nope",), ()):
            result = subprocess.run(
                ["make", "-s", "render", f"PYTHON={self.work / 'stub.sh'}", *args],
                cwd=self.work,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("usage: make shot=", result.stdout)
            self.assertFalse((self.work / "build").exists())

    def test_the_same_scale_builds_nothing(self):
        self.assets("TEXSCALE=2")
        log = (self.work / "stub.log").read_text()
        self.assets("TEXSCALE=2")
        self.assertEqual((self.work / "stub.log").read_text(), log)


if __name__ == "__main__":
    unittest.main()
