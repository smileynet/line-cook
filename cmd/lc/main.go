package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
)

// Version info - set via ldflags at build time
var (
	Version = "dev"
	Build   = "unknown"
	Commit  = "unknown"
)

// Global flags
var (
	verboseFlag bool
	quietFlag   bool
	jsonOutput  bool
)

// Command group IDs
const (
	GroupWorkflow = "workflow"
	GroupHooks    = "hooks"
)

var rootCmd = &cobra.Command{
	Use:     "lc",
	Short:   "lc - Line cook workflow orchestration for Claude Code",
	Version: Version,
	Long: `Line cook orchestrates AI coding workflows with structure and guardrails.

The workflow cycle: prep → cook → serve → tidy

Commands integrate with beads for issue tracking and Claude Code for AI assistance.`,
	PersistentPreRunE: func(cmd *cobra.Command, args []string) error {
		// Validate mutually exclusive flags
		if verboseFlag && quietFlag {
			return fmt.Errorf("--verbose and --quiet are mutually exclusive")
		}
		return nil
	},
}

func init() {
	// Set version template to include build info
	rootCmd.SetVersionTemplate(fmt.Sprintf("lc version %s (build: %s, commit: %s)\n", Version, Build, Commit))

	// Add command groups for organized help output
	rootCmd.AddGroup(
		&cobra.Group{ID: GroupWorkflow, Title: "Workflow Commands:"},
		&cobra.Group{ID: GroupHooks, Title: "Hook Commands:"},
	)

	// Register persistent flags
	rootCmd.PersistentFlags().BoolVarP(&verboseFlag, "verbose", "v", false, "Enable verbose output")
	rootCmd.PersistentFlags().BoolVarP(&quietFlag, "quiet", "q", false, "Suppress non-essential output")
	rootCmd.PersistentFlags().BoolVar(&jsonOutput, "json", false, "Output in JSON format")

	// Add subcommands
	addWorkflowCommands()
	addHookCommands()
}

// addWorkflowCommands adds the main workflow commands: prep, cook, serve, tidy, work
func addWorkflowCommands() {
	// prep command
	prepCmd := &cobra.Command{
		Use:     "prep",
		Short:   "Sync state and identify ready tasks",
		Long:    `Syncs git and beads state, then displays available work.`,
		GroupID: GroupWorkflow,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("prep: not yet implemented")
			fmt.Println("This command will sync state and show ready tasks.")
		},
	}

	// cook command
	cookCmd := &cobra.Command{
		Use:     "cook [task-id]",
		Short:   "Execute a task with completion guardrails",
		Long:    `Executes a task, tracking progress and ensuring completion criteria are met.`,
		GroupID: GroupWorkflow,
		Args:    cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			taskID := ""
			if len(args) > 0 {
				taskID = args[0]
			}
			fmt.Printf("cook: not yet implemented (task: %s)\n", taskID)
			fmt.Println("This command will execute and verify task completion.")
		},
	}

	// serve command
	serveCmd := &cobra.Command{
		Use:     "serve",
		Short:   "Review changes via headless Claude",
		Long:    `Invokes headless Claude for peer review of changes.`,
		GroupID: GroupWorkflow,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("serve: not yet implemented")
			fmt.Println("This command will review changes and categorize issues.")
		},
	}

	// tidy command
	tidyCmd := &cobra.Command{
		Use:     "tidy",
		Short:   "File discovered work, commit, and push",
		Long:    `Files beads for discovered work, commits changes, syncs beads, and pushes to remote.`,
		GroupID: GroupWorkflow,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("tidy: not yet implemented")
			fmt.Println("This command will commit, sync, and push changes.")
		},
	}

	// work command (orchestrates the full cycle)
	workCmd := &cobra.Command{
		Use:     "work [task-id]",
		Short:   "Run full prep → cook → serve → tidy cycle",
		Long:    `Orchestrates the complete workflow cycle for focused work sessions.`,
		GroupID: GroupWorkflow,
		Args:    cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			taskID := ""
			if len(args) > 0 {
				taskID = args[0]
			}
			fmt.Printf("work: not yet implemented (task: %s)\n", taskID)
			fmt.Println("This command will run the full prep → cook → serve → tidy cycle.")
		},
	}

	rootCmd.AddCommand(prepCmd, cookCmd, serveCmd, tidyCmd, workCmd)
}

// addHookCommands adds the hook command for Claude Code integration
func addHookCommands() {
	// hook command (parent for hook subcommands)
	hookCmd := &cobra.Command{
		Use:     "hook",
		Short:   "Claude Code hook handlers",
		Long:    `Handles Claude Code lifecycle events (session-start, pre-tool, post-tool, stop).`,
		GroupID: GroupHooks,
	}

	// hook session-start
	sessionStartCmd := &cobra.Command{
		Use:   "session-start",
		Short: "Handle session start event",
		Long:  `Called when a Claude Code session starts. Loads context and primes the session.`,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("hook session-start: not yet implemented")
		},
	}

	// hook pre-tool
	preToolCmd := &cobra.Command{
		Use:   "pre-tool [tool-name]",
		Short: "Handle pre-tool event",
		Long:  `Called before a tool is executed. Can modify or block tool execution.`,
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			toolName := ""
			if len(args) > 0 {
				toolName = args[0]
			}
			fmt.Printf("hook pre-tool: not yet implemented (tool: %s)\n", toolName)
		},
	}

	// hook post-tool
	postToolCmd := &cobra.Command{
		Use:   "post-tool [tool-name]",
		Short: "Handle post-tool event",
		Long:  `Called after a tool is executed. Can process results or trigger side effects.`,
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			toolName := ""
			if len(args) > 0 {
				toolName = args[0]
			}
			fmt.Printf("hook post-tool: not yet implemented (tool: %s)\n", toolName)
		},
	}

	// hook stop
	stopCmd := &cobra.Command{
		Use:   "stop",
		Short: "Handle session stop event",
		Long:  `Called when a Claude Code session ends. Performs cleanup and saves state.`,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("hook stop: not yet implemented")
		},
	}

	hookCmd.AddCommand(sessionStartCmd, preToolCmd, postToolCmd, stopCmd)
	rootCmd.AddCommand(hookCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}
