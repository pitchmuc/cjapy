# cjapy

The **cjapy** modules stands for Customer Journey Analytics python.\
It is set to wrap the different endpoints from the documentation.\
You can find the swagger documentation [here](https://www.adobe.io/cja-apis/docs/api/).

The different section will quickly explain the methods available in the differennt part of this API.

## Core components

The methods available directly from the module are the following:

### createConfigFile

This methods allows you to create JSON file that will host the different information required for your connection to Adobe IO and to retrieve the token.\
It accepts the following optional parameters:
* filename : OPTIONAL : If you want to create your config file from a specific name
* auth_type : OPTIONAL : Defaults to OauthV2 (Server-to-Server).
* verbose : OPTIONAL : Print the location of the generated file.
* proxy : OPTIONAL : Proxy URL or per-protocol mapping to include in the generated file.

It usually looks like this.

```python
import cjapy
cjapy.createConfigFile()
```

As you can see, it no arguments are required and the output of the file will look like this :

```json
{
    "org_id": "<orgId>",
    "client_id": "<clientId>",
    "secret": "<YourSecret>",
    "scopes": "<scopesServerToServer>"
}
```

You update the information from the Adobe IO account that you have setup.

#### Using a proxy

If your network requires outbound traffic to go through a proxy (common in some corporate environments), add an optional `"proxy"` key to the config file. A URL applies to both `http` and `https` traffic, for all CJA API requests, including the initial OAuth token exchange and subsequent token refreshes.

```json
{
    "org_id": "<orgID>",
    "client_id": "<APIkey>",
    "secret": "<YourSecret>",
    "scopes": "<scopes>",
    "proxy": "http://proxy.example.com:8080"
}
```

This is entirely optional. Omit the key (the default) to retain Requests' normal behavior: a direct connection unless environment proxies such as `HTTP_PROXY` or `HTTPS_PROXY` are set.

You can pre-fill the proxy when generating the template:

```python
cjapy.createConfigFile(proxy="http://proxy.example.com:8080")
```

You can also pass it programmatically, without a config file:

```python
cjapy.configure(
    org_id="<orgID>",
    client_id="<APIkey>",
    secret="<YourSecret>",
    scopes="<scopes>",
    proxy="http://proxy.example.com:8080",
)
cja = cjapy.CJA()
```

Alternatively, pass `proxy` to `ConfigObj`, or override it per instance via `CJA(config_object=..., proxy=...)`. This is useful for setting it independently of the config file, for example from an environment variable in a deployment script:

```python
import os

cjapy.importConfigFile("config.json")
cja = cjapy.CJA(proxy=os.getenv("CJA_PROXY"))
```

`CJA_PROXY` is an example variable read explicitly by this script; the library does not read it automatically. A non-empty constructor proxy takes precedence over the configuration. An omitted or empty value falls back to the configured proxy.

For separate HTTP and HTTPS proxies, use a mapping instead of a URL:

```python
cja = cjapy.CJA(proxy={
    "http": "http://http-proxy.example.com:8080",
    "https": "http://https-proxy.example.com:8080",
})
```

The same mapping format is accepted in the config file and by `configure`, `ConfigObj`, and `createConfigFile`. The resolved mapping is available as `cja.proxy` and `cja.connector.proxies`.


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
It takes the following parameters:

* org_id : REQUIRED : Organization ID
* client_id : REQUIRED : The client ID from your Adobe IO project.
* secret : REQUIRED : secret generated for your connection
* scopes : REQUIRED : The OAuth Server-to-Server scopes defined in your Adobe IO project.
* proxy : OPTIONAL : Proxy URL or per-protocol mapping for API requests and OAuth token generation. See [Using a proxy](#using-a-proxy).

### ConfigObj and multiple CJA instances

Both `importConfigFile` and `configure` accept a `return_object=True` parameter.\
When set, instead of updating the shared global config they return a `ConfigObj` instance that holds an **isolated** set of credentials and token state.

This allows you to create **multiple independent `CJA` instances** — each connected to a different Adobe IO client — and run them in parallel:

```python
import cjapy
from concurrent.futures import ThreadPoolExecutor

# Isolated config objects — one per client
cfg_a = cjapy.importConfigFile('config_client_a.json', return_object=True)
cfg_b = cjapy.configure(
    org_id='ORG_B',
    client_id='CLIENT_B',
    secret='SECRET_B',
    scopes='openid,AdobeID,read_organizations',
    return_object=True,
)

# One CJA instance per config
cja_a = cjapy.CJA(config_object=cfg_a)
cja_b = cjapy.CJA(config_object=cfg_b)

# Parallelise requests across both clients
with ThreadPoolExecutor() as pool:
    fa = pool.submit(cja_a.getDataViews)
    fb = pool.submit(cja_b.getDataViews)

print(fa.result())
print(fb.result())
```

> **Note**: The standard flow without `return_object=True` continues to work unchanged — `importConfigFile` and `configure` still update the global config used by a default `CJA()` call.

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
