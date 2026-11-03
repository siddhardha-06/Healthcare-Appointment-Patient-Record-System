"""Base Pydantic model: JSON uses camelCase (slotId, appointmentId) as in SAD 4.3."""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class Page(CamelModel):
    page: int
    total: int
