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

Runtime dependencies are declared in `pyproject.toml`:

* pandas
* requests
* deprecation

## Test

Install the existing test extra and run the offline suite from the repository root:

```cli
python -m pip install -e ".[test]"
python -m pytest tests -q
```

Tests cover package/module loading without credentials, configuration formats and
credential isolation, OAuth and HTTP serialization, API routes and payloads,
pagination, report building, Workspace loading/exports, and nested Project loading.
HTTP access is blocked; tests never require real credentials or modify Adobe data.

API expectations are based on the [Adobe API reference](https://developer.adobe.com/cja-apis/docs/api)
and its [OpenAPI source](https://github.com/AdobeDocs/cja-apis/blob/main/static/swagger.json),
reviewed on November 23, 2026. SDK-specific tests additionally check documented
file inputs, output modes, and helper behavior. This is not exhaustive endpoint or
schema coverage, and passing mocked tests does not establish live API compatibility.
Annotations and deprecated filter endpoints are not covered by the API contract
tests because the current reference does not document them.

Failures are intentionally left visible rather than skipped or marked `xfail`.
The independent clean-process import test now passes. The method-test fixture
retains its original temporary version-module alias, which does not alter source
files or affect the independent import check.

For tags and connections, tests follow the response shapes confirmed in the
[individual issue review](./docs/test-findings-review.md), rather than the
inconsistent OpenAPI schemas: tags use a `content` envelope and connections use
`lastPage`. The review records the original findings, decisions, and verification
status for all 21 issues.

### Remaining verification failures

| Method | Observed defect |
| --- | --- |
| `Workspace.to_csv` | Passes pandas an unsupported `delimiter` keyword instead of `sep` (ISSUE-19). |

## Others Sources

You can find information about the CJA API here :

* [https://www.adobe.io/cja-apis/docs/api/]
* [https://www.adobe.io/cja-apis/docs/use-cases/]

[1]: https://www.datanalyst.info

## Packaging checks

See [packaging and release checks](./docs/packaging.md) for wheel/sdist builds,
fresh-install smoke checks, and test dependencies. The project requires
Python 3.10 or newer and is licensed under Apache License 2.0.
