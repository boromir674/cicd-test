"""Run `python -m cicd_test`.

Allow running CI/CD Test Repository, also by invoking
the python module:

`python -m cicd_test`

This is an alternative to directly invoking the cli that uses python as the
"entrypoint".
"""
from __future__ import absolute_import

from cicd_test.cli import main

if __name__ == "__main__":  # pragma: no cover
    main(prog_name="cicd-test")  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
