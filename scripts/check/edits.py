import asyncio

from scripts.helpers.event import get_event


def _repository_name(reference):
    repository = reference.get("repo") if isinstance(reference, dict) else None
    name = repository.get("full_name") if isinstance(repository, dict) else None
    return name if isinstance(name, str) and name.strip() else None


async def check():
    event = get_event()
    pull_request = event["pull_request"]
    head_repository = _repository_name(pull_request.get("head"))
    base_repository = _repository_name(pull_request.get("base"))
    if not head_repository or not base_repository:
        raise SystemExit("::error::The PR repository identities are missing")
    # Same-repository branches do not need the fork-only edit permission.
    if head_repository != base_repository and pull_request.get("maintainer_can_modify") is not True:
        raise SystemExit("::error::The PR is not editable by HACS maintainers")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(check())
