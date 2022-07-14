import os
import json

import pytest
from click.testing import CliRunner
from py._path.local import LocalPath
import jprm


TEST_DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "data",
)


def test_init_repo_path(cli_runner: CliRunner, tmpdir: LocalPath):
    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "init", str(tmpdir)]
    )

    manifest = tmpdir / "manifest.json"

    assert result.exit_code == 0
    assert os.path.exists(manifest)

    with open(manifest) as fh:
        data = json.load(fh)

    assert data == []


def test_init_repo_file(cli_runner: CliRunner, tmpdir: LocalPath):
    manifest = tmpdir / "foo.json"

    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "init", str(manifest)]
    )

    assert result.exit_code == 0
    assert os.path.exists(manifest)

    with open(manifest) as fh:
        data = json.load(fh)

    assert data == []


def test_double_init_repo_path(cli_runner: CliRunner, tmpdir: LocalPath):
    # Initializing an existing repo is not allowed
    cli_runner.invoke(jprm.cli, ["--verbosity=debug", "repo", "init", str(tmpdir)])
    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "init", str(tmpdir)]
    )

    assert result.exit_code == 2


@pytest.mark.datafiles(
    os.path.join(TEST_DATA_DIR, "pluginA_1.0.0.zip"),
    os.path.join(TEST_DATA_DIR, "pluginA_1.1.0.zip"),
    os.path.join(TEST_DATA_DIR, "pluginB_1.0.0.zip"),
    os.path.join(TEST_DATA_DIR, "manifest_pluginA.json"),
    os.path.join(TEST_DATA_DIR, "manifest_pluginA2.json"),
    os.path.join(TEST_DATA_DIR, "manifest_pluginAB.json"),
)
def test_repo_add(cli_runner: CliRunner, tmpdir: LocalPath, datafiles: LocalPath):
    manifest_file = tmpdir / "repo.json"
    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "init", str(manifest_file)]
    )
    assert result.exit_code == 0

    manifest_a = json.load(datafiles / "manifest_pluginA.json")
    manifest_a2 = json.load(datafiles / "manifest_pluginA2.json")
    manifest_ab = json.load(datafiles / "manifest_pluginAB.json")

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
    manifest = json.load(manifest_file)
    assert manifest == manifest_a
    assert (tmpdir / "plugin-a" / "plugin-a_1.0.0.0.zip").exists()

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
    manifest = json.load(manifest_file)
    assert manifest == manifest_a2
    assert (tmpdir / "plugin-a" / "plugin-a_1.1.0.0.zip").exists()

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
    manifest = json.load(manifest_file)
    assert manifest == manifest_ab
    assert (tmpdir / "plugin-b" / "plugin-b_1.0.0.0.zip").exists()
    assert (tmpdir / "plugin-b" / "image.png").exists()
