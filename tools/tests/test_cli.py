import io
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from saire_cli.cli import safe_extract, normalize_origin, api_base, CLIError


class CLISafetyTests(unittest.TestCase):
    def zip_bytes(self, entries):
        b=io.BytesIO()
        with ZipFile(b,'w') as zipfile:
            for name,value in entries.items(): zipfile.writestr(name,value)
        return b.getvalue()

    def test_safe_starter_extract(self):
        with tempfile.TemporaryDirectory() as root:
            safe_extract(self.zip_bytes({'src/app.py':'print(123)'}),Path(root)/'starter')
            self.assertEqual((Path(root)/'starter/src/app.py').read_text(),'print(123)')

    def test_block_zip_traversal(self):
        for name in ['../escape.py','/absolute.py','src\\evil.py']:
            with tempfile.TemporaryDirectory() as root:
                with self.assertRaises(CLIError):
                    safe_extract(self.zip_bytes({name:'malware'}),Path(root)/'starter')

    def test_remote_requires_tls(self):
        self.assertEqual(api_base('http://127.0.0.1:8000/api/v1'),'http://127.0.0.1:8000/api/v1')
        with self.assertRaises(CLIError): api_base('http://example.com/api/v1')

    def test_normalize_github_origin(self):
        self.assertEqual(normalize_origin('git@github.com:student/my-code.git'),'https://github.com/student/my-code')
        with self.assertRaises(CLIError): normalize_origin('https://example.com/not-your-repo')

if __name__=='__main__': unittest.main()
