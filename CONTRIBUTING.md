# Contributing to this catalog fork

This is the `4alvit/default` fork of the HACS default repository catalog. Changes
here do not by themselves publish a repository in upstream HACS. Follow the
[upstream inclusion process](https://hacs.xyz/docs/publish/include) for that.
This fork maintains its catalog changes, validation scripts and workflows.

Use a pull request for changes. Describe the problem, affected catalog or command,
expected behavior and verification. For an ordinary script defect, open an issue
with a minimal example, affected commit and Python version. Never include a live
token or private repository data. Use [SECURITY.md](SECURITY.md) for vulnerabilities.

Preserve the upstream MIT license and notices. Keep lists sorted and valid against
the checked-in JSON schemas. Add automated tests for major new behavior and a
regression test for a bug fix. Existing tests cover repository-name validation,
workflow output propagation and same-repository versus fork edit permissions.
Fix actionable lint or security findings; do not disable checks to hide them.

## Local checks

Use Python 3.10 (the version in `.python-version`), Git and a virtual environment.
Run from the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
bash scripts/setup
python3 -m pip install --require-hashes --only-binary=:all: -r .github/requirements-lint.txt
python3 -m pip check
python3 -m ruff check --select E9,F scripts
python3 scripts/is_sorted.py
python3 -m unittest discover -s scripts -p 'test_*.py' -v
```

These commands do not need GitHub or Cloudflare credentials. CI additionally
checks JSON schemas, Python and Actions with CodeQL, dependency changes, and the
maintenance image. The error-focused Ruff rules check syntax, names and imports;
they do not impose a new formatting convention. See
[dependency maintenance](docs/DEPENDENCY_LOCKS.md) before updating a lock.

## Source identity and delivery

The reviewed `master` branch is this fork's source distribution. Record the full
`git rev-parse HEAD` value when reporting a problem or reproducing a check.
The fork has no independent versioned HACS application releases. Repository-list
PR descriptions should explain additions/removals and their user impact; script
PR descriptions should explain behavior, compatibility and security changes.
These descriptions support review and do not claim to be release notes for a
separate HACS distribution.

Upstream controls inclusion in the HACS catalog. The inherited upload workflows
are operator-only integrations and are not part of local validation. Do not
dispatch them to test a contribution. If this fork starts publishing independently
versioned reusable software, add an explicit version and human-written release
notes covering changes, upgrade impact and fixed project vulnerabilities.

See [script interfaces](docs/SCRIPT_INTERFACES.md) before invoking maintenance
commands: several rewrite catalog files, and not every wrapper propagates errors.
