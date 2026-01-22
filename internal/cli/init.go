package cli

import (
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"

	"github.com/smileynet/line-cook/internal/beads"
	"github.com/smileynet/line-cook/internal/output"
)

var (
	initForce       bool
	initDryRun      bool
	initWithContext bool
)

func init() {
	initCmd.Flags().BoolVar(&initForce, "force", false, "Overwrite existing Line Cook section")
	initCmd.Flags().BoolVar(&initDryRun, "dry-run", false, "Show what would be appended without making changes")
	initCmd.Flags().BoolVar(&initWithContext, "with-context", false, "Append beads context from 'bd prime --export'")
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

const sectionMarker = "## Line Cook Workflow"

func getBeadsContext(workDir string) (string, error) {
	cmd := exec.Command("bd", "prime", "--export")
	cmd.Dir = workDir

	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", err
	}

	return string(output), nil
}

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

	// Build CLI-only section content
	lineCookSection := "## Line Cook Workflow\n\n"
	lineCookSection += "> **Context Recovery**: Run `lc work` or individual commands after compaction\n\n"
	lineCookSection += "### Core Commands\n"
	lineCookSection += "| Command | Purpose |\n|---------|---------|\n"
	lineCookSection += "| `lc prep` | Sync git/beads, show ready tasks |\n"
	lineCookSection += "| `lc cook [id]` | Execute task with guardrails |\n"
	lineCookSection += "| `lc serve` | AI peer review |\n"
	lineCookSection += "| `lc tidy` | Commit, file findings, push |\n"
	lineCookSection += "| `lc work` | Full cycle orchestration |\n\n"
	lineCookSection += "### Core Guardrails\n"
	lineCookSection += "1. **Sync before work** - Always start with current state\n"
	lineCookSection += "2. **One task at a time** - Focus prevents scope creep\n"
	lineCookSection += "3. **Verify before done** - Tests pass, code compiles\n"
	lineCookSection += "4. **File, don't block** - Discoveries become beads\n"
	lineCookSection += "5. **Push before stop** - Work isn't done until pushed"

	// Append beads context if requested
	if initWithContext {
		beadsContext, err := getBeadsContext(workDir)
		if err != nil {
			out.Error("Failed to get beads context: %v", err)
			out.Text("Continuing without beads context...")
		} else {
			lineCookSection += "\n\n### Beads Context\n\n"
			lineCookSection += beadsContext
		}
	}

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
