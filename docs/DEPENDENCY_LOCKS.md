# Dependency maintenance

This fork's script dependencies and upload tools use exact package versions and
SHA-256 hashes. `scripts/setup` installs the complete `requirements.txt` lock on
the Python version in `.python-version`. The source requirements remain in
`requirements.in`; updates must regenerate the lock rather than edit hashes.
The upload workflows use Python 3.12 and a separate AWS CLI lock so they do not
change the script environment. AWS CLI is updated from 1.36.39 to 1.46.1.

Each generated lock records its `uv pip compile` command in its opening comments.
Regenerate with uv 0.12.7, review changes, and run the dependency CI jobs before
merging. The Python job installs and imports the actual dependencies and runs
the existing input/output tests. The tools job checks the real AWS CLI and
builds the maintenance image without credentials, uploads or cache purges.

The maintenance Dockerfile pins Alpine 3.23.6 by its multi-platform manifest
digest. Review the upstream registry manifest when updating that pin. APK
packages still receive distribution updates at build time; the image pin does
not freeze the external APK repository.

Hashes verify selected artifact identity, not absence of vulnerabilities.
Keep dependency review and scheduled updates enabled, and audit the entire
resolved lock. This fork's changes do not alter HACS upstream publication policy.
