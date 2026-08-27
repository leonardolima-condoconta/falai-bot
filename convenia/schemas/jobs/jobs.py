from typing import ClassVar
from pydantic import BaseModel
from ..base import BaseFilters, ConveniaSchema


class JobItem(BaseModel):
    id: int | str
    name: str | None = None

    model_config = {"extra": "allow"}


class JobsSchema(ConveniaSchema):
    endpoint: ClassVar[str] = "/api/v3/companies/jobs"
    filters_model: ClassVar[type[BaseFilters]] = BaseFilters
    response_model: ClassVar[type[BaseModel]] = JobItem
