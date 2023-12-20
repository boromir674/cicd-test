import typing as t
from pathlib import Path

import pytest

TEST_DIR: Path = Path(__file__).parent


## Workflow Data from GITHUB API ##
WORKFLOWS_DIR: Path = TEST_DIR.parent / ".github" / "workflows"
# yaml or yml files from .github/workflows
YAML_FILES: t.List[str] = sorted(
    [x.name for x in WORKFLOWS_DIR.iterdir() if x.is_file() and x.suffix in {'.yml', '.yaml'}]
)

DOCKER_TEST_WORKFLOWS = [x for x in YAML_FILES if 'docker_pol' in x]
PYPI_TEST_WORKFLOWS = [x for x in YAML_FILES if 'pypi' in x]
STATIC_CODE_ANALYSIS_WORKFLOWS = [x for x in YAML_FILES if 'static_code' in x]
VISUALIZE_PYTHON_IMPORTS_WORKFLOWS = [x for x in YAML_FILES if 'code_viz' in x]

@pytest.fixture(
    params=DOCKER_TEST_WORKFLOWS + PYPI_TEST_WORKFLOWS + \
        STATIC_CODE_ANALYSIS_WORKFLOWS + VISUALIZE_PYTHON_IMPORTS_WORKFLOWS
)
def yaml_workflow(request, github_workflow):
    import yaml

    workflow_file_name: str = request.param
    name_2_github_workflow: t.Dict[str, t.Any] = github_workflow
    yaml_workflow = yaml.safe_load((WORKFLOWS_DIR / workflow_file_name).read_bytes())
    yaml_workflow_name: str = yaml_workflow['name']

    jobs = {
        v.get('name', k): 'failure' if 'fail' in k else 'skipped' if 'skip' in k else 'success'
        for k, v in yaml_workflow['jobs'].items()
    }

    if 'docker' in workflow_file_name:
        if 'pol0' in workflow_file_name:
            jobs = dict(
                jobs,
                **{
                    v.get('name', k): 'skipped'  # Hard NO Docker
                    for k, v in yaml_workflow['jobs'].items()
                    if k.startswith('call_docker_job_after_ci')
                },
            )
            assert (
                len(jobs) == 8 if 'green' in workflow_file_name else 4
            ), f"Failed to find all jobs in {workflow_file_name}"
        elif 'pol1' in workflow_file_name:
            jobs = dict(
                jobs,
                **{
                    v.get('name', k): 'success'  # FORCE YES Docker
                    for k, v in yaml_workflow['jobs'].items()
                    if k.startswith('call_docker_job_after_ci')
                },
            )
            assert (
                len(jobs) == 7 if 'green' in workflow_file_name else 4
            ), f"Failed to find all jobs in {workflow_file_name}"
        elif 'pol2' in workflow_file_name:  # CI/CD
            if 'green' in workflow_file_name:
                jobs = dict(
                    jobs,
                    **{
                        # expected docker job conclusions, for policy 2 (aka CI/CD)
                        yaml_workflow['jobs']['call_docker_job_after_ci_skip'].get(
                            'name', 'call_docker_job_after_ci_skip'
                        ): 'skipped',  # skip docker if ci tests skipped
                        yaml_workflow['jobs']['call_docker_job_after_pass_ci'].get(
                            'name', 'call_docker_job_after_pass_ci'
                        ): 'success',  # run docker if ci tests passed
                    },
                )
                assert len(jobs) == 7, f"Failed to find all jobs in {workflow_file_name}"
            else:
                jobs = dict(
                    jobs,
                    **{
                        # expected docker job conclusions, for policy 2 (aka CI/CD)
                        yaml_workflow['jobs']['call_docker_job_after_ci_fail'].get(
                            'name', 'call_docker_job_after_ci_fail'
                        ): 'skipped',  # skip docker if ci tests failed
                    },
                )
                assert (
                    len(jobs) == 4
                ), f"Failed to find all jobs in {workflow_file_name}. Jobs: {jobs}"
        elif 'pol3' in workflow_file_name:  # CI/CDelivery
            if 'green' in workflow_file_name:
                jobs = dict(
                    jobs,
                    **{
                        # expected docker job conclusions, for policy 3 (aka CI/CDelivery)
                        yaml_workflow['jobs']['call_docker_job_after_ci_skip'].get(
                            'name', 'call_docker_job_after_ci_skip'
                        ): 'success',  # run docker if ci tests skipped
                        yaml_workflow['jobs']['call_docker_job_after_pass_ci'].get(
                            'name', 'call_docker_job_after_pass_ci'
                        ): 'success',  # run docker if ci tests passed
                    },
                )
                assert len(jobs) == 7, f"Failed to find all jobs in {workflow_file_name}"
            else:
                jobs = dict(
                    jobs,
                    **{
                        # expected docker job conclusions, for policy 2 (aka CI/CD)
                        yaml_workflow['jobs']['call_docker_job_after_ci_fail'].get(
                            'name', 'call_docker_job_after_ci_fail'
                        ): 'skipped',  # skip docker if ci tests failed
                    },
                )
                assert (
                    len(jobs) == 4
                ), f"Failed to find all jobs in {workflow_file_name}. Jobs: {jobs}"

    if 'pypi' in workflow_file_name:
        if 'red' in workflow_file_name:
            jobs = dict(
                jobs,
                **{
                    v.get('name', k): 'failure'
                    for k, v in yaml_workflow['jobs'].items()
                    if k.startswith('call_pypi')
                },
            )
        else:
            jobs = dict(
                jobs,
                **{
                    v.get('name', k): 'success'
                    for k, v in yaml_workflow['jobs'].items()
                    if k.startswith('call_pypi')
                },
            )
        assert len(jobs) == 3, f"Failed to find all jobs in {workflow_file_name}. Jobs: {jobs}"

    yield name_2_github_workflow[yaml_workflow_name], {
        'conclusion': 'success' if 'red' not in workflow_file_name else 'failure',
        'status': 'completed',
        'jobs': jobs,
    }


