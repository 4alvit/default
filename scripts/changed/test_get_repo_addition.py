"""Coverage for real get_repo calling real get_category.

Synthetic category lists live only in temporary directories. Both modules'
DEFAULT constants point at that baseline, and the process cwd is the
candidate directory. Patches and cwd are restored even when a test fails.
This does not read or write /tmp/repositories or the worktree category lists.
"""

import json
import os
import tempfile
import unittest
from unittest import mock

from scripts.changed import category
from scripts.changed import repo
from scripts.changed.repo import get_repo


FORBIDDEN_DEFAULT = "/tmp/repositories/default"


class GetRepoAdditionTests(unittest.TestCase):
    def setUp(self):
        self.baseline = tempfile.TemporaryDirectory(prefix="hacs-baseline-")
        self.candidate = tempfile.TemporaryDirectory(prefix="hacs-candidate-")
        # Cleanups run in reverse order: patches, then cwd, then directories.
        self.addCleanup(self.baseline.cleanup)
        self.addCleanup(self.candidate.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        self._start(mock.patch.object(category, "DEFAULT", self.baseline.name))
        self._start(mock.patch.object(repo, "DEFAULT", self.baseline.name))
        self._start(mock.patch.object(category, "CURRENT", {}))
        self._start(mock.patch.object(category, "CHANGED", {}))
        self.assertNotEqual(category.DEFAULT, FORBIDDEN_DEFAULT)
        self.assertNotEqual(repo.DEFAULT, FORBIDDEN_DEFAULT)

    def _start(self, patcher):
        patcher.start()
        self.addCleanup(patcher.stop)

    def _write_categories(self, additions):
        for name in category.CATEGORIES:
            baseline_repos = ["fixture/%s-base" % name]
            candidate_repos = list(baseline_repos)
            candidate_repos.extend(additions.get(name, []))
            self._write(self.baseline.name, name, baseline_repos)
            self._write(self.candidate.name, name, candidate_repos)

    def _write(self, directory, name, repos):
        with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
            json.dump(repos, handle)
            handle.write("\n")

    def _call(self):
        os.chdir(self.candidate.name)
        return get_repo()

    def test_exactly_one_addition_returns_that_repository(self):
        self._write_categories({"integration": ["fixture/integration-added"]})
        self.assertEqual(self._call(), "fixture/integration-added")

    def test_invalid_repository_names_are_rejected(self):
        for value in (
            "owner/repo\ncategory=integration", "owner/$(true)",
            "owner/repo`true`", "owner/repo?query=x", "owner/../repo",
            "owner/..", "-owner/repo", "owner-/repo", "owner/repo name",
            "https://github.com/owner/repo", 123, None,
        ):
            with self.subTest(value=value):
                self._write_categories({"integration": [value]})
                with self.assertRaises(ValueError):
                    self._call()

    def test_no_addition_exits_1(self):
        self._write_categories({})
        with self.assertRaises(SystemExit) as caught:
            self._call()
        self.assertEqual(caught.exception.code, 1)

    def test_two_additions_in_one_category_exit_1(self):
        self._write_categories({
            "plugin": ["fixture/plugin-added-a", "fixture/plugin-added-b"],
        })
        with self.assertRaises(SystemExit) as caught:
            self._call()
        self.assertEqual(caught.exception.code, 1)

    def test_additions_across_two_categories_exit_1(self):
        self._write_categories({
            "integration": ["fixture/integration-added"],
            "theme": ["fixture/theme-added"],
        })
        with self.assertRaises(SystemExit) as caught:
            self._call()
        self.assertEqual(caught.exception.code, 1)


if __name__ == "__main__":
    unittest.main()
