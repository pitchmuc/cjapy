# Release info

This page will give you the change that are occuring when a new version has been published on pypi.
The changes have been tracked starting version 0.1.0

## 0.2.2

* fixing issue on `Project` class for specific project with dynamic filtering
* supporting Guided Analysis on `Project` class\
Patch:
* Changing Oauth V2 to V3
* Accepting more elements as credentials
* Fixing some edge cases of `findComponentUsage`
* Adding more parameters for `createDataView` methods
* Fixing `updateCalculatedMetric`

## 0.2.1

* requestCreator can now set `setSearch` and `removeSearch`
* avoiding modifying initial request from `getReport` 
* fixing report output decryption from `getReport`
* adding throwing an `TimeoutError` when API Gateway of CJA is not responding.\
Patch : 
* Fixing `breakdown` method in `Workspace` class to support when result is coming from search.
* Adding the `isIn` parameter for projects.

## 0.2.0

* adding support for Oauth Server to Server configuration file
  * adding support for `createConfigFile`
  * adding support for `importConfigFile` and `configure`
* moving to pyproject.toml release

## 0.1.1

* adding the `getConnections` and `getConnection` methods
* fixing the `getMetrics` and `getMetric` methods.

## 0.1.0

Release of the beta state for the API wrapper.
Realease information:
* Support all methods from the CJA API documentation [documentation](./main.md)
* Adding `RequestCreator` module and class to prepare report statement [documentation](./requestCreator.md)
* Adding `Workspace` module and class to read report result [documentaton](./workspace.md)
* Adding Project methods and advanced use-cases [documentation](./projects.md)
* Adding a [getting started documentation](./getting_started.md)
* Adding a logging capability [documentation](./logging.md)\
Patch:
* Adding more information when retrieving the Projects
* Fixing reporting issue with dynamic filters in Workspaces. 