# Still life render project. Run every target from this directory: texture paths in the RIBs are
# relative to it.
#   make assets           write the textures and the cactus under build/
#   make shader           build the gilded shader into build/cmake
#   make shot=preview     render shots/preview into the next renders/preview/preview_vNNN.png
#   make shot=hq          the same at 1920 by 1200 with 512 paths a subpixel
#   make all              render every shot
#   make check            build, then run the C++ unit test and the unittest suites
#   GMAN=/path/to/gman make shot=preview   gman on PATH by default; its prefix finds the headers
#   GMAN_PREFIX=/prefix make shader        override the prefix CMake searches
#   FORMAT=exr make shot=preview           png by default; needs that driver in gman
#   RENDERER=gmanraytracer make shot=preview   gmanpathtracer by default
GMAN ?= gman
RENDERER ?= gmanpathtracer
FORMAT ?= png
PYTHON ?= python3 -I
CMAKE ?= cmake
GMAN_PATH := $(shell command -v $(GMAN))
GMAN_PREFIX ?= $(abspath $(dir $(GMAN_PATH))..)
SHOTS := $(notdir $(wildcard shots/*))

ASSETS = build/marble.tif build/marblenormal.tif build/cactus.tif build/cactusnormal.tif build/cactus.rib build/foil.tif build/foilnormal.tif

.PHONY: assets shader render all check clean
render: assets shader
	@test -n "$(shot)" || { echo "usage: make shot=<$(SHOTS)>"; exit 1; }
	GMAN=$(GMAN) tools/render.sh $(shot) $(RENDERER) $(FORMAT)

assets: $(ASSETS)

shader:
	$(CMAKE) -S . -B build/cmake -DCMAKE_PREFIX_PATH=$(GMAN_PREFIX)
	$(CMAKE) --build build/cmake --parallel

build/foil.tif: tools/foil.py tools/tiff16.py
	mkdir -p build
	$(PYTHON) tools/foil.py $@ build/foilnormal.tif

build/foilnormal.tif: build/foil.tif
	@test -f $@ || $(PYTHON) tools/foil.py build/foil.tif $@

build/marble.tif: tools/marble.py tools/tiff16.py
	mkdir -p build
	$(PYTHON) tools/marble.py $@ build/marblenormal.tif

build/marblenormal.tif: build/marble.tif
	@test -f $@ || $(PYTHON) tools/marble.py build/marble.tif $@

build/cactus.rib: tools/cactus.py tools/tiff16.py
	mkdir -p build
	$(PYTHON) tools/cactus.py build/cactus.tif $@ build/cactus.tif build/cactusnormal.tif

build/cactus.tif build/cactusnormal.tif: build/cactus.rib
	@test -f $@ || $(PYTHON) tools/cactus.py build/cactus.tif build/cactus.rib build/cactus.tif build/cactusnormal.tif

all: assets shader
	@for s in $(SHOTS); do GMAN=$(GMAN) tools/render.sh $$s $(RENDERER) $(FORMAT) || exit 1; done

check: shader assets
	ctest --test-dir build/cmake --output-on-failure
	GMAN=$(GMAN) $(PYTHON) -m unittest discover -s tests -v

clean:
	rm -rf build
