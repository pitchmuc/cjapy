import pandas as pd
import json
from typing import Union, IO
import time


class Workspace:
    """
    A class to return data from the getReport method.
    """

    startDate = None
    endDate = None
    settings = None

    def __init__(
        self,
        responseData: dict,
        dataRequest: dict = None,
        columns: dict = None,
        summaryData: dict = None,
        cjaConnector: object = None,
        reportType: str = "normal",
        metrics: Union[dict, list] = None,  ## for normal type, static report
        metricFilters: dict = None,
        resolveColumns: bool = True,
    ) -> None:
        """
        Setup the different values from the response of the getReport
        Argument:
            responseData : REQUIRED : data returned & predigested by the getReport method.
            dataRequest : REQUIRED : dataRequest containing the request
            columns : REQUIRED : the columns element of the response.
            summaryData : REQUIRED : summary data containing total calculated by CJA
            cjaConnector : REQUIRED : cja connector.
            reportType : OPTIONAL : define type of report retrieved.
            metrics : OPTIONAL : dictionary of the columns Id for normal report and list of columns name for Static report
            metricFilters : OPTIONAL : Filter name for the id of the filter
            resolveColumns : OPTIONAL :
        """
        for filter in dataRequest["globalFilters"]:
            if filter["type"] == "dateRange":
                self.startDate = filter["dateRange"].split("/")[0]
                self.endDate = filter["dateRange"].split("/")[1]
        self.dataRequest = dataRequest
        self.requestSize = dataRequest["settings"]["limit"]
        self.settings = dataRequest["settings"]
        self.pageRequested = dataRequest["settings"]["page"]
        self.summaryData = summaryData
        self.reportType = reportType
        ## global filters resolution
        filters = []
        for filter in dataRequest["globalFilters"]:
            if filter["type"] == "segment":
                seg = cjaConnector.getFilter(filter["segmentId"])
                filter["segmentName"] = seg["name"]
            else:
                filters.append(filter)
        self.globalFilters = filters
        self.metricFilters = metricFilters
        df_init = pd.DataFrame(responseData).T
        df_init = df_init.reset_index()
        if reportType == "normal":
            columns_data = ["itemId"]
        elif reportType == "static":
            columns_data = ["FilterName"]
        ### adding dimensions & metrics in columns names when reportType is "normal"
        if "dimension" in dataRequest.keys() and reportType == "normal":
            columns_data.append(dataRequest["dimension"])
            ### adding metrics in columns names
            columnIds = columns["columnIds"]
            for col in columnIds:
                metrics: dict = metrics  ## case when dict is used
                metricListName: list = metrics[col].split(":::")
                if resolveColumns:
                    metricResolvedName = []
                    for metric in metricListName:
                        if metric.startswith("cm") and "@AdobeOrg" in metric:
                            cm = cjaConnector.getCalculatedMetric(metric)
                            metricName = cm["name"]
                            metricResolvedName.append(metricName)
                        elif metric.startswith("s") and "@AdobeOrg" in metric:
                            seg = cjaConnector.getFilter(metric)
                            segName = seg["name"]
                            metricResolvedName.append(segName)
                        else:
                            metricResolvedName.append(metric)
                    colName = ":::".join(metricResolvedName)
                    columns_data.append(colName)
                else:
                    columns_data.append(metrics[col])
        elif reportType == "static":
            metrics: list = metrics  ## case when a list is used
            columns_data.append("FilterId")
            columns_data += metrics
        df_init.columns = columns_data
        self.row_numbers = len(df_init)
        self.columns = list(df_init.columns)
        self.dataframe = df_init

    def __str__(self):
        return json.dumps(
            {
                "startDate": self.startDate,
                "endDate": self.startDate,
                "globalFilters": self.globalFilters,
                "totalRows": self.row_numbers,
                "columns": self.columns,
            }
        )

    def __repr__(self):
        return json.dumps(
            {
                "startDate": self.startDate,
                "endDate": self.startDate,
                "globalFilters": self.globalFilters,
                "totalRows": self.row_numbers,
                "columns": self.columns,
            }
        )

    def to_csv(
        self,
        filename: str = None,
        delimiter: str = ",",
        index: bool = False,
    ) -> IO:
        """
        Save the result in a CSV
        Arguments:
            filename : OPTIONAL : name of the file
            delimiter : OPTIONAL : delimiter of the CSV
            index : OPTIONAL : should the index be included in the CSV (default False)
        """
        if filename is None:
            filename = f"cjapy_{int(time.time())}.csv"
        self.df_init.to_csv(filename, delimiter=delimiter, index=index)

    def to_json(self, filename: str = None, orient: str = "index") -> IO:
        """
        Save the result to JSON
        Arguments:
            filename : OPTIONAL : name of the file
            orient : OPTIONAL : orientation of the JSON
        """
        if filename is None:
            filename = f"cjapy_{int(time.time())}.json"
        self.df_init.to_json(filename, orient=orient)
