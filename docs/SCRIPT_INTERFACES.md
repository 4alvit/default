# Catalog and script interfaces

Run commands from the repository root in a disposable working copy when a command
can edit lists. This is a reference for the current fork, not a promise that every
inherited command is safe to invoke as a read-only check.

## Files and checks

The `appdaemon`, `blacklist`, `integration`, `netdaemon`, `plugin`, `python_script`,
`template` and `theme` files contain JSON arrays of repository names. `critical`
and `removed` contain JSON objects in arrays, with fields defined by
`tools/jsonschema/critical.schema.json` and `removed.schema.json`. The repository
array schema is `tools/jsonschema/repositories.schema.json`.

- `bash scripts/setup` installs the hashed Python lock into the active interpreter.
  It exits nonzero if installation fails and does not read production credentials.
- `python3 scripts/is_sorted.py` reads the ordinary category arrays and blacklist.
  It exits zero silently when sorted case-insensitively; otherwise it prints the
  expected/current values and exits one. It does not sort the files for you.
- `python3 -m unittest discover -s scripts -p 'test_*.py' -v` runs isolated regression
  tests. Test failures return nonzero. No live API token is needed.
- `python3 -m scripts.changed.category` compares the root category arrays with
  `/tmp/repositories/default/`. It prints the single category containing additions
  or exits one for an ambiguous result.
- `python3 -m scripts.changed.repo` performs that comparison and prints the single
  added `owner/repository`. It rejects multiple additions and malformed names.
  CI clones upstream into the comparison directory before using these commands.

## API and event checks

`python3 -m scripts.check.edits` reads the JSON event file at `GITHUB_EVENT_PATH`.
It accepts a same-repository PR, or a fork PR with maintainer edits enabled, and
exits nonzero for missing identities or disallowed edits.

`scripts.check.owner` and `scripts.check.releases` also use `REPOSITORY` and
`GITHUB_TOKEN` for GitHub API requests through aiogithubapi/aiohttp. They print
their result and fail with an Actions error annotation when a check fails.
The owner check additionally reads the PR author from `GITHUB_EVENT_PATH`.
Importing the publisher constants does not rewrite catalog files. The releases
check requires at least one release for the proposed repository.

`scripts.check.existing` and `scripts.check.removed` read `REPOSITORY`, fetch the
public `https://data-v2.hacs.xyz/` lists through Requests and fail if the repository
is already listed or removed, respectively. These are network checks, not part
of the credential-free unit test command. Existing implementations do not set an
application request timeout; use CI's job boundary when diagnosing a stalled API.

`python3 -m scripts.helpers.integration_path` finds exactly one `*manifest.json`
under `/tmp/repositories/addition` and prints its integration path, or exits one.
`scripts.helpers.domain` prints the `domain` from that manifest. These helpers
inspect the cloned candidate used by the inherited HACS validation workflow.

## Commands which edit files

`python3 scripts/sort.py` (or `bash scripts/sort`) rewrites the ordinary category
arrays and blacklist in case-insensitive order. Review the resulting Git diff.

`python3 scripts/remove_repo.py owner/repository removal_type "reason" "link"`
removes a repository from its category and updates `blacklist` and `removed`.
The last two arguments are optional; removal type is required. The script may
write a category before a later error. `bash scripts/remove_repository` prompts
for these inputs; `bash scripts/remove_archived_repo owner/repository` supplies
an archived-repository reason. Both wrappers preserve the Python exit status
and quote the script path, including when the checkout path contains spaces. Review their output and Git
diff; a direct removal can still modify a file before a later failure.
`scripts/add_repository` only prints `Not implemented`.

`python3 scripts/remove_publishers.py` rewrites lists using its checked-in publisher
list. Importing that module only loads its constants and definitions; list edits
happen only when its CLI (or its `main()` function) is explicitly invoked.

## Operator-only uploads

The inherited upload workflows transform `critical` or `removed` with `jq`,
upload an Actions artifact, synchronize files with AWS CLI to a configured R2
endpoint, and request a Cloudflare cache purge. They require operator-managed
secrets. This fork's test commands never invoke an upload, purge, notification or
repository inclusion. See [TLS runtime requirements](TLS_RUNTIME.md) before an
operator configures those integrations.
