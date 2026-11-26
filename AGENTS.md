# AGENTS.md

A path-traced still life rendered with [gman](https://github.com/jac18281828/gman): the scene, the
tools that write its textures and cactus, and the shader it needs, built against an installed gman.
The RIB files under `assets/`, `lights/` and `shots/` are the masters; everything generated goes to
`build/` or `renders/`. POSIX only: macOS and Linux. `README.md` holds the layout, the conventions
and how to render.

## Project facts

- **Docs root:** `STILL_LIFE_ROOT="${HOME}/OneDrive/Documents/projects/still-life-material"`.
  Prompts live in `${STILL_LIFE_ROOT}/prompts/`, executor reports in `${STILL_LIFE_ROOT}/reports/`.
- **Agenda:** `~/OneDrive/Documents/org/gman.org`, under `* gman — shading, lights and radiosity`.
  The orchestrator owns it; an executor edits no agenda.
- **Machine:** the owner's workstation, where gman and a CPU for path-traced renders live.
- **gman:** `gman` on `PATH`, release 1.3.1 or later; `GMAN=<path>` overrides it. The Makefile takes
  the install prefix from the binary's location, as `GMAN_PREFIX=<prefix>` overrides, and finds
  gman's headers and `find_package(gman CONFIG REQUIRED)` there. `tools/render.sh` refuses an older
  gman. `FORMAT=exr` needs a gman whose `--version` lists the `exr` driver. A unit that needs
  features newer than the latest release installs gman's `main` into a prefix of its own and names
  the commit it built.
- **Python:** `python3` with `numpy` and `Pillow`, always run with `-I`; no other dependency.

## Layout

- `assets/still-life/still-life.rib` — the scene's entry; it reads every part's
  `lookdev/<part>.rib`, each a material with its geometry. `lookdev/pot.rib` and the textures read
  generated files from `build/`.
- `lights/studio.rib` — the light rig.
- `shots/<shot>/shot.rib` — camera, format, samples and what the shot reads; it has no `Display`.
- `tools/` — `render.sh` and the generators `make` runs; nothing they write is committed. A script
  takes its inputs and outputs as arguments and writes only where told. A texture generator also
  takes a trailing `scale` that multiplies every side; `make` passes `TEXSCALE`, which is
  `ceil(width / 1920)` for a shot's `Format` width, and a changed scale rebuilds the textures.
  Scale 1 writes the same bytes as ever, and a new generator keeps its relief the same at any scale.
- `shaders/` — shader plugins, each a `MODULE` library linking `gman::gman_core`, named
  `lib<name>.so` so `Surface "<name>"` loads it.
- `tests/` — `unittest` suites, the C++ unit test and the scenes the suites render.
- `images/` — committed renders for the README. `build/` and `renders/` are generated and not
  tracked.

`gman` loads a shader by its bare file name, so a render points the loader at the build's shader
directory: `DYLD_LIBRARY_PATH` on macOS, `LD_LIBRARY_PATH` on Linux. `tools/render.sh` sets both on
its `gman` command.

## Licences

Code is MIT (`LICENSE`): `tools/`, `shaders/`, `tests/`, the `Makefile` and any CMake files. The
scene (`assets/`, `lights/`, `shots/`) and the pictures are Creative Commons Attribution 4.0
(`LICENSE-CC-BY-4.0`). A new code file carries `SPDX-License-Identifier: MIT`.

## Workflow

1. Summarize current behaviour before proposing edits.
2. **Ask each time:** new dependencies, file deletions, licence changes.
3. **Always ask:** landing on `main`, tags, force operations on any branch but your own `agent/`.

Branches are `agent/<topic>`, rebased onto `main`; `main` only fast-forwards. Every commit is signed
(`--gpg-sign`) and carries no attribution: no `Co-Authored-By`, no `Claude-Session`, no "Generated
with". Conventional Commits, lower-case `type: subject`, bodies as flowing paragraphs wrapped at 100
columns.

## C++ style

C++20. Follow gman's `AGENTS.md` for style: `T const&`, `std::` qualified, small functions, early
returns, no code comments beyond API docs. Shader classes live in `namespace gmanshader` and take
their `Surface` token as their name. Format with clang-format 22.1.8 against a `.clang-format`
copied verbatim from gman.

## Python

- A module docstring or a header comment says what the script does and how to call it. No other
  comments.
- Tests use the standard library's `unittest`, never pytest. They live in `tests/test_*.py` and read
  only files in the tree, or files they wrote to a temporary directory. A suite that renders skips
  itself until `make shader assets` has built what it needs.

## Completion gates

Run from the repository root; every gate passes before work is complete:

```sh
make check
clang-format --dry-run --Werror shaders/*.cpp shaders/*.h tests/*.cpp
make shot=preview
git status --porcelain -- assets lights shots
```

`make check` builds the shader and the assets, then runs ctest and `python3 -I -m unittest discover
-s tests -v`. The last command prints nothing: no build or render writes a master. A change to the
scene, a shader or the render path also renders `make shot=hq`, 25 minutes on an Apple M3 Max. A
render that writes no image, or an image with a NaN or all-black frame, fails the gate. If a gate
stays red after a genuine fix attempt, stop and report the error.
