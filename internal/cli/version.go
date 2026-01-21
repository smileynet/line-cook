package cli

import (
	"fmt"
	"runtime"

	"github.com/spf13/cobra"

	"github.com/smileynet/line-cook/internal/output"
)

func init() {
	rootCmd.AddCommand(versionCmd)
}

// VersionInfo holds version information
type VersionInfo struct {
	Version   string `json:"version"`
	Commit    string `json:"commit"`
	BuildDate string `json:"build_date"`
	GoVersion string `json:"go_version"`
	Platform  string `json:"platform"`
}

var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show version information",
	Long:  `Display version, build, and platform information for lc.`,
	RunE:  runVersion,
}

func runVersion(cmd *cobra.Command, args []string) error {
	out := output.NewFormatter(jsonOutput, verbose, quiet)

	info := VersionInfo{
		Version:   Version,
		Commit:    Commit,
		BuildDate: BuildDate,
		GoVersion: runtime.Version(),
		Platform:  fmt.Sprintf("%s/%s", runtime.GOOS, runtime.GOARCH),
	}

	return out.Output(info, func() {
		out.Text("lc version %s", info.Version)
		if verbose {
			out.Text("  Commit:     %s", info.Commit)
			out.Text("  Built:      %s", info.BuildDate)
			out.Text("  Go version: %s", info.GoVersion)
			out.Text("  Platform:   %s", info.Platform)
		}
	})
}
