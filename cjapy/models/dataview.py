"""Data view model."""

from typing import Any, Dict, List, Optional, Union

from ._base import CJAModel


class DataView(CJAModel):
    """A data view, as returned by ``getDataViews`` and ``getDataView``.

    Only ``id`` is required. The API leaves fields out when they are not set,
    or when the request did not ask for them.
    """

    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[Dict[str, Any]] = None
    organization: Optional[str] = None
    parentDataGroupId: Optional[str] = None
    parentConnectionId: Optional[str] = None
    isDeleted: Optional[bool] = None
    systemUserOwned: Optional[bool] = None
    editableByUser: Optional[bool] = None
    # Recorded responses send the string "true" or "false", not a boolean.
    curationEnabled: Optional[Union[bool, str]] = None
    createdDate: Optional[str] = None
    modifiedDate: Optional[str] = None
    modifiedBy: Optional[str] = None
    recentRecordedAccess: Optional[str] = None
    timezoneDesignator: Optional[str] = None
    currentTimezoneOffset: Optional[float] = None
    containerNames: Optional[Dict[str, Any]] = None
    externalData: Optional[Dict[str, Any]] = None
    segmentList: Optional[List[Any]] = None
    sessionDefinition: Optional[List[Any]] = None
