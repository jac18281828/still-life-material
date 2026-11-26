GMAN ?= gman
PYTHON ?= python3
CMAKE ?= cmake
GMAN_PREFIX ?=

SHADER_DIR = $(CURDIR)/build/cmake
GMAN_RENDER = DYLD_LIBRARY_PATH=$(SHADER_DIR) LD_LIBRARY_PATH=$(SHADER_DIR) $(GMAN)
PREFIX_ARG = $(if $(GMAN_PREFIX),-DCMAKE_PREFIX_PATH=$(GMAN_PREFIX))

ASSETS = build/marble.tif build/cactus.tif build/cactus.rib build/foil.tif build/foilnormal.tif

.PHONY: assets foil shader check preview hq

assets: $(ASSETS)

foil: build/foil.tif build/foilnormal.tif

shader:
	$(CMAKE) -S . -B build/cmake $(PREFIX_ARG)
	$(CMAKE) --build build/cmake --parallel

build/foil.tif: gen/foil.py gen/tiff16.py
	mkdir -p build
	$(PYTHON) gen/foil.py $@ build/foilnormal.tif

build/foilnormal.tif: build/foil.tif
	@test -f $@ || $(PYTHON) gen/foil.py build/foil.tif $@

check: shader foil
	ctest --test-dir build/cmake --output-on-failure
	$(PYTHON) tests/gildedcheck.py --gman '$(GMAN)' --shader-dir '$(SHADER_DIR)' --foil build/foil.tif --normal build/foilnormal.tif

build/marble.tif: gen/marble.py
	mkdir -p build
	$(PYTHON) gen/marble.py $@

build/cactus.rib: gen/cactus.py gen/tiff16.py
	mkdir -p build
	$(PYTHON) gen/cactus.py build/cactus.tif $@ build/cactus.tif

build/cactus.tif: build/cactus.rib

build/still-life-hq.rib: still-life.rib
	mkdir -p build
	sed -e 's/^Format .*/Format 1920 1200 1/' -e 's/"integer samples" \[64\]/"integer samples" [512]/' -e 's/still-life\.png/still-life-hq.png/' $< > $@

preview: $(ASSETS) shader foil
	$(GMAN_RENDER) -r gmanpathtracer still-life.rib

hq: $(ASSETS) shader foil build/still-life-hq.rib
	$(GMAN_RENDER) -r gmanpathtracer build/still-life-hq.rib
