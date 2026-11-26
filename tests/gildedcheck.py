# SPDX-License-Identifier: MIT
# Renders tests/rib/*.rib under the path tracer and the ray tracer and compares the images the
# gilded shader makes. Usage: gildedcheck.py --gman <gman> --shader-dir <dir> --foil <foil.tif> --normal <foilnormal.tif>
# Run from the repository root; every image lands under build/check/. Exits nonzero on a failed check.
import argparse
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

RENDERERS = ("gmanpathtracer", "gmanraytracer")
OUT = Path("build/check")
RIBS = Path("tests/rib")
BUMP_FRACTION = 0.01

failures = []


def fail(message):
    failures.append(message)
    print(f"FAIL: {message}")


def render(gman, shader_dir, scene, renderer):
    env = dict(os.environ, DYLD_LIBRARY_PATH=shader_dir, LD_LIBRARY_PATH=shader_dir)
    done = subprocess.run([gman, "-r", renderer, str(RIBS / f"{scene}.rib")], env=env, capture_output=True, text=True)
    produced = OUT / f"{scene}.png"
    if done.returncode != 0 or not produced.exists():
        fail(f"{scene} under {renderer} exited {done.returncode}: {done.stdout[-400:]}{done.stderr[-400:]}")
        return None
    kept = OUT / f"{scene}-{renderer}.png"
    os.replace(produced, kept)
    return np.asarray(Image.open(kept).convert("RGBA")).astype(int)


def sphere_mask(pixels):
    return pixels[..., 3] > 0


def lit(scene, renderer, pixels):
    mask = sphere_mask(pixels)
    if not mask.any() or pixels[..., :3][mask].max() == 0:
        fail(f"{scene} under {renderer} is all black")
        return False
    return True


def differing(a, b):
    return np.abs(a - b).max(axis=2) > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gman", required=True)
    parser.add_argument("--shader-dir", required=True)
    parser.add_argument("--foil", required=True)
    parser.add_argument("--normal", required=True)
    args = parser.parse_args()
    for texture in (args.foil, args.normal):
        if not Path(texture).exists():
            sys.exit(f"missing {texture}")
    OUT.mkdir(parents=True, exist_ok=True)

    images = {}
    for scene in ("shinymetal", "gildedplain", "gildedbump0", "gildedbump6", "gildednormal", "gildedpole"):
        for renderer in RENDERERS:
            pixels = render(args.gman, args.shader_dir, scene, renderer)
            if pixels is not None and lit(scene, renderer, pixels):
                images[scene, renderer] = pixels

    for renderer in RENDERERS:
        reference, plain = images.get(("shinymetal", renderer)), images.get(("gildedplain", renderer))
        if reference is not None and plain is not None:
            count = int(differing(reference, plain).sum())
            print(f"reduction {renderer}: {count} differing pixels of {reference.shape[0] * reference.shape[1]}")
            if count != 0:
                fail(f"gilded without a texture differs from shinymetal under {renderer} in {count} pixels")

        flat, bumped = images.get(("gildedbump0", renderer)), images.get(("gildedbump6", renderer))
        if flat is not None and bumped is not None:
            sphere = sphere_mask(flat) | sphere_mask(bumped)
            count = int((differing(flat, bumped) & sphere).sum())
            print(f"bump {renderer}: {count} differing pixels of {int(sphere.sum())} sphere pixels")
            if count < BUMP_FRACTION * sphere.sum():
                fail(f"the foil bump changes {count} of {int(sphere.sum())} sphere pixels under {renderer}")

        mapped = images.get(("gildednormal", renderer))
        if flat is not None and mapped is not None:
            sphere = sphere_mask(flat) | sphere_mask(mapped)
            count = int((differing(flat, mapped) & sphere).sum())
            print(f"normal map {renderer}: {count} differing pixels of {int(sphere.sum())} sphere pixels")
            if count < BUMP_FRACTION * sphere.sum():
                fail(f"the foil normal map changes {count} of {int(sphere.sum())} sphere pixels under {renderer}")

        if ("gildedpole", renderer) in images:
            print(f"pole {renderer}: rendered, {int(sphere_mask(images['gildedpole', renderer]).sum())} sphere pixels")

    if failures:
        sys.exit(1)
    print("gildedcheck: all checks passed")


if __name__ == "__main__":
    main()
