import os
from pathlib import Path

import pytest
from click.testing import CliRunner
import jprm

from .test_utils import TEST_DATA_DIR, json_load


def test_init_repo_path(cli_runner: CliRunner, tmp_path: Path):
    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "init", str(tmp_path)]
    )

    manifest = tmp_path / "manifest.json"

    assert result.exit_code == 0
    assert os.path.exists(manifest)

    data = json_load(manifest)

    assert data == []


def test_init_repo_file(cli_runner: CliRunner, tmp_path: Path):
    manifest = tmp_path / "foo.json"

    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "init", str(manifest)]
    )

    assert result.exit_code == 0
    assert os.path.exists(manifest)

    data = json_load(manifest)

    assert data == []


def test_double_init_repo_path(cli_runner: CliRunner, tmp_path: Path):
    # Initializing an existing repo is not allowed
    cli_runner.invoke(jprm.cli, ["--verbosity=debug", "repo", "init", str(tmp_path)])
    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "init", str(tmp_path)]
    )

    assert result.exit_code == 2


@pytest.mark.datafiles(
    TEST_DATA_DIR / "pluginA_1.0.0.zip",
    TEST_DATA_DIR / "pluginA_1.1.0.zip",
    TEST_DATA_DIR / "pluginB_1.0.0.zip",
    TEST_DATA_DIR / "manifest_pluginA.json",
    TEST_DATA_DIR / "manifest_pluginA2.json",
    TEST_DATA_DIR / "manifest_pluginAB.json",
)
def test_repo_add(cli_runner: CliRunner, tmp_path: Path, datafiles: Path):
    manifest_file = tmp_path / "repo.json"
    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "init", str(manifest_file)]
    )
    assert result.exit_code == 0

    manifest_a = json_load(datafiles / "manifest_pluginA.json")
    manifest_a2 = json_load(datafiles / "manifest_pluginA2.json")
    manifest_ab = json_load(datafiles / "manifest_pluginAB.json")

    cli_runner.invoke(
        jprm.cli,
        [
            "--verbosity=debug",
            "repo",
            "add",
            str(manifest_file),
            str(datafiles / "pluginA_1.0.0.zip"),
        ],
    )
    manifest = json_load(manifest_file)
    assert manifest == manifest_a
    assert (tmp_path / "plugin-a" / "plugin-a_1.0.0.0.zip").exists()

    cli_runner.invoke(
        jprm.cli,
        [
            "--verbosity=debug",
            "repo",
            "add",
            str(manifest_file),
            str(datafiles / "pluginA_1.1.0.zip"),
        ],
    )
    manifest = json_load(manifest_file)
    assert manifest == manifest_a2
    assert (tmp_path / "plugin-a" / "plugin-a_1.1.0.0.zip").exists()

    cli_runner.invoke(
        jprm.cli,
        [
            "--verbosity=debug",
            "repo",
            "add",
            str(manifest_file),
            str(datafiles / "pluginB_1.0.0.zip"),
        ],
    )
    manifest = json_load(manifest_file)
    assert manifest == manifest_ab
    assert (tmp_path / "plugin-b" / "plugin-b_1.0.0.0.zip").exists()
    assert (tmp_path / "plugin-b" / "image.png").exists()
