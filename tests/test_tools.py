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


if __name__ == "__main__":
    unittest.main()
