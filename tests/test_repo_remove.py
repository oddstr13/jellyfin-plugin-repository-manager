import os
import json

import pytest
from click.testing import CliRunner
from py._path.local import LocalPath
from testfixtures import compare
import jprm

from .test_repo import TEST_DATA_DIR


@pytest.mark.parametrize(
    "input,args,output,guid",
    [
        (
            "manifest_pluginAB.json",
            ["f5ddc434-4b42-45d0-a049-8dda7f1ed30b", "1"],
            "manifest_pluginAB2.json",
            "f5ddc434-4b42-45d0-a049-8dda7f1ed30b",
        ),
        (
            "manifest_pluginAB.json",
            ["f5ddc434-4b42-45d0-a049-8dda7f1ed30b", "1.0"],
            "manifest_pluginAB2.json",
            "f5ddc434-4b42-45d0-a049-8dda7f1ed30b",
        ),
        (
            "manifest_pluginAB.json",
            ["f5ddc434-4b42-45d0-a049-8dda7f1ed30b", "1.0.0.0"],
            "manifest_pluginAB2.json",
            "f5ddc434-4b42-45d0-a049-8dda7f1ed30b",
        ),
        (
            "manifest_pluginAB.json",
            ["plugin-a", "1.0.0.0"],
            "manifest_pluginAB2.json",
            "f5ddc434-4b42-45d0-a049-8dda7f1ed30b",
        ),
        (
            "manifest_pluginAB.json",
            ["Plugin A"],
            "manifest_pluginB.json",
            "f5ddc434-4b42-45d0-a049-8dda7f1ed30b",
        ),
        (
            "manifest_pluginAB.json",
            ["f5ddc434-4b42-45d0-a049-8dda7f1ed30b"],
            "manifest_pluginB.json",
            "f5ddc434-4b42-45d0-a049-8dda7f1ed30b",
        ),
    ],
)
@pytest.mark.datafiles(
    os.path.join(TEST_DATA_DIR, "manifest_pluginAB.json"),
    os.path.join(TEST_DATA_DIR, "manifest_pluginAB2.json"),
    os.path.join(TEST_DATA_DIR, "manifest_pluginB.json"),
)
def test_repo_remove(
    input,
    args,
    output,
    guid,
    cli_runner: CliRunner,
    datafiles: LocalPath,
):
    manifest_file: LocalPath = datafiles / "repo.json"
    (datafiles / input).copy(manifest_file)

    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "remove", str(manifest_file), *args]
    )
    assert result.exit_code == 0

    if len(args) == 1:
        assert f"removed {guid}" in result.stdout.splitlines(False)
    else:
        version = jprm.Version(args[1]).full()
        assert f"removed {guid} {version}" in result.stdout.splitlines(False)

    with open(datafiles / output) as expected_fh, open(manifest_file) as actual_fh:
        compare(
            expected=json.load(expected_fh),
            actual=json.load(actual_fh),
        )
