# SPDX-License-Identifier: MIT
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "assets" / "still-life" / "still-life.rib"
LOOKDEV = ROOT / "assets" / "still-life" / "lookdev"
MAKEFILE = (ROOT / "Makefile").read_text()
READ = re.compile(r'^\s*ReadArchive\s+"([^"]+)"', re.M)
TEXTURE = re.compile(r'"(build/[^"]+\.(?:tif|rib))"')


def archives(rib):
    return [(rib.parent / name).resolve() for name in READ.findall(rib.read_text())]


def reachable(rib, seen=None):
    seen = set() if seen is None else seen
    for path in archives(rib):
        if path in seen or ROOT / "build" in path.parents:
            continue
        seen.add(path)
        if path.exists():
            reachable(path, seen)
    return seen


class Scene(unittest.TestCase):
    def test_shots_have_no_display(self):
        shots = sorted((ROOT / "shots").glob("*/shot.rib"))
        self.assertTrue(shots)
        for shot in shots:
            with self.subTest(shot=shot.parent.name):
                self.assertNotRegex(shot.read_text(), r"^\s*Display\b", "tools/render.sh supplies Display")

    def test_every_archive_resolves(self):
        for shot in sorted((ROOT / "shots").glob("*/shot.rib")):
            for path in reachable(shot):
                with self.subTest(shot=shot.parent.name, archive=path.name):
                    self.assertTrue(path.exists())

    def test_entry_reads_every_part(self):
        read = {path.name for path in archives(ENTRY)}
        parts = {path.name for path in LOOKDEV.glob("*.rib")}
        self.assertEqual(read, parts)

    def test_every_generated_file_a_rib_names_has_a_rule(self):
        named = set()
        for rib in list(LOOKDEV.glob("*.rib")) + list((ROOT / "tests" / "rib").glob("*.rib")):
            named.update(TEXTURE.findall(rib.read_text()))
        named.update(path for path in re.findall(r'"\.\./\.\./\.\./(build/[^"]+)"', (LOOKDEV / "pot.rib").read_text()))
        self.assertTrue(named)
        for name in sorted(named):
            with self.subTest(file=name):
                self.assertIn(name, MAKEFILE)


    def test_floor_faces_up(self):
        text = (LOOKDEV / "floor.rib").read_text()
        match = re.search(r'Polygon "P" \[([^\]]+)\]', text)
        self.assertIsNotNone(match)
        values = [float(v) for v in match.group(1).split()]
        a, b, c = (values[i : i + 3] for i in (0, 3, 6))
        edge1 = [b[i] - a[i] for i in range(3)]
        edge2 = [c[i] - b[i] for i in range(3)]
        normal_y = edge1[2] * edge2[0] - edge1[0] * edge2[2]
        self.assertGreater(normal_y, 0.0, "the normal map's frame assumes the floor's normal points up")


if __name__ == "__main__":
    unittest.main()
