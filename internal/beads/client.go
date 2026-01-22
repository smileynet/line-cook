package beads

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Client wraps the bd CLI tool
type Client struct {
	workDir string
}

// NewClient creates a new beads client
func NewClient(workDir string) *Client {
	if workDir == "" {
		workDir, _ = os.Getwd()
	}
	return &Client{workDir: workDir}
}

// HasBeads returns true if .beads/ directory exists in the work directory
func (c *Client) HasBeads() bool {
	beadsDir := filepath.Join(c.workDir, ".beads")
	info, err := os.Stat(beadsDir)
	return err == nil && info.IsDir()
}

// run executes a bd command and returns the output
func (c *Client) run(args ...string) ([]byte, error) {
	cmd := exec.Command("bd", args...)
	cmd.Dir = c.workDir
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("bd %s failed: %w\nstderr: %s", strings.Join(args, " "), err, stderr.String())
	}
	return stdout.Bytes(), nil
}

// runJSON executes a bd command with --json flag and parses the output
func (c *Client) runJSON(result interface{}, args ...string) error {
	args = append(args, "--json")
	output, err := c.run(args...)
	if err != nil {
		return err
	}
	if len(output) == 0 {
		return nil
	}
	return json.Unmarshal(output, result)
}

// Sync synchronizes beads with git remote
func (c *Client) Sync() error {
	_, err := c.run("sync")
	return err
}

// Ready returns tasks that are ready to work on (no blockers)
func (c *Client) Ready() ([]Task, error) {
	var tasks []Task
	if err := c.runJSON(&tasks, "ready"); err != nil {
		return nil, err
	}
	return tasks, nil
}

// List returns tasks matching the given filters
func (c *Client) List(opts ListOptions) ([]Task, error) {
	args := []string{"list"}
	if opts.Status != "" {
		args = append(args, "--status="+opts.Status)
	}
	if opts.Type != "" {
		args = append(args, "--type="+opts.Type)
	}
	if opts.Parent != "" {
		args = append(args, "--parent="+opts.Parent)
	}
	if opts.All {
		args = append(args, "--all")
	}

	var tasks []Task
	if err := c.runJSON(&tasks, args...); err != nil {
		return nil, err
	}
	return tasks, nil
}

// ListOptions configures the List query
type ListOptions struct {
	Status string
	Type   string
	Parent string
	All    bool
}

// Blocked returns blocked tasks
func (c *Client) Blocked() ([]Task, error) {
	var tasks []Task
	if err := c.runJSON(&tasks, "blocked"); err != nil {
		return nil, err
	}
	return tasks, nil
}

// Show returns details for a specific task
func (c *Client) Show(id string) (*Task, error) {
	var tasks []Task
	if err := c.runJSON(&tasks, "show", id); err != nil {
		return nil, err
	}
	if len(tasks) == 0 {
		return nil, fmt.Errorf("task not found: %s", id)
	}
	return &tasks[0], nil
}

// Update updates a task's fields
func (c *Client) Update(id string, opts UpdateOptions) error {
	args := []string{"update", id}
	if opts.Status != "" {
		args = append(args, "--status="+opts.Status)
	}
	if opts.Assignee != "" {
		args = append(args, "--assignee="+opts.Assignee)
	}
	if opts.Priority != nil {
		args = append(args, fmt.Sprintf("--priority=%d", *opts.Priority))
	}
	_, err := c.run(args...)
	return err
}

// UpdateOptions configures the Update operation
type UpdateOptions struct {
	Status   string
	Assignee string
	Priority *int
}

// Close closes a task
func (c *Client) Close(id string, reason string) error {
	args := []string{"close", id}
	if reason != "" {
		args = append(args, "--reason="+reason)
	}
	_, err := c.run(args...)
	return err
}

// Create creates a new task
func (c *Client) Create(opts CreateOptions) (string, error) {
	args := []string{"create", "--title=" + opts.Title}
	if opts.Type != "" {
		args = append(args, "--type="+opts.Type)
	}
	if opts.Priority != nil {
		args = append(args, fmt.Sprintf("--priority=%d", *opts.Priority))
	}
	if opts.Parent != "" {
		args = append(args, "--parent="+opts.Parent)
	}
	if opts.Description != "" {
		args = append(args, "--description="+opts.Description)
	}

	output, err := c.run(args...)
	if err != nil {
		return "", err
	}
	// bd create typically outputs "Created <id>" or just the id
	// Parse the ID from output
	return strings.TrimSpace(string(output)), nil
}

// CreateOptions configures the Create operation
type CreateOptions struct {
	Title       string
	Type        string
	Priority    *int
	Parent      string
	Description string
}

// AddComment adds a comment to a task
func (c *Client) AddComment(id string, content string) error {
	_, err := c.run("comments", "add", id, content)
	return err
}

// GetComments returns comments for a task
func (c *Client) GetComments(id string) ([]Comment, error) {
	var comments []Comment
	if err := c.runJSON(&comments, "comments", id); err != nil {
		return nil, err
	}
	return comments, nil
}

// AddDependency adds a dependency between tasks
func (c *Client) AddDependency(taskID, dependsOnID string) error {
	_, err := c.run("dep", "add", taskID, dependsOnID)
	return err
}

