"""Tests for bundler functions in dev/release.py."""

import sys
import unittest
from pathlib import Path

# Add dev/ to path so we can import release module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dev"))

from release import collect_stdlib_imports, strip_hoisted_imports


class TestStripHoistedImports(unittest.TestCase):
    """Tests for strip_hoisted_imports()."""

    def test_strips_top_level_simple_import(self):
        content = "import os\n\nx = 1"
        result = strip_hoisted_imports(content)
        self.assertNotIn("import os", result)
        self.assertIn("x = 1", result)

    def test_strips_top_level_from_import(self):
        content = "from pathlib import Path\n\nx = 1"
        result = strip_hoisted_imports(content)
        self.assertNotIn("from pathlib", result)
        self.assertIn("x = 1", result)

    def test_preserves_indented_import_in_function(self):
        content = "def foo():\n    import pty as pty_module\n    return pty_module"
        result = strip_hoisted_imports(content)
        self.assertIn("import pty as pty_module", result)

    def test_preserves_indented_import_in_try(self):
        content = "def bar():\n    try:\n        import winpty\n    except ImportError:\n        pass"
        result = strip_hoisted_imports(content)
        self.assertIn("import winpty", result)

    def test_strips_relative_import_at_top_level(self):
        content = "from .config import FOO\n\nx = FOO"
        result = strip_hoisted_imports(content)
        self.assertNotIn("from .config", result)
        self.assertIn("x = FOO", result)

    def test_strips_indented_relative_import(self):
        content = "def foo():\n    from .loop import merge\n    merge()"
        result = strip_hoisted_imports(content)
        self.assertNotIn("from .loop", result)
        self.assertIn("merge()", result)

    def test_strips_multiline_relative_import(self):
        content = "from .config import (\n    FOO,\n    BAR,\n)\n\nx = FOO"
        result = strip_hoisted_imports(content)
        self.assertNotIn("from .config", result)
        self.assertNotIn("FOO,", result)
        self.assertNotIn("BAR,", result)
        self.assertIn("x = FOO", result)

    def test_strips_multiline_top_level_import(self):
        content = "from pathlib import (\n    Path,\n    PurePath,\n)\n\nx = 1"
        result = strip_hoisted_imports(content)
        self.assertNotIn("from pathlib", result)
        self.assertNotIn("Path,", result)
        self.assertIn("x = 1", result)

    def test_strips_logger_assignment(self):
        content = "logger = logging.getLogger(__name__)\n\nx = 1"
        result = strip_hoisted_imports(content)
        self.assertNotIn("logger", result)
        self.assertIn("x = 1", result)

    def test_preserves_non_import_code(self):
        content = "import os\n\nFOO = 'bar'\n\ndef baz():\n    return FOO"
        result = strip_hoisted_imports(content)
        self.assertIn("FOO = 'bar'", result)
        self.assertIn("def baz():", result)


class TestCollectStdlibImports(unittest.TestCase):
    """Tests for collect_stdlib_imports()."""

    def test_collects_simple_import(self):
        modules = [("mod.py", "import os\n\nx = 1")]
        result = collect_stdlib_imports(modules, "")
        self.assertIn("import os", result)

    def test_collects_from_import(self):
        modules = [("mod.py", "from pathlib import Path\n\nx = 1")]
        result = collect_stdlib_imports(modules, "")
        self.assertIn("from pathlib import Path", result)

    def test_skips_indented_imports(self):
        modules = [("mod.py", "def foo():\n    import winpty\n    return winpty")]
        result = collect_stdlib_imports(modules, "")
        self.assertNotIn("import winpty", result)

    def test_skips_relative_imports(self):
        modules = [("mod.py", "from .config import FOO")]
        result = collect_stdlib_imports(modules, "")
        self.assertEqual(result, [])

    def test_skips_line_loop_imports(self):
        modules = [("mod.py", "from line_loop import config")]
        result = collect_stdlib_imports(modules, "")
        self.assertEqual(result, [])

    def test_skips_type_checking_imports(self):
        modules = [("mod.py", "from typing import TYPE_CHECKING")]
        result = collect_stdlib_imports(modules, "")
        self.assertEqual(result, [])

    def test_merges_from_imports(self):
        modules = [
            ("a.py", "from typing import Optional"),
            ("b.py", "from typing import Any"),
        ]
        result = collect_stdlib_imports(modules, "")
        self.assertIn("from typing import Any, Optional", result)

    def test_deduplicates_simple_imports(self):
        modules = [
            ("a.py", "import os"),
            ("b.py", "import os"),
        ]
        result = collect_stdlib_imports(modules, "")
        self.assertEqual(result.count("import os"), 1)

    def test_collects_from_cli_content(self):
        modules = []
        cli = "import argparse\n\ndef main(): pass"
        result = collect_stdlib_imports(modules, cli)
        self.assertIn("import argparse", result)

    def test_sorts_output(self):
        modules = [("mod.py", "import sys\nimport os\nimport json")]
        result = collect_stdlib_imports(modules, "")
        self.assertEqual(result, ["import json", "import os", "import sys"])


if __name__ == "__main__":
    unittest.main()
