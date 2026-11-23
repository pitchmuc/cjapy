"""Optional Pydantic models for CJA API responses.

Install with ``pip install cjapy[models]``. A plain ``pip install cjapy`` does not
install Pydantic, and ``import cjapy`` does not import this package.

Get models from the list methods with ``output="model"``::

    dataviews = cja.getDataViews(output="model")
    dimensions = cja.getDimensions("dv_123", full=True, output="model")

or validate any raw response yourself::

    from cjapy.models import DataView
    dataview = DataView.model_validate(cja.getDataView("dv_123"))

Field names and types come from responses recorded from a real organization,
not from the API documentation alone. Nested objects (owner, settings, usage
summaries) stay plain dictionaries for now.
"""

from ._base import CJAModel
from .components import Component, Dimension, Metric
from .dataview import DataView

__all__ = ["CJAModel", "Component", "DataView", "Dimension", "Metric"]
