"""Tests for flatten_validate hook."""

import json
from unittest import mock

import pytest

from pre_commit_hooks.flatten_validate import main


@pytest.fixture()
def scadm_json(tmp_path, monkeypatch):
    """Create a temporary scadm.json and chdir to it."""
    monkeypatch.chdir(tmp_path)
    config = {
        "flatten": [
            {"src": "models/core/parts", "dest": "models/core/flattened"},
            {"src": "models/foot/parts", "dest": "models/foot/flattened"},
        ]
    }
    (tmp_path / "scadm.json").write_text(json.dumps(config))
    return tmp_path


def _mock_run(returncode=0, stdout="", stderr=""):
    """Create a mock subprocess result."""
    result = mock.MagicMock()
    result.returncode = returncode
    result.stdout = stdout
    result.stderr = stderr
    return result


@pytest.mark.usefixtures("scadm_json")
class TestFlattenValidate:
    """Tests for the flatten-validate hook."""

    @mock.patch("pre_commit_hooks.flatten_validate.subprocess.run")
    def test_all_clean(self, mock_run):
        """Hook passes when all flattened files are committed."""
        mock_run.side_effect = [
            _mock_run(0),  # scadm flatten --all
            _mock_run(0, stdout=""),  # git diff
            _mock_run(0, stdout=""),  # git ls-files
        ]
        with mock.patch("sys.argv", ["flatten-validate"]):
            assert main() == 0

    @mock.patch("pre_commit_hooks.flatten_validate.subprocess.run")
    def test_modified_files(self, mock_run):
        """Hook fails when flattened files have unstaged changes."""
        mock_run.side_effect = [
            _mock_run(0),  # scadm flatten --all
            _mock_run(0, stdout="models/core/flattened/foo.scad"),  # git diff
            _mock_run(0, stdout=""),  # git ls-files
        ]
        with mock.patch("sys.argv", ["flatten-validate"]):
            assert main() == 1

    @mock.patch("pre_commit_hooks.flatten_validate.subprocess.run")
    def test_untracked_files(self, mock_run):
        """Hook fails when there are untracked flattened files."""
        mock_run.side_effect = [
            _mock_run(0),  # scadm flatten --all
            _mock_run(0, stdout=""),  # git diff
            _mock_run(0, stdout="models/foot/flattened/bar.scad"),  # git ls-files
        ]
        with mock.patch("sys.argv", ["flatten-validate"]):
            assert main() == 1

    @mock.patch("pre_commit_hooks.flatten_validate.subprocess.run")
    def test_scadm_failure(self, mock_run):
        """Hook fails when scadm flatten returns non-zero."""
        mock_run.return_value = _mock_run(1)
        with mock.patch("sys.argv", ["flatten-validate"]):
            assert main() == 1

    @mock.patch("pre_commit_hooks.flatten_validate.subprocess.run")
    def test_missing_scadm_json(self, mock_run, tmp_path, monkeypatch):
        """Hook warns and runs scadm when scadm.json is missing."""
        monkeypatch.chdir(tmp_path)
        mock_run.return_value = _mock_run(0)
        with mock.patch("sys.argv", ["flatten-validate"]):
            assert main() == 0

    @mock.patch("pre_commit_hooks.flatten_validate.subprocess.run")
    def test_flatten_dir_override(self, mock_run, tmp_path, monkeypatch):
        """--flatten-dir overrides scadm.json discovery."""
        monkeypatch.chdir(tmp_path)
        mock_run.side_effect = [
            _mock_run(0),  # scadm flatten --all
            _mock_run(0, stdout=""),  # git diff
            _mock_run(0, stdout=""),  # git ls-files
        ]
        with mock.patch("sys.argv", ["flatten-validate", "--flatten-dir", "custom/out"]):
            assert main() == 0
        # Verify git commands used our custom dir
        diff_call = mock_run.call_args_list[1]
        assert "custom/out" in diff_call[0][0]

    @mock.patch("pre_commit_hooks.flatten_validate.subprocess.run")
    def test_git_diff_failure(self, mock_run):
        """Hook exits when git diff fails."""
        mock_run.side_effect = [
            _mock_run(0),  # scadm flatten --all
            _mock_run(128, stderr="fatal: not a git repository"),  # git diff
        ]
        with mock.patch("sys.argv", ["flatten-validate"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @mock.patch("pre_commit_hooks.flatten_validate.subprocess.run")
    def test_git_ls_files_failure(self, mock_run):
        """Hook exits when git ls-files fails."""
        mock_run.side_effect = [
            _mock_run(0),  # scadm flatten --all
            _mock_run(0, stdout=""),  # git diff
            _mock_run(128, stderr="fatal: not a git repository"),  # git ls-files
        ]
        with mock.patch("sys.argv", ["flatten-validate"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
