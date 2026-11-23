"""Data view component models: dimensions and metrics."""

from typing import Any, Dict, List, Optional, Union

from ._base import CJAModel


class Component(CJAModel):
    """Fields shared by data view dimensions and metrics.

    Only ``id`` is required. IDs keep the prefix the list methods return,
    for example ``variables/page`` or ``metrics/visits``.
    """

    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    sourceFieldId: Optional[str] = None
    sourceFieldName: Optional[str] = None
    sourceFieldType: Optional[str] = None
    schemaPath: Optional[str] = None
    schemaType: Optional[str] = None
    storageId: Optional[str] = None
    tableName: Optional[str] = None
    baseTableName: Optional[str] = None
    dataSetIds: Optional[List[str]] = None
    dataSetType: Optional[str] = None
    hasData: Optional[bool] = None
    hidden: Optional[bool] = None
    hideFromReporting: Optional[bool] = None
    required: Optional[bool] = None
    segmentable: Optional[bool] = None
    approved: Optional[bool] = None
    favorite: Optional[bool] = None
    fromGlobalLookup: Optional[bool] = None
    multiValued: Optional[bool] = None
    derivedFieldCompatible: Optional[bool] = None
    attributes: Optional[List[Any]] = None
    labels: Optional[List[Any]] = None
    tags: Optional[List[Any]] = None
    fieldDefinition: Optional[List[Any]] = None
    includeExcludeSetting: Optional[Dict[str, Any]] = None
    usageSummary: Optional[Dict[str, Any]] = None


class Dimension(Component):
    """A dimension, as returned by ``getDimensions`` and ``getDimension``."""

    noValueOptionsSetting: Optional[Dict[str, Any]] = None
    persistenceSetting: Optional[Dict[str, Any]] = None
    bucketingSetting: Optional[Dict[str, Any]] = None
    # A boolean in recorded responses, despite the name.
    defaultDimensionSort: Optional[Union[bool, Dict[str, Any]]] = None


class Metric(Component):
    """A metric, as returned by ``getMetrics`` and ``getMetric``."""

    attributionSetting: Optional[Dict[str, Any]] = None
    precision: Optional[int] = None
    polarity: Optional[str] = None
