# cjapy

The **cjapy** modules stands for Customer Journey Analytics python.\
It is set to wrap the different endpoints from the documentation.\
You can find the swagger documentation [here](https://www.adobe.io/cja-apis/docs/api/).

The different section will quickly explain the methods available in the differennt part of this API.

## Core components

The methods available directly from the module are the following:

### createConfigFile

This methods allows you to create JSON file that will host the different information required for your connection to Adobe IO and to retrieve the token.\
It has 2 possible parameters:
* filename : OPTIONAL : If you want to create your config file from a specific name
* auth_type : OPTIONAL : By default using OauthV2 (Server-to-Server) but can be changed to `jwt`. JWT will be discontinue in 2025.

It usually looks like this.

```python
import aanalytics2 as api2
api2.createConfigFile()
```

As you can see, it no arguments are required and the output of the file will look like this :

```JavaScript
{
    'org_id': '<orgId>',
    'client_id': "<clientId>",
    'tech_id': "<something>@techacct.adobe.com",
    'secret': "<YourSecret>",
    'scopes': '<scopesServerToServer>',
}
```

You update the information from the Adobe IO account that you have setup.


### importConfigFile

As you have created your JSON config file, you will need to import it before realizing any request to the Analytics API.\
The method takes the file name as an argument, or the path where your file exist.

```python
import cjapy as cja
cja.importConfigFile('config.json')
```

or

```python
import cjapy as cja
myfilePath = './myCredential/config.json'
cja.importConfigFile(myfilePath)
```

### configure

The configure method enables you to set the configuration for the `cjapy` module without importing a file.\
It obviously takes different parameters that are providing all information required for the retrieval of the token:

The different arguments are:

* org_id : REQUIRED : Organization ID
* tech_id : REQUIRED : Technical Account ID
* secret : REQUIRED : secret generated for your connection
* client_id : REQUIRED : The client_id (old api_key) provided by the JWT connection.
* scopes : REQUIRED : Require if using the oauth Server to Server
* path_to_key : REQUIRED : If you have a file containing your private key value. If using jwt.
* private_key : REQUIRED : If you do not use a file but pass a variable directly. If using jwt.

**Note**: JWT integration will be discontinue in 2025. Hence we do not recommend starting a new integration using the `path_to_key` and `private_key` parameters.

### CJA class

Once you have imported the configuration of your application, you can directly create an instance of the `CJA` class.\
The `CJA` class established the connection to the CJA API and provides the different methods that you can use.\
You can have more information on the class methods by going to this [documentation](./cja.md)

### generateLoggingObject

The `cjapy` module provide a way to write logs of your methods.\
This can provide valuable information when debugging or monitoring applications using the `cjapy` module.\
The `Logging` module is the one used behind the setup.\

The method generate this dictionary, used as the basic setup:

```python
{
  "level": "WARNING",
  "stream": True,
  "file": False,
  "format": "%(asctime)s::%(name)s::%(funcName)s::%(levelname)s::%(message)s::%(lineno)d",
  "filename": "cjapy.log",
}
```

You can obviously modify the elements in that dictionary to set the configuration that you want.\
More information and details can be found on reading the [Logging module](https://docs.python.org/3/library/logging.html)

[Back to README](../README.md)
