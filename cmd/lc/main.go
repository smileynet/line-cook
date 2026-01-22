package main

import (
	"os"

	"github.com/smileynet/line-cook/internal/cli"
)

func main() {
	if err := cli.Execute(); err != nil {
		os.Exit(1)
	}
}
