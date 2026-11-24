"""Trusted runner entrypoint. Load standard-library unittest before student paths."""
import io
import json
import sys
import unittest

# Append, not prepend: this avoids student modules shadowing Python's stdlib.
sys.path.append('/submission/src')
output = io.StringIO()
try:
    suite = unittest.defaultTestLoader.discover('/grading', pattern='test_grading.py', top_level_dir='/grading')
    result = unittest.TextTestRunner(stream=output, verbosity=2, buffer=True).run(suite)
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print('SAIRE_GRADE_RESULT:' + json.dumps({
        'passed': passed, 'failed': len(result.failures), 'errors': len(result.errors),
        'total': result.testsRun, 'log': output.getvalue()[-4000:],
    }), flush=True)
    sys.exit(0 if result.testsRun > 0 else 1)
except Exception:
    print('SAIRE_RUNNER_ERROR: trusted test discovery failed', flush=True)
    sys.exit(1)
