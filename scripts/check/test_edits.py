"""Validate editable-fork and same-repository PR metadata without GitHub access."""

import copy
import unittest
from unittest import mock

from scripts.check import edits


class EditablePullRequestTests(unittest.IsolatedAsyncioTestCase):
    def event(self, head="4alvit/default", base="4alvit/default", editable=False):
        return {
            "pull_request": {
                "head": {"repo": {"full_name": head}},
                "base": {"repo": {"full_name": base}},
                "maintainer_can_modify": editable,
            }
        }

    async def check_event(self, event):
        with mock.patch.object(edits, "get_event", return_value=event):
            await edits.check()

    async def test_same_repository_does_not_require_fork_edit_permission(self):
        for repository in ("4alvit/default", "hacs/default"):
            with self.subTest(repository=repository):
                await self.check_event(self.event(head=repository, base=repository))

    async def test_editable_fork_is_accepted(self):
        await self.check_event(self.event(head="contributor/default", editable=True))

    async def test_noneditable_fork_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "not editable"):
            await self.check_event(self.event(head="contributor/default"))

    async def test_original_upstream_is_not_a_same_repository_exception_for_a_fork(self):
        with self.assertRaisesRegex(SystemExit, "not editable"):
            await self.check_event(self.event(head="hacs/default"))

    async def test_missing_repository_identity_fails_closed_even_for_editable_pr(self):
        for branch in ("head", "base"):
            for reference in (None, {}, {"repo": None}, {"repo": {}},
                              {"repo": {"full_name": ""}},
                              {"repo": {"full_name": "   "}}):
                with self.subTest(branch=branch, reference=reference):
                    event = copy.deepcopy(self.event(editable=True))
                    event["pull_request"][branch] = reference
                    with self.assertRaisesRegex(SystemExit, "repository identities"):
                        await self.check_event(event)

    async def test_missing_fork_edit_permission_fails_closed(self):
        event = self.event(head="contributor/default")
        del event["pull_request"]["maintainer_can_modify"]
        with self.assertRaisesRegex(SystemExit, "not editable"):
            await self.check_event(event)


if __name__ == "__main__":
    unittest.main()
