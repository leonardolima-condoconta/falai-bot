"""Extrator Convenia — biblioteca isolada de leitura da API Convenia.

Núcleo entregue ao agente Hermes: cliente HTTP, persistência SQLite, configuração
e schemas Pydantic por seção da API. Sem fluxos/pipeline e sem frontend.

    from convenia import ConveniaClient, ConveniaStorage, schemas

    with ConveniaClient() as client, ConveniaStorage("convenia.db") as db:
        rows = client.fetch(schemas.employees.EmployeesSchema)
        db.save("employees", rows)
"""
from . import schemas
from .client.client import ConveniaClient
from .client.storage import ConveniaStorage
from .core.settings import Settings, get_settings
from .core.exceptions import (
    ConveniaError,
    ConveniaAuthError,
    ConveniaForbiddenError,
    ConveniaNotFoundError,
    ConveniaValidationError,
    ConveniaRateLimitError,
    ConveniaServerError,
    ConveniaConnectionError,
)

__all__ = [
    "ConveniaClient",
    "ConveniaStorage",
    "Settings",
    "get_settings",
    "schemas",
    "ConveniaError",
    "ConveniaAuthError",
    "ConveniaForbiddenError",
    "ConveniaNotFoundError",
    "ConveniaValidationError",
    "ConveniaRateLimitError",
    "ConveniaServerError",
    "ConveniaConnectionError",
]
