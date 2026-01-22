package environment

import (
	"os"
	"path/filepath"
)

// Platform represents the AI coding platform
type Platform string

const (
	PlatformClaudeCode Platform = "claude-code"
	PlatformOpenCode   Platform = "opencode"
	PlatformKiro       Platform = "kiro"
	PlatformCLIOnly    Platform = "cli-only"
)

// Capability represents a feature capability
type Capability string

const (
	CapabilityMCP         Capability = "mcp"
	CapabilityHeadless    Capability = "headless"
	CapabilityFileOutput  Capability = "file-output"
	CapabilityInteractive Capability = "interactive"
)

// CapabilitiesResult contains detected capabilities
type CapabilitiesResult struct {
	Platform     Platform     `json:"platform"`
	Capabilities []Capability `json:"capabilities"`
	MCPEnabled   bool         `json:"mcp_enabled"`
	Interactive  bool         `json:"interactive"`
}

// HasCapability checks if a specific capability is available
func (c *CapabilitiesResult) HasCapability(cap Capability) bool {
	for _, available := range c.Capabilities {
		if available == cap {
			return true
		}
	}
	return false
}

// Detector detects platform and capabilities
type Detector struct {
	workDir string
}

// NewDetector creates a new capability detector
func NewDetector(workDir string) *Detector {
	return &Detector{workDir: workDir}
}

// DetectPlatform detects the current platform
func (d *Detector) DetectPlatform() Platform {
	if os.Getenv("CLAUDE_PROJECT_DIR") != "" {
		return PlatformClaudeCode
	}
	if os.Getenv("OPENCODE") == "1" {
		return PlatformOpenCode
	}
	if os.Getenv("KIRO") == "1" {
		return PlatformKiro
	}
	return PlatformCLIOnly
}

// DetectCapabilities detects available capabilities
func (d *Detector) DetectCapabilities() []Capability {
	var caps []Capability

	if d.HasCapability(CapabilityMCP) {
		caps = append(caps, CapabilityMCP)
	}
	if d.HasCapability(CapabilityHeadless) {
		caps = append(caps, CapabilityHeadless)
	}
	if d.HasCapability(CapabilityFileOutput) {
		caps = append(caps, CapabilityFileOutput)
	}
	if d.HasCapability(CapabilityInteractive) {
		caps = append(caps, CapabilityInteractive)
	}

	return caps
}

// HasCapability checks if a specific capability is available
func (d *Detector) HasCapability(cap Capability) bool {
	switch cap {
	case CapabilityMCP:
		return d.detectMCP()
	case CapabilityHeadless:
		return d.detectHeadless()
	case CapabilityFileOutput:
		return d.detectFileOutput()
	case CapabilityInteractive:
		return !d.detectHeadless()
	default:
		return false
	}
}

// GetCapabilities returns full capabilities result
func (d *Detector) GetCapabilities() *CapabilitiesResult {
	return &CapabilitiesResult{
		Platform:     d.DetectPlatform(),
		Capabilities: d.DetectCapabilities(),
		MCPEnabled:   d.HasCapability(CapabilityMCP),
		Interactive:  !d.detectHeadless(),
	}
}

// detectMCP checks if MCP is available
func (d *Detector) detectMCP() bool {
	// Check for MCP configuration file
	mcpConfig := filepath.Join(d.workDir, ".mcp.json")
	if _, err := os.Stat(mcpConfig); err == nil {
		return true
	}

	// Check for MCP-related environment variables
	if os.Getenv("CLAUDE_MCP_SERVER") != "" {
		return true
	}
	if os.Getenv("CLAUDE_MCP_ENABLED") == "1" {
		return true
	}

	// Check for Claude Code which has MCP built-in
	if os.Getenv("CLAUDE_PROJECT_DIR") != "" {
		return true
	}

	return false
}

// detectHeadless checks if running in headless mode
func (d *Detector) detectHeadless() bool {
	// Check for explicit headless flag
	if os.Getenv("HEADLESS") == "1" {
		return true
	}

	// Check if stdin is a pipe or redirected (not a TTY)
	// This is a simplified check - for a full check, we'd use golang.org/x/crypto/ssh/terminal
	// or the newer "golang.org/x/term" package's IsTerminal
	if os.Getenv("TERM") == "dumb" {
		return true
	}

	return false
}

// detectFileOutput checks if file output is available
func (d *Detector) detectFileOutput() bool {
	// Check if we can write to the work directory
	testFile := filepath.Join(d.workDir, ".write_test")
	file, err := os.Create(testFile)
	if err != nil {
		return false
	}
	file.Close()
	os.Remove(testFile)
	return true
}
