import importlib.util
import pathlib

import pytest


def load_api_module():
    test_dir = pathlib.Path(__file__).resolve().parent
    mod_path = test_dir.parent / "api.py"
    spec = importlib.util.spec_from_file_location("api_module", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_cli_requires_subcommand(capsys):
    api = load_api_module()

    with pytest.raises(SystemExit) as exc:
        api.main([])

    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "usage:" in captured.err.lower()


def test_cli_version_flag(capsys):
    api = load_api_module()

    with pytest.raises(SystemExit) as exc:
        api.main(["--version"])

    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "Octet-Économe" in captured.out
    assert "0.1" in captured.out


# Optional: small smoke test for main compatibility with a real command
# could be added here later if needed.
