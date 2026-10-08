# Security policy

## Scope and supported versions

This repository is the `4alvit/default` fork of
[`hacs/default`](https://github.com/hacs/default). It contains repository lists
and automation for validating and maintaining those lists. This policy covers
this fork's changes, scripts and GitHub Actions workflows. It does not claim to
provide security support for every listed integration or for the upstream HACS
project.

Security fixes for this fork target the current `master` branch. Older commits
are not separately maintained. Update to the latest reviewed commit before
checking whether an issue is still reproducible.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/4alvit/default/security/advisories/new)
to contact the maintainers of this fork confidentially. Private reporting is
enabled for this repository. Do not include an unpatched vulnerability, access
token, customer data or other secret in a public issue or pull request.

Include the affected commit, script or workflow, the required permissions and
input, reproduction steps, and the expected security impact. Use dummy
credentials and a minimal example. Do not test against repositories or services
without their owner's authorization.

The maintainers aim to acknowledge reports within seven days, confirm their
scope and coordinate a fix and disclosure with the reporter. If a report also
affects upstream HACS or a listed integration, coordinate private disclosure
with that project's maintainers; this fork cannot fix or promise support for
software maintained elsewhere. Keep reproduction details private until the
maintainers and reporter have coordinated disclosure.

Ordinary repository-list corrections and feature requests may use public issues.

The [TLS runtime requirements](docs/TLS_RUNTIME.md) distinguish the verified
Python client environments from operator-only upload integrations.
