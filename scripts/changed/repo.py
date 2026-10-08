import json
import re
from scripts.changed.category import get_category

DEFAULT = "/tmp/repositories/default"


def get_repo():
    category = get_category()
    with open(f"{DEFAULT}/{category}", "r") as default:
        current = json.loads(default.read())

    with open(category, "r") as default:
        new = json.loads(default.read())

    for repo in current:
        if repo in new:
            new.remove(repo)

    if len(new) != 1:
        print(f"Bad data {new}")
        exit(1)

    repository = new.pop()
    if not isinstance(repository, str) or re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9._-]{1,100}",
        repository,
    ) is None or repository.split("/")[1] in {".", ".."}:
        raise ValueError("Expected a GitHub owner/repository name")
    return repository


if __name__ == "__main__":
    print(get_repo())
