"""Shell propagation for the preflight repository and category steps.

The historical one-line echo command substitution is fail-before evidence.
The run scripts now stored in checks.yml are the pass-after form. This test
executes only those two scripts with bash -e -o pipefail. It does not run the
workflow, actions, checkout, clone, or GitHub.
"""

import json
import os
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest

from scripts.changed import category
from scripts.changed import repo


WORKTREE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW = os.path.join(WORKTREE, ".github", "workflows", "checks.yml")
FAIL_BEFORE = {
    "Set repository": 'echo "repository=$(python3 -m scripts.changed.repo)" >> $GITHUB_OUTPUT',
    "Set category": 'echo "category=$(python3 -m scripts.changed.category)" >> $GITHUB_OUTPUT',
}


def extract_run(step_name):
    with open(WORKFLOW, encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    for index, line in enumerate(lines):
        if line.strip() != "- name: %s" % step_name:
            continue
        for run_at in range(index + 1, len(lines)):
            if lines[run_at].strip() != "run: |":
                if lines[run_at].startswith("      - "):
                    break
                continue
            body = []
            indent = None
            for body_at in range(run_at + 1, len(lines)):
                current = lines[body_at]
                if current.strip() == "":
                    body.append("")
                    continue
                current_indent = len(current) - len(current.lstrip(" "))
                if indent is None:
                    indent = current_indent
                if current_indent < indent:
                    break
                body.append(current[indent:])
            return "\n".join(body).strip() + "\n"
    raise AssertionError("run script not found for %s" % step_name)


class ChecksOutputPropagationTests(unittest.TestCase):
    def setUp(self):
        self.previous_cwd = os.getcwd()
        self.previous_defaults = (category.DEFAULT, repo.DEFAULT)
        self.previous_current = category.CURRENT
        self.previous_changed = category.CHANGED
        self.root = tempfile.TemporaryDirectory(prefix="hacs-output-")
        self.addCleanup(self.root.cleanup)
        self.addCleanup(self._restore_parent)
        self.baseline = os.path.join(self.root.name, "baseline")
        self.candidate = os.path.join(self.root.name, "candidate")
        os.mkdir(self.baseline)
        os.mkdir(self.candidate)
        self.launcher = os.path.join(self.root.name, "bin", "python3")
        os.mkdir(os.path.dirname(self.launcher))
        self._write_launcher()

    def _restore_parent(self):
        os.chdir(self.previous_cwd)
        category.DEFAULT, repo.DEFAULT = self.previous_defaults
        category.CURRENT = self.previous_current
        category.CHANGED = self.previous_changed

    def _write_launcher(self):
        script = textwrap.dedent(
            """\
            #!{python}
            import os
            import sys
            sys.path.insert(0, {worktree!r})
            allowed = {{
                ("-m", "scripts.changed.repo"): "repo",
                ("-m", "scripts.changed.category"): "category",
            }}
            key = tuple(sys.argv[1:3])
            if key not in allowed or len(sys.argv) != 3:
                sys.stderr.write("fixture launcher refused\\n")
                raise SystemExit(2)
            from scripts.changed import category, repo
            saved_cwd = os.getcwd()
            saved_defaults = (category.DEFAULT, repo.DEFAULT)
            saved_current = category.CURRENT
            saved_changed = category.CHANGED
            try:
                category.DEFAULT = os.environ["HACS_FIXTURE_BASELINE"]
                repo.DEFAULT = os.environ["HACS_FIXTURE_BASELINE"]
                category.CURRENT = {{}}
                category.CHANGED = {{}}
                os.chdir(os.environ["HACS_FIXTURE_CANDIDATE"])
                if allowed[key] == "repo":
                    print(repo.get_repo())
                else:
                    print(category.get_category())
            finally:
                os.chdir(saved_cwd)
                category.DEFAULT, repo.DEFAULT = saved_defaults
                category.CURRENT = saved_current
                category.CHANGED = saved_changed
            """
        ).format(python=sys.executable, worktree=WORKTREE)
        with open(self.launcher, "w", encoding="utf-8") as handle:
            handle.write(script)
        os.chmod(self.launcher, os.stat(self.launcher).st_mode | stat.S_IEXEC)

    def _write_categories(self, additions):
        for name in category.CATEGORIES:
            baseline_repos = ["fixture/%s-base" % name]
            candidate_repos = list(baseline_repos)
            candidate_repos.extend(additions.get(name, []))
            for directory, repos in (
                (self.baseline, baseline_repos),
                (self.candidate, candidate_repos),
            ):
                with open(os.path.join(directory, name), "w", encoding="utf-8") as handle:
                    json.dump(repos, handle)
                    handle.write("\n")

    def _run(self, script):
        output = os.path.join(self.root.name, "github-output.txt")
        with open(output, "w", encoding="utf-8") as handle:
            handle.write("")
        env = os.environ.copy()
        env["PATH"] = os.path.dirname(self.launcher) + os.pathsep + env.get("PATH", "")
        env["GITHUB_OUTPUT"] = output
        env["HACS_FIXTURE_BASELINE"] = self.baseline
        env["HACS_FIXTURE_CANDIDATE"] = self.candidate
        completed = subprocess.run(
            ["bash", "-e", "-o", "pipefail", "-c", script],
            env=env,
            cwd=self.previous_cwd,
            capture_output=True,
            text=True,
        )
        with open(output, encoding="utf-8") as handle:
            published = handle.read()
        return completed.returncode, published

    def test_one_addition_control_publishes_repository_and_category(self):
        self._write_categories({"integration": ["fixture/integration-added"]})
        repository_code, repository_out = self._run(extract_run("Set repository"))
        category_code, category_out = self._run(extract_run("Set category"))
        self.assertEqual(repository_code, 0)
        self.assertEqual(category_code, 0)
        self.assertEqual(repository_out, "repository=fixture/integration-added\n")
        self.assertEqual(category_out, "category=integration\n")
        self.assertEqual(os.getcwd(), self.previous_cwd)
        self.assertEqual((category.DEFAULT, repo.DEFAULT), self.previous_defaults)
        self.assertIs(category.CURRENT, self.previous_current)
        self.assertIs(category.CHANGED, self.previous_changed)

    def test_fail_before_echo_masks_detector_failure(self):
        self._write_categories({})
        for step_name, script in FAIL_BEFORE.items():
            exit_code, published = self._run(script)
            self.assertEqual(exit_code, 0, step_name)
            self.assertIn("Bad data []", published, step_name)

    def test_pass_after_detector_failure_publishes_nothing(self):
        with open(WORKFLOW, encoding="utf-8") as handle:
            workflow = handle.read()
        for script in FAIL_BEFORE.values():
            self.assertNotIn(script, workflow)
        self._write_categories({})
        for step_name in ("Set repository", "Set category"):
            exit_code, published = self._run(extract_run(step_name))
            self.assertNotEqual(exit_code, 0, step_name)
            self.assertEqual(published, "", step_name)


if __name__ == "__main__":
    unittest.main()
