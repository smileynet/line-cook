package git

import (
	"bytes"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Client wraps git CLI operations
type Client struct {
	workDir string
}

// NewClient creates a new git client
func NewClient(workDir string) *Client {
	if workDir == "" {
		workDir, _ = os.Getwd()
	}
	return &Client{workDir: workDir}
}

// run executes a git command and returns the output
func (c *Client) run(args ...string) (string, error) {
	cmd := exec.Command("git", args...)
	cmd.Dir = c.workDir
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("git %s failed: %w\nstderr: %s", strings.Join(args, " "), err, stderr.String())
	}
	return strings.TrimSpace(stdout.String()), nil
}

// IsRepo returns true if the work directory is a git repository
func (c *Client) IsRepo() bool {
	gitDir := filepath.Join(c.workDir, ".git")
	info, err := os.Stat(gitDir)
	if err == nil && info.IsDir() {
		return true
	}
	// Also check for worktrees
	_, err = c.run("rev-parse", "--git-dir")
	return err == nil
}

// Fetch fetches from origin
func (c *Client) Fetch() error {
	_, err := c.run("fetch", "origin")
	return err
}

// Pull pulls with rebase from origin
func (c *Client) Pull() error {
	_, err := c.run("pull", "--rebase")
	return err
}

// FetchAndPull does a fetch and pull with rebase
func (c *Client) FetchAndPull() error {
	if err := c.Fetch(); err != nil {
		return err
	}
	return c.Pull()
}

// Push pushes to origin
func (c *Client) Push() error {
	_, err := c.run("push")
	return err
}

// Branch returns the current branch name
func (c *Client) Branch() (string, error) {
	return c.run("branch", "--show-current")
}

// Status returns the git status output
func (c *Client) Status() (string, error) {
	return c.run("status", "--short")
}

// IsClean returns true if the working tree is clean
func (c *Client) IsClean() (bool, error) {
	status, err := c.Status()
	if err != nil {
		return false, err
	}
	return status == "", nil
}

// Diff returns the diff (staged + unstaged by default)
func (c *Client) Diff(opts DiffOptions) (string, error) {
	args := []string{"diff"}
	if opts.Staged {
		args = append(args, "--staged")
	}
	if opts.NameOnly {
		args = append(args, "--name-only")
	}
	if opts.Base != "" {
		args = append(args, opts.Base)
	}
	return c.run(args...)
}

// DiffOptions configures the Diff operation
type DiffOptions struct {
	Staged   bool
	NameOnly bool
	Base     string
}

// AddAll stages all changes
func (c *Client) AddAll() error {
	_, err := c.run("add", "-A")
	return err
}

// Add stages specific files
func (c *Client) Add(files ...string) error {
	args := append([]string{"add"}, files...)
	_, err := c.run(args...)
	return err
}

// Commit creates a commit with the given message
func (c *Client) Commit(message string) (string, error) {
	return c.run("commit", "-m", message)
}

// Log returns recent commit messages
func (c *Client) Log(count int) (string, error) {
	return c.run("log", fmt.Sprintf("-n%d", count), "--oneline")
}

// GetRemoteURL returns the remote URL for origin
func (c *Client) GetRemoteURL() (string, error) {
	return c.run("remote", "get-url", "origin")
}

// HasRemote returns true if origin remote exists
func (c *Client) HasRemote() bool {
	_, err := c.GetRemoteURL()
	return err == nil
}

// GetLastCommitSHA returns the SHA of the last commit
func (c *Client) GetLastCommitSHA() (string, error) {
	return c.run("rev-parse", "HEAD")
}

// IsUpToDateWithRemote checks if local branch is up to date with remote
func (c *Client) IsUpToDateWithRemote() (bool, error) {
	branch, err := c.Branch()
	if err != nil {
		return false, err
	}

	// Get local commit
	local, err := c.run("rev-parse", branch)
	if err != nil {
		return false, err
	}

	// Get remote commit (may not exist)
	remote, err := c.run("rev-parse", "origin/"+branch)
	if err != nil {
		// Remote branch doesn't exist, we're "up to date" in that sense
		return true, nil
	}

	return local == remote, nil
}

// HasUnpushedCommits returns true if there are commits to push
func (c *Client) HasUnpushedCommits() (bool, error) {
	branch, err := c.Branch()
	if err != nil {
		return false, err
	}

	// Check if there's an upstream
	_, err = c.run("rev-parse", "--abbrev-ref", branch+"@{upstream}")
	if err != nil {
		// No upstream, so no pushed commits
		return true, nil
	}

	// Count commits ahead
	output, err := c.run("rev-list", "--count", branch+"@{upstream}.."+branch)
	if err != nil {
		return false, err
	}

	return output != "0", nil
}

// ChangedFiles returns a list of changed file paths
func (c *Client) ChangedFiles() ([]string, error) {
	diff, err := c.Diff(DiffOptions{NameOnly: true})
	if err != nil {
		return nil, err
	}
	if diff == "" {
		return nil, nil
	}
	return strings.Split(diff, "\n"), nil
}

// StagedFiles returns a list of staged file paths
func (c *Client) StagedFiles() ([]string, error) {
	diff, err := c.Diff(DiffOptions{Staged: true, NameOnly: true})
	if err != nil {
		return nil, err
	}
	if diff == "" {
		return nil, nil
	}
	return strings.Split(diff, "\n"), nil
}

// ProjectName returns the project directory name
func (c *Client) ProjectName() string {
	return filepath.Base(c.workDir)
}
