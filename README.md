# Adobe Customer Journey API

-----------------------

This is a python wrapper for the Adobe Customer Journey API.\
One important element when starting with CJA API is that you need to have your adobe console.io Project containing access to AEP **and** CJA.\
You cannot use the API without having access to both elements.

## Documentation

Documentation is split in different places:

* Core methods to setup `cjapy`: [main documentation](./docs/main.md)
* Methods provided by the CJA class instance: [cja documentation](./docs/cja.md)
* Workspace class documentation: [Workspace class](./docs/workspace.md)
* RequestCreator class documentation: [RequestCreator class](./docs/requestCreator.md)
* Project class documentation : [Project class](./docs/projects.md)

## Versions

A documentation about the releases information can be found here : [cjapy releases](./docs/releases.md)

## Functionalities

Functionalities that are covered :

* Get Dimensions & Metrics
* Get, Update and Delete Tags & Shares
* Get, Update and Delete Dataview
* Get, Update and Delete Date Ranges
* Get, Update and Delete Filters
* Get Top items for a dimension
* Get, Update and delete projects
* Digest Project Information and analyse them via the `Project` class
* Run a report (by default returning a Workspace instance)
* (BETA) Run a multi dimensional report

## Getting Started

A documentation is provided to get started quickly with the CJA API wrapper in python.\
You can find it here: [get started on `cjapy`](./docs/getting_started.md)\
To install the library with PIP use:

```cli
pip install cjapy
```

or, to get the latest version from github

```cli
python -m pip install --upgrade git+<https://github.com/pitchmuc/cjapy.git#egg=cjapy>
```

## Logging capability

A logging capability is present on the module for debugging purposes.\
There is a proper documentation in place to understand how you can add the logging messages to your runtime.\
[Documentation on logging in cjapy](./docs/logging.md)

## Dependencies

In order to use this API in python, you would need to have those libraries installed :

* pandas
* requests
* json
* PyJWT
* PyJWT[crypto]
* pathlib
* pytest

## Tests

Use Python 3.10 or newer, create a virtual environment, and install the package
and test dependencies from the repository root:

```sh
python -m venv .venv
# Activate .venv using the command for your shell, e.g. source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The connector tests use a local HTTP server on an ephemeral loopback port and
synthetic, non-expiring credentials. No Adobe account, configuration file, secrets,
or external network access is needed to run them after dependencies are installed.
External connections are blocked by a test fixture; local loopback sockets must
be permitted. The tests exercise the actual requests/urllib3 retry adapter and
replace only urllib3's clock and sleep functions to verify delays without waiting.

Coverage includes JSON responses, 429 and transient 500/502/503/504 responses,
Retry-After seconds and HTTP dates, exponential backoff, and retry exhaustion.
The tests characterize current behavior: `retry=0` still permits three retries,
POST/PATCH requests are retried too, and exhaustion returns the final JSON error
(or HTTP status for DELETE) instead of raising a status-retry exception.

GitHub Actions runs the suite on Python 3.10–3.14 for pushes and pull requests.
This follows `pyproject.toml`'s `requires-python = ">=3.10"`. The older
`setup.py` declaration (`>=3.6`) and the Python 3.6–3.9 classifiers across the
metadata files conflict with that minimum. Those declarations remain unchanged;
maintainers should reconcile the support policy separately.

## Others Sources

You can find information about the CJA API here :

* [https://www.adobe.io/cja-apis/docs/api/]
* [https://www.adobe.io/cja-apis/docs/use-cases/]

[1]: https://www.datanalyst.info
