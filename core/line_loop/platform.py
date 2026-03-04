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
# PTY-based PipeReader for CLIs that need a pseudo-TTY (e.g., OpenCode)
# ---------------------------------------------------------------------------

class UnixPtyPipeReader(PipeReader):
    """Unix PTY reader using pty.openpty() + select (BP-2.1).

    OpenCode requires a PTY to flush stdout during tool calls. This reader
    creates a master/slave fd pair, spawns the child with the slave as stdout,
    and reads from the master fd using select() for timeout support.
    """

    def __init__(self, master_fd: int):
        self._master_fd = master_fd
        self._buffer = ''
        self._eof = False

    def readline(self, timeout: float) -> Optional[str]:
        if self._eof:
            return ''

        # Check for complete line in buffer first
        newline_pos = self._buffer.find('\n')
        if newline_pos >= 0:
            line = self._buffer[:newline_pos + 1]
            self._buffer = self._buffer[newline_pos + 1:]
            # Strip PTY \r artifacts (BP-2.3)
            return line.replace('\r', '')

        # Wait for data with timeout
        ready, _, _ = select.select([self._master_fd], [], [], timeout)
        if not ready:
            return None  # timeout

        try:
            data = os.read(self._master_fd, 4096)
        except OSError:
            self._eof = True
            # Flush remaining buffer
            if self._buffer:
                line = self._buffer.replace('\r', '')
                self._buffer = ''
                return line + '\n' if not line.endswith('\n') else line
            return ''

        if not data:
            self._eof = True
            if self._buffer:
                line = self._buffer.replace('\r', '')
                self._buffer = ''
                return line + '\n' if not line.endswith('\n') else line
            return ''

        self._buffer += data.decode('utf-8', errors='replace')

        # Check for complete line again
        newline_pos = self._buffer.find('\n')
        if newline_pos >= 0:
            line = self._buffer[:newline_pos + 1]
            self._buffer = self._buffer[newline_pos + 1:]
            return line.replace('\r', '')

        return None  # No complete line yet

    def drain(self) -> list[str]:
        lines = []
        # Read any remaining data
        try:
            while True:
                ready, _, _ = select.select([self._master_fd], [], [], 0.1)
                if not ready:
                    break
                data = os.read(self._master_fd, 4096)
                if not data:
                    break
                self._buffer += data.decode('utf-8', errors='replace')
        except OSError:
            pass

        # Split buffer into lines
        if self._buffer:
            for line in self._buffer.splitlines(keepends=True):
                lines.append(line.replace('\r', ''))
            self._buffer = ''
        return lines

    def close(self):
        try:
            os.close(self._master_fd)
        except OSError:
            pass


class WindowsPtyPipeReader(PipeReader):
    """Windows PTY reader using pywinpty if available, ThreadedPipeReader fallback.

    Falls back to ThreadedPipeReader with a warning if pywinpty is not installed.
    With ThreadedPipeReader fallback, output may be buffered (idle/active extension
    degraded but signals still detected at process exit).
    """

    def __init__(self, inner: PipeReader, is_native_pty: bool = False):
        self._inner = inner
        self._is_native_pty = is_native_pty

    def readline(self, timeout: float) -> Optional[str]:
        line = self._inner.readline(timeout)
        if line is not None and self._is_native_pty:
            # Strip PTY artifacts from ConPTY
            line = line.replace('\r', '')
        return line

    def drain(self) -> list[str]:
        lines = self._inner.drain()
        if self._is_native_pty:
            lines = [l.replace('\r', '') for l in lines]
        return lines

    def close(self):
        self._inner.close()


def create_pty_reader_and_process(
    cmd: list[str],
    cwd,
    stderr_file,
    env: dict,
) -> tuple[PipeReader, subprocess.Popen]:
    """Create a PTY-wrapped subprocess for CLIs that need a pseudo-TTY.

    On Unix: uses pty.openpty() for direct fd control (BP-2.1).
    On Windows: tries pywinpty, falls back to ThreadedPipeReader with warning.

    Args:
        cmd: Command list for subprocess.
        cwd: Working directory.
        stderr_file: Open file for stderr capture.
        env: Environment variables dict.

    Returns:
        Tuple of (PipeReader, Popen process).
    """
    if _IS_WINDOWS:
        return _create_windows_pty_process(cmd, cwd, stderr_file, env)
    else:
        return _create_unix_pty_process(cmd, cwd, stderr_file, env)


