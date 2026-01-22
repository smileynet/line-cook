package cli

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"github.com/smileynet/line-cook/internal/beads"
	"github.com/smileynet/line-cook/internal/git"
	"github.com/smileynet/line-cook/internal/output"
	"github.com/smileynet/line-cook/internal/session"
)

func init() {
	rootCmd.AddCommand(serveCmd)
}

var serveCmd = &cobra.Command{
	Use:   "serve [task-id]",
	Short: "Output diff and context for AI review",
	Long: `Serve outputs the diff and task context for AI peer review.

This command:
1. Gets the task (from arg, session state, or most recently closed)
2. Generates a git diff of changes
3. Outputs task details + diff + review prompt

The AI coding assistant then uses this context to review the work.`,
	RunE: runServe,
}

func runServe(cmd *cobra.Command, args []string) error {
	workDir, _ := os.Getwd()
	gitClient := git.NewClient(workDir)
	beadsClient := beads.NewClient(workDir)
	out := output.NewFormatter(jsonOutput, verbose, quiet)

	if !gitClient.IsRepo() {
		out.Error("Not a git repository")
		return nil
	}

	var taskID string
	var task *beads.Task

	// Determine task ID
	if len(args) > 0 {
		taskID = args[0]
	} else {
		// Try to get from session state
		stateMgr, err := session.NewStateManager()
		if err == nil {
			state, err := stateMgr.Load()
			if err == nil {
				if state.CurrentTask != nil {
					taskID = state.CurrentTask.ID
				} else {
					// Try recently completed
					taskID, _ = stateMgr.GetRecentlyCompleted()
				}
			}
		}
	}

	// Get task details if we have beads
	if beadsClient.HasBeads() && taskID != "" {
		t, err := beadsClient.Show(taskID)
		if err == nil {
			task = t
		}
	}

	// Get git diff
	diff, err := gitClient.Diff(git.DiffOptions{})
	if err != nil {
		out.Warning("Failed to get diff: %v", err)
	}

	// Also check staged changes
	stagedDiff, _ := gitClient.Diff(git.DiffOptions{Staged: true})
	if stagedDiff != "" && diff != "" {
		diff = "=== Staged Changes ===\n" + stagedDiff + "\n\n=== Unstaged Changes ===\n" + diff
	} else if stagedDiff != "" {
		diff = stagedDiff
	}

	// Get changed files
	changedFiles, _ := gitClient.ChangedFiles()
	stagedFiles, _ := gitClient.StagedFiles()

	// Merge file lists
	fileSet := make(map[string]bool)
	for _, f := range changedFiles {
		fileSet[f] = true
	}
	for _, f := range stagedFiles {
		fileSet[f] = true
	}
	var allFiles []string
	for f := range fileSet {
		allFiles = append(allFiles, f)
	}

	// Generate review prompt using beads client
	extraData := make(map[string]interface{})
	extraData["files"] = allFiles
	reviewPrompt, err := beadsClient.GetPromptForTool("serve", task, nil, extraData)
	if err != nil {
		out.Warning("Failed to get review prompt from beads: %v", err)
		reviewPrompt = generateReviewPrompt(task, allFiles)
	}

	result := &output.ServeContext{
		Diff:         diff,
		FilesChanged: allFiles,
		ReviewPrompt: reviewPrompt,
	}
	if task != nil {
		result.Task = *task
	}

	return out.Output(result, func() {
		if task != nil {
			out.Header(fmt.Sprintf("REVIEW: %s - %s", task.ID, task.Title))
		} else {
			out.Header("REVIEW: Changes")
		}
		out.Text("")

		out.Text("Files changed: %d", len(allFiles))
		for _, f := range allFiles {
			out.Text("  %s", f)
		}
		out.Text("")

		if diff != "" {
			out.Text("DIFF:")
			out.Text("━━━━━")
			// Truncate for display if very long
			if len(diff) > 5000 {
				out.Text("%s\n...(truncated, use --json for full diff)", diff[:5000])
			} else {
				out.Text("%s", diff)
			}
			out.Text("")
		} else {
			out.Text("No changes detected.")
			out.Text("")
		}

		out.Text("REVIEW PROMPT:")
		out.Text("━━━━━━━━━━━━━━")
		out.Text("%s", reviewPrompt)
		out.Text("")

		out.Text("NEXT STEP: After review, run: lc tidy")
	})
}

func generateReviewPrompt(task *beads.Task, files []string) string {
	prompt := `Review the following changes:

**Review Checklist:**
- [ ] Code follows project conventions
- [ ] No obvious bugs or logic errors
- [ ] Error handling is appropriate
- [ ] No security vulnerabilities introduced
- [ ] Tests cover the changes (if applicable)
- [ ] No unnecessary code or debug statements
`

	if task != nil {
		prompt += fmt.Sprintf(`
**Task Context:**
- Task: %s
- ID: %s
- Priority: %s
`, task.Title, task.ID, task.PriorityString())

		if task.Description != "" {
			prompt += fmt.Sprintf("- Description: %s\n", task.Description)
		}

		prompt += `
**Verify task completion:**
- [ ] Changes match the task description
- [ ] All acceptance criteria met
`
	}

	if len(files) > 0 {
		prompt += "\n**Files changed:**\n"
		for _, f := range files {
			prompt += fmt.Sprintf("- %s\n", f)
		}
	}

	prompt += `
**Output:**
Provide a brief review summary noting:
1. Any issues found (critical/minor)
2. Suggestions for improvement
3. Whether the changes are ready to commit
`

	return prompt
}
