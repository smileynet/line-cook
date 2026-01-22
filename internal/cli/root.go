package cli

import (
	"github.com/spf13/cobra"
)

var (
	// Global flags
	jsonOutput bool
	verbose    bool
	quiet      bool

	// Version info (set at build time)
	Version   = "dev"
	Commit    = "none"
	BuildDate = "unknown"
)

var rootCmd = &cobra.Command{
	Use:   "lc",
	Short: "Line Cook - Workflow orchestration for AI coding assistants",
	Long: `Line Cook is a CLI tool that orchestrates the prep → cook → serve → tidy workflow
for AI-assisted development sessions.

The CLI handles mechanical operations (git sync, beads queries, file operations)
and outputs structured data for AI-requiring operations.`,
	SilenceUsage:  true,
	SilenceErrors: true,
}

func init() {
	rootCmd.PersistentFlags().BoolVarP(&jsonOutput, "json", "j", false, "Output in JSON format for automation/AI parsing")
	rootCmd.PersistentFlags().BoolVarP(&verbose, "verbose", "v", false, "Enable verbose output")
	rootCmd.PersistentFlags().BoolVarP(&quiet, "quiet", "q", false, "Suppress non-essential output")
}

// Execute runs the root command
func Execute() error {
	return rootCmd.Execute()
}

// IsJSONOutput returns true if JSON output is requested
func IsJSONOutput() bool {
	return jsonOutput
}

// IsVerbose returns true if verbose output is requested
func IsVerbose() bool {
	return verbose
}

// IsQuiet returns true if quiet mode is requested
func IsQuiet() bool {
	return quiet
}
