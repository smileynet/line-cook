package cli

import (
	"github.com/spf13/cobra"

	"github.com/smileynet/line-cook/internal/output"
)

func init() {
	rootCmd.AddCommand(workCmd)
}

var workCmd = &cobra.Command{
	Use:   "work [task-id]",
	Short: "Full cycle orchestration: prep → cook → serve → tidy",
	Long: `Work orchestrates the full prep → cook → serve → tidy cycle.

Note: The full cycle requires AI to handle the cook and serve phases.
In non-interactive mode, this command outputs the context needed for each phase
and expects the calling TUI to handle AI execution between CLI calls.

For interactive use, run each command separately:
  lc prep    # Sync and show ready tasks
  lc cook    # Claim task and get execution context
  lc serve   # Get review context
  lc tidy    # Commit and push

This command is primarily useful for:
- Getting an overview of the full workflow
- Testing the cycle end-to-end
- Automation where the TUI handles AI integration`,
	RunE: runWork,
}

func runWork(cmd *cobra.Command, args []string) error {
	out := output.NewFormatter(jsonOutput, verbose, quiet)

	// In JSON mode, output a workflow descriptor
	if jsonOutput {
		result := &output.WorkResult{
			Phase:   "workflow",
			Message: "Full cycle requires TUI to handle AI phases between CLI calls",
		}
		return out.JSON(result)
	}

	// In text mode, explain the workflow
	out.Header("WORK: Full Cycle Orchestration")
	out.Text("")
	out.Text("The work cycle consists of 4 phases:")
	out.Text("")
	out.Text("  1. PREP  (mechanical)  - Sync git, show ready tasks")
	out.Text("     → lc prep")
	out.Text("")
	out.Text("  2. COOK  (AI-assisted) - Execute the selected task")
	out.Text("     → lc cook [id]")
	out.Text("     → AI executes task using returned context")
	out.Text("")
	out.Text("  3. SERVE (AI-assisted) - Review the completed work")
	out.Text("     → lc serve [id]")
	out.Text("     → AI reviews using returned context")
	out.Text("")
	out.Text("  4. TIDY  (mechanical)  - Commit and push changes")
	out.Text("     → lc tidy")
	out.Text("")
	out.Text("For automated workflows, the TUI invokes each CLI command")
	out.Text("and handles AI execution between them.")
	out.Text("")
	out.Text("To start the cycle manually:")
	out.Text("")
	out.Text("  lc prep")
	out.Text("")

	// Actually run prep to get started
	return runPrep(cmd, args)
}
