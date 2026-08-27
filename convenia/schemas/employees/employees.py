from typing import ClassVar, Any
from pydantic import BaseModel
from ..base import BaseFilters, ConveniaSchema, LookupFilters


class EmployeeFilters(BaseFilters, LookupFilters):
    pass


class Employee(BaseModel):
    """Colaborador em /api/v3/employees.

    Os campos `*_id` declarados aqui chegam sempre `null` — o vínculo real vem
    nos objetos aninhados (`department`, `job`, `cost_center`, `supervisor`,
    `address`), preservados via `extra: allow`. Ver RELATORIO_API.md.
    """

    id: int | str
    name: str | None = None
    email: str | None = None
    corporate_email: str | None = None
    status: str | None = None
    hiring_date: str | None = None
    salary: float | None = None
    department_id: int | str | None = None
    job_description_id: int | str | None = None
    cost_center_id: int | str | None = None
    team_id: int | str | None = None
    cpf: Any | None = None
    pis: Any | None = None
    rg: Any | None = None
    birth_date: str | None = None
    phone: str | None = None
    gender_id: int | str | None = None
    marital_status_id: int | str | None = None
    nationality_id: int | str | None = None
    education_id: int | str | None = None
    relationship_id: int | str | None = None
    admission_type_id: int | str | None = None
    payment_method_id: int | str | None = None
    salary_type_id: int | str | None = None

    model_config = {"extra": "allow"}


class EmployeesSchema(ConveniaSchema):
    endpoint: ClassVar[str] = "/api/v3/employees"
    filters_model: ClassVar[type[BaseFilters]] = EmployeeFilters
    response_model: ClassVar[type[BaseModel]] = Employee
