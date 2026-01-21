# Line Cook CLI Makefile

# Build variables
VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
COMMIT ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "none")
BUILD_DATE ?= $(shell date -u +"%Y-%m-%dT%H:%M:%SZ")

# Go variables
GOCMD = go
GOBUILD = $(GOCMD) build
GOTEST = $(GOCMD) test
GOVET = $(GOCMD) vet
GOFMT = gofmt
GOMOD = $(GOCMD) mod

# Build flags
LDFLAGS = -ldflags "-X github.com/smileynet/line-cook/internal/cli.Version=$(VERSION) \
	-X github.com/smileynet/line-cook/internal/cli.Commit=$(COMMIT) \
	-X github.com/smileynet/line-cook/internal/cli.BuildDate=$(BUILD_DATE)"

# Output
BINARY = lc
BINARY_DIR = bin

.PHONY: all build test clean install uninstall fmt vet lint tidy help

## Build targets

all: build ## Build the binary (default)

build: ## Build the lc binary
	@mkdir -p $(BINARY_DIR)
	$(GOBUILD) $(LDFLAGS) -o $(BINARY_DIR)/$(BINARY) ./cmd/lc

build-all: ## Build for all platforms
	@mkdir -p $(BINARY_DIR)
	GOOS=linux GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BINARY_DIR)/$(BINARY)-linux-amd64 ./cmd/lc
	GOOS=linux GOARCH=arm64 $(GOBUILD) $(LDFLAGS) -o $(BINARY_DIR)/$(BINARY)-linux-arm64 ./cmd/lc
	GOOS=darwin GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BINARY_DIR)/$(BINARY)-darwin-amd64 ./cmd/lc
	GOOS=darwin GOARCH=arm64 $(GOBUILD) $(LDFLAGS) -o $(BINARY_DIR)/$(BINARY)-darwin-arm64 ./cmd/lc
	GOOS=windows GOARCH=amd64 $(GOBUILD) $(LDFLAGS) -o $(BINARY_DIR)/$(BINARY)-windows-amd64.exe ./cmd/lc

## Test targets

test: ## Run tests
	$(GOTEST) -v ./...

test-coverage: ## Run tests with coverage
	$(GOTEST) -v -coverprofile=coverage.out ./...
	$(GOCMD) tool cover -html=coverage.out -o coverage.html

## Code quality

fmt: ## Format code
	$(GOFMT) -s -w .

vet: ## Run go vet
	$(GOVET) ./...

lint: vet fmt ## Run all linters

## Dependencies

tidy: ## Tidy and verify dependencies
	$(GOMOD) tidy
	$(GOMOD) verify

## Install targets

install: build ## Install lc to /usr/local/bin
	@echo "Installing $(BINARY) to /usr/local/bin..."
	@sudo cp $(BINARY_DIR)/$(BINARY) /usr/local/bin/$(BINARY)
	@echo "Installed successfully. Run 'lc --help' to get started."

install-local: build ## Install lc to ~/bin (no sudo)
	@mkdir -p ~/bin
	@cp $(BINARY_DIR)/$(BINARY) ~/bin/$(BINARY)
	@echo "Installed to ~/bin/$(BINARY)"
	@echo "Make sure ~/bin is in your PATH"

uninstall: ## Remove lc from /usr/local/bin
	@sudo rm -f /usr/local/bin/$(BINARY)
	@echo "Uninstalled $(BINARY)"

## Cleanup

clean: ## Remove build artifacts
	@rm -rf $(BINARY_DIR)
	@rm -f coverage.out coverage.html

## Help

help: ## Show this help
	@echo "Line Cook CLI - Makefile targets"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
