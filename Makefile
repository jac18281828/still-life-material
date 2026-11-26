# Still life render project. Run every target from this directory: texture paths in the RIBs are
# relative to it.
#   make assets           write the textures and the cactus under build/, at scale 1
#   make shader           build the gilded shader into build/cmake
#   make shot=preview     render shots/preview into the next renders/preview/preview_vNNN.png
#   make shot=hq          the same at 1920 by 1200 with 512 paths a subpixel
#   make all              render every shot
#   make check            build, then run the C++ unit test and the unittest suites
#   GMAN=/path/to/gman make shot=preview   gman on PATH by default; its prefix finds the headers
#   GMAN_PREFIX=/prefix make shader        override the prefix CMake searches
#   FORMAT=exr make shot=preview           png by default; needs that driver in gman
#   TEXSCALE=2 make assets                 textures 2 times a side; make shot=<shot> sets it from the
#                                          shot's Format width, one more for each 1920 pixels
#   RENDERER=gmanraytracer make shot=preview   gmanpathtracer by default
GMAN ?= gman
RENDERER ?= gmanpathtracer
FORMAT ?= png
PYTHON ?= python3 -I
CMAKE ?= cmake
GMAN_PATH := $(shell command -v $(GMAN))
GMAN_PREFIX ?= $(abspath $(dir $(GMAN_PATH))..)
SHOTS := $(notdir $(wildcard shots/*))
TEXSCALE ?= $(if $(shot),$(or $(shell awk '$$1 == "Format" { print int(($$2 + 1919) / 1920); exit }' shots/$(shot)/shot.rib 2>/dev/null),1),1)

ASSETS = build/marble.tif build/marblenormal.tif build/cactus.tif build/cactusnormal.tif build/cactus.rib build/foil.tif build/foilnormal.tif

.PHONY: assets shader render all check clean texscale FORCE
render: assets shader
	@test -n "$(shot)" || { echo "usage: make shot=<$(SHOTS)>"; exit 1; }
	GMAN=$(GMAN) tools/render.sh $(shot) $(RENDERER) $(FORMAT)

assets: $(ASSETS)

texscale:
	@echo $(TEXSCALE)

FORCE:

build/texscale: FORCE
	@mkdir -p build
	@echo $(TEXSCALE) | cmp -s - $@ || { rm -f $(ASSETS); echo $(TEXSCALE) > $@; }

shader:
	$(CMAKE) -S . -B build/cmake -DCMAKE_PREFIX_PATH=$(GMAN_PREFIX)
	$(CMAKE) --build build/cmake --parallel

build/foil.tif: tools/foil.py tools/tiff16.py build/texscale
	mkdir -p build
	$(PYTHON) tools/foil.py $@ build/foilnormal.tif $(TEXSCALE)

build/foilnormal.tif: build/foil.tif
	@test -f $@ || $(PYTHON) tools/foil.py build/foil.tif $@ $(TEXSCALE)

build/marble.tif: tools/marble.py tools/tiff16.py build/texscale
	mkdir -p build
	$(PYTHON) tools/marble.py $@ build/marblenormal.tif $(TEXSCALE)

build/marblenormal.tif: build/marble.tif
	@test -f $@ || $(PYTHON) tools/marble.py build/marble.tif $@ $(TEXSCALE)

build/cactus.rib: tools/cactus.py tools/tiff16.py build/texscale
	mkdir -p build
	$(PYTHON) tools/cactus.py build/cactus.tif $@ build/cactus.tif build/cactusnormal.tif $(TEXSCALE)

build/cactus.tif build/cactusnormal.tif: build/cactus.rib
	@test -f $@ || $(PYTHON) tools/cactus.py build/cactus.tif build/cactus.rib build/cactus.tif build/cactusnormal.tif $(TEXSCALE)

all: shader
	@for s in $(SHOTS); do $(MAKE) --no-print-directory render shot=$$s || exit 1; done

check: shader assets
	ctest --test-dir build/cmake --output-on-failure
	GMAN=$(GMAN) $(PYTHON) -m unittest discover -s tests -v

clean:
	rm -rf build
