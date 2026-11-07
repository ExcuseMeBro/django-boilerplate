#!/usr/bin/env python3
"""Configure a fresh checkout using only Python's standard library (3.9+).

No subprocesses, dependency installs, network calls or secret generation. Paths
are anchored to this script, not the working directory. Existing .env is opaque.
"""
import argparse
import os
from pathlib import Path
import re
import stat
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('pyproject.toml', 'uv.lock', 'config/settings.py', 'docker-compose.yaml', '.env.example')


def project_name(value):
    if not 3 <= len(value) <= 40 or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', value):
        raise argparse.ArgumentTypeError('name must be 3–40 lowercase ASCII letters/digits, separated by single hyphens')
    return value


def read_regular(relative):
    path = ROOT / relative
    for component in (path, *path.parents):
        if component == ROOT:
            break
        if component.is_symlink():
            raise ValueError(f'refusing symlink: {relative}')
    if not path.is_file():
        raise ValueError(f'expected regular file: {relative}')
    if path.stat().st_size > 2_000_000:
        raise ValueError(f'file too large: {relative}')
    return path.read_text(encoding='utf-8')


def atomic_write(path, content):
    mode = stat.S_IMODE(path.stat().st_mode)
    fd, temporary = tempfile.mkstemp(prefix='.bootstrap-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as output:
            output.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def configure(name, dry_run):
    # Preflight all sources before writing anything. Never recursively rename or
    # touch migrations, credentials, .git, media or user-created files.
    originals = {relative: read_regular(relative) for relative in FILES}
    match = re.search(r'(?m)^name = "([^"]+)"$', originals['pyproject.toml'])
    if not match or match[1] not in ('django-boilerplate', name):
        raise ValueError('checkout already has a different project name; use a fresh template')
    if originals['uv.lock'].count(f'name = "{match[1]}"\n') != 1:
        raise ValueError('expected exactly one project entry in uv.lock')
    package_names = set(re.findall(r'(?m)^name = "([^"]+)"$', originals['uv.lock']))
    if name != match[1] and name in package_names:
        raise ValueError('project name conflicts with a locked dependency')
    database_name = name.replace('-', '_')
    replacements = {
        'django-boilerplate': name,
        'unfold_boilerplate_db': database_name + '_db',
        'unfold_user': database_name,
        'unfold-boilerplate': name,
    }
    planned = {}
    for relative, original in originals.items():
        content = original
        for old, new in replacements.items():
            # Match whole identifiers, not a prefix of an already-configured
            # name such as django-boilerplate-api (reruns must remain no-ops).
            boundary = r'(?:(?<![a-zA-Z0-9_-])|(?<=:-))'  # also Compose ${KEY:-default}
            content = re.sub(boundary + re.escape(old) + r'(?![a-zA-Z0-9_-])', new, content)
        planned[relative] = content
    for relative, content in planned.items():
        if content != originals[relative]:
            print(f'{"Would update" if dry_run else "Update"} {relative}')
            if not dry_run:
                atomic_write(ROOT / relative, content)
    # lexists also sees dangling symlinks: preserve them, never follow them.
    env = ROOT / '.env'
    if os.path.lexists(env):
        print('Preserve existing .env (not read or modified)')
    else:
        print(f'{"Would create" if dry_run else "Create"} .env from .env.example; fill secrets manually')
        if not dry_run:
            # Exclusive creation prevents an existing file/symlink being overwritten.
            try:
                fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                print('Preserve .env created concurrently')
            else:
                with os.fdopen(fd, 'w', encoding='utf-8', newline='') as output:
                    output.write(planned['.env.example'])
    print('Done. No secrets generated, packages installed, or services started.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True, type=project_name, help='project slug, e.g. my-api')
    parser.add_argument('--dry-run', action='store_true', help='list planned paths without writing or showing file contents')
    args = parser.parse_args()
    try:
        configure(args.name, args.dry_run)
    except (OSError, UnicodeError, ValueError) as exc:
        # Avoid printing file contents, which could contain credentials.
        parser.exit(2, f'bootstrap: {exc}\n')


if __name__ == '__main__':
    main()
