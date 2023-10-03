import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner
from testfixtures import compare
import jprm

from .test_utils import TEST_DATA_DIR, json_load


@pytest.mark.parametrize(
    "input_file,args,output_file,guid",
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
    TEST_DATA_DIR / "manifest_pluginAB.json",
    TEST_DATA_DIR / "manifest_pluginAB2.json",
    TEST_DATA_DIR / "manifest_pluginB.json",
)
def test_repo_remove(
    input_file,
    args,
    output_file,
    guid,
    cli_runner: CliRunner,
    datafiles: Path,
):
    manifest_file = datafiles / "repo.json"
    shutil.copyfile(datafiles / input_file, manifest_file)

    result = cli_runner.invoke(
        jprm.cli, ["--verbosity=debug", "repo", "remove", str(manifest_file), *args]
    )
    assert result.exit_code == 0

    if len(args) == 1:
        assert f"removed {guid}" in result.stdout.splitlines(False)
    else:
        version = jprm.Version(args[1]).full()
        assert f"removed {guid} {version}" in result.stdout.splitlines(False)

    compare(
        expected=json_load(datafiles / output_file),
        actual=json_load(manifest_file),
    )
