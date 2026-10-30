"""SAIRE Academy CLI v0.1. All local tests are advisory, not instructor-verified."""
import argparse
import getpass
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone

HOME = Path(os.environ.get('APPDATA', Path.home() / '.config')) / 'saire-academy'
CONFIG = HOME / 'session.json'
REPORT = '.saire-test-report.json'


class CLIError(Exception):
    pass


def api_base(value):
    u = urllib.parse.urlsplit(value.rstrip('/'))
    if u.scheme != 'https' and not (u.scheme == 'http' and u.hostname in ('localhost', '127.0.0.1', '::1')):
        raise CLIError('Use HTTPS for remote APIs; HTTP is permitted only for localhost.')
    if u.username or u.password or u.query or u.fragment or not u.hostname:
        raise CLIError('Invalid API URL')
    return value.rstrip('/')


def load():
    try:
        return json.loads(CONFIG.read_text(encoding='utf8'))
    except (OSError, ValueError):
        return {}


def store(data):
    HOME.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = CONFIG.with_suffix('.tmp')
    fd = os.open(temporary, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf8') as out:
        json.dump(data, out)
    os.replace(temporary, CONFIG)
    if os.name != 'nt':
        CONFIG.chmod(0o600)


def endpoint(server, path, token='', payload=None, binary=False):
    root = api_base(server)
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Token ' + token
    if payload is not None:
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(root + path, headers=headers,
        data=json.dumps(payload).encode('utf8') if payload is not None else None,
        method='POST' if payload is not None else 'GET')
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            body = response.read(20 * 1024 * 1024 + 1)
            if len(body) > 20 * 1024 * 1024:
                raise CLIError('Response too large')
            return body if binary else json.loads(body.decode('utf8'))
    except urllib.error.HTTPError as err:
        snippet = err.read(1000).decode('utf8', errors='replace')
        raise CLIError(f'API error {err.code}: {snippet}') from err
    except urllib.error.URLError as err:
        raise CLIError(f'Cannot connect to LMS: {err.reason}') from err


def auth():
    config = load()
    if not config.get('token'):
        raise CLIError('Please run `saire login` first. Your learner account must be created by an instructor.')
    return config['server'], config['token']


def git(*args, cwd=None):
    result = subprocess.run(['git', *args], cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise CLIError(result.stderr.strip() or 'Git command failed: ' + ' '.join(args))
    return result.stdout.strip()


def normalize_origin(s):
    if s.startswith('git@github.com:'):
        s = 'https://github.com/' + s.removeprefix('git@github.com:')
    if s.endswith('.git'):
        s = s[:-4]
    s = s.rstrip('/')
    if not re.fullmatch(r'https://github\.com/[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9._-]{1,100}', s):
        raise CLIError('Only canonical GitHub repositories are supported in this MVP.')
    return s


def safe_extract(data, destination):
    """Reject traversal, symlinks, and ZIP bombs before writing anything."""
    import io
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos = z.infolist()
        if len(infos) > 100 or sum(x.file_size for x in infos) > 5 * 1024 * 1024:
            raise CLIError('Starter ZIP exceeds safety limits')
        for info in infos:
            posix = PurePosixPath(info.filename)
            mode = (info.external_attr >> 16) & 0xFFFF
            if (posix.is_absolute() or '..' in posix.parts or '\\' in info.filename or
                    not info.filename or (mode and stat.S_ISLNK(mode))):
                raise CLIError('Unsafe starter ZIP entry blocked: ' + info.filename)
        destination.mkdir(parents=True)
        for info in infos:
            path = destination.joinpath(*PurePosixPath(info.filename).parts)
            if info.is_dir():
                path.mkdir(parents=True, exist_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                with z.open(info) as src, path.open('wb') as out:
                    shutil.copyfileobj(src, out)
    (destination / '.gitignore').write_text(REPORT + '\n__pycache__/\n*.pyc\n.venv/\n', encoding='utf8')


def cmd_login(args):
    server = api_base(args.server or os.environ.get('SAIRE_API_URL', 'http://127.0.0.1:8000/api/v1'))
    username = input('SAIRE username: ').strip()
    password = getpass.getpass('Password: ')
    result = endpoint(server, '/auth/login/', payload={'username': username, 'password': password})
    store({'server': server, 'token': result['token'], 'username': result['username']})
    print('Signed in as', result['username'])
    print('Your token is stored locally. Do not use a shared device.')


def cmd_logout(_):
    config = load()
    if config.get('token'):
        try:
            endpoint(config['server'], '/auth/logout/', config['token'], {})
        finally:
            CONFIG.unlink(missing_ok=True)
    print('Signed out.')


def cmd_list(_):
    server, token = auth()
    result = endpoint(server, '/assignments/', token)
    for a in result:
        print(f"{a['slug']:<32} {a['title']} ({a['duration_days']} days)")
    if not result:
        print('No published assignments yet.')


def cmd_start(args):
    server, token = auth()
    response = endpoint(server, f'/assignments/{args.slug}/start/', token, {})
    assignment = response['assignment']
    attempt = response['attempt']
    print('Assignment:', assignment['title'])
    print('Deadline:', attempt['due_at'])
    target = Path(args.folder or args.slug).resolve()
    if target.exists():
        if args.github:
            raise CLIError('The target folder already exists; refusing to initialise or publish an existing folder automatically.')
        print('Folder exists, preserving your files:', target)
    else:
        if not assignment['has_starter']:
            raise CLIError('Assignment started, but no starter ZIP is available yet.')
        contents = endpoint(server, f'/assignments/{args.slug}/starter/', token, binary=True)
        safe_extract(contents, target)
        print('Starter extracted:', target)
        print('Next: cd', target)
        print('Run the tests with: saire test')
    if args.github:
        if not shutil.which('gh'):
            raise CLIError('Install GitHub CLI and run `gh auth login` to create a private repository.')
        git('init', cwd=target)
        git('add', '.', cwd=target)
        git('commit', '-m', 'Start SAIRE assignment', cwd=target)
        name = f'{args.slug}-{load().get("username", "student")}'.lower()
        out = subprocess.run(['gh', 'repo', 'create', name, '--private', '--source', '.', '--push'], cwd=target, text=True, capture_output=True)
        if out.returncode:
            raise CLIError('GitHub repo creation failed: ' + out.stderr.strip())
        print('GitHub repository created:', out.stdout.strip())
    else:
        print('To publish when ready, run `gh auth login` and `gh repo create <name> --private --source . --push` in your project folder.')


def cmd_test(args):
    root = Path(args.folder or '.').resolve()
    if not (root / 'tests').is_dir():
        raise CLIError('Run this command inside a project folder containing tests/.')
    result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=root,
                            capture_output=True, text=True, timeout=90)
    output = result.stdout + '\n' + result.stderr
    print(output)
    ran = re.search(r'Ran (\d+) tests?', output)
    failed_match = re.search(r'failures=(\d+)', output)
    errors_match = re.search(r'errors=(\d+)', output)
    total = int(ran.group(1)) if ran else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errors = int(errors_match.group(1)) if errors_match else 0
    passed = max(0, total - failed - errors)
    if not ran or result.returncode != 0 and failed == 0 and errors == 0:
        errors = max(errors, 1)
    (root / REPORT).write_text(json.dumps({'passed': passed, 'failed': failed, 'errors': errors,
        'run_at': datetime.now(timezone.utc).isoformat(), 'advisory_only': True}, indent=2), encoding='utf8')
    print('Local test result recorded as SELF-REPORTED evidence, not official grading.')
    if result.returncode:
        sys.exit(result.returncode)


def cmd_submit(args):
    server, token = auth()
    folder = Path(args.folder or '.').resolve()
    origin = normalize_origin(git('remote', 'get-url', 'origin', cwd=folder))
    if git('status', '--porcelain', cwd=folder):
        raise CLIError('Commit or stash your working changes before submitting.')
    sha = git('rev-parse', 'HEAD', cwd=folder)
    remote_refs = git('ls-remote', 'origin', cwd=folder)
    if not any(line.split()[0] == sha for line in remote_refs.splitlines() if line.strip()):
        raise CLIError('HEAD commit is not found at the remote branch tip. Push your commit first.')
    try:
        report = json.loads((folder / REPORT).read_text(encoding='utf8'))
    except (OSError, ValueError):
        report = {}
    result = endpoint(server, f'/assignments/{args.slug}/submit/', token, {
        'repository_url': origin, 'commit_sha': sha,
        'local_tests_passed': int(report.get('passed', 0)),
        'local_tests_failed': int(report.get('failed', 0)),
        'local_tests_errors': int(report.get('errors', 0)),
    })
    print('Submitted:', result['submission']['commit_sha'])
    print('Status: awaiting independent instructor verification and code defence.')
    print('Local test results are advisory and do not constitute an official grade.')


def cmd_grade(args):
    server, token = auth()
    attempt = endpoint(server, f'/assignments/{args.slug}/mine/', token)
    print('Assignment:', attempt['assignment'], '| Due:', attempt['due_at'])
    for s in attempt['submissions']:
        score = s['review']['final_score'] + '%' if s['review'] else 'Review pending'
        print(s['commit_sha'][:12], s['status'], '—', score, '| late days:', s['late_days'])
        if s['review'] and s['review']['feedback']:
            print('Instructor feedback:', s['review']['feedback'])


def main(argv=None):
    parser = argparse.ArgumentParser(prog='saire', description='SAIRE-Linked Academy project workflow')
    sub = parser.add_subparsers(dest='command', required=True)
    login = sub.add_parser('login', help='Sign in with an instructor-created learner account')
    login.add_argument('--server', help='URL ending in /api/v1; defaults to local Django')
    sub.add_parser('logout', help='Revoke API token')
    sub.add_parser('list', help='List available coding assignments')
    start = sub.add_parser('start', help='Start an assignment and download starter code')
    start.add_argument('slug'); start.add_argument('--folder'); start.add_argument('--github', action='store_true', help='Use GitHub CLI to create a private GitHub repository')
    test = sub.add_parser('test', help='Run visible unit tests locally')
    test.add_argument('--folder')
    submit = sub.add_parser('submit', help='Submit the pushed Git commit for instructor assessment')
    submit.add_argument('slug'); submit.add_argument('--folder')
    grade = sub.add_parser('grade', help='View submission status and instructor review')
    grade.add_argument('slug')
    args = parser.parse_args(argv)
    funcs = {'login': cmd_login, 'logout': cmd_logout, 'list': cmd_list, 'start': cmd_start,
             'test': cmd_test, 'submit': cmd_submit, 'grade': cmd_grade}
    try:
        funcs[args.command](args)
    except (CLIError, FileNotFoundError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
