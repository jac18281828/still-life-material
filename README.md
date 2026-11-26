# Still life with cactus

![A path-traced still life: a gold-leaf ball on a pedestal, a glass ball, a potted prickly pear, a mirror ball and a blue torus on a marble floor before a red clay wall](images/still-life.png)

A still life path-traced with [gman](https://github.com/jac18281828/gman), a RenderMan-compatible
renderer. A gold ball sits on a pedestal; a glass ball in front turns the potted prickly pear behind
it upside down, like a lens; a mirror ball and a blue torus stand at the right, on a marble floor
before a clay wall. A warm disk light overhead and a small blue lamp light the scene, and every
bounce between them is traced.

Everything in the frame is generated. Python scripts write the marble floor and the cactus's 16-bit
skin, and a RIB archive builds the cactus itself: four pads, each areole a green cushion with a
white tuft of glochids and a straw spine or two, and three pink buds.

## What you need

- **gman 1.3.1 or later**, installed with its headers and on your `PATH`: the
  [release archive](https://github.com/jac18281828/gman/releases) installs it. The Makefile takes
  the install prefix from the `gman` it finds, so nothing else needs configuring. A different
  gman is `GMAN=/path/to/gman`, and a different prefix is `GMAN_PREFIX=/prefix`.
- **CMake 3.21 or later** and a C++20 compiler, which build the gilded shader.
- **Python 3** with `numpy` and `Pillow`: `pip install numpy Pillow`.
- **make**.

## Render it

Run every command from this directory: the RIBs name textures relative to it.

```sh
make shot=preview                 # next renders/preview/preview_vNNN.png
make shot=hq                      # next renders/hq/hq_vNNN.png
make all                          # every shot
RENDERER=gmanraytracer make shot=preview    # gmanpathtracer by default
FORMAT=exr make shot=preview      # png by default; needs that driver in gman
```

A render writes the textures and the cactus under `build/` and builds the gilded shader that
finishes the gold ball first. It never overwrites an earlier version: `tools/render.sh` writes a
frame RIB under `build/frames/` that names the output and reads the shot, and versions count across
formats.

`preview` renders 640 by 400 with 64 paths through each of four subpixels, about 25 seconds on an
Apple M3 Max. `hq` renders 1920 by 1200 with 512 paths a subpixel, 2,048 a pixel, which smooths the
grain on the floor and in the metal; expect about 25 minutes. The picture above is an `hq` render
scaled to 1280 by 800.

Three lines at the top of a `shots/<shot>/shot.rib` set the quality:

```
Format 640 400 1
PixelSamples 2 2
Option "pathtracer" "integer samples" [64]
```

`Format` sets the size in pixels. `integer samples` sets the paths traced through each subpixel;
`PixelSamples 2 2` makes four subpixels a pixel. Noise falls with the square root of the paths, so
four times the samples halves the grain. A new shot is a directory under `shots/` with a `shot.rib`
that has no `Display`.

### Texture size

The textures grow with the render. `make shot=<shot>` reads the shot's `Format` width and builds the
textures at scale `ceil(width / 1920)`: 1 up to 1920 pixels wide, 2 up to 3840, 3 up to 5760, and
so on. A scale multiplies the side of every texture, and the normal maps' strength follows so the
relief keeps its height. `preview` and `hq` stay at scale 1, whose textures are byte-identical to
the ones before this rule. `TEXSCALE=<n> make assets` sets the scale by hand. A change of scale
discards the textures and builds them again, so `preview` after a wider shot rebuilds at scale 1.

The marble stops at scale 2: its normal map is already 4096 by 4096 and 8192 by 8192 at scale 2,
about 400 MB and 16 GB of memory to build. The foil, the cactus and the marble's colour grow
without that limit.

## Check it

```sh
make check
```

builds the shader and the assets, runs the C++ unit test, and runs the `unittest` suites in
`tests/`, which render small scenes to verify the shader under both renderers.

## What is in it

| Path | Holds |
|---|---|
| `assets/still-life/still-life.rib` | The scene's entry: every part with its look |
| `assets/still-life/lookdev/<part>.rib` | One part's material and geometry: `floor`, `wall`, `pedestal`, `gold`, `glass`, `mirror`, `torus`, `pot` |
| `lights/studio.rib` | A warm disk light overhead and a small blue lamp |
| `shots/<shot>/shot.rib` | Camera, format, samples and what the shot reads: `preview` and `hq` |
| `tools/render.sh` | Renders a shot into the next free version |
| `tools/marble.py` | `build/marble.tif`, a 2048 by 2048 checkerboard (scale 1) of cream and slate marble, and `build/marblenormal.tif`, its normal map of recessed bevelled grout and tiles that each sit a hair off level |
| `tools/foil.py` | `build/foil.tif`, the crinkled gold-leaf texture of the gold ball, and `build/foilnormal.tif`, its 16-bit normal map with sharp creases |
| `tools/cactus.py` | `build/cactus.tif`, the 16-bit cactus skin, `build/cactusnormal.tif`, its normal map of undulation and fine pebbling, and `build/cactus.rib`, the cactus |
| `tools/tiff16.py` | The 16-bit TIFF writer the generators share |
| `shaders/gmangilded.cpp` | `libgilded.so`, the shader that turns the foil and its normal map into gold leaf |
| `tests/` | `unittest` suites and a C++ unit test |
| `images/still-life.png` | The picture above |
| `build/`, `renders/` | Generated; not tracked |

## Conventions

- Axes are RenderMan camera space: x right, y up, z away from the camera, and the camera looks down
  +z. Y is up in the scene.
- The RIB files are the masters; every texture and the cactus are generated into `build/`.
- The normal maps, the gold ball's, the cactus pads' and the floor's, follow `paintedplastic`'s convention: red
  along `dPdu`, green along `-dPdv`, blue along the normal.

## Licence

The code is under the [MIT licence](LICENSE): the scripts under `tools/`, the tests, the `Makefile`
and any shader this repository builds. The scene, under `assets/`, `lights/` and `shots/`, and the
pictures under `images/` are under [Creative Commons Attribution 4.0](LICENSE-CC-BY-4.0). gman itself
is LGPL-2.1-or-later; a shader here links it as a plugin, and its own code stays MIT.
