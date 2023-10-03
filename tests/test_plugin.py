from pathlib import Path
import shutil

import pytest
import jprm

from .test_utils import TEST_DATA_DIR


@pytest.mark.datafiles(
    TEST_DATA_DIR / "jprm.yaml",
)
def test_package_plugin(tmp_path_factory, datafiles: Path):
    bindir: Path = tmp_path_factory.mktemp("bin")
    plugin: Path = tmp_path_factory.mktemp("plugin")
    artifacts: Path = tmp_path_factory.mktemp("artifacts")

    (bindir / "dummy.dll").write_text("", "utf-8")

    shutil.copy(datafiles / "jprm.yaml", plugin)

    output_path = Path(
        jprm.package_plugin(
            str(plugin), version="5.0", binary_path=str(bindir), output=str(artifacts)
        )
    )

    assert output_path.exists()
    assert (artifacts / "plugin-a_5.0.0.0.zip").is_file()
    assert (artifacts / "plugin-a_5.0.0.0.zip.meta.json").is_file()
    assert (artifacts / "plugin-a_5.0.0.0.zip.md5sum").is_file()

    res = jprm.run_os_command(
        "md5sum -c plugin-a_5.0.0.0.zip.md5sum", cwd=str(artifacts)
    )
    assert res[2] == 0

    # res = jprm.run_os_command('unzip -t plugin-a_5.0.0.0.zip', cwd=str(artifacts))
    # assert res[2] == 0