def _create_unix_pty_process(
    cmd: list[str],
    cwd,
    stderr_file,
    env: dict,
) -> tuple[PipeReader, subprocess.Popen]:
    """Create Unix PTY process using pty.openpty()."""
    import pty as pty_module

    master_fd, slave_fd = pty_module.openpty()

    try:
        process = subprocess.Popen(
            cmd,
            stdout=slave_fd,
            stdin=slave_fd,   # Child sees terminal; parent never writes (non-interactive)
            stderr=stderr_file,
            cwd=cwd,
            env=env,
        )
    except Exception:
        os.close(master_fd)
        os.close(slave_fd)
        raise

    # Parent closes slave fd immediately (BP-2.2 — prevents EOF hang)
    os.close(slave_fd)

    reader = UnixPtyPipeReader(master_fd)
    return reader, process


def _create_windows_pty_process(
    cmd: list[str],
    cwd,
    stderr_file,
    env: dict,
) -> tuple[PipeReader, subprocess.Popen]:
    """Create Windows PTY process, with pywinpty or ThreadedPipeReader fallback."""
    try:
        import winpty  # type: ignore[import-untyped]

        pty_proc = winpty.PtyProcess.spawn(
            cmd,
            cwd=str(cwd),
            env=env,
        )
        # Wrap in a PipeReader-compatible interface
        reader = _WinPtyReader(pty_proc)
        # Create a Popen-like wrapper for the winpty process
        process = _WinPtyProcessWrapper(pty_proc)
        return WindowsPtyPipeReader(reader, is_native_pty=True), process

    except ImportError:
        logger.warning(
            "pywinpty not installed — OpenCode output will be buffered. "
            "Install pywinpty for real-time output tracking on Windows: pip install pywinpty"
        )
        # Fallback: standard Popen with ThreadedPipeReader
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=stderr_file,
            text=True,
            cwd=cwd,
            env=env,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        reader = ThreadedPipeReader(process.stdout)
        return WindowsPtyPipeReader(reader, is_native_pty=False), process


class _WinPtyReader(PipeReader):
    """Adapter wrapping winpty.PtyProcess as a PipeReader.

    Uses a background thread for non-blocking reads since PtyProcess.read()
    blocks and doesn't support timeout. Lines are queued and consumed
    via readline() with timeout support (same pattern as ThreadedPipeReader).
    """

    _EOF = object()  # sentinel

    def __init__(self, pty_proc):
        self._proc = pty_proc
        self._queue: Queue = Queue()
        self._eof_seen = False
        self._thread = threading.Thread(target=self._reader, daemon=True)
        self._thread.start()

    def _reader(self):
        """Background thread: reads from PTY and enqueues complete lines."""
        buffer = ''
        try:
            while True:
                try:
                    data = self._proc.read(4096)
                except EOFError:
                    break
                if not data:
                    break
                buffer += data
                # Split into lines and enqueue complete ones
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    self._queue.put(line + '\n')
            # Flush any remaining partial line
            if buffer:
                self._queue.put(buffer + '\n')
        except Exception:
            pass
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
        try:
            self._proc.close()
        except Exception:
            pass
        if self._thread.is_alive():
            self._thread.join(timeout=5)


class _WinPtyProcessWrapper:
    """Minimal Popen-like wrapper around winpty.PtyProcess for process management."""

    def __init__(self, pty_proc):
        self._proc = pty_proc
        self.pid = pty_proc.pid
        self.returncode = None

    def poll(self) -> Optional[int]:
        if not self._proc.isalive():
            self.returncode = self._proc.exitstatus or 0
            return self.returncode
        return None

    def wait(self, timeout=None):
        self._proc.wait()
        self.returncode = self._proc.exitstatus or 0
        return self.returncode

    def terminate(self):
        try:
            self._proc.close(force=False)
        except Exception:
            pass

    def kill(self):
        try:
            self._proc.close(force=True)
        except Exception:
            pass


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
