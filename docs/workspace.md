# Workspace Class

The `getReport` method available in cjapy is returning an instance of a class by default. This class is the `Workspace` class.\
It enables storage of attributes from your report directly into that instance and attaching methods to it.\
Most important elements are attributes of the instance, we will see what are these attributes and then focus on the methods.

## Attributes of Workspace

### startDate  & endDate

The Workspace instance will possess a startDate and endDates attributes, so you can know what was the dates selection of that report.

### dataframe

Each result data of a getReport method is contained in a dataframe (from the pandas library).\
Accessing the dataframe attribute will permit the access of these data requested.

### 

### settings
    endDate = None
    settings = None