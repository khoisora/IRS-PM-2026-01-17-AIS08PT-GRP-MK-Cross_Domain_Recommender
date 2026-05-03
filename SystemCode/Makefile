IMAGE_NAME := crossrec
CONTAINER_NAME := crossrec-app
PORT := 8000

# Python interpreter used to bootstrap .venv (recommended: 3.11+).
# Override on the CLI, e.g.: make install PYTHON=python3.11
PYTHON ?= python3

.PHONY: install export dev all rebuild download-data \
        build run stop logs restart clean

# Raw Amazon Reviews 2023 dataset (McAuley Lab, UCSD) — inputs to process_data.py
RAW_DIR := ml/data/amazon_2023/raw
AMAZON_BASE := https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw

# ============================================================
# Local (non-Docker) workflow
# ============================================================

# Create venv and install Python dependencies
install:
	@$(PYTHON) --version
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

# Export model artifacts (run before first build or first dev run)
export:
	PYTHONPATH=. .venv/bin/python ml/scripts/export_demo_artifacts.py

# Run locally without Docker
dev:
	PYTHONPATH=. .venv/bin/uvicorn backend.demo.main:app --host 0.0.0.0 --port $(PORT) --reload

# New-user path: install deps then run dev server (uses pre-built artifacts/demo/)
all: install dev

# Re-train and re-export artifacts, then run dev server
retrain: install export dev

# Download the 4 raw JSONL.gz files (~3.3 GB) into ml/data/amazon_2023/raw/.
# Source: McAuley Lab — https://amazon-reviews-2023.github.io/
# Required only if you want to run process_data.py from scratch; the demo
# ships with pre-built artifacts/demo/ and does not need this.
download-data:
	@mkdir -p $(RAW_DIR)
	curl -L --fail --progress-bar -o $(RAW_DIR)/movies_reviews_2023.jsonl.gz $(AMAZON_BASE)/review_categories/Movies_and_TV.jsonl.gz
	curl -L --fail --progress-bar -o $(RAW_DIR)/movies_meta_2023.jsonl.gz    $(AMAZON_BASE)/meta_categories/meta_Movies_and_TV.jsonl.gz
	curl -L --fail --progress-bar -o $(RAW_DIR)/games_reviews_2023.jsonl.gz  $(AMAZON_BASE)/review_categories/Video_Games.jsonl.gz
	curl -L --fail --progress-bar -o $(RAW_DIR)/games_meta_2023.jsonl.gz     $(AMAZON_BASE)/meta_categories/meta_Video_Games.jsonl.gz
	@echo "Raw dataset downloaded to $(RAW_DIR)"

# ============================================================
# Docker workflow
# ============================================================

# Build Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run container (detached). SQLite DB lives inside the container.
# To persist ratings across restarts, add: -v $(PWD)/data:/app/data
run:
	docker run -d --name $(CONTAINER_NAME) \
		-p $(PORT):8000 \
		$(IMAGE_NAME)
	@echo "CrossRec running at http://localhost:$(PORT)"

# Stop and remove container
stop:
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true

# View logs
logs:
	docker logs -f $(CONTAINER_NAME)

# Stop, rebuild, run
restart: stop build run

# Remove image and container
clean: stop
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
