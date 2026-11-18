GMAN ?= gman
PYTHON ?= python3

ASSETS = build/marble.tif build/cactus.tif build/cactus.rib

.PHONY: assets preview hq

assets: $(ASSETS)

build/marble.tif: gen/marble.py
	mkdir -p build
	$(PYTHON) gen/marble.py $@

build/cactus.rib: gen/cactus.py
	mkdir -p build
	$(PYTHON) gen/cactus.py build/cactus.tif $@ build/cactus.tif

build/cactus.tif: build/cactus.rib

build/still-life-hq.rib: still-life.rib
	mkdir -p build
	sed -e 's/^Format .*/Format 1920 1200 1/' -e 's/"integer samples" \[64\]/"integer samples" [512]/' -e 's/still-life\.png/still-life-hq.png/' $< > $@

preview: $(ASSETS)
	$(GMAN) -r gmanpathtracer still-life.rib

hq: $(ASSETS) build/still-life-hq.rib
	$(GMAN) -r gmanpathtracer build/still-life-hq.rib
