# Define variables
CONFIG_DIR=./config
OUTPUT_DIR=./docker

# Default target
all: install

# Target to create output directory
create_output_dir:
	@mkdir -p $(OUTPUT_DIR)

# Function to save Docker image as a .tar.xz file
define save_image
	$(eval IMAGE_NAME := $(shell jq -r '.image' $(1)))
	$(eval IMAGE_TAG := $(shell echo $(IMAGE_NAME) | cut -d':' -f2))
	$(eval IMAGE_REPO := $(shell echo $(IMAGE_NAME) | cut -d':' -f1))
	$(eval OUTPUT_FILE := $(OUTPUT_DIR)/$$(notdir $(IMAGE_REPO)).tar.xz)
	docker pull $(IMAGE_NAME)
	docker save $(IMAGE_NAME) | xz > $(OUTPUT_FILE)
	@echo "Saved $(IMAGE_NAME) to $(OUTPUT_FILE)"
endef

# Install phase
install: create_output_dir
	$(foreach file, $(wildcard $(CONFIG_DIR)/*), $(call save_image,$(file)))
	@echo "Installation complete."

.PHONY: all create_output_dir install