## HELPER indepodent/pure FUNCTIONS, wrapping http requests##


@pytest.fixture
def github_workflow():
    import json
    import subprocess

    # gh api -X GET "/repos/${my_owner}/${my_repo}/actions/workflows" | jq '.workflows[] | .name,.id'
    res = subprocess.run(
        ["gh", "api", "-X", "GET", "/repos/boromir674/cicd-test/actions/workflows"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0, f"Failed to get workflows: {res.stderr}"

    data: t.Dict = json.loads(res.stdout)

    iiter = iter(
        [
            {
                'name': workflow['name'],
                'id': workflow['id'],
            }
            for workflow in data['workflows']
        ]
    )
    name_2_github_workflow: t.Dict[str, t.Any] = {x['name']: x for x in iiter}
    return name_2_github_workflow


@pytest.fixture
def trigger_workflow():
    """Triggers Github Action Workflow, on 'main' branch, using the Github API"""
    import requests

    def _trigger_workflow(
        workflow_resource: t.Dict[str, t.Union[str, int]], github_token: str
    ) -> requests.Response:
        response = requests.post(
            "https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches".format(
                owner=workflow_resource.get('owner', 'boromir674'),
                repo=workflow_resource.get('repo', 'cicd-test'),
                workflow_id=workflow_resource['id'],
            ),
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {github_token}",
            },
            # PAYLOAD
            json={"ref": "main"},  # branch/ref to trigger the workflow on
        )
        # response.raise_for_status()
        return response

    return _trigger_workflow


@pytest.fixture
def get_workflow_runs():
    """Get Workflow Runs, using the Github API"""
    import requests

    def _get_workflow_runs(
        workflow_resource: t.Dict[str, t.Union[str, int]], github_token: str
    ) -> requests.Response:
        response = requests.get(
            "https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs".format(
                owner=workflow_resource.get('owner', 'boromir674'),
                repo=workflow_resource.get('repo', 'cicd-test'),
                workflow_id=workflow_resource['id'],
            ),
            headers={
                "Authorization": f"Bearer {github_token}",
            },
        )
        response.raise_for_status()
        return response

    return _get_workflow_runs


@pytest.fixture
def get_workflow_run_status():
    import requests

    def _get_workflow_run_status(
        workflow_run_resource: t.Dict[str, t.Union[str, int]], github_token: str
    ):
        response = requests.get(
            "https://api.github.com/repos/{owner}/{repo}/actions/runs/{run_id}".format(
                owner=workflow_run_resource.get('owner', 'boromir674'),
                repo=workflow_run_resource.get('repo', 'cicd-test'),
                run_id=workflow_run_resource['id'],
            ),
            headers={
                "Authorization": f"Bearer {github_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        response.raise_for_status()
        return response

    return _get_workflow_run_status
