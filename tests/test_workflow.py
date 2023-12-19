def test_workflow_and_its_jobs_are_green(
    trigger_workflow,
    get_workflow_runs,
    get_workflow_run_status,
    yaml_workflow,
):
    import time
    import typing as t

    import requests

    owner = "boromir674"
    repo = "cicd-test"
    import os

    TOKEN_ENV_VAR: str = "CICD_TEST_GH_TOKEN"
    token = os.environ.get(TOKEN_ENV_VAR)

    workflow, expectations = yaml_workflow
    workflow_id: int = workflow['id']
    workflow_name: str = workflow['name']

    # Check how many times the workflow has ran

    workflow_runs_response = get_workflow_runs({'id': workflow_id}, token)
    assert (
        workflow_runs_response.status_code == 200
    ), f"Failed to get workflow runs for Workflow {workflow_id}"
    workflow_runs: t.Dict = workflow_runs_response.json()

    latest_run: int = max(workflow_runs["workflow_runs"], key=lambda x: x["run_number"])
    print(f"[DEBUG] Previous Workflow Run Number: {latest_run['run_number']}")

    #### TRIGGER WORKFLOW ####
    response = trigger_workflow({'id': workflow_id}, token)
    triggered: bool = response.status_code == 204
    assert triggered, (
        "Failed to trigger the workflow, as part of the Test Case.\n"
        f"Status code: {response.status_code}\n"
        f"Reponse: {response}\n"
        f"JSON: {response.json()}"
    )
    print(f"[pINFO] Triggered Workflow {workflow_id}")

    runner_triggered = False
    while not runner_triggered:
        workflow_runs_response = get_workflow_runs({'id': workflow_id}, token)
        assert (
            workflow_runs_response.status_code == 200
        ), f"Failed to get workflow runs for Workflow {workflow_id}"
        workflow_runs: t.Dict = workflow_runs_response.json()
        new_latest_run: int = max(
            workflow_runs["workflow_runs"], key=lambda x: x["run_number"]
        )
        runner_triggered = new_latest_run['run_number'] == latest_run['run_number'] + 1

    # THEN Workflow number of runs, increases by 1
    assert new_latest_run['run_number'] == latest_run['run_number'] + 1

    run_id = new_latest_run.get("id")
    assert run_id, f"Failed to find the workflow run id for {workflow_id}"

    # Wait for the workflow run to complete (adjust the sleep interval based on your workflow duration)
    NOT_FINISHED_STATES = {"queued", "in_progress"}
    workflow_run: t.Dict[str, t.Any]
    workflow_finished: bool = (
        workflow_run := get_workflow_run_status({'id': run_id}, token).json()
    )["status"] not in NOT_FINISHED_STATES
    while not workflow_finished:
        print("\n[DEBUG]: ----- Workflow Status: " + workflow_run["status"])
        time.sleep(5)  # Adjust the interval as needed
        workflow_finished = (
            workflow_run := get_workflow_run_status({'id': run_id}, token).json()
        )["status"] not in NOT_FINISHED_STATES

    # Assertions on overall workflow status
    runtime_status: str = workflow_run["status"]
    expected_status: str = 'completed'
    assert (
        runtime_status == expected_status
    ), f"Workflow '{workflow_name}' ID {workflow_id} and RUN ID {run_id} Completed with status: {runtime_status}. But We expected status {expected_status}."

    runtime_conclusion = workflow_run["conclusion"]
    expected_conclusion = expectations["conclusion"]
    assert (
        runtime_conclusion == expected_conclusion
    ), f"Workflow '{workflow_name}' ID {workflow_id} and RUN ID {run_id} Completed with conclusion: {runtime_conclusion}. But We expected conclusion {expected_conclusion}."

    jobs_info_response = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/actions" f"/runs/{run_id}/jobs",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    assert (
        jobs_info_response.status_code == 200
    ), f"Failed to get jobs info for {workflow_run['run_number']}. Reported run_number's: {[i['run_number'] for i in workflow_runs['workflow_runs']]}"

    jobs_info = jobs_info_response.json()

    # Assertions on individual job statuses
    for job in jobs_info["jobs"]:
        assert job["status"] == "completed"
        print(f"[DEBUG] Job {job['name']} Completed with conclusion: {job['conclusion']}")

        # At runtime all Caller Jobs get their names (as rendered on gh actions UI) appended with the Called workflow name
        # we remove that part, for "defensive-programming"
        job_key: str = job["name"].split(" / ")[0]

        expected_job_conclusion: str = expectations["jobs"][job_key]
        assert (
            job["conclusion"] == expected_job_conclusion
        ), f"Job {job['name']} Completed with conclusion: {job['conclusion']}. But We expected conclusion {expected_job_conclusion}."
