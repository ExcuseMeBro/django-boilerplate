"""Check the local launcher without installing packages or starting services."""

import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.parametrize(
    ("fail_at", "expected_count", "returncode"),
    [("", 3, 0), ("sync", 1, 23), ("run --locked python manage.py migrate", 2, 23)],
)
def test_start_dev_uses_locked_uv_and_stops_on_failure(tmp_path, fail_at, expected_count, returncode):
    project = tmp_path / "project with spaces"
    project.mkdir()
    shutil.copyfile(Path(__file__).resolve().parents[1] / "start_dev.sh", project / "start_dev.sh")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "commands.log"
    uv = bin_dir / "uv"
    uv.write_text(
        '#!/bin/sh\n'
        'printf "%s|%s\\n" "$PWD" "$*" >> "$UV_TEST_LOG"\n'
        'case "$*" in\n'
        '  "$UV_TEST_FAIL_AT"*) [ -z "$UV_TEST_FAIL_AT" ] || exit 23 ;;\n'
        'esac\n'
    )
    uv.chmod(0o755)
    # No Python or pip on PATH: dependency setup must go through uv.
    dirname = bin_dir / "dirname"
    dirname.write_text('#!/bin/sh\nprintf "%s\\n" "${1%/*}"\n')
    dirname.chmod(0o755)

    result = subprocess.run(
        ["/bin/sh", str(project / "start_dev.sh")],
        cwd=tmp_path,
        env={
            **os.environ,
            "PATH": str(bin_dir),
            "UV_TEST_LOG": str(log),
            "UV_TEST_FAIL_AT": fail_at,
        },
        capture_output=True,
        text=True,
    )

    assert result.returncode == returncode, result.stderr
    expected = [
        "sync --locked",
        "run --locked python manage.py migrate",
        "run --locked python manage.py runserver 0.0.0.0:8000",
    ]
    assert log.read_text().splitlines() == [f"{project}|{command}" for command in expected[:expected_count]]
