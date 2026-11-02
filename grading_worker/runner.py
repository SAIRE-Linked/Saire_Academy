"""SAIRE ProofLoop's independently deployed assessment worker.

No Docker socket, GitHub token or worker secret goes into the student container.
Run this only on a segregated runner host. Never on the Django machine.
"""
import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import selectors
import shutil
import stat
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile

REPOS = re.compile(r'^https://github\.com/([A-Za-z0-9][A-Za-z0-9-]{0,38})/([A-Za-z0-9._-]{1,100})$')
SHA = re.compile(r'^[0-9a-f]{40}$')
SUITES = {'saire-quotation-engine': 'quotation_engine'}  # Only instructor-authored suites.
BASE = Path(__file__).resolve().parent
MAX_ARCHIVE = 8 * 1024 * 1024
MAX_UNPACKED = 12 * 1024 * 1024
MAX_FILES = 400
MAX_LOG = 5000


class GraderError(Exception):
    pass


def require_backend_url(value):
    parsed = urllib.parse.urlsplit(value.rstrip('/'))
    if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1', '::1')):
        raise GraderError('Backend API must use HTTPS except on localhost')
    if parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.hostname:
        raise GraderError('Invalid backend API URL')
    return value.rstrip('/')


def send_api(path, payload):
    url = require_backend_url(os.environ.get('SAIRE_WORKER_API_URL', 'http://127.0.0.1:8000/api/v1')) + path
    token = os.environ.get('SAIRE_WORKER_SHARED_TOKEN', '')
    if len(token) < 32:
        raise GraderError('Set a random SAIRE_WORKER_SHARED_TOKEN (at least 32 characters)')
    req = urllib.request.Request(url, json.dumps(payload).encode(), method='POST', headers={
        'X-Saire-Worker-Token': token, 'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read(65536).decode('utf8'))
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise GraderError(f'Backend API not available: {type(exc).__name__}') from exc


class GitHubRedirects(urllib.request.HTTPRedirectHandler):
    """Never forward an authenticated GitHub request to an unrelated host."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        url = urllib.parse.urlsplit(newurl)
        if (url.scheme != 'https' or url.hostname not in ('api.github.com', 'codeload.github.com', 'github.com')
                or url.port not in (None, 443) or url.username or url.password):
            raise GraderError('GitHub returned unexpected redirect host')
        forwarded = super().redirect_request(req, fp, code, msg, headers, newurl)
        # Token must not follow redirects, even to the permitted hosts.
        if forwarded:
            forwarded.remove_header('Authorization')
            forwarded.remove_unredirected_header('Authorization')
        return forwarded


def github_get(owner, repo, suffix, *, limit):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}', owner) or not re.fullmatch(r'[A-Za-z0-9._-]{1,100}', repo):
        raise GraderError('Invalid repository')
    url = f'https://api.github.com/repos/{owner}/{repo}/{suffix}'
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'SAIRE-Academy-Grader/0.2',
               'X-GitHub-Api-Version': '2022-11-28'}
    token = os.environ.get('GITHUB_TOKEN', '')
    if token:
        headers['Authorization'] = f'Bearer {token}'
    opener = urllib.request.build_opener(GitHubRedirects())
    try:
        with opener.open(urllib.request.Request(url, headers=headers), timeout=25) as response:
            payload = response.read(limit+1)
            if len(payload) > limit:
                raise GraderError('GitHub archive or response is too large')
            return payload
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 404):
            raise GraderError('GitHub commit unavailable: confirm access and the exact SHA') from e
        raise GraderError(f'GitHub request failed with HTTP {e.code}') from e
    except urllib.error.URLError as e:
        raise GraderError('GitHub request failed') from e


def verify_and_download(repository_url, commit_sha):
    found = REPOS.fullmatch(repository_url)
    if not found or not SHA.fullmatch(commit_sha):
        raise GraderError('Invalid canonical GitHub URL or 40-character SHA')
    owner, repo = found.groups()
    commit = json.loads(github_get(owner, repo, f'commits/{commit_sha}', limit=256000))
    if commit.get('sha', '').lower() != commit_sha:
        raise GraderError('Commit SHA does not match the GitHub API response')
    # GitHub's archive endpoint resolves this immutable commit ref, not the branch tip.
    archive = github_get(owner, repo, f'zipball/{commit_sha}', limit=MAX_ARCHIVE)
    return archive


def safe_archive_extract(archive, destination):
    """Strip GitHub's root folder; reject symlinks, traversal and oversized archives."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(archive))
    except (zipfile.BadZipFile, ValueError) as exc:
        raise GraderError('GitHub did not return a valid ZIP') from exc
    with zf as z:
        infos = z.infolist()
        if not infos or len(infos) > MAX_FILES or sum(x.file_size for x in infos) > MAX_UNPACKED:
            raise GraderError('Too many files or decompressed archive too large')
        roots = set()
        names = set()
        prepared = []
        for entry in infos:
            path = PurePosixPath(entry.filename)
            mode = (entry.external_attr >> 16) & 0xffff
            if (path.is_absolute() or '\\' in entry.filename or '\x00' in entry.filename or
                '..' in path.parts or (mode and (stat.S_ISLNK(mode) or
                stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISFIFO(mode)))):
                raise GraderError('Unsafe GitHub archive entry')
            roots.add(path.parts[0])
            if len(path.parts) == 1:
                if not entry.is_dir():
                    raise GraderError('Unexpected root file')
                continue
            relative = PurePosixPath(*path.parts[1:])
            if str(relative) in names:
                raise GraderError('Duplicate GitHub archive filename')
            names.add(str(relative))
            if entry.file_size > 2 * 1024 * 1024:
                raise GraderError('File exceeds size limit')
            prepared.append((entry, relative))
        if len(roots) != 1:
            raise GraderError('Archive has multiple top-level roots')
        destination.mkdir(mode=0o755)
        for entry, relative in prepared:
            target = destination.joinpath(*relative.parts)
            if entry.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                with z.open(entry) as source, target.open('wb') as output:
                    shutil.copyfileobj(source, output)
                target.chmod(0o644)
    if not (destination / 'src' / 'quotation.py').is_file():
        raise GraderError('Expected src/quotation.py in submitted repository')


def docker_args(source, suite, container_name, image):
    return [
        'docker', 'run', '--rm', '--name', container_name,
        '--network', 'none', '--read-only', '--cap-drop', 'ALL',
        '--security-opt', 'no-new-privileges', '--pids-limit', '64',
        '--memory', '256m', '--cpus', '1', '--user', '65534:65534',
        '--tmpfs', '/tmp:rw,nosuid,nodev,noexec,size=16m',
        '--mount', f'type=bind,src={source.resolve()},dst=/submission,readonly',
        '--mount', f'type=bind,src={suite.resolve()},dst=/grading,readonly',
        '--workdir', '/grading',
        '-e', 'PYTHONDONTWRITEBYTECODE=1',
        image, 'python', '-B', '/grading/run_tests.py',
    ]


def docker_run(source, suite):
    if not shutil.which('docker'):
        raise GraderError('Docker is not installed on the dedicated worker host')
    image = os.environ.get('SAIRE_GRADER_IMAGE', 'python:3.12-slim')
    if not re.fullmatch(r'[A-Za-z0-9._/:-]+(?:@sha256:[0-9a-f]{64})?', image):
        raise GraderError('Invalid grader image configured')
    name = 'saire-grade-' + uuid.uuid4().hex[:18]
    timeout = int(os.getenv('SAIRE_GRADING_TIMEOUT', '90'))
    if timeout < 10 or timeout > 180:
        raise GraderError('Timeout must be between 10 and 180 seconds')
    command = docker_args(source, suite, name, image)
    proc = None
    log_bytes = bytearray()
    started = time.monotonic()
    try:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with selectors.DefaultSelector() as sel:
            sel.register(proc.stdout, selectors.EVENT_READ)
            while True:
                if time.monotonic() - started > timeout:
                    raise GraderError('Isolated test run timed out')
                ready = sel.select(timeout=0.2)
                if ready:
                    chunk = os.read(proc.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    log_bytes.extend(chunk)
                    if len(log_bytes) > 32768:
                        raise GraderError('Grading output exceeded resource limit')
                elif proc.poll() is not None:
                    # Poll can return before all buffered output has been read.
                    continue
        proc.wait(timeout=5)
        return log_bytes.decode('utf8', 'replace'), proc.returncode
    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)
        # Clean up any container if the docker client was interrupted.
        subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=10, check=False)


def interpret_result(log, returncode):
    # The trusted entrypoint writes a compact summary *after* the test runner.
    # A failed or interrupted test run without a valid summary is not graded.
    marker = 'SAIRE_GRADE_RESULT:'
    lines = [line for line in log.splitlines() if line.startswith(marker)]
    if not lines:
        raise GraderError('Test runner did not produce a trusted summary')
    try:
        report = json.loads(lines[-1][len(marker):])
        passed, failed, errors, total = (report[key] for key in ('passed', 'failed', 'errors', 'total'))
    except (ValueError, KeyError, TypeError):
        raise GraderError('Malformed grading summary')
    if (any(type(v) is not int or v < 0 for v in (passed, failed, errors, total)) or
        not 1 <= total <= 1000 or passed + failed + errors != total or returncode != 0):
        raise GraderError('Test runner exited unexpectedly or returned invalid counts')
    return {'outcome': 'complete', 'passed': passed, 'failed': failed, 'errors': errors,
            'score': round(100 * passed / total), 'log': str(report.get('log',''))[-MAX_LOG:],
            'github_commit_verified': True}


def grade(job):
    slug = job['assignment_slug']
    if slug not in SUITES:
        raise GraderError('No instructor-approved grading suite for this assignment')
    suite = BASE / 'test_suites' / SUITES[slug]
    if not suite.is_dir():
        raise GraderError('Trusted suite missing from the worker image')
    # GitHub API access happens only on the worker host, before Docker starts.
    archive = verify_and_download(job['repository_url'], job['commit_sha'])
    with tempfile.TemporaryDirectory(prefix='saire-grader-') as td:
        src = Path(td) / 'submitted'
        safe_archive_extract(archive, src)
        log, code = docker_run(src, suite)
    return interpret_result(log, code)


def run_once():
    response = send_api('/internal/grading/claim/', {})
    job = response.get('job')
    if not job:
        return False
    try:
        result = grade(job)
    except Exception as exc:
        # Never leak GitHub tokens, archive content or stack traces to learners.
        result = {'outcome': 'error', 'github_commit_verified': False,
                  'failure_reason': str(exc)[:250] if isinstance(exc, GraderError) else 'Unexpected worker error',
                  'log': ''}
    send_api('/internal/grading/report/', {'job_id': job['id'], 'claim_token': job['claim_token'], **result})
    return True


def main():
    parser = argparse.ArgumentParser(description='SAIRE isolated grading worker (dedicated host only)')
    parser.add_argument('--once', action='store_true', help='Process at most one queue item, then exit')
    parser.add_argument('--interval', type=int, default=10, help='Idle polling interval, seconds')
    args = parser.parse_args()
    try:
        while True:
            did_work = run_once()
            if args.once:
                break
            if not did_work:
                time.sleep(max(2, args.interval))
    except GraderError as err:
        parser.exit(1, f'Worker error: {err}\n')


if __name__ == '__main__':
    main()
