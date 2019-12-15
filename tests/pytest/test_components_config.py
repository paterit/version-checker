from updater import components, git_check, plumbum_msg
from pathlib import Path
from rex import rex
import tempfile
import shutil
import pytest
import os
from plumbum import local


FIXTURE_DIR = Path(".").absolute() / "tests/test_files"

comp = {
    "logspout": {
        "component_type": "docker-image",
        "repo_name": "gliderlabs",
        "component_name": "logspout",
        "current_version_tag": "v3.1",
    },
    "glances": {
        "component_type": "docker-image",
        "repo_name": "nicolargo",
        "component_name": "glances",
        "current_version_tag": "v2.11.1",
    },
    "Django": {
        "component_type": "pypi",
        "component_name": "Django",
        "current_version_tag": "2.1.2",
    },
    "requests": {
        "component_type": "pypi",
        "component_name": "requests",
        "current_version_tag": "2.20.0",
    },
    "wily": {
        "component_type": "pypi",
        "component_name": "wily",
        "current_version_tag": "100.0.0",
    },
}


def config_from_copy_of_test_dir():
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(FIXTURE_DIR, test_dir)
    config = components.Config(test_dir / "components.yaml")
    config.git_commit = False
    config.read_from_yaml()
    return config


def config_from_copy_of_test_dir_with_dir_param():
    test_dir = Path(tempfile.TemporaryDirectory().name)
    shutil.copytree(FIXTURE_DIR, test_dir)
    os.makedirs(test_dir / "conf")
    shutil.move(test_dir / "components.yaml", test_dir / "conf/components_new.yaml")
    config = components.Config(test_dir / "conf/components_new.yaml")
    config.project_dir = test_dir
    config.git_commit = False
    config.read_from_yaml()
    return config


def test_get_status_all_to_update():
    config = config_from_copy_of_test_dir()
    components_to_check = config.check()
    config.update_files()
    status = config.get_status()
    for comp in components_to_check:
        assert "UPDATE_STARTED for " + comp[0] in status
        assert "UPDATE_DONE for " + comp[0] in status


def test_get_status_skip_update():
    config = components.Config(components_yaml_file=None)
    config.add(components.factory.get(**comp["wily"]))
    config.check()
    config.update_files()
    status = config.get_status()
    assert "UPDATE_SKIPPED for wily" in status


def test_load_config_without_yaml_file():
    config = components.Config(components_yaml_file=None)
    config.add(components.factory.get(**comp["Django"]))
    assert config.count_components_to_update() == 1


def test_save_next_version_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.add(components.factory.get(**comp["Django"]))
    to_update = config.count_components_to_update()
    assert to_update == 2
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert file_content.count("next-version:") == 2


def test_save_prefix_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].prefix = "version_prefix"
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "version_prefix" in file_content


def test_save_version_pattern_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].version_pattern = "{version}:{version}"
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "{version}:{version}" in file_content
    config.components[0].version_pattern = config.components[0].DEFAULT_VERSION_PATTERN
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "version-pattern" not in file_content


def test_exlude_versions_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].exclude_versions = ["v3.2.6"]
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "exclude-versions:" in file_content
    assert "v3.2.6" in file_content


def test_save_files_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].files = ["file1", "file2"]
    config.save_to_yaml()
    file_content = config_file.read_text()
    assert "file1" in file_content
    assert "file2" in file_content


def test_use_filter_for_component_to_yaml(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["logspout"]))
    config.components[0].prefix = "v"
    config.components[0].filter = "/^v\d+\.\d+\.\d+$/"
    config.components[0].check()
    assert config.components[0].next_version_tag == rex(config.components[0].filter)


def test_components_list_write_read_yaml_file(tmp_path):
    config_file = tmp_path / "components.yaml"
    config = components.Config(components_yaml_file=config_file)
    config.add(components.factory.get(**comp["glances"]))
    config.add(components.factory.get(**comp["logspout"]))
    dict1 = config.components_to_dict()
    config.save_to_yaml()
    config.read_from_yaml()
    dict2 = config.components_to_dict()
    assert dict1 == dict2


def test_components_to_dict(tmp_path):
    config = components.Config(tmp_path / "components.yaml")
    config.add(components.factory.get(**comp["glances"]))
    config.add(components.factory.get(**comp["logspout"]))
    config.add(components.factory.get(**comp["Django"]))
    result = {
        "glances": {
            "component-type": "docker-image",
            "current-version": "v2.11.1",
            "docker-repo": "nicolargo",
            "next-version": "v2.11.1",
        },
        "logspout": {
            "component-type": "docker-image",
            "current-version": "v3.1",
            "docker-repo": "gliderlabs",
            "next-version": "v3.1",
        },
        "Django": {
            "component-type": "pypi",
            "current-version": "2.1.2",
            "next-version": "2.1.2",
        },
    }
    assert result == config.components_to_dict()


