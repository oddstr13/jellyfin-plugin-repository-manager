import os

import pytest
from click.testing import CliRunner
from py._path.local import LocalPath
import jprm


TEST_DATA_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "data",
)


@pytest.mark.datafiles(
    os.path.join(TEST_DATA_DIR, "jprm.yaml"),
)
def test_package_plugin(cli_runner: CliRunner, tmpdir_factory, datafiles: LocalPath):
    bindir: LocalPath = tmpdir_factory.mktemp("bin")
    plugin: LocalPath = tmpdir_factory.mktemp("plugin")
    artifacts: LocalPath = tmpdir_factory.mktemp("artifacts")

    bindir.join("dummy.dll").write_text("", "utf-8")

    datafiles.join("jprm.yaml").copy(plugin)

    output_path = jprm.package_plugin(
        str(plugin), version="5.0", binary_path=str(bindir), output=str(artifacts)
    )

    assert os.path.exists(output_path)
    assert artifacts.join("plugin-a_5.0.0.0.zip").check(file=True)
    assert artifacts.join("plugin-a_5.0.0.0.zip.meta.json").check(file=True)
    assert artifacts.join("plugin-a_5.0.0.0.zip.md5sum").check(file=True)

    res = jprm.run_os_command(
        "md5sum -c plugin-a_5.0.0.0.zip.md5sum", cwd=str(artifacts)
    )
    assert res[2] == 0

    # res = jprm.run_os_command('unzip -t plugin-a_5.0.0.0.zip', cwd=str(artifacts))
    # assert res[2] == 0
