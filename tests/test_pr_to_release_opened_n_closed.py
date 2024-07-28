import typing as t
import pytest

# Pull Request Model for searching PRs
# type alias of a key/value with keys 'owner', 'repo', 'pr_number'

class PRInfo(t.TypedDict):
    owner: str
    repo: str
    # PR: head --> base
    head_branch: str
    base_branch: str


@pytest.fixture
def get_pr_status():
    """Get PR status, using the Github API"""
    import requests

    def _get_pr_status(
        pr_info: PRInfo,
        github_token: str,
    ) -> requests.Response:


        # DEBUG Code

        response = requests.get(
        "https://api.github.com/repos/{owner}/{repo}/pulls?state=all&base={base_branch}".format(
            owner=pr_info["owner"],
            repo=pr_info["repo"],
            base_branch=pr_info["base_branch"],
        ),
        headers={
            "Authorization": f"Bearer {github_token}",
        },
    )
        # find PRs with given base branch
        response.raise_for_status()

        print(f"\n[DEBUG] PRs with base branch: {pr_info['base_branch']}")
        from pprint import pprint
        pprint(response.json())
        print()

        # PROD Code
        # Find PR head --> base, assuming head name is Unique!
        response = requests.get(
            "https://api.github.com/repos/{owner}/{repo}/pulls?state=all&head={head_branch}&base={base_branch}".format(
                owner=pr_info["owner"],
                repo=pr_info["repo"],
                head_branch=pr_info["head_branch"],
                base_branch=pr_info["base_branch"],
            ),
            headers={
                "Authorization": f"Bearer {github_token}",
            },
        )
        # find PRs with given base branch
        response.raise_for_status()

        data = response.json()
        return data

    return _get_pr_status


@pytest.fixture
def verify_pr_opened_n_closed(
    get_pr_status,
):
    def _verify_pr_opened_n_closed(head_branch: str, base_branch: str, github_token: str):
    # GIVEN a way to query for the PR status for the relevant github repository
        def pr_status():
            return [x['state'] for x in get_pr_status(
                pr_info={
                    "owner": "boromir674",
                    "repo": "gitops-automation",
                    "head_branch": head_branch,
                    "base_branch": base_branch,                    
                },
                github_token=github_token,
            )]
            # Can be one of: open, closed

        # we poll and try to encounter first 'open' and then 'closed' PR
        # we dim success if we only find a 'closed', assuming we were slow to start poll

        encountered_opened = False
        encountered_closed = False

        # use perf time measure lib
        import time
        start_time = time.time()
        time_limit = 60 # seconds

        stop_condition = encountered_closed or (start_time + time_limit < time.time())
        while not stop_condition:
            states = pr_status()
            assert len(states) <= 2, f"States: {states}"

            if 'open' in states:
                encountered_opened = True
            elif 'closed' in states:
                encountered_closed = True
            elif len(states) == 0:
                pass  # nothing found on remote github server
            else:
                raise ValueError(f"Unexpected PR states: {states}")

            stop_condition = encountered_closed or (start_time + time_limit < time.time())
            time.sleep(3.5)

        # THEN verify PR has opened and closed from User Br to 'release' br
        assert encountered_closed, f"Expecting to observe the PR status closed"
        assert encountered_opened and encountered_closed, "Expecting to observe the PR status both opened and closed"

    return _verify_pr_opened_n_closed

# Requires prior Git Ops event
@pytest.mark.gitops
def test_pr_to_release_opened_n_closed(verify_pr_opened_n_closed):
    import os
    verify_pr_opened_n_closed(
        head_branch=os.getenv("GO_HEAD_BRANCH"),
        base_branch='release',
        github_token=os.getenv("GITHUB_TOKEN"),
    )
