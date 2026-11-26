# SPDX-License-Identifier: MIT
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
FOIL = ROOT / "tools" / "foil.py"
CACTUS = ROOT / "tools" / "cactus.py"
MARBLE = ROOT / "tools" / "marble.py"
TOLERANCE = 0.02


def read_tiff16(path):
    raw = path.read_bytes()
    ifd = struct.unpack(">I", raw[4:8])[0]
    count = struct.unpack(">H", raw[ifd : ifd + 2])[0]
    tags = {}
    for i in range(count):
        tag, _, _, value = struct.unpack(">HHII", raw[ifd + 2 + 12 * i : ifd + 14 + 12 * i])
        tags[tag] = value
    width, height, offset = tags[256], tags[257], tags[273]
    pixels = np.frombuffer(raw[offset : offset + width * height * 6], dtype=">u2")
    return pixels.reshape(height, width, 3).astype(float) / 65535.0


class Foil(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.foil = Path(cls.tmp.name) / "foil.tif"
        cls.normal = Path(cls.tmp.name) / "foilnormal.tif"
        subprocess.run([sys.executable, "-I", str(FOIL), str(cls.foil), str(cls.normal)], check=True)

    def test_foil_is_2048_by_1024(self):
        with Image.open(self.foil) as image:
            self.assertEqual(image.size, (2048, 1024))

    def test_normal_map_holds_unit_normals_facing_out(self):
        decoded = read_tiff16(self.normal) * 2.0 - 1.0
        self.assertEqual(decoded.shape, (1024, 2048, 3))
        self.assertLess(np.abs(np.linalg.norm(decoded, axis=2) - 1.0).max(), TOLERANCE)
        self.assertGreater(decoded[..., 2].min(), 0.0)

    def test_normal_map_has_relief(self):
        decoded = read_tiff16(self.normal) * 2.0 - 1.0
        self.assertGreater(decoded[..., :2].std(), 0.05)


class Cactus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.skin = Path(cls.tmp.name) / "cactus.tif"
        cls.rib = Path(cls.tmp.name) / "cactus.rib"
        cls.normal = Path(cls.tmp.name) / "cactusnormal.tif"
        subprocess.run(
            [sys.executable, "-I", str(CACTUS), str(cls.skin), str(cls.rib), "build/cactus.tif", str(cls.normal)],
            check=True,
            capture_output=True,
        )

    def test_pads_name_the_normal_map(self):
        pads = [line for line in self.rib.read_text().splitlines() if "paintedplastic" in line]
        self.assertEqual(len(pads), 4)
        for line in pads:
            self.assertIn(f'"string normalname" ["{self.normal}"]', line)

    def test_normal_map_holds_unit_normals_facing_out(self):
        decoded = read_tiff16(self.normal) * 2.0 - 1.0
        self.assertLess(np.abs(np.linalg.norm(decoded, axis=2) - 1.0).max(), TOLERANCE)
        self.assertGreater(decoded[..., 2].min(), 0.0)
        self.assertGreater(decoded[..., :2].std(), 0.02)

    def test_normal_map_wraps_around_the_pad(self):
        decoded = read_tiff16(self.normal) * 2.0 - 1.0
        seam = np.abs(decoded[:, 0] - decoded[:, -1]).mean()
        inside = np.abs(decoded[:, 1:] - decoded[:, :-1]).mean()
        self.assertLess(seam, 1.5 * inside)


class Marble(unittest.TestCase):
    TILES = 20

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.marble = Path(cls.tmp.name) / "marble.tif"
        cls.normal = Path(cls.tmp.name) / "marblenormal.tif"
        subprocess.run([sys.executable, "-I", str(MARBLE), str(cls.marble), str(cls.normal)], check=True)
        cls.decoded = read_tiff16(cls.normal) * 2.0 - 1.0

    def test_marble_is_2048_square(self):
        with Image.open(self.marble) as image:
            self.assertEqual(image.size, (2048, 2048))

    def test_normal_map_holds_unit_normals_facing_out(self):
        self.assertLess(np.abs(np.linalg.norm(self.decoded, axis=2) - 1.0).max(), TOLERANCE)
        self.assertGreater(self.decoded[..., 2].min(), 0.0)

    def test_grout_is_bevelled_and_tiles_sit_nearly_level(self):
        size = self.decoded.shape[0]
        tilt = np.linalg.norm(self.decoded[..., :2], axis=2)
        along = (np.arange(size) / size * self.TILES) % 1.0
        edge = np.minimum(along, 1.0 - along)
        edge = np.minimum(edge[:, None], edge[None, :])
        self.assertGreater(tilt[edge < 0.05].max(), 0.4, "the bevel is steep")
        self.assertLess(tilt[edge > 0.1].max(), 0.1, "a tile's face is nearly level")

    def test_every_tile_has_its_own_tilt(self):
        size = self.decoded.shape[0]
        step = size // self.TILES
        centres = self.decoded[step // 2 :: step, step // 2 :: step, 0]
        self.assertEqual(centres.shape, (self.TILES, self.TILES))
        self.assertGreater(centres.std(), 0.005)


if __name__ == "__main__":
    unittest.main()
