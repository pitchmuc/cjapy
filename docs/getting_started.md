[Back to README](../README.md)

# Getting Started with the python wrapper for Adobe Customer Journey API

On this page, a quick example on how to start with the wrapper.
More details explanation are available in the [main file](./main.md) or one the [datanalyst.info website](https://www.datanalyst.info/category/python/adobe-analytics-api-2-0/)

## 1. Create an Adobe IO console account

First you should create an Adobe IO account and create a Project that connect to 2 API :

* Adobe Experience Platform API
* CJA API

At the time of the writting, permission to both API are required in your project for the token to be generated.
CJA API is currently only supporting the JWT connection type.

When you create your Adobe IO account, you can either let Adobe generate a certificate for you or you set a certificate, keep the key nearby because you will need it.
In case you want to generate your own certificate, you can follow this [tutorial](https://www.datanalyst.info/python/adobe-io-user-management/adobe-io-jwt-authentication-with-python/)

You have a documentation available on the official [Adobe website](https://www.adobe.io/cja-apis/docs/getting-started/)

## 2. Download the library

You can directly install the library from the command line:

```cli
pip install cjapy
```

or

```cli
python -m pip install --upgrade git+<https://github.com/pitchmuc/cjapy.git#egg=cjapy>
```

## 3. Setup a config file with your information

Starting with the wrapper, you can import it and create a template for the JSON file that will store your credential to your Adobe IO account.

```python
import cjapy
cjapy.createConfigFile()
```

This will create a JSON and you will need to fill it with the information available in your adobe io account.

**NOTE**: Starting version 0.2.0 the `createConfigFile` will by default generate a config file supporting Oauth Server to Server integration. 

## 4. Import the configuration file

Once this is done, you can import the configuration file.
I would recommend to store the config file and the key in the folder that you are using, however, the element will work if you are using correct path.

```python
import cjapy
cjapy.importConfigFile('myconfig.json')
```

**NOTE**: Starting version 0.2.0 the `importConfigFile` will detect the type of authentication based on the parameter. If `scopes` is provided, Oauth Server to Server will be used.

### Alternative : Using the configure method

When you want to connect to the Analytics API from a server application, you may want to use the `configure` method and passing the element directly.
You can see more details on that connection method on the [authentication without config json page](./authenticating_without_config_json.md)

## 5. Generate a CJA instance

Once all of these setup steps are completed, you can instantiate the `CJA` class.\
The instance of the CJA class will establish the connection to the CJA API endpoints and provide all of the methods available on the API.

```python
import cjapy
cjapy.importConfigFile('myconfig.json')

cja = cjapy.CJA()
```

## 6. Use the methods in your instance

Once you have the instance created, you can use the different methods available to them.
Don't hesitate to use the _help()_ function in order to have more details on the different possible parameters.
Example :

```python
filters = cja.getFilters()
```

or

```python
myreport = cja.getReport('myRequest.json')
```

You have more information on the method available on the CJA class in that documentation: [CJA class](./cja.md)

[Back to README](../README.md)
