from typing import ClassVar
from pydantic import BaseModel
from ..base import BaseFilters, ConveniaSchema, LookupFilters


class TokenPermissionFilters(BaseFilters, LookupFilters):
    pass


class TokenPermissionField(BaseModel):
    name: str | None = None
    translated_name: str | None = None

    model_config = {"extra": "allow"}


class TokenPermission(BaseModel):
    """Uma permissão concedida ao token, com os campos que ela libera."""

    id: int | str | None = None
    name: str | None = None
    translated_name: str | None = None
    fields: list[TokenPermissionField] | None = None

    model_config = {"extra": "allow"}


class TokenPermissionItem(BaseModel):
    """Envelope da resposta: nome do token + lista de permissões."""

    name: str | None = None
    permissions: list[TokenPermission] | None = None

    model_config = {"extra": "allow"}


class TokenPermissionsSchema(ConveniaSchema):
    endpoint: ClassVar[str] = "/api/v3/tokens/permissions"
    filters_model: ClassVar[type[BaseFilters]] = TokenPermissionFilters
    response_model: ClassVar[type[BaseModel]] = TokenPermissionItem