def test_update_components_files():
    config = config_from_copy_of_test_dir()
    assert config.check() == [
        ("glances", True),
        ("logspout", True),
        ("Django", True),
        ("requests", True),
        ("python", True),
    ]
    assert config.update_files() == 6


def test_save_config_dry_run():
    config = config_from_copy_of_test_dir()
    content1 = config.config_file.read_text()
    config.save_config(destination_file=None, dry_run=True, print_yaml=False)
    content2 = config.config_file.read_text()
    assert content1 == content2


def test_save_config_in_different_location(tmp_path):
    config_file = tmp_path / "components2.yaml"
    config = config_from_copy_of_test_dir()
    config.save_config(destination_file=None, dry_run=False, print_yaml=False)
    config.save_config(destination_file=config_file, dry_run=False, print_yaml=False)
    content1 = config.config_file.read_text()
    content2 = config_file.read_text()
    assert content1 == content2


def test_save_config_print_yaml(capfd):
    config = config_from_copy_of_test_dir()
    config.save_config(destination_file=None, dry_run=True, print_yaml=True)
    captured = capfd.readouterr()
    assert "nicolargo" in captured.out, captured.out


def test_dry_run_update_file():
    config = config_from_copy_of_test_dir()
    config.check()
    c0, c1 = config.components[0], config.components[1]

    assert c0.current_version != c0.next_version
    assert c1.current_version != c1.next_version
    content1 = config.config_file.parent.joinpath(c0.files[0]).read_text()
    config.update_files(dry_run=True)
    content2 = config.config_file.parent.joinpath(c0.files[0]).read_text()
    assert content1 == content2
    config.update_files(dry_run=False)
    content2 = config.config_file.parent.joinpath(c0.files[0]).read_text()
    assert content1 != content2


def test_exclude_versions_param():
    config = config_from_copy_of_test_dir()
    config.check()
    config.save_config()
    assert "next-version: v3.2.6" not in config.config_file.read_text()


def test_update_components_files_with_testing_positive(capfd):
    config = config_from_copy_of_test_dir()
    config.test_command = ["make", "test"]
    assert config.check() == [
        ("glances", True),
        ("logspout", True),
        ("Django", True),
        ("requests", True),
        ("python", True),
    ]
    assert config.update_files() == 6
    captured = capfd.readouterr()
    assert captured.out.count("Test OK") == 5, captured.out


def test_update_components_files_with_project_dir_param(capfd):
    config = config_from_copy_of_test_dir_with_dir_param()
    config.test_command = ["make", "test"]
    assert config.check() == [
        ("glances", True),
        ("logspout", True),
        ("Django", True),
        ("requests", True),
        ("python", True),
    ]
    assert config.update_files() == 6
    captured = capfd.readouterr()
    assert captured.out.count("Test OK") == 5, captured.out


def test_update_components_files_with_testing_negative(capfd):
    config = config_from_copy_of_test_dir()
    config.test_command = ["make", "test-fail"]
    assert config.check() == [
        ("glances", True),
        ("logspout", True),
        ("Django", True),
        ("requests", True),
        ("python", True),
    ]
    with pytest.raises(AssertionError) as excinfo:
        config.update_files()
    assert "Error" in str(excinfo.value)
    captured = capfd.readouterr()
    assert "Test KO" in captured.out, captured.out


def test_commit_changes():
    config = config_from_copy_of_test_dir()
    config.git_commit = True
    git = local["git"]
    with local.cwd(config.config_file.parent):
        ret = git_check(git["init"].run(retcode=None))
        ret = git_check(
            git["config", "--local", "user.name", "'Wojtek Tester'"].run(retcode=None)
        )
        ret = git_check(
            git["config", "--local", "user.email", "'wojtek.tester@gmail.com'"].run(
                retcode=None
            )
        )
        ret = git_check(git["add", "."].run(retcode=None))
        ret = git_check(git["commit", "-m", "'Initial commit'"].run(retcode=None))
        config.check()
        config.update_files()
        ret = git_check(git["rev-list", "HEAD", "--count"].run(retcode=None))
        assert "6\n" in plumbum_msg(ret)


def test_get_versions_info():
    config = config_from_copy_of_test_dir()
    config.check()
    info = config.get_versions_info()
    assert "Django - current: 2.2.8 next:" in info[0]
    assert "glances - current: v2.11.0 next:" in info[1]
    assert "logspout - current: v3.1 next:" in info[2]
    assert "python - current: 3.6.6-alpine3.8 next:" in info[3]
    assert "requests - current: 2.20.0 next:" in info[4]
