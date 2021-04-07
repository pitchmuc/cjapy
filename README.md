# Adobe Customer Journey API

-----------------------

This is a python wrapper for the Adobe Customer Journey API.\
One important element when starting with CJA API is that you need to have your adobe console.io Project containing access to AEP **and** CJA.\
You cannot use the API without having access to both elements.

## Documentation

[Getting Started details on Github](./docs/getting_started.md).

## Versions

A documentation about the releases information can be found here : [cjapy releases](./docs/releases.md)

## Functionalities

Functionalities that are covered :

* Get Dimensions & Metrics
* Get, Update and Delete Tags & Shares
* Get, Update and Delete Dataview
* Get, Update and Delete Filters
* Get Top items for a dimension
* Run a report

documentation on reporting [here](./docs/main.md)

### Data Ingestion APIs

* Data Ingestion API from API 1.4
* Bulk Data Insertion API

documentation on ingestion APIs [here](./docs/ingestion.md)

## Legacy Analytics API 1.4

This module provide limited support for the 1.4 API.
It basically wrapped your request with some internal module and you can pass your request path, method, parameters and / or data.
More information in the [dedicated documentation for 1.4](./docs/legacyAnalytics.md)

## Project Data

There is a BETA feature to retrieve the Workspace projects and the components used.\
Refer to this [documentation on Project](./docs/projects.md) for more information.

## Getting Started

To install the library with PIP use:

```cli
pip install aanalytics2
```

or

```cli
python -m pip install --upgrade git+<https://github.com/pitchmuc/adobe_analytics_api_2.0.git#egg=aanalytics2>
```

## Dependencies

In order to use this API in python, you would need to have those libraries installed :

* pandas
* requests
* json
* PyJWT
* PyJWT[crypto]
* pathlib
* dicttoxml
* pytest

## Test

A test support has been added with pytest.
The complete documentation to run the test can be found here : [testing aanalytics2](./docs/test.md)

## Others Sources

You can find information about the Adobe Analytics API 2.0 here :

* [https://adobedocs.github.io/analytics-2.0-apis][2]
* [https://github.com/AdobeDocs/analytics-2.0-apis/blob/master/reporting-guide.md][3]

[1]: https://www.datanalyst.info
[2]: https://adobedocs.github.io/analytics-2.0-apis
[3]: https://github.com/AdobeDocs/analytics-2.0-apis/blob/master/reporting-guide.md
