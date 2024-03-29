import pprint
from pathlib import Path
import tempfile
import shutil
from updater import config_yaml
from check_version import cli
import pytest
from click.testing import CliRunner

from plumbum import local  # type: ignore

pp = pprint.PrettyPrinter(indent=4)
FIXTURE_DIR = Path(".").absolute() / "tests/test_files"


def config_from_copy_of_test_dir_broken() -> config_yaml.Config:
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(FIXTURE_DIR, test_dir)
    config = config_yaml.Config(test_dir / "components.yaml")
    config.git_commit = False
    config.read_from_yaml()
    # remove expected file
    shutil.rmtree(test_dir / "app")
    return config


def config_from_copy_of_test_dir() -> config_yaml.Config:
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(FIXTURE_DIR, test_dir)
    config = config_yaml.Config(test_dir / "components.yaml")
    config.git_commit = False
    config.read_from_yaml()
    return config


@pytest.mark.check_version
def test_check():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "check",
                "--type=pypi",
                "--component=Django",
                "--version_tag=2.0.0",
                "--ignore-default-file",
                "--verbose",
            ],
        )
        assert result.exit_code == 0
        assert "1 components to update" in result.output


@pytest.mark.check_version
def test_update_fail():
    config = config_from_copy_of_test_dir_broken()
    runner = CliRunner()

    with local.cwd(config.project_dir):
        with pytest.raises(AssertionError) as excinfo:
            runner.invoke(cli, ["--print", "update", "--verbose"])
            assert "No config file provided" in str(excinfo.value)


@pytest.mark.check_version
def test_update_verbose():
    config = config_from_copy_of_test_dir()
    runner = CliRunner()
    if config.config_file:
        with local.cwd(config.config_file.parent):
            result = runner.invoke(cli, ["update", "--verbose"])
            assert result.exit_code == 0
            assert "5 components updated, 7 files updated" in result.output


@pytest.mark.check_version
def test_update():
    config = config_from_copy_of_test_dir()
    runner = CliRunner()
    if config.config_file:
        with local.cwd(config.config_file.parent):
            result = runner.invoke(cli, ["--print", "update", "--verbose"])
            pp.pprint(result)
            assert result.exit_code == 0
            assert "next-version" in result.output


@pytest.mark.check_version
def test_import_req():
    config = config_from_copy_of_test_dir()
    req_file = (
        config.config_file.parent / "requirements.txt" if config.config_file else None
    )
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            f"--file={str(config.config_file)}",
            "--print",
            "import-req",
            "--source=pipfile",
            f"--requirements-file={str(req_file)}",
        ],
    )
    assert result.exit_code == 0
    pp.pprint(result.output)
    assert "xwrong" in result.output


@pytest.mark.check_version
@pytest.mark.slow
def test_check_clear_cache():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["check", "--clear-cache"])
        assert result.exit_code == 0
