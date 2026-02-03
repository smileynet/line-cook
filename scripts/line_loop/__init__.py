"""Line Loop - Autonomous loop execution for Line Cook workflow.

This package modularizes line-loop.py into focused modules:

- config: Constants and configuration values
- models: Dataclasses for state tracking (BeadSnapshot, ServeResult, etc.)
- parsing: Output parsing functions (serve_result, intent, feedback)
- phase: Phase execution (run_phase, streaming)
- iteration: Single iteration logic
- loop: Main loop orchestration

Usage:
    from line_loop import run_loop
    run_loop(cwd=Path.cwd(), max_iterations=25)
"""

__version__ = "0.1.0"
