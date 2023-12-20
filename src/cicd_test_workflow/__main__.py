"""Run `python -m cicd_test_workflow`.

Allow running CI/CD Test Repository, also by invoking
the python module:

`python -m cicd_test_workflow`

This is an alternative to directly invoking the cli that uses python as the
"entrypoint".
"""
from __future__ import absolute_import

from cicd_test_workflow.cli import main

if __name__ == "__main__":  # pragma: no cover
    main(  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
        prog_name="cicd-test"
    )
