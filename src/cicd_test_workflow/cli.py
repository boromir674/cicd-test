"""Main `cicd_test_workflow` CLI."""

import os
import sys

import click

from cicd_test_workflow import __version__

this_file_location = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))


def version_msg():
    """cicd_test_workflow version, location and Python version.

    Get message about cicd_test_workflow version, location
    and Python version.
    """
    python_version = sys.version[:3]
    message = u"CI/CD Test Repository %(version)s from {} (Python {})"
    location = os.path.dirname(this_file_location)
    return message.format(location, python_version)


@click.command(context_settings=dict(help_option_names=[u'-h', u'--help']))
@click.version_option(__version__, u'-V', u'--version', message=version_msg())
@click.option('-v', '--verbose', is_flag=True, help='Print debug information', default=False)
def main(
    verbose,  # pylint: disable=unused-argument
):
    """TODO Write this content that gets renders when invoking with --help flag!

    Eg:
    Create a Project from the project template.

    Cookiecutter Python Package is Free/Libre Open Source Software. If you would
    like to get in touch, please see
    https://github.com/boromir674/cookiecutter-python-package.
    """
    try:
        pass
    except Exception as error:  # pylint: disable=broad-except
        click.echo(error)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()  # pylint: disable=no-value-for-parameter
