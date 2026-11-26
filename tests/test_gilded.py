# SPDX-License-Identifier: MIT
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RIBS = ROOT / "tests" / "rib"
SHADER_DIR = ROOT / "build" / "cmake"
TEXTURES = [ROOT / "build" / "foil.tif", ROOT / "build" / "foilnormal.tif"]
RENDERERS = ("gmanpathtracer", "gmanraytracer")
CHANGED_FRACTION = 0.01
GMAN = os.environ.get("GMAN") or shutil.which("gman")

BUILT = (SHADER_DIR / "libgilded.so").exists() and all(t.exists() for t in TEXTURES) and GMAN is not None


@unittest.skipUnless(BUILT, "run make shader assets, with gman on PATH or GMAN set")
class GildedRenders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.images = {}

    @classmethod
    def render(cls, scene, renderer):
        key = scene, renderer
        if key not in cls.images:
            out = Path(cls.tmp.name) / f"{scene}-{renderer}.png"
            frame = Path(cls.tmp.name) / f"{scene}-{renderer}.rib"
            frame.write_text(f'Display "{out}" "file" "rgba"\nReadArchive "{RIBS / (scene + ".rib")}"\n')
            env = dict(os.environ, DYLD_LIBRARY_PATH=str(SHADER_DIR), LD_LIBRARY_PATH=str(SHADER_DIR))
            done = subprocess.run([GMAN, "-r", renderer, str(frame)], cwd=ROOT, env=env, capture_output=True, text=True)
            if done.returncode != 0 or not out.exists():
                raise AssertionError(f"{scene} under {renderer} exited {done.returncode}: {done.stdout[-400:]}{done.stderr[-400:]}")
            cls.images[key] = np.asarray(Image.open(out).convert("RGBA")).astype(int)
        return cls.images[key]

    def sphere(self, *images):
        mask = images[0][..., 3] > 0
        for image in images[1:]:
            mask = mask | (image[..., 3] > 0)
        return mask

    def differing(self, a, b):
        return np.abs(a - b).max(axis=2) > 0

    def test_every_scene_is_lit(self):
        for renderer in RENDERERS:
            for scene in ("shinymetal", "gildedplain", "gildedbump0", "gildedbump6", "gildednormal", "gildedpole"):
                with self.subTest(scene=scene, renderer=renderer):
                    pixels = self.render(scene, renderer)
                    mask = pixels[..., 3] > 0
                    self.assertTrue(mask.any(), "nothing rendered")
                    self.assertGreater(pixels[..., :3][mask].max(), 0, "all black")

    def test_without_a_texture_gilded_is_shinymetal(self):
        for renderer in RENDERERS:
            with self.subTest(renderer=renderer):
                count = int(self.differing(self.render("shinymetal", renderer), self.render("gildedplain", renderer)).sum())
                self.assertEqual(count, 0)

    def test_bump_and_normal_map_change_the_sphere(self):
        for renderer in RENDERERS:
            flat = self.render("gildedbump0", renderer)
            for scene in ("gildedbump6", "gildednormal"):
                with self.subTest(scene=scene, renderer=renderer):
                    other = self.render(scene, renderer)
                    mask = self.sphere(flat, other)
                    count = int((self.differing(flat, other) & mask).sum())
                    self.assertGreaterEqual(count, CHANGED_FRACTION * mask.sum())


if __name__ == "__main__":
    unittest.main()
