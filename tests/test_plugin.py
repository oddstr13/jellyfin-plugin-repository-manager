from pathlib import Path
import shutil
import sys

import pytest
from click.testing import CliRunner
import jprm

from .test_utils import TEST_DATA_DIR, json_load


@pytest.fixture
def package_plugin_paths(tmp_path_factory, datafiles: Path):
    bindir: Path = tmp_path_factory.mktemp("bin")
    plugin: Path = tmp_path_factory.mktemp("plugin")
    artifacts: Path = tmp_path_factory.mktemp("artifacts")

    (bindir / "dummy.dll").write_text("", "utf-8")

    shutil.copy(datafiles / "jprm.yaml", plugin)

    return bindir, plugin, artifacts


@pytest.mark.xfail(sys.platform.startswith("win"), reason="md5sum command unavailable on Windows")
@pytest.mark.datafiles(
    TEST_DATA_DIR / "jprm.yaml",
)
def test_package_plugin(package_plugin_paths):
    bindir, plugin, artifacts = package_plugin_paths

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


@pytest.mark.datafiles(
    TEST_DATA_DIR / "jprm.yaml",
)
def test_package_plugin_changelog_override(package_plugin_paths):
    bindir, plugin, artifacts = package_plugin_paths

    changelog = "Line one\nLine two"
    output_path = Path(
        jprm.package_plugin(
            str(plugin),
            version="5.0",
            changelog=changelog,
            binary_path=str(bindir),
            output=str(artifacts),
        )
    )

    meta = json_load(Path(str(output_path) + ".meta.json"))
    manifest = jprm.generate_plugin_manifest(str(output_path), meta=meta, md5="deadbeef")

    assert meta["changelog"] == changelog
    assert manifest["versions"][0]["changelog"] == changelog


@pytest.mark.datafiles(
    TEST_DATA_DIR / "jprm.yaml",
)
def test_package_plugin_empty_changelog_override_uses_config(package_plugin_paths):
    bindir, plugin, artifacts = package_plugin_paths

    output_path = Path(
        jprm.package_plugin(
            str(plugin),
            version="5.0",
            changelog="",
            binary_path=str(bindir),
            output=str(artifacts),
        )
    )

    meta = json_load(Path(str(output_path) + ".meta.json"))

    assert meta["changelog"] == "Initial Release\n"


def test_cli_plugin_build_changelog_option(cli_runner: CliRunner, tmp_path: Path, monkeypatch):
    build_cfg = {
        "name": "Plugin A",
        "guid": "f5ddc434-4b42-45d0-a049-8dda7f1ed30b",
        "description": "Test plugin A",
        "overview": "Test plugin A",
        "owner": "Oddstr13",
        "category": "Other",
        "version": "1.0.0.0",  # NOSONAR(S1313) not an ip address
        "changelog": "Initial Release\n",
        "targetAbi": "10.8.0.0",  # NOSONAR(S1313) not an ip address
        "artifacts": ["dummy.dll"],
    }
    captured = {}

    monkeypatch.setattr(jprm, "get_config", lambda path: build_cfg)
    monkeypatch.setattr(jprm, "build_plugin", lambda *args, **kwargs: None)

    def fake_package_plugin(*args, **kwargs):
        captured["changelog"] = kwargs.get("changelog")
        return "artifact.zip"

    monkeypatch.setattr(jprm, "package_plugin", fake_package_plugin)

    changelog = "Line one\nLine two"
    result = cli_runner.invoke(
        jprm.cli,
        ["plugin", "build", str(tmp_path), "--changelog", changelog],
    )

    assert result.exit_code == 0
    assert captured["changelog"] == changelog
    assert "artifact.zip" in result.stdout.splitlines(False)
