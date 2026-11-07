# Packaging and release checks

The build backend remains setuptools (77.0.3 or newer for SPDX license metadata).
Package metadata and runtime dependencies are configured in `pyproject.toml`;
the version comes from the literal
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

The Packaging workflow runs these checks on Python 3.10-3.14.

## Test dependencies

pytest is a test-only dependency; runtime modules do not import it. Install it
explicitly when working on tests:

```sh
python -m pip install -e '.[test]'
```

`requirements.txt` retains the existing runtime dependency lower bounds, without
pytest. The package uses Python's standard-library `pathlib` instead of external
backport dependencies. `setuptools-scm` is no longer a build requirement:
the version is read from the package's version file, and
`MANIFEST.in` explicitly retains the documentation previously found via Git.

## License

The project uses Apache License 2.0. `pyproject.toml` declares the SPDX expression
`Apache-2.0` and includes the existing `LICENSE` file in distributions. The stale
GPL declarations and license classifiers have been removed.

## Python support and packaging configuration

Python 3.10 is the minimum supported version, declared by `requires-python` in
`pyproject.toml`. Python 3.6-3.9 are no longer advertised or accepted by installers.
The distribution check verifies that built metadata also declares `>=3.10`.

`setup.py` has been removed: modern pip and `python -m build` use the setuptools
backend declared in `pyproject.toml` without it. All package metadata, dependency
declarations, package discovery, and version configuration now live in that file.
Use `python -m build` rather than legacy `python setup.py` commands.
