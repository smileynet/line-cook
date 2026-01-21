package cli

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"

	"github.com/smileynet/line-cook/internal/beads"
	"github.com/smileynet/line-cook/internal/git"
	"github.com/smileynet/line-cook/internal/output"
	"github.com/smileynet/line-cook/internal/session"
)

var (
	tidyMessage string
	tidyNoPush  bool
)

func init() {
	tidyCmd.Flags().StringVarP(&tidyMessage, "message", "m", "", "Commit message (auto-generated if not provided)")
	tidyCmd.Flags().BoolVar(&tidyNoPush, "no-push", false, "Skip pushing to remote")
	rootCmd.AddCommand(tidyCmd)
}

var tidyCmd = &cobra.Command{
	Use:   "tidy",
	Short: "Commit findings, push changes",
	Long: `Tidy commits changes and pushes to remote.

This is a fully mechanical operation that:
1. Files any findings from the session as beads
2. Closes in-progress tasks if changes match
3. Commits all changes
4. Syncs beads
5. Pushes to remote`,
	RunE: runTidy,
}

func runTidy(cmd *cobra.Command, args []string) error {
	workDir, _ := os.Getwd()
	gitClient := git.NewClient(workDir)
	beadsClient := beads.NewClient(workDir)
	out := output.NewFormatter(jsonOutput, verbose, quiet)

	if !gitClient.IsRepo() {
		out.Error("Not a git repository")
		return nil
	}

	result := &output.TidyResult{}

	// Load session state
	var currentTaskID string
	stateMgr, _ := session.NewStateManager()
	if stateMgr != nil {
		state, err := stateMgr.Load()
		if err == nil && state.CurrentTask != nil {
			currentTaskID = state.CurrentTask.ID
		}

		// File findings as beads
		if err == nil && len(state.Findings) > 0 && beadsClient.HasBeads() {
			for _, finding := range state.Findings {
				priority := finding.Priority
				taskType := "task"
				if finding.Type == session.FindingBug {
					taskType = "bug"
				}

				id, err := beadsClient.Create(beads.CreateOptions{
					Title:       finding.Title,
					Type:        taskType,
					Priority:    &priority,
					Description: finding.Description,
				})
				if err == nil {
					result.FiledBeads = append(result.FiledBeads, strings.TrimSpace(id))
				}
			}
			stateMgr.ClearFindings()
		}
	}

	// Check for changes
	clean, err := gitClient.IsClean()
	if err != nil {
		out.Error("Failed to check git status: %v", err)
		return nil
	}

	if clean {
		out.Text("No changes to commit.")

		// Still try to close task if one was in progress
		if currentTaskID != "" && beadsClient.HasBeads() {
			if err := beadsClient.Close(currentTaskID, "Completed via lc tidy"); err == nil {
				result.ClosedBeads = append(result.ClosedBeads, currentTaskID)
				if stateMgr != nil {
					stateMgr.CompleteTask(currentTaskID)
				}
			}
		}

		// Sync beads
		if beadsClient.HasBeads() {
			beadsClient.Sync()
		}

		// Push if there are unpushed commits
		if !tidyNoPush {
			unpushed, _ := gitClient.HasUnpushedCommits()
			if unpushed {
				if err := gitClient.Push(); err != nil {
					out.Warning("Push failed: %v", err)
				} else {
					result.Pushed = true
				}
			}
		}

		return out.Output(result, func() {
			out.Header("TIDY: Complete")
			out.Text("")
			if len(result.ClosedBeads) > 0 {
				out.Success("Closed: %s", strings.Join(result.ClosedBeads, ", "))
			}
			if result.Pushed {
				out.Success("Pushed to remote")
			}
			out.Text("")
			out.Text("NEXT STEP: lc prep (for next task)")
		})
	}

	// Stage all changes
	if err := gitClient.AddAll(); err != nil {
		out.Error("Failed to stage changes: %v", err)
		return nil
	}

	// Generate commit message if not provided
	commitMsg := tidyMessage
	if commitMsg == "" {
		commitMsg = generateCommitMessage(gitClient, beadsClient, currentTaskID)
	}

	// Commit
	commitOutput, err := gitClient.Commit(commitMsg)
	if err != nil {
		out.Error("Commit failed: %v", err)
		return nil
	}
	out.Verbose("Commit: %s", commitOutput)

	// Get commit SHA
	sha, _ := gitClient.GetLastCommitSHA()
	if len(sha) > 7 {
		sha = sha[:7]
	}
	result.CommitSHA = sha

	// Close current task if any
	if currentTaskID != "" && beadsClient.HasBeads() {
		if err := beadsClient.Close(currentTaskID, fmt.Sprintf("Completed in commit %s", sha)); err == nil {
			result.ClosedBeads = append(result.ClosedBeads, currentTaskID)
			if stateMgr != nil {
				stateMgr.CompleteTask(currentTaskID)
			}
		}
	}

	// Sync beads
	if beadsClient.HasBeads() {
		if err := beadsClient.Sync(); err != nil {
			out.Warning("Beads sync failed: %v", err)
		}
	}

	// Push
	if !tidyNoPush {
		if err := gitClient.Push(); err != nil {
			out.Warning("Push failed: %v", err)
		} else {
			result.Pushed = true
		}
	}

	result.Summary = commitMsg

	return out.Output(result, func() {
		out.Header("TIDY: Complete")
		out.Text("")
		out.Success("Committed: %s", sha)
		out.Text("  %s", commitMsg)
		out.Text("")

		if len(result.FiledBeads) > 0 {
			out.Success("Filed %d beads: %s", len(result.FiledBeads), strings.Join(result.FiledBeads, ", "))
		}
		if len(result.ClosedBeads) > 0 {
			out.Success("Closed: %s", strings.Join(result.ClosedBeads, ", "))
		}
		if result.Pushed {
			out.Success("Pushed to remote")
		} else if tidyNoPush {
			out.Text("Skipped push (--no-push)")
		} else {
			out.Warning("Push failed or not attempted")
		}
		out.Text("")
		out.Text("NEXT STEP: lc prep (for next task)")
	})
}

func generateCommitMessage(gitClient *git.Client, beadsClient *beads.Client, taskID string) string {
	// Try to get task title for commit message
	if taskID != "" && beadsClient.HasBeads() {
		task, err := beadsClient.Show(taskID)
		if err == nil {
			// Use task title as commit message
			msg := task.Title
			// Normalize to lowercase and add prefix based on type
			switch task.IssueType {
			case "bug":
				msg = "fix: " + strings.ToLower(msg)
			case "feature":
				msg = "feat: " + strings.ToLower(msg)
			default:
				if !strings.Contains(strings.ToLower(msg), ":") {
					msg = "chore: " + strings.ToLower(msg)
				}
			}
			return msg
		}
	}

	// Fallback to generic message
	changedFiles, _ := gitClient.ChangedFiles()
	if len(changedFiles) == 1 {
		return fmt.Sprintf("chore: update %s", changedFiles[0])
	}
	return "chore: update files"
}
