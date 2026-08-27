from typing import ClassVar
from pydantic import BaseModel
from ..base import BaseFilters, ConveniaSchema


class CostCenterItem(BaseModel):
    id: int | str
    name: str | None = None

    model_config = {"extra": "allow"}


class CostCentersSchema(ConveniaSchema):
    endpoint: ClassVar[str] = "/api/v3/companies/cost-centers"
    filters_model: ClassVar[type[BaseFilters]] = BaseFilters
    response_model: ClassVar[type[BaseModel]] = CostCenterItem
