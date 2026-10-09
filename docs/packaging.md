# Packaging and release checks

The build backend remains setuptools. Package metadata and runtime dependencies
are configured in `pyproject.toml`; the version comes from the literal
`__version__` in `cjapy/__version__.py`. Building does not import cjapy or require
Adobe credentials. Only the `cjapy` package is included in the wheel. The sdist
also includes contributor documentation and the distribution-check script.

## Build and check distributions

Use a fresh virtual environment with Python 3.10 or newer, then run from the
repository root:

```sh
python -m venv .venv
# Activate the environment, for example: source .venv/bin/activate
python -m pip install -r requirements-build.txt
python -m build
python scripts/check_distributions.py dist
```

Use a clean `dist` directory: the check requires exactly one wheel and one sdist.
By default, `python -m build` builds an sdist, then builds a wheel from that sdist
in an isolated build environment. The check installs each artifact into its own
fresh virtual environment, runs `pip check`, and checks import and version
availability without credentials. It also verifies that pytest is absent and
that the accidental `dynamic` extra is gone.

The import checks run with Python's `-I` flag from a temporary directory outside
the repository. They assert that `cjapy.__file__` belongs to that environment's
site-packages and agrees with installed distribution metadata, and that the
installed version matches the source version literal. Socket access is blocked
during imports. Installing dependencies and building the sdist still require
access to a package index (or a preconfigured local mirror/cache).

The Packaging workflow runs these checks on Python 3.10–3.14. This is a validation
matrix, not a resolution of the conflicting support declarations below.

## Test dependencies

pytest is a test-only dependency; runtime modules do not import it. Install it
explicitly when working on tests:

```sh
python -m pip install -e '.[test]'
```

`requirements.txt` retains the existing runtime dependency lower bounds, without
pytest. The package's existing runtime dependency versions and the legacy
pathlib/pathlib2 dependencies are unchanged. `setuptools-scm` is no longer a
build requirement: the version is read from the package's version file, and
`MANIFEST.in` explicitly retains the documentation previously found via Git.

## Questions for maintainers

These declarations remain unchanged until maintainers confirm the intended policy:

- **Python:** `pyproject.toml` declares `>=3.10`, whereas `setup.py` declares
  `>=3.6`; both have classifiers advertising older versions. The baseline build
  with setuptools 84 emits `Requires-Python: >=3.6`, despite the pyproject value.
  Should all declarations converge on 3.10+, or is older Python still supported?
  This PR preserves the declarations and baseline built requirement; it does not
  claim that the untested older versions work.
- **License:** `LICENSE` contains Apache License 2.0 and `pyproject.toml` names
  Apache License 2.0, while `setup.py` says GPL and both files include a GPLv3
  classifier. Which license metadata should releases publish? No license text,
  field, or classifier is changed here. Existing setuptools license deprecation
  warnings remain pending that decision.

`setup.py` deliberately retains only those unresolved legacy policy declarations.
Its duplicate dependency list, version parser, package discovery, and other
metadata have moved to the existing pyproject configuration. Do not remove the
remaining declarations without checking both the intended policy and built
metadata.
