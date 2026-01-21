package output

import (
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/smileynet/line-cook/internal/beads"
)

// Formatter handles output formatting
type Formatter struct {
	writer  io.Writer
	json    bool
	verbose bool
	quiet   bool
}

// NewFormatter creates a new output formatter
func NewFormatter(json, verbose, quiet bool) *Formatter {
	return &Formatter{
		writer:  os.Stdout,
		json:    json,
		verbose: verbose,
		quiet:   quiet,
	}
}

// SetWriter sets the output writer (for testing)
func (f *Formatter) SetWriter(w io.Writer) {
	f.writer = w
}

// JSON outputs the data as JSON
func (f *Formatter) JSON(data interface{}) error {
	enc := json.NewEncoder(f.writer)
	enc.SetIndent("", "  ")
	return enc.Encode(data)
}

// Text outputs a line of text
func (f *Formatter) Text(format string, args ...interface{}) {
	if f.quiet {
		return
	}
	fmt.Fprintf(f.writer, format+"\n", args...)
}

// Verbose outputs only when verbose mode is on
func (f *Formatter) Verbose(format string, args ...interface{}) {
	if !f.verbose {
		return
	}
	fmt.Fprintf(f.writer, format+"\n", args...)
}

// Header outputs a section header
func (f *Formatter) Header(title string) {
	if f.quiet || f.json {
		return
	}
	f.Text("%s", title)
	f.Text(strings.Repeat("━", 45))
}

// SubHeader outputs a subsection header
func (f *Formatter) SubHeader(title string) {
	if f.quiet || f.json {
		return
	}
	f.Text("")
	f.Text("%s", title)
}

// Error outputs an error message
func (f *Formatter) Error(format string, args ...interface{}) {
	fmt.Fprintf(os.Stderr, "Error: "+format+"\n", args...)
}

// Warning outputs a warning message
func (f *Formatter) Warning(format string, args ...interface{}) {
	if f.quiet {
		return
	}
	fmt.Fprintf(f.writer, "Warning: "+format+"\n", args...)
}

// Success outputs a success message with checkmark
func (f *Formatter) Success(format string, args ...interface{}) {
	if f.quiet || f.json {
		return
	}
	f.Text("✓ "+format, args...)
}

// Failure outputs a failure message with X
func (f *Formatter) Failure(format string, args ...interface{}) {
	if f.json {
		return
	}
	f.Text("✗ "+format, args...)
}

// TaskLine formats a task for display
func (f *Formatter) TaskLine(task beads.Task) string {
	return fmt.Sprintf("  %s [P%d] %s", task.ID, task.Priority, task.Title)
}

// TaskList outputs a list of tasks
func (f *Formatter) TaskList(tasks []beads.Task, label string) {
	if f.json || f.quiet {
		return
	}
	if len(tasks) == 0 {
		f.Text("%s: 0", label)
		return
	}
	f.Text("%s: %d", label, len(tasks))
	for _, task := range tasks {
		f.Text("%s", f.TaskLine(task))
	}
}

// Output handles the main output logic - JSON or text
func (f *Formatter) Output(data interface{}, textFn func()) error {
	if f.json {
		return f.JSON(data)
	}
	textFn()
	return nil
}

// PrepResult represents the output of lc prep
type PrepResult struct {
	Project    string       `json:"project"`
	Branch     string       `json:"branch"`
	SyncStatus string       `json:"sync_status"`
	ReadyTasks []beads.Task `json:"ready_tasks"`
	InProgress []beads.Task `json:"in_progress"`
	Blocked    []beads.Task `json:"blocked"`
	NextTask   *beads.Task  `json:"next_task,omitempty"`
	Epic       *beads.Task  `json:"epic,omitempty"`
}

// CookContext represents the output of lc cook
type CookContext struct {
	Task           beads.Task  `json:"task"`
	Epic           *beads.Task `json:"epic,omitempty"`
	ProjectContext string      `json:"project_context"`
	AIPrompt       string      `json:"ai_prompt"`
}

// ServeContext represents the output of lc serve
type ServeContext struct {
	Task         beads.Task `json:"task"`
	Diff         string     `json:"diff"`
	FilesChanged []string   `json:"files_changed"`
	ReviewPrompt string     `json:"review_prompt"`
}

// TidyResult represents the output of lc tidy
type TidyResult struct {
	FiledBeads  []string `json:"filed_beads"`
	ClosedBeads []string `json:"closed_beads"`
	CommitSHA   string   `json:"commit_sha"`
	Pushed      bool     `json:"pushed"`
	Summary     string   `json:"summary"`
}

// WorkResult represents the output of lc work
type WorkResult struct {
	Phase        string        `json:"phase"`
	PrepResult   *PrepResult   `json:"prep,omitempty"`
	CookContext  *CookContext  `json:"cook,omitempty"`
	ServeContext *ServeContext `json:"serve,omitempty"`
	TidyResult   *TidyResult   `json:"tidy,omitempty"`
	Message      string        `json:"message,omitempty"`
}
