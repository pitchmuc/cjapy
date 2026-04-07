import json
import os
from pathlib import Path
from typing import Optional
import time

# Non standard libraries
from cjapy.config import config_object, header


def find_path(path: str) -> Optional[Path]:
    """Checks if the file denoted by the specified `path` exists and returns the Path object
    for the file.

    If the file under the `path` does not exist and the path denotes an absolute path, tries
    to find the file by converting the absolute path to a relative path.

    If the file does not exist with either the absolute and the relative path, returns `None`.
    """
    if Path(path).exists():
        return Path(path)
    elif path.startswith("/") and Path("." + path).exists():
        return Path("." + path)
    elif path.startswith("\\") and Path("." + path).exists():
        return Path("." + path)
    else:
        return None


def createConfigFile(
    filename: str = "config_analytics_template.json",
    auth_type:str = "OauthV2",
    verbose: bool = False, 
     **kwargs
) -> None:
    """Creates a `config_admin.json` file with the pre-defined configuration format
    to store the access data in under the specified `destination`.
    Parameters: 
        filename : OPTIONAL : : name of the config file.
        auth_type : OPTIONAL : type of authentication. Default is oauthV2
        verbose : OPTIONAL : set to true, gives you a print stateent where is the location.
    """
    json_data = {
        "org_id": "<orgID>",
        "client_id": "<APIkey>",
        "secret": "<YourSecret>",
        "scopes": "<scope1,scope2>",
    }
    with open(filename, "w") as cf:
        cf.write(json.dumps(json_data, indent=4))
    if verbose:
        print(
            f" file created at this location : {os.getcwd()}{os.sep}config_analytics.json"
        )


def importConfigFile(
        path: str = None,
        client_secret_index: int = 0,
        return_object: bool = False,
        ) -> Optional["ConfigObj"]:
    """Reads the file denoted by the supplied `path` and retrieves the configuration information
    from it.

    Arguments:
        path: REQUIRED : path to the configuration file. Can be either a fully-qualified or relative.
        client_secret_index : OPTIONAL : choose which of your client secrets that you want to use, specify the index, default 0.
        return_object : OPTIONAL : If True, returns a ConfigObj instance instead of updating the global config. Default False.
    
    Example of path value.
    "config.json"
    "./config.json"
    "/my-folder/config.json"
    """

    config_file_path: Optional[Path] = find_path(path)
    if config_file_path is None:
        raise FileNotFoundError(
            f"Unable to find the configuration file under path `{path}`."
        )
    with open(config_file_path, "r") as file:
        provided_config = json.load(file)
        provided_keys = provided_config.keys()
        if "api_key" in provided_keys:
            ## old naming for client_id
            client_id = provided_config["api_key"]
        elif "client_id" in provided_keys:
            ## old lowercase naming for client_id
            client_id = provided_config["client_id"]
        elif "CLIENT_ID" in provided_keys:
            client_id = provided_config["CLIENT_ID"]
        else:
            raise RuntimeError(
                f"Either an `api_key` or a `client_id` or a `CLIENT_ID` should be provided."
            )
        
        if "secret" in provided_keys:
            ## old naming for client_secret
            client_secret = provided_config["secret"]
        elif "CLIENT_SECRETS" in provided_keys:
            client_secret = provided_config["CLIENT_SECRETS"]
        else:
            raise RuntimeError(
                f"Either an `secret` or a `CLIENT_SECRETS` should be provided."
            )
        
        if "scopes" in provided_keys:
            scopes = provided_config["scopes"]
        elif "SCOPES" in provided_keys:
            scopes = provided_config["SCOPES"]
        else:
            raise RuntimeError(
                "Either a `scopes` or a `SCOPES` key should be provided."
            )
        
        client_secret = client_secret[client_secret_index] if type(client_secret) == list else client_secret
        args = {
            "org_id": provided_config["org_id"] if provided_config.get("org_id") is not None else provided_config["ORG_ID"],
            "client_id": client_id,
            "secret": client_secret,
            "scopes": ",".join(scopes) if type(scopes) == list else scopes.replace(' ',''),
        }
        if return_object:
            return ConfigObj(
                org_id=args["org_id"],
                client_id=args["client_id"],
                secret=args["secret"],
                scopes=args["scopes"],
            )
        configure(**args)


def configure(
    org_id: str = None,
    secret: str = None,
    client_id: str = None,
    scopes: str = None,
    return_object: bool = False,
) -> Optional["ConfigObj"]:
    """Performs programmatic configuration of the API using provided values.
    Arguments:
        org_id : REQUIRED : Organization ID
        secret : REQUIRED : secret generated for your connection
        client_id : REQUIRED : The client_id (old api_key) provided by the connection.
        scopes : REQUIRED : The scopes defined in your project for your API connection.
        return_object : OPTIONAL : If True, returns a ConfigObj instance instead of updating the global config. Default False.
    """
    if not org_id:
        raise ValueError("`org_id` must be specified in the configuration.")
    if not client_id:
        raise ValueError("`client_id` must be specified in the configuration.")
    if not scopes:
        raise ValueError("`scopes` must be specified in the configuration.")
    if not secret:
        raise ValueError("`secret` must be specified in the configuration.")
    config_object["org_id"] = org_id
    config_object["client_id"] = client_id
    header["x-api-key"] = client_id
    header["x-gw-ims-org-id"] = org_id
    config_object["secret"] = secret
    config_object["scopes"] = scopes
    config_object["oauthTokenEndpoint"] = f"{config_object['imsEndpoint']}/ims/token/v3"

    # ensure the reset of the state by overwriting possible values from previous import.
    config_object["date_limit"] = 0
    config_object["token"] = ""
    if return_object:
        return ConfigObj(
            org_id=org_id,
            client_id=client_id,
            secret=secret,
            scopes=scopes,
        )

class ConfigObj:
    """
    Holds an isolated set of credentials and configuration for a single CJA API connection.
        cfg = importConfigFile("config_client_a.json", return_object=True)
        cfg = configure(org_id="...", client_id="...", secret="...", scopes="...", return_object=True)
        cja = CJA(config_object=cfg)
    Attributes:
        config_object : dict holding all credential and token state.
        header : dict holding the HTTP headers for API requests.
    """

    def __init__(
        self,
        org_id: str = "",
        client_id: str = "",
        secret: str = "",
        scopes: str = None,
    ) -> None:
        ims_endpoint = "https://ims-na1.adobelogin.com"
        self.config_object: dict = {
            "org_id": org_id,
            "client_id": client_id,
            "secret": secret,
            "date_limit": 0,
            "token": "",
            "scopes": scopes,
            "imsEndpoint": ims_endpoint,
            "oauthTokenEndpoint": f"{ims_endpoint}/ims/token/v3",
        }
        self.header: dict = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Bearer ",
            "x-api-key": client_id,
            "x-gw-ims-org-id": org_id,
        }


def generateLoggingObject(level:str="WARNING",filename:str="cjapy.log") -> dict:
    """
    Generates a dictionary for the logging object with basic configuration.
    You can find the information for the different possible values on the logging documentation.
        https://docs.python.org/3/library/logging.html
    Output:
        level : Level of the logger to display information (NOTSET, DEBUG,INFO,WARNING,EROR,CRITICAL)
        stream : If the logger should display print statements
        file : If the logger should write the messages to a file
        filename : name of the file where log are written
        format : format of the logs
    """
    myObject = {
        "level": level,
        "stream": True,
        "file": False,
        "format": "%(asctime)s::%(name)s::%(funcName)s::%(levelname)s::%(message)s::%(lineno)d",
        "filename": filename,
    }
    return myObject
