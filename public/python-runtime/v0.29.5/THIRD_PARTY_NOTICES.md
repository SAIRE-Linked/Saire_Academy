# Bundled browser Python runtime

These runtime files are unmodified files from the official `pyodide@0.29.5` npm package. The package archive was checked using its npm SHA-512 integrity metadata. `SHA256.json` records the extracted runtime/metadata/licence file hashes.

Pyodide source and licence: https://github.com/pyodide/pyodide/tree/0.29.5 — see `PYODIDE_LICENSE.txt` (MPL-2.0). Corresponding source and build instructions are available in that versioned repository. CPython 3.13 licence/history is included in `PYTHON_LICENSE.txt`; source is at https://github.com/python/cpython/tree/3.13. Original licence notices in distributed JavaScript files are retained. No runtime source file was modified for this Academy integration.

The Academy's editor, message bridge and frame policy are separate project files. Do not edit the versioned runtime bytes in place: update to a new reviewed version/path and regenerate the checksums if replacing the runtime.
