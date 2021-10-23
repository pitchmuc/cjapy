# Adobe Customer Journey API

-----------------------

This is a python wrapper for the Adobe Customer Journey API.\
One important element when starting with CJA API is that you need to have your adobe console.io Project containing access to AEP **and** CJA.\
You cannot use the API without having access to both elements.

## Documentation

Documentation is split in different places:

* Core methods to setup `cjapy`: [main documentation](./docs/main.md)
* Methods provided by the CJA class: [cja documentation](./docs/cja.md)
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

## Test

TBW

## Others Sources

You can find information about the CJA API here :

* [https://www.adobe.io/cja-apis/docs/api/]
* [https://www.adobe.io/cja-apis/docs/use-cases/]

[1]: https://www.datanalyst.info
