package beads

import "time"

// Dependency represents a relationship between tasks
type Dependency struct {
	IssueID     string `json:"issue_id"`
	DependsOnID string `json:"depends_on_id"`
	Type        string `json:"type"`
	CreatedAt   string `json:"created_at"`
	CreatedBy   string `json:"created_by"`
}

// Task represents a beads issue/task
type Task struct {
	ID           string       `json:"id"`
	Title        string       `json:"title"`
	Description  string       `json:"description,omitempty"`
	Status       string       `json:"status"`
	Priority     int          `json:"priority"`
	IssueType    string       `json:"issue_type"`
	Parent       string       `json:"parent,omitempty"`
	Assignee     string       `json:"assignee,omitempty"`
	Labels       []string     `json:"labels,omitempty"`
	Dependencies []Dependency `json:"dependencies,omitempty"`
	CreatedAt    time.Time    `json:"created_at,omitempty"`
	UpdatedAt    time.Time    `json:"updated_at,omitempty"`
	ClosedAt     *time.Time   `json:"closed_at,omitempty"`
}

// Comment represents a beads comment
type Comment struct {
	ID        string    `json:"id"`
	Author    string    `json:"author"`
	Content   string    `json:"content"`
	CreatedAt time.Time `json:"created_at"`
}

// Stats represents project statistics
type Stats struct {
	Open       int `json:"open"`
	InProgress int `json:"in_progress"`
	Closed     int `json:"closed"`
	Blocked    int `json:"blocked"`
	Total      int `json:"total"`
}

// IsEpic returns true if the task is an epic
func (t *Task) IsEpic() bool {
	return t.IssueType == "epic"
}

// IsOpen returns true if the task is open
func (t *Task) IsOpen() bool {
	return t.Status == "open"
}

// IsInProgress returns true if the task is in progress
func (t *Task) IsInProgress() bool {
	return t.Status == "in_progress"
}

// IsClosed returns true if the task is closed
func (t *Task) IsClosed() bool {
	return t.Status == "closed"
}

// PriorityString returns a human-readable priority string
func (t *Task) PriorityString() string {
	switch t.Priority {
	case 0:
		return "P0 (critical)"
	case 1:
		return "P1 (high)"
	case 2:
		return "P2 (medium)"
	case 3:
		return "P3 (low)"
	case 4:
		return "P4 (backlog)"
	default:
		return "P?"
	}
}
