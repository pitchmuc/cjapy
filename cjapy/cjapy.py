# Created by julien piccini
# email : piccini.julien@gmail.com
import json
from copy import deepcopy
from pathlib import Path
from typing import IO, Union, List
from collections import defaultdict, deque
import time, logging, re
from itertools import tee
from datetime import datetime, timedelta
import string

# Non standard libraries
import pandas as pd
from cjapy import config, connector
from .workspace import Workspace
from .requestCreator import RequestCreator
from .projects import Project

JsonOrDataFrameType = Union[pd.DataFrame, dict]
JsonListOrDataFrameType = Union[pd.DataFrame, List[dict]]


class CJA:
    """
    Class that instantiate a connection to a single CJA API connection.
    You can pass a logging object to log information.
    """

    loggingEnabled = False
    logger = None

    def __init__(
        self,
        config_object: dict = config.config_object,
        header: dict = config.header,
        loggingObject: dict = None,
    ) -> None:
        """
        Instantiate the class with the information provided.
        Arguments:
            loggingObject : OPTIONAL :If you want to set logging capability for your actions.
            header : REQUIRED : config header loaded (DO NOT MODIFY)
            config_object : REQUIRED : config object loaded (DO NOT MODIFY)
        """
        if loggingObject is not None and sorted(
            ["level", "stream", "format", "filename", "file"]
        ) == sorted(list(loggingObject.keys())):
            self.loggingEnabled = True
            self.logger = logging.getLogger(f"{__name__}.login")
            self.logger.setLevel(loggingObject["level"])
            formatter = logging.Formatter(loggingObject["format"])
            if loggingObject["file"]:
                fileHandler = logging.FileHandler(loggingObject["filename"])
                fileHandler.setFormatter(formatter)
                self.logger.addHandler(fileHandler)
            if loggingObject["stream"]:
                streamHandler = logging.StreamHandler()
                streamHandler.setFormatter(formatter)
                self.logger.addHandler(streamHandler)
        self.connector = connector.AdobeRequest(
            config_object=config_object,
            header=header,
            loggingEnabled=self.loggingEnabled,
            logger=self.logger,
        )
        self.header = self.connector.header
        self.endpoint = config.endpoints["global"]
        self.listProjectIds = []
        self.projectsDetails = {}
        self.filters = []
        self.calculatedMetrics: JsonListOrDataFrameType = []

    def getCurrentUser(self, admin: bool = False, useCache: bool = True, **kwargs) -> dict:
        """
        return the current user
        """
        if self.loggingEnabled:
            self.logger.debug("getCurrentUser start")
        path = "/configuration/users/me"
        params = {"useCache": useCache}
        if admin:
            params["expansion"] = "admin"
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        return res
    
    def getUsers(self,limit:int=100,page:int=0)->list:
        """
        Get all the users in an organization.
        Arguments:
            limit : OPTIONAL : Number of result per request.
            page : OPTIONAL : page used to request
        """
        path = "/configuration/org/users"
        params = {'limit': limit,"page":page}
        res = self.connector.getData(self.endpoint+path,params=params)
        data = res.get('content',[])
        last_page = res.get('lastPage',True)
        while last_page == False:
            params["page"] += 1
            res = self.connector.getData(self.endpoint+path,params=params)
            data += res.get('content',[])
            last_page = res.get('lastPage',True)          
        return data

    def getCalculatedMetrics(
        self,
        full: bool = False,
        inclType: str = "all",
        dataIds: str = None,
        ownerId: str = None,
        limit: int = 1000,
        filterByIds: str = None,
        favorite: bool = False,
        approved: bool = False,
        cache: bool = True,
        output: str = "df",
        **kwargs
    ) -> JsonListOrDataFrameType:
        """
        Returns a dataframe or the list of calculated Metrics.
        Arguments:
            full : OPTIONAL : returns all possible attributs if set to True (False by default)
            inclType : OPTIONAL : returns the type selected.Possible options are:
                - all (default)
                - shared
                - templates
                - unauthorized
                - deleted
                - internal
                - curatedItem
            dataIds : OPTIONAL : Filters the result to calculated metrics tied to a specific Data View ID (comma-delimited)
            ownerId : OPTIONAL : Filters the result by specific loginId.
            limit : OPTIONAL : Number of results per request (Default 100)
            filterByIds : OPTIONAL : Filter list to only include calculated metrics in the specified list (comma-delimited),
            favorite : OPTIONAL : If set to true, return only favorties calculated metrics. (default False)
            approved : OPTIONAL : If set to true, returns only approved calculated metrics. (default False)
            cache : OPTIONAL : cache the result in a local variable.
            output : OPTIONAL : by default returns a "dataframe", can also return the list when set to "raw"
        """
        if self.loggingEnabled:
            self.logger.debug(f"getCalculatedMetrics start, output: {output}")
        path = "/calculatedmetrics"
        params = {
            "limit": limit,
            "includeType": inclType,
            "pagination": False,
            "page": 0,
        }
        if full:
            params[
                "expansion"
            ] = "definition,dataName,approved,favorite,shares,tags,sharesFullName,usageSummary,usageSummaryWithRelevancyScore,reportSuiteName,siteTitle,ownerFullName,modified,migratedIds,isDeleted,definition,authorization,compatibility,legacyId,internal,dataGroup,categories"
        if dataIds is not None:
            params["dataIds"] = dataIds
        if ownerId is not None:
            params["ownerId"] = ownerId
        if filterByIds is not None:
            params["filterByIds"] = filterByIds
        if favorite:
            params["favorite"] = favorite
        if approved:
            params["approved"] = approved
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        data = res["content"]
        lastPage = res.get("lastPage", True)
        while lastPage != True:
            params["page"] += 1
            res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
            data += res["content"]
            lastPage = res.get("lastPage", True)
        if output == "df":
            df = pd.DataFrame(data)
            if cache:
                self.calculatedMetrics = df
            return df
        if cache:
            self.calculatedMetrics = data
        return res

    def getCalculatedMetricsFunctions(
        self, output: str = "raw"
    ) -> JsonListOrDataFrameType:
        """
        Returns a list of calculated metrics functions.
        Arguments:
            output : OPTIONAL : default to "raw", can return "dataframe".
        """
        if self.loggingEnabled:
            self.logger.debug(f"getCalculatedMetricsFunctions start, output: {output}")
        path = "/calculatedmetrics/functions"
        res = self.connector.getData(self.endpoint + path)
        if output == "dataframe":
            df = pd.DataFrame(res)
            return df
        return res

    def getCalculatedMetric(self, calcId: str = None, full: bool = True, **kwargs) -> dict:
        """
        Return a single calculated metrics based on its ID.
        Arguments:
            calcId : REQUIRED : The calculated metric
            full : OPTIONAL : If you want to have all details
        """
        if calcId is None:
            raise ValueError("Requires a Calculated Metrics ID")
        if self.loggingEnabled:
            self.logger.debug(f"getCalculatedMetric start, id: {calcId}")
        path = f"/calculatedmetrics/{calcId}"
        params = {"includeHidden": True}
        if full:
            params[
                "expansion"
            ] = "approved,favorite,shares,tags,sharesFullName,usageSummary,usageSummaryWithRelevancyScore,reportSuiteName,siteTitle,ownerFullName,modified,migratedIds,isDeleted,definition,authorization,compatibility,legacyId,internal,dataGroup,categories"
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        return res

    def createCalculatedMetric(self, data: dict = None) -> dict:
        """
        Create a calculated metrics based on the dictionary.
        Arguments:
            data : REQUIRED : dictionary that will set the creation.
        """
        if data is None:
            raise ValueError("Require a dictionary to create the calculated metrics")
        if self.loggingEnabled:
            self.logger.debug(f"createCalculatedMetric start")
        path = "/calculatedmetrics"
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def validateCalculatedMetric(self, data: dict = None) -> dict:
        """
        Validate a calculated metrics definition dictionary.
        Arguments:
            data : REQUIRED : dictionary that will set the creation.
        """
        if data is None or type(data) == dict:
            raise ValueError("Require a dictionary to create the calculated metrics")
        if self.loggingEnabled:
            self.logger.debug(f"validateCalculatedMetric start")
        path = "/calculatedmetrics/validate"
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def deleteCalculateMetrics(self, calcId: str = None) -> dict:
        """
        Delete a calculated metrics based on its ID.
        Arguments:
            calcId : REQUIRED : The calculated metrics ID that will be deleted.
        """
        if calcId is None:
            raise ValueError("requires a calculated metrics ID")
        if self.loggingEnabled:
            self.logger.debug(f"deleteCalculateMetrics start, id: {calcId}")
        path = f"/calculatedmetrics/{calcId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def updateCalculatedMetrics(self, calcId: str = None, data: dict = None, **kwargs) -> dict:
        """
        Will overwrite the calculated metrics object with the new object (PUT method)
        Arguments:
            calcId : REQUIRED : The calculated metric ID to be updated
            data : REQUIRED : The dictionary that will overwrite.
        """
        if calcId is None:
            raise ValueError("Require a calculated metrics")
        if data is None or type(data) != dict:
            raise ValueError("Require a dictionary to create the calculated metrics")
        if self.loggingEnabled:
            self.logger.debug(f"updateCalculatedMetrics start, id: {calcId}")
        path = f"/calculatedmetrics/{calcId}"
        res = self.connector.putData(self.endpoint + path, data=data, **kwargs)
        return res

    def getShares(
        self,
        userId: str = None,
        inclType: str = "sharedTo",
        limit: int = 100,
        useCache: bool = True,
        **kwargs
    ) -> dict:
        """
        Returns the elements shared.
        Arguments:
            userId : OPTIONAL : User ID to return details for.
            inclType : OPTIONAL : Include additional shares not owned by the user
            limit : OPTIONAL : number of result per request.
            useCache: OPTIONAL : Caching the result (default True)
        """
        if self.loggingEnabled:
            self.logger.debug(f"getShares start")
        params = {"limit": limit, "includeType": inclType, "useCache": useCache}
        path = "/componentmetadata/shares"
        if userId is not None:
            params["userId"] = userId
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        return res

    def getShare(self, shareId: str = None, useCache: bool = True) -> dict:
        """
        Returns a specific share element.
        Arguments:
            shareId : REQUIRED : the element ID.
            useCache : OPTIONAL : If caching the response (True by default)
        """
        if self.loggingEnabled:
            self.logger.debug(f"getShare start")
        params = {"useCache": useCache}
        if shareId is None:
            raise ValueError("Require an ID to retrieve the element")
        path = f"/componentmetadata/shares/{shareId}"
        res = self.connector.getData(self.endpoint + path, params=params)
        return res

    def deleteShare(self, shareId: str = None) -> dict:
        """
        Delete the shares of an element.
        Arguments:
            shareId : REQUIRED : the element ID to be deleted.
        """
        if shareId is None:
            raise ValueError("Require an ID to retrieve the element")
        if self.loggingEnabled:
            self.logger.debug(f"deleteShare start, id: {shareId}")
        path = f"/componentmetadata/shares/{shareId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res
    
    def getAssetCount(self, imsUserId:str=None)->list:
        """
        Get the assets own by a specific user.
        Arguments:
            imsUserId : REQUIRED : The user ID owning the assets.
        """
        if imsUserId is None:
            raise ValueError("Require an IMS user ID")
        path = f"/componentmetadata/assets/{imsUserId}/counts"
        res = self.connector.getData(self.endpoint+path)
        return res
    
    def transferAssets(self,imsUserId:str=None,assets:list=None)->list:
        """
        Transfer the assets own by a specific user.
        Arguments:
            imsUserId : REQUIRED : The user ID to transfer the assets to.
            assets : REQUIRED : The list of assets to be transfered.
                Example:
                [
                    {
                        "componentType": "string",
                        "componentIds": [
                        "string"
                        ]
                    }
                ]
        """
        if imsUserId is None:
            raise ValueError("Require an IMS user ID")
        path = f"/componentmetadata/assets/{imsUserId}/transfer"
        res = self.connector.putData(self.endpoint+path,data=assets)
        return res

    def searchShares(
        self, data: dict = None, full: bool = False, limit: int = 10
    ) -> dict:
        """
        Search for multiple shares on component based on the data passed.
        Arguments:
            data : REQUIRED : dictionary specifying the search.
                example: {
                    "componentType": "string",
                    "componentIds": [
                        "string"
                    ],
                    "dataId": "string"
                }
            full : OPTIONAL : add additional data in the results.(Default False)
            limit : OPTIONAL : number of result per page (10 per default)
        """
        path = "/componentmetadata/shares/component/search"
        if data is None:
            raise ValueError("require a dictionary to specify the search.")
        if self.loggingEnabled:
            self.logger.debug(f"searchShares start")
        params = {"limit": limit}
        if full:
            params["expansion"] = "sharesFullName"
        res = self.connector.postData(self.endpoint + path, data=data, params=params)
        return res

    def updateShares(self, data: list = None, useCache: bool = True) -> dict:
        """
        Create one/many shares for one/many components at once. This is a PUT request.
        For each component object in the passed list, the given shares will replace the current set of shares for each component.
        Arguments:
            data : REQUIRED : list of dictionary containing the component to share.
                Example  [
                    {
                        "componentType": "string",
                        "componentId": "string",
                        "shares": [
                        {
                            "shareToId": 0,
                            "shareToImsId": "string",
                            "shareToType": "string",
                            "accessLevel": "string"
                        }
                        ]
                    }
                ]
            useCache : OPTIONAL : Boolean to use caching. Default is True.
        """
        if data is None or type(data) != list:
            raise ValueError("Require a list of element to share")
        if self.loggingEnabled:
            self.logger.debug(f"updateShares start")
        path = "/componentmetadata/shares"
        params = {"useCache": useCache}
        res = self.connector.putData(self.endpoint + path, params=params, data=data)
        return res

    def getDateRanges(
        self,
        limit: int = 1000,
        filterByIds: str = None,
        full: bool = True,
        includeType: str = "all",
        output: str = "df",
        **kwargs
    ) -> JsonListOrDataFrameType:
        """
        Return daterange information in a list or in a dataframe
        Arguments:
            limit : OPTIONAL : Number of result per request.
            filterByIds : OPTIONAL : Filter list to only include date ranges in the specified list (comma-delimited list of IDs)
            full : OPTIONAL : additional meta data information included.
            includeType : OPTIONAL : Show daterange not owned by user (default "all")
                Possible values are "all", "shared", "templates"
            output : OPTIONAL : Type of result returned.
        """
        if self.loggingEnabled:
            self.logger.debug(f"getDateRanges start")
        path = f"/dateranges"
        params = {"limit": limit}
        if filterByIds is not None:
            params["filterByIds"] = filterByIds
        if full:
            params[
                "expansion"
            ] = "definition,modified,ownerFullName,sharesFullName,shares,tags"
        if includeType is not None:
            params["includeType"] = includeType
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        data = res.get("content", [])
        if output == "df":
            df = pd.DataFrame(data)
            return df
        return data

    def getDateRange(self, dateRangeId: str = None, **kwargs) -> dict:
        """
        Return a single dateRange definition.
        Argument:
            dateRangeId : REQUIRED : date range ID to be returned
        """
        if dateRangeId is None:
            raise ValueError("Require a date range ID")
        if self.loggingEnabled:
            self.logger.debug(f"getDateRange start")
        path = f"/dateranges/{dateRangeId}"
        params = {
            "expansion": "definition,modified,ownerFullName,sharesFullName,shares,tags"
        }
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        return res

    def deleteDateRange(self, dateRangeId: str = None) -> dict:
        """
        Delete a single dateRange definition.
        Argument:
            dateRangeId : REQUIRED : date range ID to be deleted
        """
        if dateRangeId is None:
            raise ValueError("Require a date range ID")
        if self.loggingEnabled:
            self.logger.debug(f"deleteDateRange start")
        path = f"/dateranges/{dateRangeId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def updateDateRange(self, dateRangeId: str = None, data: dict = None) -> dict:
        """
        Update a single dateRange with the new object
        Arguments:
            dateRangeId : REQUIRED : date range ID to be updated
            data : REQUIRED : dictionary holding the new definition
        """
        if dateRangeId is None:
            raise ValueError("Require a date range ID")
        if data is None:
            raise ValueError("Require a dictionary with the new information")
        if self.loggingEnabled:
            self.logger.debug(f"updateDateRange start")
        path = f"/dateranges/{dateRangeId}"
        res = self.connector.putData(self.endpoint + path, data=data)
        return res

    def createDateRange(self, dateRangeData: dict = None, **kwargs) -> dict:
        """
        Create a single dateRange with the dictionary passed
        Argument:
            dateRangeData : REQUIRED : date range ID to be created
        """
        if dateRangeData is None:
            raise ValueError("Require a dictionary with the information")
        if self.loggingEnabled:
            self.logger.debug(f"createDateRange start")
        path = f"/dateranges/"
        res = self.connector.putData(self.endpoint + path, data=dateRangeData, **kwargs)
        return res

    def getTags(self, limit: int = 100) -> dict:
        """
        Return the tags for the company.
        Arguments:
            limit : OPTIONAL : Number of result per request.
        """
        if self.loggingEnabled:
            self.logger.debug(f"getTags start")
        path = "/componentmetadata/tags"
        params = {"limit": limit}
        res = self.connector.getData(self.endpoint + path, params=params)
        return res

    def createTags(self, data: list = None) -> dict:
        """
        Create tags for the company, attached to components.
        Arguments:
            data : REQUIRED : list of elements to passed.
                Example [
                    {
                        "id": 0,
                        "name": "string",
                        "description": "string",
                        "components": [
                        null
                        ]
                    }
                ]
        """
        path = "/componentmetadata/tags"
        if data is None and type(data) != list:
            raise ValueError("Require a list of tags to be created")
        if self.loggingEnabled:
            self.logger.debug(f"createTags start")
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def deleteTags(self, componentIds: str = None, componentType: str = None) -> dict:
        """
        Removes all tags from the passed componentIds.
        Note that currently this is done in a single DB query, so there is a single combined response for the entire operation.
        Arguments:
            componentIds : REQUIRED : comma separated list of component ids to remove tags.
            componentType : REQUIRED : The component type to operate on.
                could be any of the following ; "segment" "dashboard" "bookmark" "calculatedMetric" "project" "dateRange" "metric" "dimension" "virtualReportSuite" "scheduledJob" "alert" "classificationSet" "dataView"
        """
        path = "/componentmetadata/tags"
        if componentIds is None:
            raise ValueError("Require a component ID")
        if componentType is None:
            raise ValueError("Require a component type")
        if componentType not in [
            "segment",
            "dashboard",
            "bookmark",
            "calculatedMetric",
            "project",
            "dateRange",
            "metric",
            "dimension",
            "virtualReportSuite",
            "scheduledJob",
            "alert",
            "classificationSet",
            "dataView",
        ]:
            raise KeyError("componentType not in the enum")
        if self.loggingEnabled:
            self.logger.debug(f"deleteTags start")
        params = {componentType: componentType, componentIds: componentIds}
        res = self.connector.deleteData(self.endpoint + path, params=params)
        return res

    def getTag(self, tagId: str = None) -> dict:
        """
        Return a single tag data by its ID.
        Arguments:
            tagId : REQUIRED : The tag ID to retrieve.
        """
        if tagId is None:
            raise ValueError("Require a tag ID")
        if self.loggingEnabled:
            self.logger.debug(f"getTag start, id: {tagId}")
        path = f"/componentmetadata/tags/{tagId}"
        res = self.connector.getData(self.endpoint + path)
        return res

    def getComponentTags(
        self, componentId: str = None, componentType: str = None
    ) -> dict:
        """
        Return tags for a component based on its ID and type.
        Arguments:
            componentId : REQUIRED : The component ID
            componentType : REQUIRED : The component type.
                could be any of the following ; "segment" "dashboard" "bookmark" "calculatedMetric" "project" "dateRange" "metric" "dimension" "virtualReportSuite" "scheduledJob" "alert" "classificationSet" "dataView"
        """
        if componentId is None:
            raise ValueError("Require a component ID")
        if componentType is None:
            raise ValueError("Require a component type")
        if componentType not in [
            "segment",
            "dashboard",
            "bookmark",
            "calculatedMetric",
            "project",
            "dateRange",
            "metric",
            "dimension",
            "virtualReportSuite",
            "scheduledJob",
            "alert",
            "classificationSet",
            "dataView",
        ]:
            raise KeyError("componentType not in the enum")
        if self.loggingEnabled:
            self.logger.debug(f"getComponentTags start")
        params = {"componentId": componentId, "componentType": componentType}
        path = "/componentmetadata/tags/search"
        res = self.connector.getData(self.endpoint + path, params=params)
        return res

    def updateTags(self, data: list = None) -> dict:
        """
        This endpoint allows many tags at once to be created/deleted. PUT method.
        Any tags passed to this endpoint will become the only tags for that componentId (all other tags will be removed).
        Arguments:
            data : REQUIRED : List of tags and component to be tagged.
                Example [
                            {
                                "componentType": "string",
                                "componentId": "string",
                                "tags": [
                                    {
                                        "id": 0,
                                        "name": "string",
                                        "description": "string",
                                        "components": [
                                        null
                                        ]
                                    }
                                ]
                            }
                        ]
        """
        path = "/componentmetadata/tags/tagitems"
        if data is None or type(data) != list:
            raise ValueError("Require a list of elements to update")
        if self.loggingEnabled:
            self.logger.debug(f"updateTags start")
        res = self.connector.putData(self.endpoint + path, data=data)
        return res

    def getTopItems(
        self,
        dataId: str = None,
        dimension: str = None,
        dateRange: str = None,
        startDate: str = None,
        endDate: str = None,
        limit: int = 100,
        searchClause: str = None,
        searchAnd: str = None,
        searchOr: str = None,
        searchNot: str = None,
        searchPhrase: str = None,
        remoteLoad: bool = True,
        xml: bool = False,
        noneValues: bool = True,
        **kwargs,
    ) -> dict:
        """
        Get the top X items (based on paging restriction) for the specified dimension and dataId. Defaults to last 90 days.
        Arguments:
            dataId : REQUIRED : Data Group or Data View to run the report against
            dimension : REQUIRED : Dimension to run the report against. Example: "variables/page"
            dateRange : OPTIONAL : Format: YYYY-MM-DD/YYYY-MM-DD (default 90 days)
            startDate: OPTIONAL : Format: YYYY-MM-DD
            endDate : OPTIONAL : Format: YYYY-MM-DD
            limit : OPTIONAL : Number of results per request (default 100)
            searchClause : OPTIONAL : General search string; wrap with single quotes. Example: 'PageABC'
            searchAnd : OPTIONAL : Search terms that will be AND-ed together. Space delimited.
            searchOr : OPTIONAL : Search terms that will be OR-ed together. Space delimited.
            searchNot : OPTIONAL : Search terms that will be treated as NOT including. Space delimited.
            searchPhrase : OPTIONAL : A full search phrase that will be searched for.
            remoteLoad : OPTIONAL : tells to load the result in Oberon if possible (default True)
            xml : OPTIONAL : returns the XML for debugging (default False)
            noneValues : OPTIONAL : Controls None values to be included (default True)
        """
        path = "/reports/topItems"
        if dataId is None:
            raise ValueError("Require a data ID")
        if dimension is None:
            raise ValueError("Require a dimension")
        if self.loggingEnabled:
            self.logger.debug(f"getTopItems start")
        params = {
            "dataId": dataId,
            "dimension": dimension,
            "limit": limit,
            "allowRemoteLoad": "true",
            "includeOberonXml": False,
            "lookupNoneValues": True,
        }
        if dateRange is not None:
            params["dateRange"] = dateRange
        if startDate is not None and endDate is not None:
            params["startDate"] = startDate
            params["endDate"] = endDate
        if searchClause is not None:
            params["search-clause"] = searchClause
        if searchAnd is not None:
            params["searchAnd"] = searchAnd
        if searchOr is not None:
            params["searchOr"] = searchOr
        if searchNot is not None:
            params["searchNot"] = searchNot
        if searchPhrase is not None:
            params["searchPhrase"] = searchPhrase
        if remoteLoad == False:
            params["allowRemoteLoad"] = "false"
        if xml:
            params["includeOberonXml"] = True
        if noneValues == False:
            params["lookupNoneValues"] = False
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        return res

    def getDimensions(
        self,
        dataviewId: str = None,
        full: bool = False,
        inclType: str = None,
        verbose: bool = False,
        output: str = "df",
        **kwargs
    ) -> dict:
        """
        Used to retrieve dimensions for a dataview
        Arguments:
            dataviewId : REQUIRED : the Data View ID to retrieve data from.
            full : OPTIONAL : To add additional elements (default False)
            inclType : OPTIONAL : Possibility to add "hidden" values
            output : OPTIONAL : Type of output selected, either "df" (default) or "raw"
        """
        if dataviewId is None:
            raise ValueError("Require a Data View ID")
        if self.loggingEnabled:
            self.logger.debug(f"getDimensions start")
        path = f"/data/dataviews/{dataviewId}/dimensions"
        params = {"page":0}
        if full:
            params[
                "expansion"
            ] = "approved,favorite,tags,usageSummary,usageSummaryWithRelevancyScore,description,sourceFieldId,segmentable,required,hideFromReporting,hidden,includeExcludeSetting,fieldDefinition,bucketingSetting,noValueOptionsSetting,defaultDimensionSort,persistenceSetting,storageId,tableName,dataSetIds,dataSetType,type,schemaPath,hasData,sourceFieldName,schemaType,sourceFieldType,fromGlobalLookup,multiValued,precision"
        if inclType == "hidden":
            params["includeType"] = "hidden"
        res = self.connector.getData(
            self.endpoint + path, params=params, verbose=verbose, **kwargs
        )
        dimensions = res.get("content", [])
        lastPage = res.get('lastPage',True)
        while lastPage == False:
            params["page"] += 1
            res = self.connector.getData(
            self.endpoint + path, params=params, verbose=verbose, **kwargs
            )
            dimensions += res.get('content',[])
            lastPage = res.get('lastPage',True)
        if output == "df":
            df = pd.DataFrame(dimensions)
            return df
        return dimensions

    def getSharedComponentsMatrix(self, include_dimensions=True, include_metrics=True):
        """
        Build a matrix of shared components (dimensions and/or metrics) across dataviews.

        Parameters
        ----------
        include_dimensions : bool, optional
            Whether to include shared dimensions (default: True).
        include_metrics : bool, optional
            Whether to include shared metrics (default: True).

        Returns
        -------
        pandas.DataFrame
            A DataFrame where rows are components (with id, type, name) 
            and columns are dataview names, containing 1/0 for presence.

        Example
        -------
        >>> # Get shared dimensions and metrics matrix
        >>> df = cja.getSharedComponentsMatrix()
        >>> df.head()
                   type            name  Claims Dataview  Member Portal
        id
        d1      dimension    Customer ID               1              1
        m1        metric         Revenue               1              0
        """
        print(
            f"Shared components matrix generation started..."
        )
        dataviews = self.getDataViews()
        dv_map = dict(zip(dataviews["id"], dataviews["name"]))

        def build_shared_matrix(fetch_fn, comp_type):
            results = {}
            id_to_name = {}

            for dv_id, dv_name in dv_map.items():
                try:
                    comps = fetch_fn(dv_id, inclType=True, full=True)
                    shared = comps[comps["sharedComponent"] == True][["id", "name"]]
                    results[dv_name] = set(shared["id"].tolist())
                    id_to_name.update(dict(zip(shared["id"], shared["name"])))
                except Exception as e:
                    print(f"Error fetching {comp_type} for {dv_id} ({dv_name}): {e}")

            all_ids = sorted(set().union(*results.values()))
            df = pd.DataFrame(index=all_ids)

            for dv_name, comp_ids in results.items():
                df[dv_name] = df.index.isin(comp_ids).astype(int)

            df.insert(0, "name", df.index.map(id_to_name))
            df.insert(0, "type", comp_type)
            return df

        dfs = []
        if include_dimensions:
            dfs.append(build_shared_matrix(self.getDimensions, "dimension"))
        if include_metrics:
            dfs.append(build_shared_matrix(self.getMetrics, "metric"))

        if not dfs:
            raise ValueError("At least one of include_dimensions/include_metrics must be True")
        
        print(
            f"Shared components matrix created"
            "Hint: use `df.head()` to preview or `display(df)`."
        )

        return pd.concat(dfs)

    
    def getDimension(
        self, dataviewId: str = None, 
        dimensionId: str = None, 
        full: bool = True,
        **kwargs
    ):
        """
        Return a specific dimension based on the dataview ID and dimension ID passed.
        Arguments:
            dataviewId : REQUIRED : the Data View ID to retrieve data from.
            dimensionId : REQUIRED : the dimension ID to return
            full : OPTIONAL : To add additional elements (default True)
        """
        if dataviewId is None:
            raise ValueError("Require a Data View ID")
        if dimensionId is None:
            raise ValueError("Require a Dimension ID")
        if self.loggingEnabled:
            self.logger.debug(f"getDimension start, id: {dimensionId}")
        path = f"/data/dataviews/{dataviewId}/dimensions/{dimensionId}"
        params = {}
        if full:
            params[
                "expansion"
            ] = "approved,favorite,tags,usageSummary,usageSummaryWithRelevancyScore,description,sourceFieldId,segmentable,required,hideFromReporting,hidden,includeExcludeSetting,fieldDefinition,storageId,tableName,dataSetIds,dataSetType,type,schemaPath,hasData,sourceFieldName,schemaType,sourceFieldType,fromGlobalLookup,multiValued,precision"
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        return res

    def getMetrics(
        self,
        dataviewId: str = None,
        full: bool = False,
        inclType: str = None,
        verbose: bool = False,
                output: str = "df",
        **kwargs
    ) -> dict:
        """
        Used to retrieve metrics for a dataview
        Arguments:
            dataviewId : REQUIRED : the Data View ID to retrieve data from.
            full : OPTIONAL : To add additional elements (default False)
            inclType : OPTIONAL : Possibility to add "hidden" values
            output : OPTIONAL : Type of output selected, either "df" (default) or "raw"
        """
        if dataviewId is None:
            raise ValueError("Require a Data View ID")
        if self.loggingEnabled:
            self.logger.debug(f"getMetrics start")
        path = f"/data/dataviews/{dataviewId}/metrics"
        params = {"page":0}
        if full:
            params[
                "expansion"
            ] = "approved,favorite,tags,usageSummary,usageSummaryWithRelevancyScore,description,sourceFieldId,segmentable,required,hideFromReporting,hidden,includeExcludeSetting,fieldDefinition,storageId,tableName,dataSetIds,dataSetType,type,schemaPath,hasData,sourceFieldName,schemaType,sourceFieldType,fromGlobalLookup,multiValued,precision"
        if inclType == "hidden":
            params["includeType"] = "hidden"
        res = self.connector.getData(
            self.endpoint + path, params=params, verbose=verbose, **kwargs
        )
        metrics = res.get('content',[])
        lastPage = res.get('lastPage',True)
        while lastPage == False:
            params["page"] += 1
            res = self.connector.getData(
            self.endpoint + path, params=params, verbose=verbose, **kwargs
            )
            metrics += res.get('content',[])
            lastPage = res.get('lastPage',True)
        if output =='df':
            df = pd.DataFrame(metrics)
            return df
        return res

    def getMetric(
        self, dataviewId: str = None, metricId: str = None, full: bool = True, **kwargs
    ):
        """
        Return a specific metric based on the dataview ID and dimension ID passed.
        Arguments:
            dataviewId : REQUIRED : the Data View ID to retrieve data from.
            metricId : REQUIRED : the metric ID to return
            full : OPTIONAL : To add additional elements (default True)
        """
        if dataviewId is None:
            raise ValueError("Require a Data View ID")
        if metricId is None:
            raise ValueError("Require a Dimension ID")
        if self.loggingEnabled:
            self.logger.debug(f"getMetric start, id: {metricId}")
        path = f"/data/dataviews/{dataviewId}/metrics/{metricId}"
        params = {}
        if full:
            params[
                "expansion"
            ] = "approved,favorite,tags,usageSummary,usageSummaryWithRelevancyScore,description,sourceFieldId,segmentable,required,hideFromReporting,hidden,includeExcludeSetting,fieldDefinition,bucketingSetting,noValueOptionsSetting,defaultDimensionSort,persistenceSetting,storageId,tableName,dataSetIds,dataSetType,type,schemaPath,hasData,sourceFieldName,schemaType,sourceFieldType,fromGlobalLookup,multiValued,precision"
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        return res

    def getDataViews(
        self,
        limit: int = 100,
        full: bool = True,
        output: str = "df",
        parentDataGroupId: str = None,
        externalIds: str = None,
        externalParentIds: str = None,
        includeType: str = "all",
        cached: bool = True,
        verbose: bool = False,
        **kwargs,
    ) -> JsonListOrDataFrameType:
        """
        Returns the Data View configuration.
        Arguments:
            limit : OPTIONAL : number of results per request (default 100)
            full : OPTIONAL : define if all possible information are returned (default True).
            output : OPTIONAL : Type of output selected, either "df" (default) or "raw"
            parentDataGroupId : OPTIONAL : Filters data views by a single parentDataGroupId
            externalIds : OPTIONAL : Comma-delimited list of external ids to limit the response with.
            externalParentIds : OPTIONAL : Comma-delimited list of external parent ids to limit the response with.
            dataViewIds : OPTIONAL : Comma-delimited list of data view ids to limit the response with.
            includeType : OPTIONAL : include additional DataViews not owned by user.(default "all")
            cached : OPTIONAL : return cached results
            verbose : OPTIONAL : add comments in the console.
        """
        if self.loggingEnabled:
            self.logger.debug(f"getDataViews start, output: {output}")
        path = "/data/dataviews"
        params = {
            "limit": limit,
            "includeType": includeType,
            "cached": cached,
            "page": 0,
        }
        if full:
            params[
                "expansion"
            ] = "name,description,owner,isDeleted,parentDataGroupId,segmentList,currentTimezoneOffset,timezoneDesignator,modified,createdDate,organization,curationEnabled,recentRecordedAccess,sessionDefinition,curatedComponents,externalData,containerNames"
        if parentDataGroupId:
            params["parentDataGroupId"] = parentDataGroupId
        if externalIds:
            params["externalIds"] = externalIds
        if externalParentIds:
            params["externalParentIds"] = externalParentIds
        res = self.connector.getData(
            self.endpoint + path, params=params, verbose=verbose, **kwargs
        )
        data = res["content"]
        last = res.get("last", True)
        while last != True:
            params["page"] += 1
            res = self.connector.getData(
                self.endpoint + path, params=params, verbose=verbose, **kwargs
            )
            data += res["content"]
            last = res.get("last", True)
        if output == "df":
            df = pd.DataFrame(data)
            return df
        return data

    def getDataView(
        self, dataViewId: str = None, full: bool = True, save: bool = False, **kwargs
    ) -> dict:
        """
        Returns a specific Data View configuration from Configuration ID.
        Arguments:
            dataViewId : REQUIRED : The data view ID to retrieve.
            full : OPTIONAL : getting extra information on the data view
            save : OPTIONAL : save the response in JSON format
        """
        if dataViewId is None:
            raise ValueError("dataViewId is required")
        if self.loggingEnabled:
            self.logger.debug(f"getDataView start")
        path = f"/data/dataviews/{dataViewId}"
        params = {}
        if full:
            params[
                "expansion"
            ] = "name,description,owner,isDeleted,parentDataGroupId,segmentList,currentTimezoneOffset,timezoneDesignator,modified,createdDate,organization,curationEnabled,recentRecordedAccess,sessionDefinition,curatedComponents,externalData,containerNames"
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        if save:
            with open(f"{dataViewId}_{int(time.time())}.json", "w") as f:
                f.write(json.dumps(res, indent=4))
        return res

    def getConnections(self,limit:int=1000,full:bool=True,output:str='df',**kwargs)-> JsonListOrDataFrameType:
        """
        Retrieve the connections associated to that company.
        Arguments:
            limit : OPTIONAL : number of results per request (default 100)
            full : OPTIONAL : define if all possible information are returned (default True).
            output : OPTIONAL : Type of output selected, either "df" (default) or "raw"
        """
        if self.loggingEnabled:
            self.logger.debug(f"getConnections start")
        path = f"/data/connections"
        params = {"limit":limit,"page":0}
        if full:
            params["expansion"] ="granularBackfills,granularStreaming,backfillsSummaryConnection,name,description,isDeleted,isDisabled,dataSets,createdDate,modified,sandboxName,organization,backfillEnabled,modifiedBy,ownerFullName"
        res = self.connector.getData(self.endpoint + path,params=params, **kwargs)
        data = res.get('content',[])
        lastpage = res.get('lastPage',True)
        while lastpage != True:
            params['page'] += 1
            res = self.connector.getData(self.endpoint + path,params=params, **kwargs)
            data += res.get('content',[])
            lastpage = res.get('lastPage',True)
        if output == "df":
            df = pd.DataFrame(data)
            return df
        return data
    
    def getConnection(self,connectionId:str=None,**kwargs)->dict:
        """
        Returns the dictionary of a single connection based on its ID, without prefix.
        Arguments:
            connectionId : REQUIRED : The ID of the connection without prefix.
        """
        if connectionId is None:
            raise ValueError("Require a connection ID")
        path = f"/data/connections/{connectionId}"
        params = {'expansion':"granularBackfills,granularStreaming,backfillsSummaryConnection,name,description,isDeleted,isDisabled,dataSets,createdDate,modified,sandboxName,organization,backfillEnabled,modifiedBy,ownerFullName"}
        res = self.connector.getData(self.endpoint + path,params=params, **kwargs)
        return res

    def validateDataView(self, data: Union[dict, IO]) -> dict:
        """
        Validate the dictionary for the creation of a data view.
        Argument:
            data : REQUIRED : The dictionary or json file that holds the definition for the dataview to be created.
        """
        if data is None:
            raise ValueError("Require information to be passed for data view creation")
        if self.loggingEnabled:
            self.logger.debug(f"validateDataView start")
        path = "/data/dataviews/validate"
        if ".json" in data:
            with open(data, "r") as f:
                data = json.load(f)
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def createDataView(self, 
                       data: Union[dict, IO] = None,
                       name:str=None,
                       connectionId:str=None,
                       description:str="power by cjapy",
                       timeZone:str="US/Mountain",
                       minuteInactivity:int=30,
                       **kwargs) -> dict:
        """
        Create and stores the given Data View in the db.
        Arguments:
            data : REQUIRED : The dictionary or json file that holds the definition for the dataview to be created.
            name : OPTIONAL : If you want to pass the name of the data View (and not pass the whole definition)
            connectionId : OPTIONAL : If you want to pass the connectionId of the data View (and not pass the whole definition)
            timezone : OPTIONAL : The timezone to use in the data View (see here: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
                common timezone: US/Montain, US/Pacific, US/Michigan, US/Central, Europe/London, Europe/Paris, Asia/Tokyo, Australia/Sydney
            minuteInactivity : OPTIONAL : number of minutes of inactivity before closing a session
        """
        path = "/data/dataviews/"
        if data is None and name is None and connectionId is None:
            raise ValueError("Require information to be passed for data view creation")
        if data is not None:
            if ".json" in data:
                with open(data, "r", encoding=kwargs.get("encoding", "utf-8")) as f:
                    data = json.load(f)
            data = data
        if data is None and name is not None and connectionId is not None:
            data = {
                "name": name,
                "description": description,
                "parentDataGroupId": connectionId,
                "timezoneDesignator": timeZone,
                "sessionDefinition": [
                    {
                    "numPeriods": minuteInactivity,
                    "granularity": "MINUTE",
                    "func": "INACTIVITY",
                    "events": [
                        "string"
                    ]
                    }
                ],
                "organization": self.connector.config['org_id'],
                "externalData": {
                    "externalParentId": connectionId
                }

            }
        if self.loggingEnabled:
            self.logger.debug(f"createDataView start")
        res = self.connector.postData(self.endpoint + path, data=data, **kwargs)
        return res

    def deleteDataView(self, dataViewId: str = None) -> str:
        """
        Delete a data view by its ID.
        Argument:
            dataViewId : REQUIRED : the data view ID to be deleted
        """
        if dataViewId is None:
            raise ValueError("Require a data view ID")
        if self.loggingEnabled:
            self.logger.debug(f"deleteDataView start, id: {dataViewId}")
        path = f"/data/dataviews/{dataViewId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def updateDataView(
        self, dataViewId: str = None, data: Union[dict, IO] = None, **kwargs
    ) -> dict:
        """
        Update the Data View definition (PUT method)
        Arguments:
            dataViewId : REQUIRED : the data view ID to be updated
            data : REQUIRED : The dictionary or JSON file that holds the definition for the dataview to be updated
        possible kwargs:
            encoding : if you pass a JSON file, you can change the encoding to read it.
        """
        if dataViewId is None:
            raise ValueError("Require a Data View ID")
        if data is None:
            raise ValueError("Require data to be passed for the update")
        if self.loggingEnabled:
            self.logger.debug(f"updateDataView start, id: {dataViewId}")
        path = f"/data/dataviews/{dataViewId}"
        if ".json" in data:
            with open(data, "r", encoding=kwargs.get("encoding", "utf-8")) as f:
                data = json.load(f.read())
        res = self.connector.putData(self.endpoint + path, data=data)
        return res

    def copyDataView(self, dataViewId: str = None, **kwargs) -> dict:
        """
        Copy the setting of a specific data view.
        Arguments:
            dataViewId : REQUIRED : Data View ID to copy the setting on
        """
        if dataViewId is None:
            raise ValueError("Require a data view ID")
        if self.loggingEnabled:
            self.logger.debug(f"copyDataView start, id: {dataViewId}")
        path = f"/data/dataviews/copy/{dataViewId}"
        res = self.connector.putData(self.endpoint + path, **kwargs)
        return res

    def getFilters(
        self,
        limit: int = 1000,
        full: bool = False,
        output: str = "df",
        includeType: str = "all",
        name: str = None,
        dataIds: str = None,
        ownerId: str = None,
        filterByIds: str = None,
        cached: bool = True,
        cache: bool = True,
        verbose: bool = False,
        **kwargs
    ) -> JsonListOrDataFrameType:
        """
        Returns a list of filters used in CJA.
        Arguments:
            limit : OPTIONAL : number of result per request (default 100)
            full : OPTIONAL : add additional information to the filters
            output : OPTIONAL : Type of output selected, either "df" (default) or "raw"
            includeType : OPTIONAL : Include additional segments not owned by user.(default all)
                possible values are "shared" "templates" "deleted" "internal"
            name : OPTIONAL : Filter list to only include filters that contains the Name
            dataIds : OPTIONAL : Filter list to only include filters tied to the specified data group ID list (comma-delimited)
            ownerId : OPTIONAL : Filter by a specific owner ID.
            filterByIds : OPTIONAL : Filters by filter ID (comma-separated list)
            cached : OPTIONAL : return cached results
            cache : OPTIONAL : If you want to cache the results in a local variable
            toBeUsedInRsid : OPTIONAL : The report suite where the filters is intended to be used. This report suite will be used to determine things like compatibility and permissions.
        """
        if self.loggingEnabled:
            self.logger.debug(f"getFilters start, output: {output}")
        path = "/filters"
        params = {
            "limit": limit,
            "cached": cached,
            "includeType": includeType,
            "page": 0,
        }
        if full:
            params[
                "expansion"
            ] = "compatibility,definition,internal,modified,isDeleted,definitionLastModified,createdDate,recentRecordedAccess,performanceScore,owner,dataId,ownerFullName,dataName,sharesFullName,approved,favorite,shares,tags,usageSummary,usageSummaryWithRelevancyScore"
        if name is not None:
            params["name"] = name
        if dataIds is not None:
            params["dataIds"] = dataIds
        if ownerId is not None:
            params["ownerId"] = ownerId
        if filterByIds is not None:
            params["filterByIds"] = filterByIds
        res = self.connector.getData(
            self.endpoint + path, params=params, verbose=verbose, **kwargs
        )
        lastPage = res.get("lastPage", True)
        data = res["content"]
        while lastPage == False:
            params["page"] += 1
            res = self.connector.getData(
                self.endpoint + path, params=params, verbose=verbose, **kwargs
            )
            data += res["content"]
            lastPage = res.get("lastPage", True)
        if cache:
            self.filtes = data
        if output == "df":
            df = pd.DataFrame(data)
            return df
        return data

    def getFilter(
        self,
        filterId: str = None,
        full: bool = False,
        **kwargs
    ) -> dict:
        """
        Returns a single filter definition by its ID.
        Arguments:
            filterId : REQUIRED : ID of the filter
            full : OPTIONAL : Boolean to define additional elements
        """
        if filterId is None:
            raise ValueError("Require a filter ID")
        if self.loggingEnabled:
            self.logger.debug(f"getFilter start, id: {filterId}")
        path = f"/filters/{filterId}"
        params = {}
        if full:
            params[
                "expansion"
            ] = "compatibility,definition,internal,modified,isDeleted,definitionLastModified,createdDate,recentRecordedAccess,performanceScore,owner,dataId,ownerFullName,dataName,sharesFullName,approved,favorite,shares,tags,usageSummary,usageSummaryWithRelevancyScore"
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        return res

    def deleteFilter(self, filterId: str = None) -> str:
        """
        Delete a filter based on its ID.
        Arguments:
            filterId : REQUIRED : Filter ID to be deleted
        """
        if filterId is None:
            raise ValueError("Require a filter ID")
        if self.loggingEnabled:
            self.logger.debug(f"deleteFilter start, id: {filterId}")
        path = f"/filters/{filterId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def validateFilter(self, data: Union[dict, IO] = None, **kwargs) -> dict:
        """
        Validate the syntax for filter creation.
        Arguments:
            data : REQUIRED : Dictionary or JSON file to create a filter
        possible kwargs:
            encoding : if you pass a JSON file, you can change the encoding to read it.
        """
        if data is None:
            raise ValueError("Require some data to validate")
        if self.loggingEnabled:
            self.logger.debug(f"validateFilter start")
        path = "/filters/validate"
        if ".json" in data:
            with open(data, "r", encoding=kwargs.get("encoding", "utf-8")) as f:
                data = json.load(f.read())
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def createFilter(self, data: Union[dict, IO] = None, **kwargs) -> dict:
        """
        Create a filter.
        Arguments:
            data : REQUIRED : Dictionary or JSON file to create a filter
        possible kwargs:
            encoding : if you pass a JSON file, you can change the encoding to read it.
        """
        if data is None:
            raise ValueError("Require some data to validate")
        if self.loggingEnabled:
            self.logger.debug(f"createFilter start")
        path = "/filters"
        if ".json" in data:
            with open(data, "r", encoding=kwargs.get("encoding", "utf-8")) as f:
                data = json.load(f)
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def updateFilter(
        self, filterId: str = None, data: Union[dict, IO] = None, **kwargs
    ) -> dict:
        """
        Update a filter based on the filter ID.
        Arguments:
            filterId : REQUIRED : Filter ID to be updated
            data : REQUIRED : Dictionary or JSON file to update the filter
        possible kwargs:
            encoding : if you pass a JSON file, you can change the encoding to read it.
        """
        if filterId is None:
            raise ValueError("Require a filter ID")
        if data is None:
            raise ValueError("Require some data to validate")
        if self.loggingEnabled:
            self.logger.debug(f"updateFilter start, id: {filterId}")
        path = f"/filters/{filterId}"
        if ".json" in data:
            with open(data, "r", encoding=kwargs.get("encoding", "utf-8")) as f:
                data = json.load(f.read())
        res = self.connector.putData(self.endpoint + path, data=data, **kwargs)
        return res

    def getAuditLogs(
        self,
        startDate: str = None,
        endDate: str = None,
        action: str = None,
        component: str = None,
        componentId: str = None,
        userType: str = None,
        userId: str = None,
        userEmail: str = None,
        description: str = None,
        pageSize: int = 100,
        n_results: Union[str, int] = "inf",
        output: str = "df",
        save: bool = False,
    ) -> JsonListOrDataFrameType:
        """
        Get Audit Log when few filters are applied.
        All filters are applied with an AND condition.
        Arguments:
            startDate : OPTIONAL : begin range date, format: YYYY-01-01T00:00:00-07 (required if endDate is used)
            endDate : OPTIONAL : begin range date, format: YYYY-01-01T00:00:00-07 (required if startDate is used)
            action : OPTIONAL : The type of action a user or system can make.
                Possible values : CREATE, EDIT, DELETE, LOGIN_FAILED, LOGIN_SUCCESSFUL, API_REQUEST
            component : OPTIONAL :The type of component.
                Possible values : CALCULATED_METRIC, CONNECTION, DATA_GROUP, DATA_VIEW, DATE_RANGE, FILTER, MOBILE, PROJECT, REPORT, SCHEDULED_PROJECT
            componentId : OPTIONAL : The id of the component.
            userType : OPTIONAL : The type of user.
            userId : OPTIONAL : The ID of the user.
            userEmail : OPTIONAL : The email address of the user.
            description : OPTIONAL : The description of the audit log.
            pageSize : OPTIONAL : Number of results per page. If left null, the default size is 100.
            n_results : OPTIONAL : Total number of results you want for that search. Default "inf" will return everything
            output : OPTIONAL : DataFrame by default, can be "raw"
        """
        if self.loggingEnabled:
            self.logger.debug(f"getAuditLogs start")
        params = {"pageNumber": 0, "pageSize": pageSize}
        path = "/auditlogs/api/v1/auditlogs"
        if startDate is not None and endDate is not None:
            params["startDate"] = startDate
            params["endDate"] = endDate
        if action is not None:
            params["action"] = action
        if component is not None:
            params["component"] = component
        if componentId is not None:
            params["componentId"] = componentId
        if userType is not None:
            params["userType"]
        if userId is not None:
            params["userId"] = userId
        if userEmail is not None:
            params["userEmail"] = userEmail
        if description is not None:
            params["description"] = description
        lastPage = False
        data = []
        while lastPage != True:
            res = self.connector.getData(self.endpoint + path, params=params)
            data += res.get("content", [])
            lastPage = res.get("last", True)
            if len(data) > float(n_results):
                lastPage = True
            params["pageNumber"] += 1
        if output == "raw":
            if save:
                with open(f"audit_logs_{int(time.time())}.json", "w") as f:
                    f.write(json.dumps(data))
        df = pd.DataFrame(data)
        try:
            df["userId"] = df["user"].apply(lambda x: x.get("id", ""))
        except:
            if self.loggingEnabled:
                self.logger.debug(f"issue extracting userId")
        try:
            df["componentId"] = df["component"].apply(lambda x: x.get("id", ""))
        except:
            if self.loggingEnabled:
                self.logger.debug(f"issue extracting componentId")
        try:
            df["componentType"] = df["component"].apply(lambda x: x.get("idType", ""))
        except:
            if self.loggingEnabled:
                self.logger.debug(f"issue extracting componentType")
        try:
            df["componentName"] = df["component"].apply(lambda x: x.get("name", ""))
        except:
            if self.loggingEnabled:
                self.logger.debug(f"issue extracting componentName")
        if save:
            df.to_csv(f"audit_logs.{int(time.time())}.csv", index=False)
        return df

    SAMPLE_FILTERMESSAGE_LOGS = {
        "criteria": {
            "fieldOperator": "AND",
            "fields": [
                {
                    "fieldType": "COMPONENT",
                    "value": ["FILTER", "CALCULATED_METRIC"],
                    "operator": "IN",
                },
                {
                    "fieldType": "DESCRIPTION",
                    "value": ["created"],
                    "operator": "CONTAINS",
                },
            ],
            "subCriteriaOperator": "AND",
            "subCriteria": {
                "fieldOperator": "OR",
                "fields": [
                    {
                        "fieldType": "USER_EMAIL",
                        "value": ["jane"],
                        "operator": "NOT_EQUALS",
                    },
                    {
                        "fieldType": "USER_EMAIL",
                        "value": ["john"],
                        "operator": "EQUALS",
                    },
                ],
                "subCriteriaOperator": None,
                "subCriteria": None,
            },
        },
        "pageSize": 100,
        "pageNumber": 0,
    }

    def searchAuditLogs(self, filterMessage: dict = None) -> JsonListOrDataFrameType:
        """
        Get Audit Log when several filters are applied. You can define the different type of operator and connector to use.
        Operators: EQUALS, CONTAINS, NOT_EQUALS, IN
        Connectors: AND, OR
        Arguments:
            filterMessage : REQUIRED : A dictionary of the search to the Audit Log.
        """
        path = "/auditlogs/api/v1/auditlogs/search"
        if self.loggingEnabled:
            self.logger.debug(f"searchAuditLogs start")
        if filterMessage is None:
            raise ValueError("Require a filterMessage")
        res = self.connector.postData(self.endpoint + path, data=filterMessage)
        return res
    
    def getAnnotations(self,full:bool=True,includeType:str='all',limit:int=1000,page:int=0)->list:
        """
        Returns a list of the available annotations 
        Arguments:
            full : OPTIONAL : If set to True (default), returned all available information of the annotation.
            includeType : OPTIONAL : use to return only "shared" or "all"(default) annotation available.
            limit : OPTIONAL : number of result per page (default 1000)
            page : OPTIONAL : page used for pagination
        """
        params = {"includeType":includeType,"page":page}
        if full:
            params['expansion'] = "name,description,dateRange,color,applyToAllReports,scope,createdDate,modifiedDate,modifiedById,tags,shares,approved,favorite,owner,usageSummary,companyId,dataId"
        path = f"/annotations"
        lastPage = False
        data = []
        while lastPage == False:
            res = self.connector.getData(self.endpoint + path,params=params)
            data += res.get('content',[])
            lastPage = res.get('lastPage',True)
            params['page'] += 1
        return data
    
    def getAnnotation(self,annotationId:str=None)->dict:
        """
        Return a specific annotation definition.
        Arguments:
            annotationId : REQUIRED : The annotation ID
        """
        if annotationId is None:
            raise ValueError("Require an annotation ID")
        path = f"/annotations/{annotationId}"
        params ={
            "expansion" : "name,description,dateRange,color,applyToAllReports,scope,createdDate,modifiedDate,modifiedById,tags,shares,approved,favorite,owner,usageSummary,companyId,dataId"
        }
        res = self.connector.getData(self.endpoint + path,params=params)
        return res
    
    def deleteAnnotation(self,annotationId:str=None)->dict:
        """
        Delete a specific annotation definition.
        Arguments:
            annotationId : REQUIRED : The annotation ID to be deleted
        """
        if annotationId is None:
            raise ValueError("Require an annotation ID")
        path = f"/annotations/{annotationId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def createAnnotation(self,
                        name:str=None,
                        dateRange:str=None,
                        dataViewId:str=None,
                        metricIds:list=None,
                        dimensionObj:list=None,
                        description:str=None,
                        filterIds:list=None,
                        applyToAllReports:bool=False,
                        **kwargs)->dict:

        """
        Create an Annotation.
        Arguments:
            name : REQUIRED : Name of the annotation
            dateRange : REQUIRED : Date range of the annotation to be used. 
                Example: 2022-04-19T00:00:00/2022-04-19T23:59:59
            dataViewId : REQUIRED : Data View ID 
            metricIds : OPTIONAL : List of metrics ID to be annotated
            filterIds : OPTIONAL : List of filters ID to apply for annotation for context.
            dimensionObj : OPTIONAL : List of dimensions object specification:
                {
                    componentType: "dimension"
                    dimensionType: "string"
                    id: "variables/product"
                    operator: "streq"
                    terms: ["unknown"]
                }
            applyToAllReports : OPTIONAL : If the annotation apply to all ReportSuites.
        possible kwargs:
            colors: Color to be used, examples: "STANDARD1"
            shares: List of userId for sharing the annotation
            tags: List of tagIds to be applied
            favorite: boolean to set the annotation as favorite (false by default)
            approved: boolean to set the annotation as approved (false by default)
        """
        path = f"/annotations"
        if name is None:
            raise ValueError("A name must be specified")
        if dateRange is None:
            raise ValueError("A dateRange must be specified")
        if dataViewId is None:
            raise ValueError("a master dataViewId must be specified")
        description = description or "api generated"

        data = {
            "name": name,
            "description": description,
            "dateRange": dateRange,
            "color": kwargs.get('colors',"STANDARD1"),
            "applyToAllReports": applyToAllReports,
            "scope": {
                "metrics":[],
                "filters":[]
            },
            "tags": [],
            "approved": kwargs.get('approved',False),
            "favorite": kwargs.get('favorite',False),
            "dataId": dataViewId
        }
        if metricIds is not None and type(metricIds) == list:
            for metric in metricIds:
                data['scopes']['metrics'].append({
                    "id" : metric,
                    "componentType":"metric"
                })
        if filterIds is None and type(filterIds) == list:
            for filter in filterIds:
                data['scopes']['filters'].append({
                    "id" : filter,
                    "componentType":"segment"
                })
        if dimensionObj is not None and type(dimensionObj) == list:
            for obj in dimensionObj:
                data['scopes']['filters'].append(obj)
        if kwargs.get("shares",None) is not None:
            data['shares'] = []
            for user in kwargs.get("shares",[]):
                data['shares'].append({
                    "shareToId" : user,
                    "shareToType":"user"
                })
        if kwargs.get('tags',None) is not None:
            for tag in kwargs.get('tags'):
                res = self.getTag(tag)
                data['tags'].append({
                    "id":tag,
                    "name":res['name']
                })
        res = self.connector.postData(self.endpoint + path,data=data)
        return res       

    def updateAnnotation(self,annotationId:str=None,annotationObj:dict=None)->dict:
        """
        Update an annotation based on its ID. PUT method.
        Arguments:
            annotationId : REQUIRED : The annotation ID to be updated
            annotationObj : REQUIRED : The object to replace the annotation.
        """
        if annotationObj is None or type(annotationObj) != dict:
            raise ValueError('Require a dictionary representing the annotation definition')
        if annotationId is None:
            raise ValueError('Require the annotation ID')
        path = f"/annotations/{annotationId}"
        res = self.connector.putData(self.endpoint+path,data=annotationObj)
        return res

    def getProjects(
        self,
        full: bool = True,
        includeType: str = "all",
        filterByIds: str = None,
        ownerId: str = None,
        limit : int = None,
        usedIn : bool = False,
        n_results : int = 'inf',
        save: bool = False,
        output: str = "df",
        cache: bool = True,
        **kwargs,
    ) -> JsonListOrDataFrameType:
        """
        Returns a list of project ID with their meta information attached to it.
        Arguments:
            full : OPTIONAL : add all metadata attached to the project (default True)
            includeType : OPTIONAL : Include additional segments not owned by user. ("all" or "shared")
            filterByIds : OPTIONAL : Filter list to only include projects in the specified list (comma-delimited list of IDs)
            ownerId : OPTIONAL : Filter list to only include projects owned by the specified imsUserId
            limit : OPTIONAL : To limit the number of resutls returned per page.
            n_results : OPTIONAL : If you want to restrict to a certain number of requests (default: "inf" loop through all)
            usedIn : OPTIONAL : Additional parameter to compute some usage of the projects. Recommended to be used with limit
            save : OPTIONAL : if you want to save the result
            cache : OPTIONAL : if you want to save the project in a local Variable.
            output : OPTIONAL : the type of output to return "df" or "raw"
        Possible kwargs:
            page : the page number to reach.
        """
        if self.loggingEnabled:
            self.logger.debug(f"getProjects start")
        path = "/projects"
        params = {"includeType": includeType}
        if limit is not None:
            params["limit"] = limit
            params["page"] = kwargs.get('page',0)
            params["pagination"] = "true"
        if full:
            params[
                "expansion"
            ] = "shares,tags,accessLevel,modified,externalReferences,definition,ownerFullName,sharesFullName,complexity,lastRecordedAccess,usageSummary"
        if usedIn:
            params['expansion'] += ',usedIn'
        if filterByIds:
            params["filterByIds"] = filterByIds
        if ownerId:
            params["ownerId"] = ownerId
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        if params.get('pagination','false') != 'true':
            data = res
        else:
            lastPage = res.get('lastPage',False)
            data = res["content"]
            while float(len(data)) < float(n_results) and lastPage == False:
                params["page"] +=1
                res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
                data += res["content"]
                lastPage = res.get('lastPage',False)
                if float(len(data)) >= float(n_results):
                    lastPage=True
        if output == "raw":
            if save:
                with open(f"projects_{int(time.time())}.json", "w") as f:
                    f.write(json.dumps(res, indent=2))
            return data
        if cache:
            self.listProjectIds = data
        data = pd.DataFrame(data)
        if save:
            data.to_csv(f"projects_{int(time.time())}", index=False)
        return data

    def getProject(
        self,
        projectId: str = None,
        projectClass: bool = False,
        cache: bool = True,
        dvIdSuffix: bool = False,
        **kwargs,
    ) -> dict:
        """
        Return a specific project with its definition
        Arguments:
            projectId : REQUIRED : a project ID to return
            projectClass : OPTIONAL : Return a Project class that digest the info.
            cache : OPTIONAL : if you want to save the project in a local Variable.
            dvIdSuffix : OPTIONAL : If you want to add data view ID as suffix of metrics and dimensions (::dvId)
        """
        if projectId is None:
            raise ValueError("Require a Project ID")
        if self.loggingEnabled:
            self.logger.debug(f"getProject start")
        path = f"/projects/{projectId}"
        params = {
            "expansion": "shares,tags,accessLevel,modified,externalReferences,definition"
        }
        res = self.connector.getData(self.endpoint + path, params=params, **kwargs)
        if projectClass:
            return Project(res, dvIdSuffix=dvIdSuffix)
        if cache:
            try:
                self.projectsDetails[projectId] = Project(res)
            except:
                if self.loggingEnabled:
                    self.logger.warning(f"Cannot convert Project to Project class")
        return res

    def getAllProjectDetails(
        self,
        projects: JsonListOrDataFrameType = None,
        filterNameProject: str = None,
        filterNameOwner: str = None,
        useAttribute: bool = True,
        cache: bool = False,
        dvIdSuffix: bool = False,
        output:str="dict",
    ) -> dict:
        """
        Retrieve all projects details. You can either pass the list of dataframe returned from the getProjects methods and some filters.
        Returns a dict of ProjectId and the value is the Project class instance for that project.
        Arguments:
            projects : OPTIONAL : Takes the type of object returned from the getProjects (all data - not only the ID).
                    If None is provided and you never ran the getProjects method, we will call the getProjects method and retrieve the elements.
                    Otherwise you can pass either a limited list of elements that you want to check details for.
            filterNameProject : OPTIONAL : If you want to retrieve project details for project with a specific string in their name.
            filterNameOwner : OPTIONAL : If you want to retrieve project details for project with an owner having a specific name.
            useAttribute : OPTIONAL : True by default, it will use the projectList saved in the listProjectIds attribute.
                If you want to start from scratch on the retrieval process of your projects.
            dvIdSuffix : OPTIONAL : If you want to add data view ID as suffix of metrics and dimensions (::dvId)
            cache : OPTIONAL : If you want to cache the different elements retrieved for future usage.
            output : OPTIONAL : If you want to return a "list" or "dict" from this method. (default "dict")
        Not using filter may end up taking a while to retrieve the information.
        """
        if self.loggingEnabled:
            self.logger.debug(f"starting getAllProjectDetails")
        ## if no project data
        if projects is None:
            if self.loggingEnabled:
                self.logger.debug(f"No projects passed")
            if len(self.listProjectIds) > 0 and useAttribute:
                fullProjectIds = self.listProjectIds
            else:
                fullProjectIds = self.getProjects(output="raw", cache=cache)
        ## if project data is passed
        elif projects is not None:
            if self.loggingEnabled:
                self.logger.debug(f"projects passed")
            if isinstance(projects, pd.DataFrame):
                fullProjectIds = projects.to_dict(orient="records")
            elif isinstance(projects, list):
                fullProjectIds = (proj["id"] for proj in projects)
        if filterNameProject is not None:
            if self.loggingEnabled:
                self.logger.debug(f"filterNameProject passed")
            fullProjectIds = [
                project
                for project in fullProjectIds
                if filterNameProject in project["name"]
            ]
        if filterNameOwner is not None:
            if self.loggingEnabled:
                self.logger.debug(f"filterNameOwner passed")
            fullProjectIds = [
                project
                for project in fullProjectIds
                if filterNameOwner in project["owner"].get("name", "")
            ]
        if self.loggingEnabled:
            self.logger.info(f"{len(fullProjectIds)} project details to retrieve")
            self.logger.debug(
                f"estimated time required : {int(len(fullProjectIds)/60)} minutes"
            )
        projectIds = (project["id"] for project in fullProjectIds)
        projectsDetails = {
            projectId: self.getProject(
                projectId, projectClass=True, dvIdSuffix=dvIdSuffix
            )
            for projectId in projectIds
        }
        if filterNameProject is None and filterNameOwner is None:
            self.projectsDetails = projectsDetails
        if output == "list":
            list_projectsDetails = [projectsDetails[key] for key in projectsDetails]
            return list_projectsDetails
        return projectsDetails

    def deleteProject(self, projectId: str = None) -> dict:
        """
        Delete a project by its ID.
        Arguments:
            projectId : REQUIRED : ID of the project to delete.
        """
        if projectId is None:
            raise ValueError("Require a project ID")
        if self.loggingEnabled:
            self.logger.debug(f"deleteProject start")
        path = f"/projects/{projectId}"
        res = self.connector.deleteData(self.endpoint + path)
        return res

    def createProject(self, projectDefinition: dict = None, **kwargs) -> dict:
        """
        Create a project based on the definition provided in the argument.
        Argument:
            projectDefinition : REQUIRED : the project dictionary defining the creation.
        """
        if projectDefinition is None or type(projectDefinition) != dict:
            raise ValueError("a project definition dictionary is required")
        if self.loggingEnabled:
            self.logger.debug(f"createProject start")
        path = "/projects"
        res = self.connector.postData(self.endpoint + path, data=projectDefinition, **kwargs)
        return res

    def validateProject(self, projectDefinition: dict = None) -> dict:
        """
        Validates a Project definition.
        Arguments:
            projectDefinition : REQUIRED : the project dictionary defining the creation.
        """
        if projectDefinition is None or type(projectDefinition) != dict:
            raise ValueError("a project definition dictionary is required")
        if self.loggingEnabled:
            self.logger.debug(f"validateProject start")
        path = "/projects/validate"
        data = {"projects": projectDefinition}
        res = self.connector.postData(self.endpoint + path, data=data)
        return res

    def updateProject(
        self, projectId: str = None, projectDefinition: dict = None, **kwargs
    ) -> dict:
        """
        Update a project based on the definition provided in the argument. (PUT Method)
        Arguments:
            projectId : REQUIRED : ID of the project to update.
            projectDefinition : REQUIRED : the project dictionary defining the creation.
        """
        if projectDefinition is None or type(projectDefinition) != dict:
            raise ValueError("a project definition dictionary is required")
        if projectId is None:
            raise ValueError("Require a project ID")
        if self.loggingEnabled:
            self.logger.debug(f"updateProject start")
        path = f"/projects/{projectId}"
        params = {
            "expansion": "shares,tags,accessLevel,modified,externalReferences,definition"
        }
        res = self.connector.putData(
            self.endpoint + path, data=projectDefinition, params=params, **kwargs
        )
        return res

    def findComponentsUsage(
        self,
        components: list = None,
        projectDetails: list = None,
        filters: Union[list, pd.DataFrame] = None,
        calculatedMetrics: Union[list, pd.DataFrame] = None,
        recursive: bool = False,
        regexUsed: bool = False,
        resetProjectDetails: bool = False,
        dvIdSuffix: bool = False,
    ) -> dict:
        """
        Find the usage of components in the different part of Adobe Analytics setup.
        Projects, Segment, Calculated metrics.
        Arguments:
            components : REQUIRED : list of component to look for.
                        Example : _tenant.dimensions.val1,filterId, calculatedMetricsId
            ProjectDetails: OPTIONAL : list of instances of Project class.
            filters : OPTIONAL : If you wish to pass the filters to look for. (should contain definition)
                Should be the list or dataframe return by the getFilters method.
            calculatedMetrics : OPTIONAL : If you wish to pass the segments to look for. (should contain definition)
                Should be the list or dataframe return by the getCalculatedMetrics method.
            recursive : OPTIONAL : if set to True, will also find the reference where the meta component are used.
                segments based on your elements will also be searched to see where they are located.
            regexUsed : OPTIONAL : If set to True, the element are definied as a regex and some default setup is turned off.
            resetProjectDetails : OPTIONAL : Set to false by default. If set to True, it will NOT use the cache.
            dvIdSuffix : OPTIONAL : If you do not give projectDetails and you want to look for rsid usage in report for dimensions and metrics.
        """
        if components is None or type(components) != list:
            raise ValueError("components must be present as a list")
        if self.loggingEnabled:
            self.logger.debug(f"starting findComponentsUsage for {components}")
        listRecusion = []  # for findings on recursion
        if regexUsed:
            if self.loggingEnabled:
                self.logger.debug(f"regex is used")
        ## Segments
        if self.loggingEnabled:
            self.logger.debug(f"retrieving filters")
        if len(self.filters) == 0 and filters is None:
            self.filters = self.getFilters(full=True)
            myFilters = self.filters
        elif len(self.filters) > 0 and filters is None:
            if type(self.filters) == list:
                myFilters = pd.DataFrame(self.filters)
            myFilters = self.filters
        elif filters is not None:
            if type(filters) == list:
                myFilters = pd.DataFrame(filters)
        else:
            myFilters = filters
        ### Calculated Metrics
        if self.loggingEnabled:
            self.logger.debug(f"retrieving calculated metrics")
        if len(self.calculatedMetrics) == 0 and calculatedMetrics is None:
            self.calculatedMetrics = self.getCalculatedMetrics(full=True)
            myMetrics = self.calculatedMetrics
        elif len(self.calculatedMetrics) > 0 and calculatedMetrics is None:
            if type(self.calculatedMetrics) == list:
                myMetrics = pd.DataFrame(self.calculatedMetrics)
            elif type(self.calculatedMetrics) == pd.DataFrame:
                myMetrics = self.calculatedMetrics
        elif calculatedMetrics is not None:
            if type(calculatedMetrics) == list:
                myMetrics = pd.DataFrame(calculatedMetrics)
        else:
            myMetrics = calculatedMetrics
        ### Projects
        if (
            len(self.projectsDetails) == 0 and projectDetails is None
        ) or resetProjectDetails:
            if self.loggingEnabled:
                self.logger.debug(f"retrieving projects details")
            self.projectDetails = self.getAllProjectDetails(dvIdSuffix=dvIdSuffix)
            myProjectDetails = (
                self.projectsDetails[key].to_dict() for key in self.projectsDetails
            )
        elif (
            len(self.projectsDetails) > 0
            and projectDetails is None
            and resetProjectDetails == False
        ):
            if self.loggingEnabled:
                self.logger.debug(f"transforming projects details")
            myProjectDetails = (
                self.projectsDetails[key].to_dict() for key in self.projectsDetails
            )
        elif projectDetails is not None:
            if self.loggingEnabled:
                self.logger.debug(f"setting the project details")
            if isinstance(projectDetails[0], Project):
                myProjectDetails = (item.to_dict() for item in projectDetails)
            elif isinstance(projectDetails[0], dict):
                myProjectDetails = (Project(item).to_dict() for item in projectDetails)
        else:
            raise Exception("Project details were not able to be processed")
        teeProjects: tuple = tee(
            myProjectDetails
        )  ## duplicating the project generator for recursive pass (low memory - intensive computation)
        returnObj = {
            element: {"filters": [], "calculatedMetrics": [], "projects": []}
            for element in components
        }
        recurseObj = defaultdict(list)
        if self.loggingEnabled:
            self.logger.debug(f"search started")
            self.logger.debug(f"recursive option : {recursive}")
            self.logger.debug("Analyzing Filters")
        for _, seg in myFilters.iterrows():
            for comp in components:
                if re.search(f"{comp}", str(seg["definition"])):
                    returnObj[comp]["filters"].append({seg["name"]: seg["id"]})
                    if recursive:
                        listRecusion.append(seg["id"])
        if self.loggingEnabled:
            self.logger.debug(f"Analyzing calculated metrics")
        for _, met in myMetrics.iterrows():
            for comp in components:
                if re.search(f"{comp}", str(met["definition"])):
                    returnObj[comp]["calculatedMetrics"].append(
                        {met["name"]: met["id"]}
                    )
                    if recursive:
                        listRecusion.append(met["id"])
        if self.loggingEnabled:
            self.logger.debug(f"Analyzing projects")
        for proj in teeProjects[0]:
            ## mobile reports don't have dimensions.
            if proj["reportType"] == "desktop":
                for comp in components:
                    for element in proj["dimensions"]:
                        if re.search(f"{comp}", element):
                            returnObj[comp]["projects"].append(
                                {proj["name"]: proj["id"]}
                            )
                    for element in proj["metrics"]:
                        if re.search(f"{comp}", element):
                            returnObj[comp]["projects"].append(
                                {proj["name"]: proj["id"]}
                            )
                    for element in proj.get("filters", []):
                        if re.search(f"{comp}", element):
                            returnObj[comp]["projects"].append(
                                {proj["name"]: proj["id"]}
                            )
                    for element in proj.get("calculatedMetrics", []):
                        if re.search(f"{comp}", element):
                            returnObj[comp]["projects"].append(
                                {proj["name"]: proj["id"]}
                            )
        if recursive:
            if self.loggingEnabled:
                self.logger.debug(f"recursive option checked")
            for proj in teeProjects[1]:
                for rec in listRecusion:
                    for element in proj.get("filters", []):
                        if re.search(f"{rec}", element):
                            recurseObj[rec].append({proj["name"]: proj["id"]})
                    for element in proj.get("calculatedMetrics", []):
                        if re.search(f"{rec}", element):
                            recurseObj[rec].append({proj["name"]: proj["id"]})
        if recursive:
            returnObj["recursion"] = recurseObj
        return returnObj

    def _prepareData(
        self,
        dataRows: list = None,
        reportType: str = "normal",
    ) -> dict:
        """
        Read the data returned by the getReport and returns a dictionary used by the Workspace class.
        Arguments:
            dataRows : REQUIRED : data rows data from CJA API getReport
            reportType : REQUIRED : "normal" or "static"
        """
        if dataRows is None:
            raise ValueError("Require dataRows")
        data_rows = deepcopy(dataRows)
        expanded_rows = {}
        if reportType == "normal":
            for row in data_rows:
                expanded_rows[row["itemId"]] = [row["value"]]
                expanded_rows[row["itemId"]] += row["data"]
        elif reportType == "static":
            expanded_rows = data_rows
        return expanded_rows

    def _decrypteStaticData(
        self, dataRequest: dict = None, response: dict = None
    ) -> dict:
        """
        From the request dictionary and the response, decrypte the data to standardise the reading.
        """
        dataRows = []
        ## retrieve StaticRow ID and segmentID
        if len([metric for metric in dataRequest['metricContainer'].get('metricFilters',[]) if metric.get('id','').startswith("STATIC_ROW_COMPONENT")])>0:
            if  "dateRange" in list(dataRequest['metricContainer'].get('metricFilters',[])[0].keys()):
                tableSegmentsRows = {
                    obj["id"]: obj["dateRange"]
                    for obj in dataRequest["metricContainer"]["metricFilters"]
                    if obj["id"].startswith("STATIC_ROW_COMPONENT")
                }
            elif "segmentId" in list(dataRequest['metricContainer'].get('metricFilters',[])[0].keys()):
                tableSegmentsRows = {
                    obj["id"]: obj["segmentId"]
                    for obj in dataRequest["metricContainer"]["metricFilters"]
                    if obj["id"].startswith("STATIC_ROW_COMPONENT")
                }
        else:
            tableSegmentsRows = {
                obj["id"]: obj["segmentId"]
                for obj in dataRequest["metricContainer"].get("metricFilters",[])
            }
        ## retrieve place and segmentID
        segmentApplied = {}
        for obj in dataRequest["metricContainer"].get("metricFilters",[]):
            if obj["id"].startswith("STATIC_ROW") == False:
                if obj["type"] == "breakdown":
                    segmentApplied[obj["id"]] = f"{obj['dimension']}:::{obj['itemId']}"
                elif obj["type"] == "segment":
                    segmentApplied[obj["id"]] = obj["segmentId"]
                elif obj["type"] == "dateRange":
                    segmentApplied[obj["id"]] = obj["dateRange"]
        ### table columnIds and StaticRow IDs
        tableColumnIds = {
            obj["columnId"]: obj.get("filters",[])[0]
            for obj 
            in dataRequest["metricContainer"]["metrics"]
        }
        ### create relations for metrics with Filter on top
        filterRelations = {
            obj["filters"][0]: obj["filters"][1:]
            for obj in dataRequest["metricContainer"]["metrics"]
            if len(obj["filters"]) > 1
        }
        staticRows = set(val for val in tableSegmentsRows.values())
        nb_rows = len(staticRows)  ## define  how many segment used as rows
        nb_columns = int(
            len(dataRequest["metricContainer"]["metrics"]) / nb_rows
        )  ## use to detect rows
        staticRows = set(val for val in tableSegmentsRows.values())
        staticRowsNames = []
        for row in staticRows:
            if row.startswith("s") and "@AdobeOrg" in row:
                filter = self.getFilter(row)
                staticRowsNames.append(filter["name"])
            else:
                staticRowsNames.append(row)
        staticRowDict = {
            row: rowName for row, rowName in zip(staticRows, staticRowsNames)
        }
        ### metrics
        dataRows = defaultdict(list)
        for row in staticRowDict:  ## iter on the different static rows
            for column, data in zip(
                response["columns"]["columnIds"], response["summaryData"]["totals"]
            ):
                if tableSegmentsRows[tableColumnIds[column]] == row:
                    ## check translation of metricId with Static Row ID
                    if row not in dataRows[staticRowDict[row]]:
                        dataRows[staticRowDict[row]].append(row)
                    dataRows[staticRowDict[row]].append(data)
                ## should ends like : {'segmentName' : ['STATIC',123,456]}
        return nb_columns, tableColumnIds, segmentApplied, filterRelations, dataRows

    def getReport(
        self,
        request: Union[dict, IO] = None,
        limit: int = 20000,
        n_results: Union[int, str] = "inf",
        allowRemoteLoad: str = "default",
        useCache: bool = True,
        useResultsCache: bool = False,
        includeOberonXml: bool = False,
        includePredictiveObjects: bool = False,
        returnsNone: bool = None,
        countRepeatInstances: bool = None,
        ignoreZeroes: bool = None,
        dataViewId: str = None,
        resolveColumns: bool = True,
        save: bool = False,
        returnClass: bool = True,
    ) -> Union[Workspace, dict]:
        """
        Return an instance of Workspace that contains the data requested.
        Argumnents:
            request : REQUIRED : either a dictionary of a JSON file that contains the request information.
            limit : OPTIONAL : number of results per request (default 1000)
            n_results : OPTIONAL : total number of results returns. Use "inf" to return everything (default "inf")
            allowRemoteLoad : OPTIONAL : Controls if Oberon should remote load data. Default behavior is true with fallback to false if remote data does not exist
            useCache : OPTIONAL : Use caching for faster requests (Do not do any report caching)
            useResultsCache : OPTIONAL : Use results caching for faster reporting times (This is a pass through to Oberon which manages the Cache)
            includeOberonXml : OPTIONAL : Controls if Oberon XML should be returned in the response - DEBUG ONLY
            includePredictiveObjects : OPTIONAL : Controls if platform Predictive Objects should be returned in the response. Only available when using Anomaly Detection or Forecasting- DEBUG ONLY
            returnsNone : OPTIONAL: Overwritte the request setting to return None values.
            countRepeatInstances : OPTIONAL: Overwritte the request setting to count repeatInstances values.
            ignoreZeroes : OPTIONAL : Ignore zeros in the results
            dataViewId : OPTIONAL : Overwrite the data View ID used for report. Only works if the same components are presents.
            resolveColumns: OPTIONAL : automatically resolve columns from ID to name for calculated metrics & segments. Default True. (works on returnClass only)
            save : OPTIONAL : If you want to save the data (in JSON or CSV, depending the class is used or not)
            returnClass : OPTIONAL : return the class building dataframe and better comprehension of data. (default yes)
        """
        if self.loggingEnabled:
            self.logger.debug(f"Start getReport")
        path = "/reports"
        params = {
            "allowRemoteLoad": allowRemoteLoad,
            "useCache": useCache,
            "useResultsCache": useResultsCache,
            "includeOberonXml": includeOberonXml,
            "includePlatformPredictiveObjects": includePredictiveObjects,
        }
        if type(request) == dict:
            dataRequest = deepcopy(request)
        elif type(request) == RequestCreator:
            dataRequest = request.to_dict()
        elif ".json" in request:
            with open(request, "r") as f:
                dataRequest = json.load(f)
        else:
            raise ValueError("Require a JSON or Dictionary to request data")
        ### Settings
        dataRequest["settings"]["page"] = 0
        dataRequest["settings"]["limit"] = limit
        if returnsNone:
            dataRequest["settings"]["nonesBehavior"] = "return-nones"
        else:
            dataRequest["settings"]["nonesBehavior"] = "exclude-nones"
        if countRepeatInstances:
            dataRequest["settings"]["countRepeatInstances"] = True
        else:
            dataRequest["settings"]["countRepeatInstances"] = False
        if dataViewId is not None:
            dataRequest["dataId"] = dataViewId
        if ignoreZeroes:
            dataRequest["statistics"]["ignoreZeroes"] = True
        else:
            dataRequest["statistics"]["ignoreZeroes"] = False
        ### Request data
        if self.loggingEnabled:
            self.logger.debug(f"getReport request: {json.dumps(dataRequest,indent=4)}")
        res = self.connector.postData(
            self.endpoint + path, data=dataRequest, params=params
        )
        if "rows" in res.keys():
            reportType = "normal"
            if self.loggingEnabled:
                self.logger.debug(f"reportType: {reportType}")
            dataRows = res.get("rows")
            columns = res.get("columns")
            summaryData = res.get("summaryData")
            resultsTruncated = res.get("resultsTruncated")
            totalElements = res.get("numberOfElements")
            lastPage = res.get("lastPage", True)
            if float(len(dataRows)) >= float(n_results):
                ## force end of loop when a limit is set on n_results
                lastPage = True
            while lastPage != True:
                dataRequest["settings"]["page"] += 1
                res = self.connector.postData(
                    self.endpoint + path, data=dataRequest, params=params
                )
                dataRows += res.get("rows")
                lastPage = res.get("lastPage", True)
                totalElements += res.get("numberOfElements")
                if float(len(dataRows)) >= float(n_results):
                    ## force end of loop when a limit is set on n_results
                    lastPage = True
            if self.loggingEnabled:
                self.logger.debug(f"loop for report over: {len(dataRows)} results")
            if returnClass == False:
                return dataRows
            ### create relation between metrics and filters applied
            columnIdRelations = {
                obj["columnId"]: obj["id"]
                for obj in dataRequest["metricContainer"]["metrics"]
            }
            filterRelations = {
                obj["columnId"]: obj["filters"]
                for obj in dataRequest["metricContainer"]["metrics"]
                if len(obj.get("filters", [])) > 0
            }
            metricFilters = {}
            metricFilterTranslation = {}
            for filter in dataRequest["metricContainer"].get("metricFilters", []):
                filterId = filter["id"]
                if filter["type"] == "breakdown":
                    filterValue = f"{filter['dimension']}:{filter['itemId']}"
                    metricFilters[filter["dimension"]] = filter["itemId"]
                if filter["type"] == "dateRange":
                    filterValue = f"{filter['dateRange']}"
                    metricFilters[filterValue] = filterValue
                if filter["type"] == "segment":
                    filterValue = f"{filter['segmentId']}"
                    if filterValue.startswith("s") and "@AdobeOrg" in filterValue:
                        seg = self.getFilter(filterValue)
                        metricFilters[filterValue] = seg["name"]
                metricFilterTranslation[filterId] = filterValue
            metricColumns = {}
            for colId in columnIdRelations.keys():
                metricColumns[colId] = columnIdRelations[colId]
                for element in filterRelations.get(colId, []):
                    metricColumns[colId] += f":::{metricFilterTranslation[element]}"
        else:
            if 'error-504' in res.keys():
                raise TimeoutError(res['error-504'])
            if returnClass == False:
                return res
            reportType = "static"
            if self.loggingEnabled:
                self.logger.debug(f"reportType: {reportType}")
            columns = None  ## no "columns" key in response
            summaryData = res.get("summaryData")
            resultsTruncated = res.get("resultsTruncated")
            (
                nb_columns,
                tableColumnIds,
                segmentApplied,
                filterRelations,
                dataRows,
            ) = self._decrypteStaticData(dataRequest=dataRequest, response=res)
            ### Findings metrics
            metricFilters = {}
            metricColumns = []
            for i in range(nb_columns):
                metric: str = res["columns"]["columnIds"][i]
                metricName = metric.split(":::")[0]
                if metricName.startswith("cm"):
                    calcMetric = self.getCalculatedMetric(metricName)
                    metricName = calcMetric["name"]
                correspondingStatic = tableColumnIds[metric]
                ## if the static row has a filter
                if correspondingStatic in list(filterRelations.keys()):
                    ## finding segment applied to metrics
                    for element in filterRelations[correspondingStatic]:
                        segId = segmentApplied[element]
                        metricName += f":::{segId}"
                        metricFilters[segId] = segId
                        if segId.startswith("s") and "@AdobeOrg" in segId:
                            seg = self.getFilter(segId)
                            metricFilters[segId] = seg["name"]
                metricColumns.append(metricName)
                ### ending with ['metric1','metric2 + segId',...]
        ### preparing data points
        if self.loggingEnabled:
            self.logger.debug(f"preparing data")
        preparedData = self._prepareData(dataRows, reportType=reportType)
        if returnClass:
            if self.loggingEnabled:
                self.logger.debug(f"returning Workspace class")
            ## Using the class
            data = Workspace(
                responseData=preparedData,
                dataRequest=dataRequest,
                columns=columns,
                summaryData=summaryData,
                resultsTruncated=resultsTruncated,
                cjaConnector=self,
                reportType=reportType,
                metrics=metricColumns,  ## for normal type   ## for staticReport
                metricFilters=metricFilters,
                resolveColumns=resolveColumns,
            )
            if save:
                data.to_csv()
            return data

    def getMultidimensionalReport(
        self,
        dimensions: list = None,
        dimensionLimit: dict = None,
        metrics: list = None,
        dataViewId: str = None,
        globalFilters: list = None,
        metricFilters: dict = None,
        countRepeatInstances: bool = True,
        returnNones: bool = True,
    ) -> pd.DataFrame:
        """
        Realize a multi-level breakdown report from the elements provided.
        Returns either
        Arguments:
            dimensions : REQUIRED : list of the dimension to breakdown. In the order of the breakdown.
            dimensionLimit : REQUIRED : the number of results to return for each breakdown.
                dictionnary like this: {'dimension1':5,'dimension2':10}
                You can ask to return everything from a dimension by using the 'inf' method
            metrics : REQUIRED : list of metrics to return
            dataViewId : REQUIRED : The dataView Id to use for your report.
            globalFilters : REQUIRED : list of filtersID to be used.
                example : ["filterId1","2020-01-01T00:00:00.000/2020-02-01T00:00:00.000"]
            metricFilters : OPTIONAL : dictionary of the filter you want to apply to the metrics.
                dictionnary like this : {"metric1":"segId1","metric":"segId2"}
            countRepeatInstances : OPTIONAL : set to count repeatInstances values (or not). True by default.
            returnNones : OPTIONAL : Set the behavior of the None values in that request. (True by default)
        """
        if dimensions is None:
            raise ValueError("Require a list of dimensions")
        if dimensionLimit is None:
            raise ValueError(
                "Require a dictionary of dimensions with their number of results"
            )
        if metrics is None:
            raise ValueError("Require a list of metrics")
        if dataViewId is None:
            raise ValueError("Require a Data View ID")
        if self.loggingEnabled:
            self.logger.debug(f"Starting getMultidimensionalReport")
        template = RequestCreator()
        template.setDataViewId(dataViewId)
        template.setRepeatInstance(countRepeatInstances)
        template.setNoneBehavior(returnNones)
        for filter in globalFilters:
            template.addGlobalFilter(filter)
        for metric in metrics:
            template.addMetric(metric)
        if metricFilters is not None:
            for filterKey in metricFilters:
                template.addMetricFilter(
                    metricId=filterKey, filterId=metricFilters[filterKey]
                )
        if self.loggingEnabled:
            self.logger.debug(
                f"first request: {json.dumps(template.to_dict(),indent=2)}"
            )
        level = 0
        list_breakdown = deepcopy(
            dimensions[1:]
        )  ## use to assign the correct variable to the itemsId retrieved
        dict_breakdown_itemId = defaultdict(list)  ## for dimension - itemId
        dict_breakdown_relation = defaultdict(list)  ## for itemId - Sub itemId
        translate_itemId_value = {}  ## for translation between itemId and Value
        for dimension in dimensions:
            df_final = pd.DataFrame()
            template.setDimension(dimension)
            if float(dimensionLimit[dimension]) > 20000:
                template.setLimit("20000")
                limit = "20000"
            else:
                template.setLimit(dimensionLimit[dimension])
                limit = dimensionLimit[dimension]
            ### if we need to add filters
            if dimension == dimensions[0]:
                if self.loggingEnabled:
                    self.logger.debug(f"Starting first iteration: {dimension}")
                request = template.to_dict()
                res = self.getReport(
                    request=request,
                    n_results=dimensionLimit[dimension],
                    limit=limit,
                )
                dataframe = res.dataframe
                dict_breakdown_itemId[list_breakdown[level]] = list(dataframe["itemId"])
                ### ex : {'dimension1' : [itemID1,itemID2,...]}
                translate_itemId_value[dimension] = {
                    itemId: value
                    for itemId, value in zip(
                        list(dataframe["itemId"]), list(dataframe.iloc[:, 1])
                    )
                }  ### {"dimension1":{'itemIdValue':'realValue'}}
            else:  ### starting breakdowns
                if self.loggingEnabled:
                    self.logger.debug(f"Starting breakdowns")
                for itemId in dict_breakdown_itemId[dimension]:
                    ### for each item in the previous element
                    if level > 1:
                        ## adding previous breakdown value to the metric filter
                        original_filterId = dict_breakdown_relation[itemId]
                        for metric in metrics:
                            template.addMetricFilter(
                                metricId=metric, filterId=original_filterId
                            )
                    filterId = f"{dimensions[level - 1]}:::{itemId}"
                    for metric in metrics:
                        template.addMetricFilter(metricId=metric, filterId=filterId)
                    request = template.to_dict()
                    if self.loggingEnabled:
                        self.logger.info(json.dumps(request, indent=4))
                    res = self.getReport(
                        request=request,
                        n_results=dimensionLimit[dimension],
                        limit=limit,
                    )
                    ## cleaning breakdown filters
                    template.removeMetricFilter(filterId=filterId)
                    if level > 1:
                        original_filterId = dict_breakdown_relation[itemId]
                        template.removeMetricFilter(filterId=original_filterId)
                    if self.loggingEnabled:
                        self.logger.debug(json.dumps(template.to_dict(), indent=4))
                    dataframe = res.dataframe
                    list_itemIds = list(dataframe["itemId"])
                    dict_breakdown_itemId[dimension] = list_itemIds
                    ### ex : {'dimension2' : [itemID1,itemID2,...]}
                    dict_breakdown_relation = {
                        itemId: filterId for itemId in list_itemIds
                    }
                    ## translating itemId to value
                    ## {'dimension1':{'itemId':'value'}}
                    translate_itemId_value[dimension] = {
                        itemId: value
                        for itemId, value in zip(
                            list(dataframe["itemId"]), list(dataframe.iloc[:, 1])
                        )
                    }
                    ## in case breakdown doesn't have values.
                    if dataframe.empty == False:
                        nb_metrics = len(metrics)
                        metricsCols = list(dataframe.columns[-nb_metrics:])
                        dictReplace = {
                            oldColName: newColName
                            for oldColName, newColName in zip(metricsCols, metrics)
                        }
                        dataframe.rename(columns=dictReplace, inplace=True)
                        columns_order = deque(dataframe.columns)
                        for lvl in range(level):
                            dataframe[dimensions[lvl]] = translate_itemId_value[
                                dimensions[lvl]
                            ].get(itemId, itemId)
                            columns_order.appendleft(dimensions[lvl])
                        if df_final.empty:
                            df_final = dataframe
                        else:
                            df_final = df_final.append(dataframe, ignore_index=True)
                    df_final = df_final[columns_order]
            level += 1
        workspace = Workspace(
            df_final,
            dataRequest=template.to_dict(),
            summaryData="notApplicable",
            cjaConnector=self,
            reportType="multi",
            metricFilters="notApplicable",
        )
        return workspace

    def getFreeformTable(
        self,
        dimension: str = None,
        metrics: Union[str] = None,
        dataviewId: str = None,
        start_date: Union[str, datetime] = None,
        end_date: Union[str, datetime] = None,
        top_n: int = 400,
        filterId: str = None,
        search: Union[str, list] = None,
        search_operator: str = "OR",
    ) -> pd.DataFrame:
        """
        Retrieves a freeform table report with the specified parameters.
        
        Arguments:
            dimension : REQUIRED : The dimension to include in the report.
            metrics : REQUIRED : List of metrics to include in the report.
            dataviewId : REQUIRED : The dataView ID to use for your report.
            start_date : OPTIONAL : The start date for the report in 'YYYY-MM-DD' format or datetime object (defaults to 30 days ago).
            end_date : OPTIONAL : The end date for the report in 'YYYY-MM-DD' format or datetime object (defaults to today).
            top_n : OPTIONAL : Number of top results to return (default 400).
            filterId : OPTIONAL : The segment ID to filter the report.
            search : OPTIONAL : A search parameter (string or list of strings) to filter the dimension values.
            search_operator : OPTIONAL : The logical operator to combine search terms (default is OR).
        
        Returns:
            A pandas DataFrame containing the report data.
        """
        if dimension is None:
            raise ValueError("Require at least a dimension")
        if metrics is None:
            raise ValueError("Require at least a metric")
        if dataviewId is None:
            raise ValueError("Require a Data View ID")
        def ensure_dimension_prefix(dimension: str) -> str:
            if not dimension.startswith("variables/"):
                return f"variables/{dimension}"
            return dimension
        def ensure_metric_prefix(metric: str) -> str:
            if not metric.startswith("metrics/"):
                return f"metrics/{metric}"
            return metric
        def ensure_datetime_format(date: Union[str, datetime], is_start: bool) -> str:
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            if date.time() == datetime.min.time():
                if is_start:
                    return date.strftime('%Y-%m-%dT00:00:00.000')
                else:
                    return date.strftime('%Y-%m-%dT23:59:59.999')
            return date.strftime('%Y-%m-%dT%H:%M:%S.000')
        if search_operator not in ["OR", "AND"]:
            raise ValueError("search_operator must be 'OR' or 'AND'")
        if start_date is None:
            start_date = datetime.today() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.today()
        start_date_str = ensure_datetime_format(start_date, is_start=True)
        end_date_str = ensure_datetime_format(end_date, is_start=False)
        date_range = f"{start_date_str}/{end_date_str}"
        dimension = ensure_dimension_prefix(dimension)
        metrics = [ensure_metric_prefix(metric) for metric in metrics]
        template = RequestCreator()
        template.setDataViewId(dataviewId)
        template.setDimension(dimension)
        for metric in metrics:
            template.addMetric(metric)
        if filterId:
            template.addGlobalFilter(filterId)
        template.addGlobalFilter(date_range)
        if search:
            if isinstance(search, str):
                search = [search]
            search_clause = f" {search_operator} ".join([f"CONTAINS '{term}'" for term in search])
            template.setSearch(clause=search_clause)
        if top_n < 50000:
            limit = top_n
            n_results = top_n
        else:
            limit = 50000
            n_results = 20
        request = template.to_dict()
        response = self.getReport(request=request, limit=limit, n_results=n_results)
        df = response.dataframe
        # Drop the itemId column if it exists
        if 'itemId' in df.columns:
            df = df.drop(columns=['itemId'])

        # Remove any rows that exceed the requested top_n
        if len(df) > top_n:
            df = df.head(top_n)
        
        # Clean the column names to remove prefixes
        def clean_column_name(col):
            if col.startswith("variables/"):
                return col.replace("variables/", "")
            elif col.startswith("metrics/"):
                return col.replace("metrics/", "")
            return col
        
        df.columns = [clean_column_name(col) for col in df.columns]
        return df

    def getPersonProfiles(
        self,
        dataviewId: str = None,
        personId: str = "variables/adobe_identitynamespace_personid",
        featureMetrics: list = None,
        targetMetric: str = None,
        binaryTargetMetric: bool = False,
        startDate: Union[str, datetime] = None,
        endDate: Union[str, datetime] = None,
        sampleSize: int = 50000,
        sampleSeed: int = 0,
        fullPersonHistoryOnly: bool = False,
        removeSingleEventPeople: bool = False,
        filterId: str = None
    ) -> pd.DataFrame:
        """
        Retrieves a dataset where every row is a person profile.
        
        Arguments:
            dataviewId : REQUIRED : The dataView ID to use for your report.
            personId : OPTIONAL : The dimension to use as your person ID. Defaults to adobe_identitynamespace_personid.
            featureMetrics : REQUIRED : List of metrics to include in the customer profiles.
            targetMetric : OPTIONAL : A target metric for supervised learning algorithms.
            TODO: featureDimensions (only supported when "flat view" is supported)
            binaryTargetMetric : OPTIONAL: Sets the target metric to 1 if the metric sum for a person is > 0 otherwise sets it to 0
            startDate : OPTIONAL : The start date for the report in 'YYYY-MM-DD' format or datetime object (defaults to 90 days ago).
            endDate : OPTIONAL : The end date for the report in 'YYYY-MM-DD' format or datetime object (defaults to today).
            sampleSize : OPTIONAL : Number of sampled person profiles to return (default 50000). All person profiles are returned if sample is greater than the total population.
            sampleSeed: OPTIONAL : A seed value for the random sampling of person profiles (default 0).
            fullPersonHistoryOnly : OPTIONAL : Filters the sample to only people whose entire history is present in the date range. Defaults to false.
            removeSingleEventPeople : OPTIONAL : Removes people that had only a single event in the date range.
            filterId : OPTIONAL : The segment ID to filter the report with.
        
        Returns:
            A pandas DataFrame containing the person profile data.
        """

        if featureMetrics is None:
            raise ValueError("Require at least one feature metric")
        if dataviewId is None:
            raise ValueError("Require a Data View ID")
        def ensure_dimension_prefix(dimension: str) -> str:
            if not dimension.startswith("variables/"):
                return f"variables/{dimension}"
            return dimension
        def ensure_metric_prefix(metric: str) -> str:
            if not metric.startswith("metrics/"):
                return f"metrics/{metric}"
            return metric
        def ensure_datetime_format(date: Union[str, datetime], is_start: bool) -> str:
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            if date.time() == datetime.min.time():
                if is_start:
                    return date.strftime('%Y-%m-%dT00:00:00.000')
                else:
                    return date.strftime('%Y-%m-%dT23:59:59.999')
            return date.strftime('%Y-%m-%dT%H:%M:%S.000')
        if startDate is None:
            startDate = datetime.today() - timedelta(days=90)
        if endDate is None:
            endDate = datetime.today()
        start_date_str = ensure_datetime_format(startDate, is_start=True)
        end_date_str = ensure_datetime_format(endDate, is_start=False)
        date_range = f"{start_date_str}/{end_date_str}"
        personId = ensure_dimension_prefix(personId)
        metrics = [ensure_metric_prefix(metric) for metric in featureMetrics]
        targetMetric = ensure_metric_prefix(targetMetric)
        
        dataRequest = RequestCreator()
        dataRequest.setDataViewId(dataviewId)

        sampling_metric_definition = {
            "func": "calc-metric",
            "formula": {
                "func": "add",
                "col1": {
                "func": "modulo",
                "description": "Modulo",
                "col1": {
                    "func": "add",
                    "col1": {
                    "func": "multiply",
                    "col1": {
                        "func": "visualization-group",
                        "col": {
                        "func": "add",
                        "col1": {
                            "func": "cumul",
                            "description": "Cumulative",
                            "n": 0,
                            "col": 1
                        },
                        "col2": sampleSeed
                        }
                    },
                    "col2": 1664525
                    },
                    "col2": 1013904223
                },
                "col2": {
                    "func": "pow",
                    "description": "Power operator",
                    "col1": 2,
                    "col2": 32
                }
                },
                "col2": {
                "func": "visualization-group",
                "col": {
                    "func": "multiply",
                    "col1": {
                    "func": "metric",
                    "name": "metrics/occurrences",
                    "description": "Events"
                    },
                    "col2": 0
                }
                }
            },
            "version": [
                1,
                0,
                0
            ]
            }

        dataRequest.addMetric(metricDefinition=sampling_metric_definition)

        for metric in metrics:
            dataRequest.addMetric(metric)

        if binaryTargetMetric:
            binary_metric_definition = {
                "func": "calc-metric",
                "formula": {
                    "func": "if",
                    "description": "If",
                    "cond": {
                    "func": "gt",
                    "description": "Greater Than",
                    "col1": {
                        "func": "metric",
                        "name": f"{targetMetric}",
                        "description": "Binary Target Metric"
                    },
                    "col2": 0
                    },
                    "then": 1,
                    "else": 0
                },
                "version": [
                    1,
                    0,
                    0
                ]
            }
            dataRequest.addMetric(metricDefinition=binary_metric_definition)
        else:
            dataRequest.addMetric(targetMetric)

        dataRequest.setDimension(personId)
        dataRequest.setNoneBehavior(returnNones=False)
        
        if filterId:
            dataRequest.addGlobalFilter(filterId)
        dataRequest.addGlobalFilter(date_range)

        if fullPersonHistoryOnly:
            fullHistoryFilter = {
                "container": {
                    "func": "container",
                    "context": "visitors",
                    "pred": {
                        "func": "eq",
                        "num": 1,
                        "val": {
                            "func": "attr",
                            "name": "variables/adobe_firstvreturn_sessiontype"
                        },
                        "description": "Session Type"
                    }
                },
                "func": "segment",
                "version": [
                    1,
                    0,
                    0
                ]
            }
            dataRequest.addGlobalFilter(adHocFilter=fullHistoryFilter)

        if removeSingleEventPeople:
            excludeSingleEventPeopleFilter = {
                "container": {
                    "func": "container",
                    "context": "visitors",
                    "pred": {
                        "func": "without",
                        "pred": {
                            "func": "eq",
                            "num": 1,
                            "val": {
                                "func": "total",
                                "evt": {
                                    "func": "event",
                                    "name": "metrics/occurrences"
                                }
                            },
                            "description": "Events"
                        }
                    }
                },
                "func": "segment",
                "version": [
                    1,
                    0,
                    0
                ]
            }
            dataRequest.addGlobalFilter(adHocFilter=excludeSingleEventPeopleFilter)

        response = self.getReport(request=dataRequest, n_results=sampleSize)

        df = response.dataframe
        
        # Drop the itemId column if it exists
        if 'itemId' in df.columns:
            df = df.drop(columns=['itemId'])
        
        # Drop the sampling metric
        if 'ad_hoc_cm_0' in df.columns:
            df = df.drop(columns=['ad_hoc_cm_0'])

        # Remove any rows that exceed the requested top_n
        if len(df) > sampleSize:
            df = df.head(sampleSize)
        
        # Clean the column names to remove prefixes
        def clean_column_name(col):
            if col.startswith("variables/"):
                return col.replace("variables/", "")
            elif col.startswith("metrics/"):
                return col.replace("metrics/", "")
            return col
        
        df.columns = [clean_column_name(col) for col in df.columns]

        # Rename the last column if binaryTargetMetric is True and targetMetric is provided
        if binaryTargetMetric and targetMetric:
            # Ensure the last column is renamed
            df.columns.values[-1] = f"{clean_column_name(targetMetric)}_binary"

        # Randomize the rows
        df_randomized = df.sample(frac=1).reset_index(drop=True)
        
        return df_randomized
