package session

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"
)

// State holds the current session state
type State struct {
	// Current session info
	ProjectDir string    `json:"project_dir"`
	Branch     string    `json:"branch"`
	StartedAt  time.Time `json:"started_at"`

	// Current task being worked on
	CurrentTask *TaskState `json:"current_task,omitempty"`

	// Findings collected during cooking (to be filed in tidy)
	Findings []Finding `json:"findings,omitempty"`

	// Recently completed tasks (for serve to reference)
	RecentlyCompleted []string `json:"recently_completed,omitempty"`
}

// TaskState tracks the current task being worked on
type TaskState struct {
	ID        string    `json:"id"`
	Title     string    `json:"title"`
	StartedAt time.Time `json:"started_at"`
}

// Finding represents a discovered issue or improvement during cooking
type Finding struct {
	Type        FindingType `json:"type"`
	Title       string      `json:"title"`
	Description string      `json:"description,omitempty"`
	Priority    int         `json:"priority"`
}

// FindingType categorizes findings
type FindingType string

const (
	FindingTask        FindingType = "task"
	FindingBug         FindingType = "bug"
	FindingImprovement FindingType = "improvement"
)

// StateManager handles session state persistence
type StateManager struct {
	statePath string
}

// NewStateManager creates a state manager
// State is stored in ~/.cache/line-cook/session.json
func NewStateManager() (*StateManager, error) {
	cacheDir, err := os.UserCacheDir()
	if err != nil {
		return nil, fmt.Errorf("get cache dir: %w", err)
	}

	stateDir := filepath.Join(cacheDir, "line-cook")
	if err := os.MkdirAll(stateDir, 0755); err != nil {
		return nil, fmt.Errorf("create state dir: %w", err)
	}

	return &StateManager{
		statePath: filepath.Join(stateDir, "session.json"),
	}, nil
}

// Load loads the current session state
func (m *StateManager) Load() (*State, error) {
	data, err := os.ReadFile(m.statePath)
	if err != nil {
		if os.IsNotExist(err) {
			return &State{}, nil
		}
		return nil, fmt.Errorf("read state: %w", err)
	}

	var state State
	if err := json.Unmarshal(data, &state); err != nil {
		return nil, fmt.Errorf("parse state: %w", err)
	}

	return &state, nil
}

// Save saves the session state
func (m *StateManager) Save(state *State) error {
	data, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal state: %w", err)
	}

	if err := os.WriteFile(m.statePath, data, 0644); err != nil {
		return fmt.Errorf("write state: %w", err)
	}

	return nil
}

// Clear removes the session state
func (m *StateManager) Clear() error {
	if err := os.Remove(m.statePath); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("remove state: %w", err)
	}
	return nil
}

// StartSession initializes a new session
func (m *StateManager) StartSession(projectDir, branch string) (*State, error) {
	state := &State{
		ProjectDir: projectDir,
		Branch:     branch,
		StartedAt:  time.Now(),
	}
	if err := m.Save(state); err != nil {
		return nil, err
	}
	return state, nil
}

// StartTask marks a task as being worked on
func (m *StateManager) StartTask(id, title string) error {
	state, err := m.Load()
	if err != nil {
		return err
	}

	state.CurrentTask = &TaskState{
		ID:        id,
		Title:     title,
		StartedAt: time.Now(),
	}

	return m.Save(state)
}

// CompleteTask marks the current task as complete
func (m *StateManager) CompleteTask(id string) error {
	state, err := m.Load()
	if err != nil {
		return err
	}

	state.CurrentTask = nil
	state.RecentlyCompleted = append([]string{id}, state.RecentlyCompleted...)
	// Keep only last 5
	if len(state.RecentlyCompleted) > 5 {
		state.RecentlyCompleted = state.RecentlyCompleted[:5]
	}

	return m.Save(state)
}

// AddFinding adds a finding to be filed during tidy
func (m *StateManager) AddFinding(finding Finding) error {
	state, err := m.Load()
	if err != nil {
		return err
	}

	state.Findings = append(state.Findings, finding)
	return m.Save(state)
}

// ClearFindings removes all findings (after filing)
func (m *StateManager) ClearFindings() error {
	state, err := m.Load()
	if err != nil {
		return err
	}

	state.Findings = nil
	return m.Save(state)
}

// GetRecentlyCompleted returns the most recently completed task ID
func (m *StateManager) GetRecentlyCompleted() (string, error) {
	state, err := m.Load()
	if err != nil {
		return "", err
	}

	if len(state.RecentlyCompleted) == 0 {
		return "", nil
	}

	return state.RecentlyCompleted[0], nil
}
