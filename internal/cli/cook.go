package cli

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/cobra"

	"github.com/smileynet/line-cook/internal/beads"
	"github.com/smileynet/line-cook/internal/environment"
	"github.com/smileynet/line-cook/internal/output"
	"github.com/smileynet/line-cook/internal/session"
)

func init() {
	rootCmd.AddCommand(cookCmd)
}

var cookCmd = &cobra.Command{
	Use:   "cook [task-id]",
	Short: "Claim task and output context for AI execution",
	Long: `Cook claims a task and outputs context for AI execution.

This command:
1. Selects a task (from arg or auto-selects highest priority ready task)
2. Updates task status to in_progress
3. Outputs task details + project context + AI prompt

The AI coding assistant then uses this context to execute the task.`,
	RunE: runCook,
}

func runCook(cmd *cobra.Command, args []string) error {
	workDir, _ := os.Getwd()
	beadsClient := beads.NewClient(workDir)
	out := output.NewFormatter(jsonOutput, verbose, quiet)

	// Detect environment and capabilities
	envDetector := environment.NewDetector(workDir)
	capabilities := envDetector.GetCapabilities()

	if !beadsClient.HasBeads() {
		out.Error("No .beads/ directory found. Run 'bd init' first.")
		return nil
	}

	var taskID string
	var task *beads.Task
	var epic *beads.Task

	// Select task
	if len(args) > 0 {
		// Explicit task ID provided
		taskID = args[0]
		t, err := beadsClient.Show(taskID)
		if err != nil {
			out.Error("Failed to get task %s: %v", taskID, err)
			return nil
		}
		task = t
	} else {
		// Auto-select from filtered ready list
		ready, err := beadsClient.FilterReadyTasks()
		if err != nil {
			out.Error("Failed to get ready tasks: %v", err)
			return nil
		}

		if len(ready) == 0 {
			out.Error("No actionable tasks ready.")
			out.Text("All ready tasks may be in Retrospective or Backlog epics.")
			out.Text("")
			out.Text("To work on parked items: lc cook <specific-task-id>")
			return nil
		}

		// Get first task
		firstTask := ready[0]

		// Check if it's an epic
		if firstTask.IsEpic() {
			epic = &firstTask

			// Find first ready child of the epic
			children, err := beadsClient.List(beads.ListOptions{Parent: firstTask.ID})
			if err != nil {
				out.Error("Failed to get epic children: %v", err)
				return nil
			}

			for i := range children {
				if children[i].IsOpen() {
					task = &children[i]
					break
				}
			}

			if task == nil {
				out.Error("Epic %s has no ready children", firstTask.ID)
				return nil
			}
		} else {
			task = &firstTask
		}
	}

	// Handle epic selection
	if task.IsEpic() {
		out.Text("EPIC SELECTED: %s - %s", task.ID, task.Title)
		out.Header("")
		out.Text("Epics contain no direct work. Finding first ready child...")
		out.Text("")

		children, err := beadsClient.List(beads.ListOptions{Parent: task.ID, All: true})
		if err != nil {
			out.Error("Failed to get epic children: %v", err)
			return nil
		}

		epic = task
		task = nil

		out.Text("Children (%d total):", len(children))
		for i := range children {
			child := &children[i]
			if child.IsOpen() && task == nil {
				task = child
				out.Text("  ○ %s: %s [P%d] ← selected", child.ID, child.Title, child.Priority)
			} else if child.IsClosed() {
				out.Text("  ✓ %s: %s (closed)", child.ID, child.Title)
			} else {
				out.Text("  ○ %s: %s [P%d]", child.ID, child.Title, child.Priority)
			}
		}

		if task == nil {
			out.Error("No ready children in epic")
			return nil
		}

		out.Text("")
		out.Text("Proceeding with: %s", task.ID)
	}

	// Claim the task
	if err := beadsClient.Update(task.ID, beads.UpdateOptions{Status: "in_progress"}); err != nil {
		out.Warning("Failed to claim task: %v", err)
	}

	// Add comment
	beadsClient.AddComment(task.ID, "PHASE: COOK\nStatus: started")

	// Update session state
	stateMgr, err := session.NewStateManager()
	if err == nil {
		stateMgr.StartTask(task.ID, task.Title)
	}

	// Load project context (CLAUDE.md)
	projectContext := loadProjectContext(workDir)

	// Generate AI prompt
	aiPrompt := generateCookPrompt(task, epic, capabilities)

	result := &output.CookContext{
		Task:           *task,
		Epic:           epic,
		ProjectContext: projectContext,
		AIPrompt:       aiPrompt,
		Capabilities:   capabilities,
	}

	return out.Output(result, func() {
		out.Header(fmt.Sprintf("COOKING: %s - %s", task.ID, task.Title))
		out.Text("")

		if epic != nil {
			out.Text("Part of epic: %s - %s", epic.ID, epic.Title)
			out.Text("")
		}

		out.Text("Priority: %s", task.PriorityString())
		out.Text("Status: in_progress (claimed)")
		out.Text("")

		if task.Description != "" {
			out.Text("Description:")
			out.Text("%s", task.Description)
			out.Text("")
		}

		out.Text("AI PROMPT:")
		out.Text("━━━━━━━━━━")
		out.Text("%s", aiPrompt)
		out.Text("")

		out.Text("NEXT STEP: Execute the task, then run: lc serve")
	})
}

func loadProjectContext(workDir string) string {
	// Try CLAUDE.md in current dir
	claudeMD := filepath.Join(workDir, "CLAUDE.md")
	if data, err := os.ReadFile(claudeMD); err == nil {
		return string(data)
	}

	// Try README.md as fallback
	readmeMD := filepath.Join(workDir, "README.md")
	if data, err := os.ReadFile(readmeMD); err == nil {
		// Return first 2000 chars
		content := string(data)
		if len(content) > 2000 {
			content = content[:2000] + "\n...(truncated)"
		}
		return content
	}

	return ""
}

func generateCookPrompt(task *beads.Task, epic *beads.Task, capabilities *environment.CapabilitiesResult) string {
	prompt := fmt.Sprintf(`Execute the following task:

**Task:** %s
**ID:** %s
**Priority:** %s
 `, task.Title, task.ID, task.PriorityString())

	if task.Description != "" {
		prompt += fmt.Sprintf("\n**Description:**\n%s\n", task.Description)
	}

	if epic != nil {
		prompt += fmt.Sprintf("\n**Context:** This task is part of epic '%s' (%s)\n", epic.Title, epic.ID)
	}

	// Adapt prompt based on capabilities
	if capabilities != nil {
		if capabilities.HasCapability(environment.CapabilityMCP) {
			prompt += "\n**Note:** MCP tools are available for enhanced functionality.\n"
		}
		if capabilities.HasCapability(environment.CapabilityHeadless) {
			prompt += "\n**Note:** Running in headless mode. Avoid interactive prompts.\n"
		}
	}

	prompt += `
**Guidelines:**
1. Break task into steps before starting
2. Verify each step completes successfully
3. Note any discovered issues for later (don't create beads during cooking)
4. Ensure code compiles and tests pass before completing

**When done:**
- Summarize what was accomplished
- List any findings (new tasks, bugs, improvements discovered)
- Run: lc serve (for AI review) or lc tidy (to commit)
`

	return prompt
}
