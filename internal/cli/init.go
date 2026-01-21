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
	Long: `Init appends Line Cook workflow context to the project's AGENTS.md file.

This command:
1. Checks for .beads/ (requires beads to be initialized)
2. Checks if ## Line Cook Workflow section exists
3. Appends workflow context (or overwrites with --force)

Similar to 'bd prime', this command helps agents recover context.`,
	RunE: runInit,
}

const lineCookSection = `## Line Cook Workflow

> **Context Recovery**: Run ` + "`lc work`" + ` or individual commands after compaction

### Commands
| Command | Purpose |
|---------|---------|
| ` + "`/line:prep`" + ` | Sync git/beads, show ready tasks |
| ` + "`/line:cook`" + ` | Execute task with guardrails |
| ` + "`/line:serve`" + ` | AI peer review |
| ` + "`/line:tidy`" + ` | Commit, file findings, push |
| ` + "`/line:work`" + ` | Full cycle orchestration |

### CLI
` + "```bash" + `
lc prep              # Sync and show ready tasks
lc cook [id]         # Claim task, output AI context
lc serve [id]        # Output diff and review context
lc tidy              # Commit and push
lc init              # Add this section to AGENTS.md
` + "```" + `

### Core Guardrails
1. **Sync before work** - Always start with current state
2. **One task at a time** - Focus prevents scope creep
3. **Verify before done** - Tests pass, code compiles
4. **File, don't block** - Discoveries become beads
5. **Push before stop** - Work isn't done until pushed
`

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

	// Write the file
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
