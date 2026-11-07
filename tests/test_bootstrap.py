"""Exercise the real CLI in disposable copies, never the working checkout."""
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tomllib

import pytest

ROOT = Path(__file__).resolve().parents[1]
FILES = ('pyproject.toml', 'uv.lock', '.env.example', 'docker-compose.yaml', 'manage.py', '.gitignore')


@pytest.fixture
def project(tmp_path):
    destination = tmp_path / 'project with spaces'
    destination.mkdir()
    for relative in FILES:
        shutil.copyfile(ROOT / relative, destination / relative)
    for directory in ('scripts', 'config', 'core', 'messaging', 'templates'):
        shutil.copytree(ROOT / directory, destination / directory, ignore=shutil.ignore_patterns('__pycache__'))
    return destination


def run(project, *args):
    return subprocess.run(
        [sys.executable, str(project / 'scripts/bootstrap.py'), *args],
        cwd=project.parent, capture_output=True, text=True, timeout=15,
    )


def snapshot(project):
    return {str(p.relative_to(project)): p.read_bytes() for p in project.rglob('*') if p.is_file()}


def test_dry_run_changes_nothing_and_does_not_print_secrets(project):
    (project / '.env').write_text('SECRET_KEY=private-marker\nDB_PASSWORD=private-password\n')
    before = snapshot(project)
    result = run(project, '--name', 'example-api', '--dry-run')
    assert result.returncode == 0, result.stderr
    assert 'Would update pyproject.toml' in result.stdout
    assert 'Preserve existing .env' in result.stdout
    assert 'private-marker' not in result.stdout + result.stderr
    assert 'private-password' not in result.stdout + result.stderr
    assert snapshot(project) == before


def test_valid_bootstrap_is_idempotent_preserves_credentials_and_passes_django_check(project):
    credentials = project / 'firebase-credentials.json'
    credentials.write_text('{"private_key": "synthetic-do-not-touch"}')
    existing = 'SECRET_KEY=synthetic-private-marker\nDB_PASSWORD=synthetic-password\nCUSTOM=keep\n'
    (project / '.env').write_text(existing)
    result = run(project, '--name', 'example-api')
    assert result.returncode == 0, result.stderr
    metadata = tomllib.loads((project / 'pyproject.toml').read_text())
    lock = tomllib.loads((project / 'uv.lock').read_text())
    assert metadata['project']['name'] == 'example-api'
    assert [p['name'] for p in lock['package'] if p['source'] == {'virtual': '.'}] == ['example-api']
    assert 'DB_NAME=example_api_db' in (project / '.env.example').read_text()
    assert 'DB_USER=example_api' in (project / '.env.example').read_text()
    assert 'MINIO_BUCKET_NAME=example-api' in (project / '.env.example').read_text()
    assert 'example_api_db' in (project / 'config/settings.py').read_text()
    assert 'example_api_db' in (project / 'docker-compose.yaml').read_text()
    assert (project / '.env').read_text() == existing
    assert credentials.read_text() == '{"private_key": "synthetic-do-not-touch"}'
    before = snapshot(project)
    assert run(project, '--name', 'example-api').returncode == 0
    assert snapshot(project) == before
    check = subprocess.run(
        [sys.executable, 'manage.py', 'check'], cwd=project, capture_output=True, text=True,
        env={**os.environ, 'DEBUG': 'True', 'USE_MINIO': 'False', 'CACHE_URL': '', 'REDIS_URL': ''}, timeout=30,
    )
    assert check.returncode == 0, check.stdout + check.stderr


def test_missing_env_created_private_with_blank_secrets(project):
    before = snapshot(project)
    assert run(project, '--name', 'new-api', '--dry-run').returncode == 0
    assert snapshot(project) == before and not (project / '.env').exists()
    result = run(project, '--name', 'new-api')
    assert result.returncode == 0, result.stderr
    env = project / '.env'
    assert env.read_bytes() == (project / '.env.example').read_bytes()
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    values = dict(line.split('=', 1) for line in env.read_text().splitlines() if '=' in line and not line.startswith('#'))
    for key in ('SECRET_KEY', 'DB_PASSWORD', 'MINIO_ROOT_USER', 'MINIO_ROOT_PASSWORD', 'FCM_SERVER_KEY'):
        assert values[key] == ''
    assert values['DB_NAME'] == 'new_api_db'


@pytest.mark.parametrize('name', ['', 'x', '../escape', '/tmp/escape', 'Bad-Name', 'a b', 'ab;id', 'abc\nDEF', 'a--b', 'a'*41, 'django'])
def test_invalid_names_fail_without_writes(project, name):
    before = snapshot(project)
    result = run(project, '--name', name)
    assert result.returncode == 2
    assert snapshot(project) == before


@pytest.mark.parametrize('name', ['django-boilerplate-api', 'unfold-boilerplate-api', 'unfold-user-api'])
def test_starter_prefix_names_are_idempotent(project, name):
    assert run(project, '--name', name).returncode == 0
    before = snapshot(project)
    assert run(project, '--name', name).returncode == 0
    assert snapshot(project) == before


def test_refuses_different_second_name_without_writes(project):
    assert run(project, '--name', 'first-api').returncode == 0
    before = snapshot(project)
    assert run(project, '--name', 'other-api').returncode == 2
    assert snapshot(project) == before


@pytest.mark.parametrize('relative', ['uv.lock', 'config/settings.py'])
def test_symlinked_sources_fail_preflight_without_writing(project, tmp_path, relative):
    target = tmp_path / 'external'
    target.write_bytes((project / relative).read_bytes())
    (project / relative).unlink()
    (project / relative).symlink_to(target)
    before = snapshot(project)
    assert run(project, '--name', 'example-api').returncode == 2
    assert snapshot(project) == before and not (project / '.env').exists()


def test_existing_dangling_env_symlink_is_preserved(project, tmp_path):
    target = tmp_path / 'never-create'
    (project / '.env').symlink_to(target)
    assert run(project, '--name', 'example-api').returncode == 0
    assert (project / '.env').is_symlink() and not target.exists()
