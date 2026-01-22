package cli

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"

	"github.com/smileynet/line-cook/internal/beads"
	"github.com/smileynet/line-cook/internal/output"
)

var (
	initForce  bool
	initDryRun bool
)

func init() {
	initCmd.Flags().BoolVar(&initForce, "force", false, "Overwrite existing Line Cook section")
	initCmd.Flags().BoolVar(&initDryRun, "dry-run", false, "Show what would be appended without making changes")
	rootCmd.AddCommand(initCmd)
}

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Add Line Cook workflow context to AGENTS.md",
	Long: `Init appends Line Cook workflow context to project's AGENTS.md file.

This command:
1. Checks for .beads/ (requires beads to be initialized)
2. Checks if ## Line Cook Workflow section exists
3. Appends workflow context (or overwrites with --force)

Similar to 'bd prime', this command helps agents recover context.`,
	RunE: runInit,
}

func detectPlatform() string {
	_, err := os.Stat("/home/sam/.opencode/bin/opencode")
	if err == nil {
		return "opencode"
	}
	_, err = os.Stat("/usr/local/bin/claude")
	if err == nil {
		return "claude-code"
	}
	_, err = os.Stat(os.ExpandEnv("$HOME/.kiro/bin/kiro"))
	if err == nil {
		return "kiro"
	}
	return "cli-only"
}

func getCommandTable(platform string) string {
	switch platform {
	case "opencode":
		return "| Command | Purpose |\n|---------|---------|\n| /line-prep | Sync git/beads, show ready tasks |\n| /line-cook | Execute task with guardrails |\n| /line-serve | AI peer review |\n| /line-tidy | Commit, file findings, push |\n| /line-work | Full cycle orchestration |"
	case "claude-code":
		return "| Command | Purpose |\n|---------|---------|\n| /line:prep | Sync git/beads, show ready tasks |\n| /line:cook | Execute task with guardrails |\n| /line:serve | AI peer review |\n| /line:tidy | Commit, file findings, push |\n| /line:work | Full cycle orchestration |"
	case "kiro":
		return "| Command | Purpose |\n|---------|---------|\n| prep | Sync git/beads, show ready tasks |\n| cook | Execute task with guardrails |\n| serve | AI peer review |\n| tidy | Commit, file findings, push |\n| work | Full cycle orchestration |"
	default:
		return "| Command | Purpose |\n|---------|---------|\n| lc prep | Sync git/beads, show ready tasks |\n| lc cook | Execute task with guardrails |\n| lc serve | AI peer review |\n| lc tidy | Commit, file findings, push |\n| lc work | Full cycle orchestration |"
	}
}

func getCLITable(platform string) string {
	// Note: Cannot use backticks in Go string literals with raw strings due to escaping
	// Using plain text representation instead
	switch platform {
	case "opencode":
		return "OpenCode Commands\n" +
			"  /line-prep\n" +
			"  /line-cook [id]\n" +
			"  /line-serve [id]\n" +
			"  /line-tidy\n" +
			"  /line-work\n"
	case "claude-code":
		return "Claude Code Commands\n" +
			"  /line:prep\n" +
			"  /line:cook [id]\n" +
			"  /line:serve [id]\n" +
			"  /line:tidy\n" +
			"  /line:work\n"
	case "kiro":
		return "Kiro Commands\n" +
			"  prep\n" +
			"  cook [id]\n" +
			"  serve [id]\n" +
			"  tidy\n" +
			"  work\n"
	default:
		return "CLI Commands\n" +
			"  lc prep\n" +
			"  lc cook [id]\n" +
			"  lc serve [id]\n" +
			"  lc tidy\n" +
			"  lc work\n"
	}
}

const sectionMarker = "## Line Cook Workflow"

func runInit(cmd *cobra.Command, args []string) error {
	workDir, _ := os.Getwd()
	beadsClient := beads.NewClient(workDir)
	out := output.NewFormatter(jsonOutput, verbose, quiet)

	// Check for beads
	if !beadsClient.HasBeads() {
		out.Error("No .beads/ directory found. Run 'bd init' first.")
		return nil
	}

	agentsMD := filepath.Join(workDir, "AGENTS.md")

	// Read existing AGENTS.md
	var existingContent string
	if data, err := os.ReadFile(agentsMD); err == nil {
		existingContent = string(data)
	}

	// Check if section already exists
	hasSection := strings.Contains(existingContent, sectionMarker)

	if hasSection && !initForce {
		out.Success("Line Cook section already exists in AGENTS.md")
		out.Text("Use --force to overwrite")
		return nil
	}

	// Detect platform
	platform := detectPlatform()
	out.Text("Detected platform: %s", platform)

	// Build section content
	commandsTable := getCommandTable(platform)
	cliTable := getCLITable(platform)
	lineCookSection := "## Line Cook Workflow\n\n"
	lineCookSection += "> **Context Recovery**: Run lc work or individual commands after compaction\n\n"
	lineCookSection += "### Commands\n"
	lineCookSection += commandsTable + "\n\n"
	lineCookSection += "### CLI\n"
	lineCookSection += cliTable + "\n\n"
	lineCookSection += "### Core Guardrails\n"
	lineCookSection += "1. **Sync before work** - Always start with current state\n"
	lineCookSection += "2. **One task at a time** - Focus prevents scope creep\n"
	lineCookSection += "3. **Verify before done** - Tests pass, code compiles\n"
	lineCookSection += "4. **File, don't block** - Discoveries become beads\n"
	lineCookSection += "5. **Push before stop** - Work isn't done until pushed"

	// Prepare new content
	var newContent string
	if hasSection && initForce {
		// Remove existing section and everything after it until next ## or EOF
		idx := strings.Index(existingContent, sectionMarker)
		beforeSection := existingContent[:idx]

		// Find next ## section after Line Cook
		afterSection := existingContent[idx+len(sectionMarker):]
		nextSectionIdx := strings.Index(afterSection, "\n## ")
		if nextSectionIdx >= 0 {
			// Keep content after Line Cook section
			afterSection = afterSection[nextSectionIdx:]
		} else {
			afterSection = ""
		}

		newContent = strings.TrimRight(beforeSection, "\n") + "\n\n" + lineCookSection
		if afterSection != "" {
			newContent += "\n" + strings.TrimLeft(afterSection, "\n")
		}
	} else {
		// Append section
		if existingContent == "" {
			newContent = lineCookSection
		} else {
			newContent = strings.TrimRight(existingContent, "\n") + "\n\n" + lineCookSection
		}
	}

	if initDryRun {
		out.Header("DRY RUN - Would append to AGENTS.md:")
		out.Text("")
		out.Text("%s", lineCookSection)
		return nil
	}

	// Write to file
	if err := os.WriteFile(agentsMD, []byte(newContent), 0644); err != nil {
		out.Error("Failed to write AGENTS.md: %v", err)
		return nil
	}

	if hasSection && initForce {
		out.Success("Replaced Line Cook section in AGENTS.md")
	} else {
		out.Success("Added Line Cook workflow context to AGENTS.md")
	}

	return nil
}
