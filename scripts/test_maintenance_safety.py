import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
CATEGORIES = (
    "appdaemon",
    "integration",
    "netdaemon",
    "plugin",
    "python_script",
    "template",
    "theme",
)


class PublisherMaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="catalog maintenance ")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(
            SCRIPTS, self.root / "scripts", ignore=shutil.ignore_patterns("__pycache__")
        )
        for category in (*CATEGORIES, "blacklist", "removed"):
            value = (
                ["fixture/keep", "reharmsen/synthetic"]
                if category == "integration"
                else []
            )
            (self.root / category).write_text(json.dumps(value))

    def test_importing_owner_check_constants_does_not_modify_catalog(self):
        before = {
            name: (self.root / name).read_bytes()
            for name in (*CATEGORIES, "blacklist", "removed")
        }
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "from scripts.remove_publishers import REMOVED_PUBLISHERS; assert REMOVED_PUBLISHERS",
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        self.assertEqual(result.stdout, "")
        self.assertEqual(
            before, {name: (self.root / name).read_bytes() for name in before}
        )

    def test_explicit_module_command_still_applies_removals(self):
        subprocess.run(
            [sys.executable, "-m", "scripts.remove_publishers"],
            cwd=self.root,
            text=True,
            capture_output=True,
            timeout=10,
            check=True,
        )
        self.assertEqual(
            json.loads((self.root / "integration").read_text()), ["fixture/keep"]
        )
        self.assertEqual(
            json.loads((self.root / "blacklist").read_text()), ["reharmsen/synthetic"]
        )
        self.assertEqual(
            json.loads((self.root / "removed").read_text()),
            [
                {
                    "repository": "reharmsen/synthetic",
                    "link": "https://github.com/hacs/integration/issues/2192",
                    "reason": "Author removed",
                    "removal_type": "removal",
                }
            ],
        )


class RemovalWrapperTests(unittest.TestCase):
    def test_wrappers_preserve_arguments_and_return_the_python_status(self):
        with tempfile.TemporaryDirectory(prefix="catalog wrapper ") as temporary:
            root = Path(temporary)
            scripts = root / "scripts with spaces"
            scripts.mkdir()
            executable = root / "python3"
            executable.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE"\nexit "$TEST_STATUS"\n'
            )
            executable.chmod(0o755)
            for name in ("remove_archived_repo", "remove_repository"):
                shutil.copyfile(SCRIPTS / name, scripts / name)
                for status in (0, 7):
                    with self.subTest(wrapper=name, status=status):
                        capture = root / "arguments"
                        environment = {
                            **os.environ,
                            "PATH": str(root) + os.pathsep + os.defpath,
                            "CAPTURE": str(capture),
                            "TEST_STATUS": str(status),
                        }
                        args = (
                            ["fixture/repository"]
                            if name == "remove_archived_repo"
                            else []
                        )
                        stdin = "fixture/repository\nexample reason\nremove\nhttps://example.invalid/issue\n"
                        result = subprocess.run(
                            ["bash", str(scripts / name), *args],
                            input=stdin,
                            text=True,
                            capture_output=True,
                            env=environment,
                            timeout=10,
                        )
                        self.assertEqual(result.returncode, status)
                        expected = [
                            str(scripts / "remove_repo.py"),
                            "fixture/repository",
                            "remove",
                        ]
                        expected += (
                            ["Repository is archived", "N/A"]
                            if args
                            else ["example reason", "https://example.invalid/issue"]
                        )
                        self.assertEqual(capture.read_text().splitlines(), expected)


if __name__ == "__main__":
    unittest.main()
