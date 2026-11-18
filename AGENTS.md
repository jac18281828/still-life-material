# AGENTS.md

A path-traced still life rendered with [gman](https://github.com/jac18281828/gman): the scene, the
generators that write its textures and cactus, and any shader it needs, built against an installed
gman. POSIX only: macOS and Linux.

## Project facts

- **Docs root:** `STILL_LIFE_ROOT="${HOME}/OneDrive/Documents/projects/still-life-material"`.
  Prompts live in `${STILL_LIFE_ROOT}/prompts/`, executor reports in `${STILL_LIFE_ROOT}/reports/`.
- **Agenda:** `~/OneDrive/Documents/org/gman.org`, under `* gman — shading, lights and radiosity`.
  The orchestrator owns it; an executor edits no agenda.
- **Machine:** the owner's workstation.
- **gman:** found through `find_package(gman CONFIG REQUIRED)` with `CMAKE_PREFIX_PATH` pointing at
  an install prefix. A unit that needs gman features newer than its latest release installs gman's
  `main` into a prefix of its own and names the commit it built.
- **Python:** `python3` with `numpy` and `Pillow`; scripts take their inputs and outputs as
  arguments and write only under `build/`.

## Layout

- `still-life.rib` — the scene; it reads every generated file from `build/`.
- `gen/` — generators run by `make`; nothing they write is committed.
- `shaders/` — shader plugins, each a `MODULE` library linking `gman::gman_core`, named
  `lib<name>.so` so `Surface "<name>"` loads it.
- `images/` — committed renders for the README.

`gman` loads a shader by its bare file name, so a render points the loader at the build's shader
directory: `DYLD_LIBRARY_PATH` on macOS, `LD_LIBRARY_PATH` on Linux. A `Makefile` target that renders
with a shader of this repository sets both on its `gman` command.

## Licences

Code is MIT (`LICENSE`): `gen/`, `shaders/`, the `Makefile` and any CMake files. The scene and the
pictures are Creative Commons Attribution 4.0 (`LICENSE-CC-BY-4.0`). A new code file carries
`SPDX-License-Identifier: MIT`.

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

## Completion gates

Before marking work complete, run and report:

```sh
make assets
make preview
```

Once `shaders/` exists, also:

```sh
cmake -S . -B build/cmake -DCMAKE_PREFIX_PATH="${GMAN_PREFIX}" && cmake --build build/cmake --parallel
clang-format --dry-run --Werror shaders/*.cpp
```

A render that writes no image, or an image with a NaN or all-black frame, fails the gate. If a gate
stays red after a genuine fix attempt, stop and report the error.