// Stats returns project statistics
func (c *Client) Stats() (*Stats, error) {
	var stats Stats
	if err := c.runJSON(&stats, "stats"); err != nil {
		return nil, err
	}
	return &stats, nil
}

// EpicStatus returns epic status information
func (c *Client) EpicStatus() ([]Task, error) {
	var tasks []Task
	if err := c.runJSON(&tasks, "epic", "status"); err != nil {
		return nil, err
	}
	return tasks, nil
}

// FilterParkingLotEpics returns IDs of parking-lot epics (Retrospective, Backlog)
func (c *Client) FilterParkingLotEpics() ([]string, error) {
	epics, err := c.List(ListOptions{Type: "epic"})
	if err != nil {
		return nil, err
	}

	var ids []string
	for _, epic := range epics {
		title := strings.ToLower(epic.Title)
		if title == "retrospective" || title == "backlog" {
			ids = append(ids, epic.ID)
		}
	}
	return ids, nil
}

// FilterReadyTasks returns ready tasks excluding parking-lot epic children
func (c *Client) FilterReadyTasks() ([]Task, error) {
	ready, err := c.Ready()
	if err != nil {
		return nil, err
	}

	parkingLotEpics, err := c.FilterParkingLotEpics()
	if err != nil {
		return nil, err
	}

	if len(parkingLotEpics) == 0 {
		return ready, nil
	}

	// Filter out tasks that are children of parking-lot epics
	parkingLotSet := make(map[string]bool)
	for _, id := range parkingLotEpics {
		parkingLotSet[id] = true
	}

	var filtered []Task
	for _, task := range ready {
		if task.Parent == "" || !parkingLotSet[task.Parent] {
			filtered = append(filtered, task)
		}
	}
	return filtered, nil
}

// PrimeForTool returns tool-specific prompt content from bd prime
// Attempts to use --for-tool flag, falls back to full output if flag not supported
func (c *Client) PrimeForTool(tool string) (string, error) {
	args := []string{"prime"}

	// Try with --for-tool flag (if supported)
	output, err := c.run(append(args, "--for-tool="+tool)...)
	if err == nil {
		return string(output), nil
	}

	// Flag not supported, fall back to full output
	output, err = c.run(args...)
	if err != nil {
		return "", err
	}
	return string(output), nil
}

// GetPromptForTool returns a tool-specific execution prompt
// Combines beads workflow context (from bd prime) with tool-specific instructions
func (c *Client) GetPromptForTool(tool string, task *Task, epic *Task, extraData map[string]interface{}) (string, error) {
	// Get beads workflow context
	beadsContext, err := c.PrimeForTool(tool)
	if err != nil {
		beadsContext = ""
	}

	// Get tool-specific prompt
	toolPrompt, err := c.getToolPrompt(tool, task, epic, extraData)
	if err != nil {
		return "", err
	}

	// Combine: workflow context + tool-specific prompt
	if beadsContext != "" {
		return beadsContext + "\n\n" + toolPrompt, nil
	}
	return toolPrompt, nil
}

// getToolPrompt returns the prompt template for a specific tool
func (c *Client) getToolPrompt(tool string, task *Task, epic *Task, extraData map[string]interface{}) (string, error) {
	switch tool {
	case "cook":
		return c.getCookPrompt(task, epic, extraData)
	case "serve":
		return c.getServePrompt(task, extraData)
	case "tidy":
		return c.getTidyPrompt(extraData)
	default:
		return "", nil
	}
}

// getCookPrompt generates the cook-specific execution prompt
func (c *Client) getCookPrompt(task *Task, epic *Task, extraData map[string]interface{}) (string, error) {
	var prompt string

	if task != nil {
		prompt = fmt.Sprintf(`Execute the following task:

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
	}

	// Add capabilities note if available (checking for interface to avoid import cycles)
	if caps, ok := extraData["capabilities"]; ok {
		if capsInterface, ok := caps.(interface{ HasCapability(string) bool }); ok {
			if capsInterface.HasCapability("mcp") {
				prompt += "\n**Note:** MCP tools are available for enhanced functionality.\n"
			}
			if capsInterface.HasCapability("headless") {
				prompt += "\n**Note:** Running in headless mode. Avoid interactive prompts.\n"
			}
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

	return prompt, nil
}

// getServePrompt generates the serve-specific review prompt
func (c *Client) getServePrompt(task *Task, extraData map[string]interface{}) (string, error) {
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

	// Add files changed if available
	if files, ok := extraData["files"].([]string); ok && len(files) > 0 {
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

	return prompt, nil
}

// getTidyPrompt generates the tidy-specific completion prompt
func (c *Client) getTidyPrompt(extraData map[string]interface{}) (string, error) {
	return `Complete the workflow:

**Final Checklist:**
- [ ] All changes are committed
- [ ] Findings are filed as beads (if any)
- [ ] Current task is closed (if in progress)
- [ ] Beads are synced with remote
- [ ] Changes are pushed to remote

Work is not complete until pushed. If push fails, resolve and retry.
`, nil
}
