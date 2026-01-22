package cli

import (
	"os"

	"github.com/spf13/cobra"

	"github.com/smileynet/line-cook/internal/beads"
	"github.com/smileynet/line-cook/internal/environment"
	"github.com/smileynet/line-cook/internal/git"
	"github.com/smileynet/line-cook/internal/output"
	"github.com/smileynet/line-cook/internal/session"
)

func init() {
	rootCmd.AddCommand(prepCmd)
}

var prepCmd = &cobra.Command{
	Use:   "prep",
	Short: "Sync state, load context, show ready tasks",
	Long: `Prep synchronizes git and beads state, then displays available work.

This is a fully mechanical operation that:
1. Fetches and pulls from git origin
2. Syncs beads (if .beads/ exists)
3. Shows ready tasks (filtering out parking-lot epics)
4. Identifies the next recommended task`,
	RunE: runPrep,
}

func runPrep(cmd *cobra.Command, args []string) error {
	workDir, _ := os.Getwd()
	gitClient := git.NewClient(workDir)
	beadsClient := beads.NewClient(workDir)
	out := output.NewFormatter(jsonOutput, verbose, quiet)

	// Detect environment and capabilities
	envDetector := environment.NewDetector(workDir)
	capabilities := envDetector.GetCapabilities()

	// Check if we're in a git repo
	if !gitClient.IsRepo() {
		out.Error("Not a git repository")
		return nil
	}

	result := &output.PrepResult{
		Project:      gitClient.ProjectName(),
		Capabilities: capabilities,
	}

	// Get branch
	branch, err := gitClient.Branch()
	if err != nil {
		out.Error("Failed to get branch: %v", err)
		return nil
	}
	result.Branch = branch

	// Sync git
	syncStatus := "up to date"
	if err := gitClient.FetchAndPull(); err != nil {
		syncStatus = "sync failed: " + err.Error()
		out.Warning("Git sync failed: %v", err)
	}
	result.SyncStatus = syncStatus

	// Sync beads if present
	if beadsClient.HasBeads() {
		if err := beadsClient.Sync(); err != nil {
			out.Warning("Beads sync failed: %v", err)
		}

		// Get ready tasks (filtered)
		ready, err := beadsClient.FilterReadyTasks()
		if err != nil {
			out.Warning("Failed to get ready tasks: %v", err)
		} else {
			result.ReadyTasks = ready
		}

		// Get in-progress tasks
		inProgress, err := beadsClient.List(beads.ListOptions{Status: "in_progress"})
		if err != nil {
			out.Warning("Failed to get in-progress tasks: %v", err)
		} else {
			result.InProgress = inProgress
		}

		// Get blocked tasks
		blocked, err := beadsClient.Blocked()
		if err != nil {
			out.Warning("Failed to get blocked tasks: %v", err)
		} else {
			result.Blocked = blocked
		}

		// Determine next task
		if len(result.ReadyTasks) > 0 {
			nextTask := result.ReadyTasks[0]

			// Check if it's an epic
			if nextTask.IsEpic() {
				result.Epic = &nextTask

				// Find first ready child of the epic
				children, err := beadsClient.List(beads.ListOptions{Parent: nextTask.ID})
				if err == nil {
					for _, child := range children {
						if child.IsOpen() {
							result.NextTask = &child
							break
						}
					}
				}
			} else {
				result.NextTask = &nextTask
			}
		}
	}

	// Initialize session state
	stateMgr, err := session.NewStateManager()
	if err == nil {
		stateMgr.StartSession(workDir, branch)
	}

	// Output
	return out.Output(result, func() {
		out.Header("SESSION: " + result.Project + " @ " + result.Branch)
		out.Text("")

		// Sync status
		if syncStatus == "up to date" {
			out.Success("Sync: up to date")
		} else {
			out.Warning("Sync: %s", syncStatus)
		}
		out.Text("")

		// Task counts
		out.Text("Ready: %d tasks", len(result.ReadyTasks))
		out.Text("In progress: %d", len(result.InProgress))
		out.Text("Blocked: %d", len(result.Blocked))

		// Epic context if applicable
		if result.Epic != nil {
			out.Text("")
			out.Text("EPIC IN FOCUS:")
			out.Text("  %s [P%d] %s", result.Epic.ID, result.Epic.Priority, result.Epic.Title)
		}

		// Next task
		if result.NextTask != nil {
			out.Text("")
			if result.Epic != nil {
				out.Text("NEXT TASK (part of epic):")
			} else {
				out.Text("NEXT TASK:")
			}
			out.Text("  %s [P%d] %s", result.NextTask.ID, result.NextTask.Priority, result.NextTask.Title)
			if result.NextTask.Description != "" {
				// Show first line of description
				desc := result.NextTask.Description
				if idx := firstNewline(desc); idx > 0 {
					desc = desc[:idx]
				}
				if len(desc) > 60 {
					desc = desc[:57] + "..."
				}
				out.Text("  %s", desc)
			}
		} else if len(result.ReadyTasks) == 0 {
			out.Text("")
			out.Text("No actionable tasks ready.")
			out.Text("All ready tasks may be in Retrospective or Backlog epics.")
			out.Text("")
			out.Text("To work on parked items: lc cook <specific-task-id>")
		}

		out.Text("")
		out.Text("NEXT STEP: lc cook")
		if result.NextTask != nil {
			out.Text("           (or lc cook %s for this task)", result.NextTask.ID)
		}
	})
}

func firstNewline(s string) int {
	for i, c := range s {
		if c == '\n' {
			return i
		}
	}
	return -1
}
