"""Platform-specific abstractions for line-loop.

Isolates all Windows vs Unix differences so that phase.py and the CLI
remain platform-agnostic.

Abstractions:
- PipeReader: Non-blocking line reading from subprocess stdout
- create_stderr_file / read_and_cleanup_stderr: Temp file for stderr capture
- kill_process_tree: Terminate process and children
- make_popen_kwargs: Build platform-appropriate Popen kwargs
- setup_signals: Register signal handlers (SIGHUP guard)
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
from abc import ABC, abstractmethod
from queue import Queue, Empty
from typing import Optional

logger = logging.getLogger(__name__)

_IS_WINDOWS = sys.platform == 'win32'

# select only works on sockets on Windows; use __import__ to survive bundler stripping
select = __import__('select') if not _IS_WINDOWS else None


# ---------------------------------------------------------------------------
# PipeReader hierarchy
# ---------------------------------------------------------------------------

class PipeReader(ABC):
    """Abstract interface for non-blocking line reading from a pipe."""

    @abstractmethod
    def readline(self, timeout: float) -> Optional[str]:
        """Read one line with timeout.

        Returns:
            A line string (with newline) on data,
            '' (empty string) on EOF,
            None on timeout (no data available yet).
        """

    @abstractmethod
    def drain(self) -> list[str]:
        """Read all remaining buffered lines after process exits."""

    @abstractmethod
    def close(self):
        """Clean up resources (join threads, etc.)."""

    @staticmethod
    def create(pipe) -> 'PipeReader':
        """Factory: returns the right implementation for the current platform."""
        if _IS_WINDOWS:
            return ThreadedPipeReader(pipe)
        return SelectPipeReader(pipe)


class SelectPipeReader(PipeReader):
    """Unix implementation using select.select() for timeout support."""

    def __init__(self, pipe):
        self._pipe = pipe

    def readline(self, timeout: float) -> Optional[str]:
        ready, _, _ = select.select([self._pipe], [], [], timeout)
        if ready:
            line = self._pipe.readline()
            if not line:
                return ''  # EOF
            return line
        return None  # timeout

    def drain(self) -> list[str]:
        remaining = self._pipe.read()
        if remaining:
            return remaining.splitlines(keepends=True)
        return []

    def close(self):
        pass  # pipe owned by Popen


class ThreadedPipeReader(PipeReader):
    """Windows implementation using a reader thread + Queue."""

    _EOF = object()  # sentinel

    def __init__(self, pipe):
        self._pipe = pipe
        self._queue: Queue = Queue()
        self._eof_seen = False
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self):
        try:
            for line in iter(self._pipe.readline, ''):
                self._queue.put(line)
        except ValueError:
            pass  # pipe closed
        finally:
            self._queue.put(self._EOF)

    def readline(self, timeout: float) -> Optional[str]:
        if self._eof_seen:
            return ''
        try:
            item = self._queue.get(timeout=timeout)
        except Empty:
            return None  # timeout
        if item is self._EOF:
            self._eof_seen = True
            return ''  # EOF
        return item

    def drain(self) -> list[str]:
        self._thread.join(timeout=5)
        lines = []
        while True:
            try:
                item = self._queue.get_nowait()
            except Empty:
                break
            if item is self._EOF:
                break
            lines.append(item)
        return lines

    def close(self):
        if self._thread.is_alive():
            self._thread.join(timeout=5)


# ---------------------------------------------------------------------------
# Stderr temp file helpers
# ---------------------------------------------------------------------------

def create_stderr_file(phase: str):
    """Create a temporary file for capturing subprocess stderr.

    On Windows, NamedTemporaryFile holds an exclusive lock (O_TEMPORARY),
    preventing the child process from writing. Use mkstemp + open instead.

    Returns:
        A file object opened for writing. The caller must pass it to
        read_and_cleanup_stderr() when done.
    """
    prefix = f'line-loop-{phase}-stderr-'
    if _IS_WINDOWS:
        fd, path = tempfile.mkstemp(prefix=prefix, suffix='.log')
        os.close(fd)  # release the fd so subprocess can write
        return open(path, 'w+')
    else:
        return tempfile.NamedTemporaryFile(
            mode='w+', prefix=prefix, suffix='.log', delete=False
        )


def read_and_cleanup_stderr(stderr_file) -> str:
    """Read stderr content and remove the temp file.

    On Windows, the file must be fully closed before it can be deleted.
    """
    try:
        name = stderr_file.name
        if _IS_WINDOWS:
            stderr_file.close()
            with open(name, 'r') as f:
                content = f.read().strip()
            try:
                os.unlink(name)
            except OSError:
                pass
        else:
            stderr_file.seek(0)
            content = stderr_file.read().strip()
            stderr_file.close()
            os.unlink(name)
        return content
    except (OSError, AttributeError):
        return ""


def cleanup_stderr_file(stderr_file):
    """Close and remove a stderr temp file, ignoring errors."""
    try:
        name = stderr_file.name
        stderr_file.close()
        os.unlink(name)
    except (OSError, AttributeError):
        pass


# ---------------------------------------------------------------------------
# Process termination
# ---------------------------------------------------------------------------

def kill_process_tree(process):
    """Kill a process and its children.

    On Windows, taskkill /T kills the entire process tree.
    On Unix, process.kill() sends SIGKILL to the direct child.
    """
    try:
        if _IS_WINDOWS:
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(process.pid)],
                capture_output=True, timeout=10
            )
        else:
            process.kill()
        process.wait(timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        logger.warning(f"Process {process.pid} did not terminate after kill")


# ---------------------------------------------------------------------------
# Popen kwargs builder
# ---------------------------------------------------------------------------

def make_popen_kwargs(cwd, stderr_file) -> dict:
    """Build platform-appropriate kwargs for subprocess.Popen.

    - Scrubs CLAUDE_CODE_* and CLAUDECODE* env vars on ALL platforms
      to prevent the child from inheriting loop-specific state.
    - Sets CREATE_NEW_PROCESS_GROUP on Windows for proper signal handling.
    """
    env = os.environ.copy()
    # Scrub Claude Code env vars to prevent child inheriting loop state
    for key in list(env.keys()):
        if key.startswith('CLAUDE_CODE_') or key.startswith('CLAUDECODE'):
            del env[key]

    kwargs = {
        'stdout': subprocess.PIPE,
        'stderr': stderr_file,
        'text': True,
        'cwd': cwd,
        'env': env,
    }

    if _IS_WINDOWS:
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP

    return kwargs


# ---------------------------------------------------------------------------
# Signal setup
# ---------------------------------------------------------------------------

def setup_signals(handler):
    """Register shutdown signal handlers, guarding SIGHUP on Windows."""
    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, handler)
