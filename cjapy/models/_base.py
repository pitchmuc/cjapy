"""Shared base class for cjapy models."""

try:
    from pydantic import BaseModel, ConfigDict
except ImportError as error:
    raise ImportError(
        "cjapy.models requires Pydantic 2. Install it with: pip install cjapy[models]"
    ) from error


class CJAModel(BaseModel):
    """Base class for every cjapy model.

    The CJA API changes often, so the models are permissive:

    * Fields a model does not list are kept (``extra="allow"``). Read them with
      ``model.model_extra``. A new field from the API never breaks a caller.
    * Models can be built by field name (``populate_by_name=True``).
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)
