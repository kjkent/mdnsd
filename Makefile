# Makefile for mdns-repeater by geekman
# https://github.com/geekman/mdns-repeater

NAME := mdns-repeater

INSTALL_DIR := $(PREFIX)/bin
OUT_DIR := build
SRC_DIR := lib/mdns-repeater

BUILD := $(OUT_DIR)/$(NAME)
SRC := $(SRC_DIR)/$(NAME).c
OBJ := $(BUILD).o

GITVERFILE := $(OUT_DIR)/gitversion
GITVERSION := $(shell git rev-parse --short=8 HEAD 2>/dev/null || echo -n 'unknown')

CFLAGS += -DHGVERSION="\"$(GITVERSION)\"" -Wall -s
LDFLAGS += -s

# Build targets

$(BUILD): $(OBJ)
	$(CC) $(LDFLAGS) $< -o $@

$(OBJ): $(SRC)
	$(CC) $(CFLAGS) -c $< -o $@

$(SRC): $(GITVERFILE)
	git submodule update --init --force --checkout

# | $(OUT_DIR) ignores timestamp; only runs mkdir once
$(GITVERFILE): | $(OUT_DIR)
	cmp -s $(cat $@) $(GITVERSION) || echo $(GITVERSION) > $@

$(OUT_DIR):
	mkdir -p $@

.PHONY: all clean install docker-build docker-push

all: $(BUILD)

clean:
	rm -rf $(OUT_DIR)

install: $(BUILD)
	install -m 0751 -t $(INSTALL_DIR) $<

docker-build: $(BUILD)
	IMAGE_VERSION=$(GITVERSION) \
		docker compose -f docker/docker-compose.yaml \
		build

docker-push: docker-build
# TODO: Finish docker-push