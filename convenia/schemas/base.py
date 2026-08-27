from typing import Any, ClassVar, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class BaseFilters(BaseModel):
    model_config = {"populate_by_name": True}

    def to_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {}
        for field_name, value in self.model_dump(exclude_none=True).items():
            if isinstance(value, dict):
                for k, v in value.items():
                    params[f"{field_name}[{k}]"] = v
            else:
                params[field_name] = value
        return params


class LookupFilters(BaseModel):
    match: dict[str, str] | None = None
    different: dict[str, str] | None = None
    like: dict[str, str] | None = None
    paginate: int | None = None
    page: int | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    current_page: int
    total: int
    per_page: int
    data: list[T]
    first_page_url: str | None = None
    last_page_url: str | None = None
    next_page_url: str | None = None
    prev_page_url: str | None = None


class ConveniaSchema:
    endpoint: ClassVar[str]
    filters_model: ClassVar[type[BaseFilters]]
    response_model: ClassVar[type[BaseModel]]
