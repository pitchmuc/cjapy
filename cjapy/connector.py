import json
import time
from copy import deepcopy
from typing import Dict

# Non standard libraries
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cjapy import config


class AdobeRequest:
    """
    Handle request to Audience Manager and taking care that the request have a valid token set each time.
    Attributes:
        restTime : Time to rest before sending new request when reaching too many request status code.
    """

    loggingEnabled = False

    def __init__(
        self,
        config_object: dict = config.config_object,
        header: dict = config.header,
        verbose: bool = False,
        retry: int = 0,
        loggingEnabled: bool = False,
        logger: object = None,
    ) -> None:
        """
        Set the connector to be used for handling request to AAM
        Arguments:
            config_object : OPTIONAL : Require the importConfig file to have been used.
            header : OPTIONAL : header of the config modules
            verbose : OPTIONAL : display comment on the request.
            retry : OPTIONAL : If you wish to retry failed GET requests
            loggingEnabled : OPTIONAL : if the logging is enable for that instance.
            logger : OPTIONAL : instance of the logger created
        """
        if config_object["org_id"] == "":
            raise Exception(
                "You have to upload the configuration file with importConfigFile method."
            )
        self.config = deepcopy(config_object)
        self.header = deepcopy(header)
        self.loggingEnabled = loggingEnabled
        self.logger = logger
        self.restTime = 30
        self.retry = retry
        self.connectionType = 'oauthV2'
        if self.config["token"] == "" or time.time() > self.config["date_limit"]:
            self.connectionType = 'oauthV2'
            token_and_expiry = self.get_oauth_token_and_expiry_for_config(
                config=self.config,
                verbose=verbose
            )
            token = token_and_expiry["token"]
            expiry = token_and_expiry["expiry"]
            if self.loggingEnabled:
                self.logger.info(f"token retrieved: {token}")
            self.token = token
            self.config["token"] = token
            self.config["date_limit"] = time.time() + expiry - 500
            self.header.update({"Authorization": f"Bearer {token}"})
        self.session = self._build_session(self.retry)

    def get_oauth_token_and_expiry_for_config(self, config: dict, 
            verbose: bool = False,
            save: bool = False
        ) -> Dict[str, str]:
            """
            Retrieve the access token by using the OAuth information provided by the user
            during the import importConfigFile function.
            Arguments :
                config : REQUIRED : Configuration object.
                verbose : OPTIONAL : Default False. If set to True, print information.
                save : OPTIONAL : Default False. If set to True, save the toke in the .
            """
            oauth_payload = {
                "grant_type": "client_credentials",
                "client_id": config["client_id"],
                "client_secret": config["secret"],
                "scope": config["scopes"]
            }
            response = requests.post(
                config["oauthTokenEndpoint"], data=oauth_payload
            )
            responseJson = response.json()
            token = responseJson.get('access_token')
            expiry = responseJson.get("expires_in")
            if token is None or expiry is None:
                raise Exception(f"OAuth response missing required fields. Response: {responseJson}")
            return {'token': token, 'expiry': expiry}

    def _build_session(self, max_retries: int) -> requests.Session:
        """
        Build a requests.Session with an HTTPAdapter configured for retrying
        on 429 and common 5xx server errors with exponential back-off.

        The adapter honours the ``Retry-After`` response header so the wait
        time advertised by the server is respected automatically.
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=max(max_retries, 3),
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={"DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT", "TRACE"},
            backoff_factor=1,
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update(self.header)
        return session

    def _checkingDate(self) -> None:
        """
        Checking if the token is still valid
        """
        now = time.time()
        if now > self.config["date_limit"]:
            if self.loggingEnabled:
                self.logger.warning("token expired. Trying to retrieve a new token")
            token_with_expiry = self.get_oauth_token_and_expiry_for_config(
                config=self.config)
            token = token_with_expiry["token"]
            expiry = token_with_expiry["expiry"]
            if self.loggingEnabled:
                self.logger.info(f"new token retrieved : {token}")
            self.config["token"] = token
            self.config["date_limit"] = time.time() + expiry - 500
            self.header.update({"Authorization": f"Bearer {token}"})
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            
    def getData(
        self,
        endpoint: str,
        params: dict = None,
        data: dict = None,
        headers: dict = None,
        *args,
        **kwargs,
    ):
        """
        Abstraction for getting data
        """
        expansion = kwargs.get("expansion")
        if expansion:
            if params is None:
                params = {}
            params["expansion"] = expansion
        self._checkingDate()
        res = self.session.get(endpoint, params=params, data=data, headers=headers)
        if self.loggingEnabled:
            self.logger.debug(f"request_URL : {res.request.url}")
            self.logger.debug(f"header used: {json.dumps(dict(self.session.headers))}")
            self.logger.debug(f"status_code: {res.status_code}")
            self.logger.debug(f"parameters used: {json.dumps(params)}")
        try:
            res_json = res.json()
        except:
            ## handling 1.4
            if kwargs.get("legacy", False):
                try:
                    return json.loads(res.text)
                except:
                    if self.loggingEnabled:
                        self.logger.error(
                            f"GET method failed: {res.status_code}, {res.text}"
                        )
                    return res.text
            res_json = {"error": "Request Error"}
        return res_json

    def postData(
        self,
        endpoint: str,
        params: dict = None,
        data: dict = None,
        headers: dict = None,
        *args,
        **kwargs,
    ):
        """
        Abstraction for posting data
        """
        expansion = kwargs.get("expansion")
        if expansion:
            if params is None:
                params = {}
            params["expansion"] = expansion
        self._checkingDate()
        if params is None and data is None:
            res = self.session.post(endpoint, headers=headers)
        elif params is not None and data is None:
            res = self.session.post(endpoint, params=params, headers=headers)
        elif params is None and data is not None:
            res = self.session.post(endpoint, data=json.dumps(data), headers=headers)
        elif params is not None and data is not None:
            res = self.session.post(endpoint, params=params, data=json.dumps(data), headers=headers)
        if self.loggingEnabled:
            self.logger.debug(f"request_URL : {res.request.url}")
            self.logger.debug(f"status_code: {res.status_code}")
        try:
            res_json = res.json()
        except:
            ## handling 1.4
            if kwargs.get("legacy", False):
                try:
                    return json.loads(res.text)
                except:
                    if self.loggingEnabled:
                        self.logger.error(
                            f"POST method failed: {res.status_code}, {res.text}"
                        )
                    return res.text
            if res.status_code == 504:
                res_json = {"error-504": "504 Gateway Time-out"}
            else:
                res_json = {"error": f"Request Error, status: {res.status_code}"}
        return res_json

    def patchData(
        self,
        endpoint: str,
        params: dict = None,
        data=None,
        headers: dict = None,
        *args,
        **kwargs,
    ):
        """
        Abstraction for patching data
        """
        self._checkingDate()
        if params is None and data is None:
            res = self.session.patch(endpoint, headers=headers)
        elif params is not None and data is None:
            res = self.session.patch(endpoint, params=params, headers=headers)
        elif params is None and data is not None:
            res = self.session.patch(endpoint, data=json.dumps(data), headers=headers)
        elif params is not None and data is not None:
            res = self.session.patch(endpoint, params=params, data=json.dumps(data), headers=headers)
        if self.loggingEnabled:
            self.logger.debug(f"request_URL : {res.request.url}")
            self.logger.debug(f"status_code: {res.status_code}")
        try:
            res_json = res.json()
        except:
            if self.loggingEnabled:
                self.logger.error(f"PATCH method failed: {res.status_code}, {res.text}")
            res_json = {"error": "Request Error"}
        return res_json

    def putData(
        self,
        endpoint: str,
        params: dict = None,
        data=None,
        headers: dict = None,
        *args,
        **kwargs,
    ):
        """
        Abstraction for putting data
        """
        expansion = kwargs.get("expansion")
        if expansion:
            if params is None:
                params = {}
            params["expansion"] = expansion
        self._checkingDate()
        if params is not None and data is None:
            res = self.session.put(endpoint, params=params, headers=headers)
        elif params is None and data is not None:
            res = self.session.put(endpoint, data=json.dumps(data), headers=headers)
        elif params is not None and data is not None:
            res = self.session.put(endpoint, params=params, data=json.dumps(data), headers=headers)
        elif params is None and data is None:
            res = self.session.put(endpoint, headers=headers)
        if self.loggingEnabled:
            self.logger.debug(f"request_URL : {res.request.url}")
            self.logger.debug(f"status_code: {res.status_code}")
        try:
            status_code = res.json()
        except:
            if self.loggingEnabled:
                self.logger.error(f"PUT method failed: {res.status_code}, {res.text}")
            status_code = {"error": "Request Error"}
        return status_code

    def deleteData(
        self, endpoint: str, params: dict = None, headers: dict = None, *args, **kwargs
    ):
        """
        Abstraction for deleting data
        """
        self._checkingDate()
        if params is None:
            res = self.session.delete(endpoint, headers=headers)
        elif params is not None:
            res = self.session.delete(endpoint, params=params, headers=headers)
        try:
            status_code = res.status_code
        except:
            if self.loggingEnabled:
                self.logger.error(f"DELETE method failed: {res.status_code}, {res.text}")
            status_code = {"error": "Request Error"}
        return status_code
