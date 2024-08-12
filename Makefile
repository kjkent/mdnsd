# Makefile for mdns-repeater by geekman
# https://github.com/geekman/mdns-repeater

NAME := mdns-repeater

INSTALL_DIR := $(PREFIX)/bin
OUT_DIR := build
SRC_DIR := lib/mdns-repeater

TARGET := $(OUT_DIR)/$(NAME)
SRC := $(SRC_DIR)/$(NAME).c
OBJ := $(TARGET).o

GITVERFILE := $(OUT_DIR)/gitversion
GITVERSION := $(shell git rev-parse --short=8 HEAD 2>/dev/null || echo -n 'unknown')

CFLAGS += -DHGVERSION="\"$(GITVERSION)\"" -Wall -s
LDFLAGS += -s

$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) $< -o $@

$(OBJ): $(GITVERFILE)
	$(CC) $(CFLAGS) -c $(SRC) -o $@

.PHONY: all clean install docker-build docker-push

all: $(TARGET)

clean:
	@rm -rf $(OUT_DIR)

install: $(TARGET)
	install -m 0751 -t $(INSTALL_DIR) $(TARGET)

$(OUT_DIR):
	mkdir -p $(OUT_DIR)

# | $(OUT_DIR) ignores timestamp; only runs mkdir once
$(GITVERFILE): | $(OUT_DIR)
	cmp -s $(cat $@) $(GITVERSION) || echo $(GITVERSION) > $@

docker-build: $(TARGET)
	IMAGE_VERSION=$(GITVERSION) \
		docker compose -f docker/docker-compose.yaml \
		build

docker-push: docker-build
# TODO: Finish docker-push