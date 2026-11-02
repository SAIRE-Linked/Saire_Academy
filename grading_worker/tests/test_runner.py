import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock
import zipfile

from grading_worker.runner import (GraderError, REPOS, docker_args, safe_archive_extract,
                                   interpret_result, require_backend_url, verify_and_download,
                                   grade, SUITES)


def zip_bytes(files):
    file = io.BytesIO()
    with zipfile.ZipFile(file, 'w') as z:
        for name, content in files.items():
            z.writestr(name, content)
    return file.getvalue()


class WorkerSecurityTests(unittest.TestCase):
    def test_only_https_github_repos(self):
        self.assertTrue(REPOS.fullmatch('https://github.com/student/project'))
        for url in ('https://github.com.evil.org/student/project',
                    'https://github.com/student/project?x=1', 'http://github.com/student/project'):
            self.assertFalse(REPOS.fullmatch(url))

    def test_backend_must_use_https_except_localhost(self):
        self.assertEqual(require_backend_url('http://127.0.0.1:8000/api/v1'), 'http://127.0.0.1:8000/api/v1')
        with self.assertRaises(GraderError):
            require_backend_url('http://public.example/api/v1')

    def test_archive_extract_strips_root_and_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as td:
            safe_archive_extract(zip_bytes({'github-root/': '', 'github-root/src/quotation.py': 'pass'}), Path(td)/'dst')
            self.assertEqual((Path(td)/'dst/src/quotation.py').read_text(), 'pass')
            for path in ('github-root/../../escape', '/absolute', 'github-root/../escape'):
                with self.assertRaises(GraderError):
                    safe_archive_extract(zip_bytes({path: 'bad', 'github-root/src/quotation.py': 'ok'}), Path(td)/'new')

    def test_archive_rejects_zip_bomb(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(GraderError):
                safe_archive_extract(zip_bytes({'abc/src/quotation.py': 'x' * (13*1024*1024)}), Path(td)/'new')

    def test_docker_args_no_network_root_privileges_or_shell(self):
        args = docker_args(Path('/tmp/project'), Path('/tmp/suite'), 'saire-grade-abc', 'python:3.12-slim')
        self.assertEqual(args[0], 'docker')
        self.assertIn('none', args)
        self.assertIn('no-new-privileges', args)
        self.assertIn('65534:65534', args)
        self.assertIn('--read-only', args)
        self.assertIn('--cap-drop', args)
        self.assertNotIn('sh', args)
        self.assertNotIn('bash', args)
        self.assertIn('readonly', ' '.join(args))

    def test_commit_sha_checked_before_archive(self):
        data = json.dumps({'sha':'a'*40}).encode()
        with patch('grading_worker.runner.github_get', side_effect=[data, b'archive']) as get:
            self.assertEqual(verify_and_download('https://github.com/student/repo', 'a'*40), b'archive')
            self.assertIn('commits/', get.call_args_list[0].args[2])
            self.assertIn('zipball/', get.call_args_list[1].args[2])
        with patch('grading_worker.runner.github_get', return_value=json.dumps({'sha':'b'*40}).encode()):
            with self.assertRaises(GraderError):
                verify_and_download('https://github.com/student/repo', 'a'*40)

    def test_suite_is_server_defined_not_from_job(self):
        self.assertEqual(SUITES, {'saire-quotation-engine': 'quotation_engine'})
        with self.assertRaises(GraderError):
            grade({'assignment_slug': '../../malicious', 'repository_url': 'x', 'commit_sha': 'a'*40})

    def test_results_parsed_and_invalid_rejected(self):
        report = lambda passed,failed,errors: 'SAIRE_GRADE_RESULT:' + json.dumps({'passed':passed,'failed':failed,'errors':errors,'total':passed+failed+errors,'log':'check'})
        self.assertEqual(interpret_result(report(9,2,1),0)['score'],75)
        self.assertEqual(interpret_result(report(12,0,0),0)['score'],100)
        with self.assertRaises(GraderError):
            interpret_result(report(12,0,0),1)
        with self.assertRaises(GraderError):
            interpret_result('Traceback',1)


if __name__ == '__main__':
    unittest.main()
