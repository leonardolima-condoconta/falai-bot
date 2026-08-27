import time
import threading
import httpx
from collections import deque
from typing import Any
from pydantic import BaseModel

from ..core.exceptions import (
    ConveniaAuthError,
    ConveniaForbiddenError,
    ConveniaNotFoundError,
    ConveniaValidationError,
    ConveniaRateLimitError,
    ConveniaServerError,
    ConveniaConnectionError,
)
from ..schemas.base import BaseFilters, ConveniaSchema, PaginatedResponse
from ..core.settings import Settings, get_settings


class _RateLimiter:
    """Sliding-window rate limiter. Tracks request timestamps over the last `window` seconds."""

    def __init__(self, max_calls: int = 50, window: float = 60.0) -> None:
        self._max_calls = max_calls
        self._window = window
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            while self._timestamps and now - self._timestamps[0] >= self._window:
                self._timestamps.popleft()

            if len(self._timestamps) >= self._max_calls:
                sleep_for = self._window - (now - self._timestamps[0]) + 0.05
                if sleep_for > 0:
                    time.sleep(sleep_for)
                now = time.monotonic()
                while self._timestamps and now - self._timestamps[0] >= self._window:
                    self._timestamps.popleft()

            self._timestamps.append(time.monotonic())


class ConveniaClient:
    def __init__(self, settings: Settings | None = None) -> None:
        cfg = settings or get_settings()
        self._page_size = cfg.page_size
        self._rate_limiter = _RateLimiter(max_calls=50, window=60.0)
        self._client = httpx.Client(
            base_url=cfg.base_url,
            headers={"token": cfg.api_key, "Accept": "application/json"},
            timeout=cfg.timeout,
            follow_redirects=True,
        )

    def _build_url(self, endpoint: str, path_params: dict[str, Any]) -> str:
        try:
            return endpoint.format(**path_params)
        except KeyError as e:
            raise ValueError(f"Missing path parameter: {e}") from e

    def _raise_for_status(self, response: httpx.Response) -> None:
        code = response.status_code
        try:
            body = response.json()
            message = body.get("message", response.text)
        except Exception:
            message = response.text

        if code == 401:
            raise ConveniaAuthError(message, code)
        if code == 403:
            raise ConveniaForbiddenError(message, code)
        if code == 404:
            raise ConveniaNotFoundError(message, code)
        if code == 422:
            raise ConveniaValidationError(message, code)
        if code == 429:
            raise ConveniaRateLimitError(message, code)
        if code >= 500:
            raise ConveniaServerError(message, code)
        if code >= 400:
            from ..core.exceptions import ConveniaError
            raise ConveniaError(message, code)

    def _safe_json(self, response: httpx.Response) -> Any:
        if not response.content:
            return []
        try:
            return response.json()
        except Exception:
            raise ConveniaServerError(
                f"Resposta inválida (status {response.status_code}): {response.text[:200]}",
                response.status_code,
            )

    def _get(self, url: str, params: dict[str, Any]) -> httpx.Response:
        """GET com rate limiting e retry automático em 429 (até 3 tentativas, 60s de espera cada)."""
        max_retries = 3
        last: httpx.Response | None = None

        for attempt in range(max_retries + 1):
            self._rate_limiter.acquire()
            try:
                last = self._client.get(url, params=params)
            except httpx.ConnectError as e:
                raise ConveniaConnectionError(str(e)) from e
            except httpx.TimeoutException as e:
                raise ConveniaConnectionError(f"Request timed out: {e}") from e

            if last.status_code != 429:
                return last

            if attempt < max_retries:
                print(f"  [rate limit] aguardando 60s (tentativa {attempt + 2}/{max_retries + 1})...")
                time.sleep(60.0)

        self._raise_for_status(last)
        return last  # unreachable

    def _parse_page(
        self, raw: Any, response_model: type[BaseModel]
    ) -> tuple[list[BaseModel], bool, int]:
        """Returns (items, is_paginated, total)."""
        if isinstance(raw, dict) and "data" in raw and "total" in raw:
            PaginatedResponse[response_model].model_validate(raw)  # type: ignore[valid-type]
            return [response_model.model_validate(item) for item in raw["data"]], True, raw["total"]

        if isinstance(raw, list):
            return [response_model.model_validate(item) for item in raw], False, len(raw)

        if isinstance(raw, dict) and "data" in raw and isinstance(raw["data"], list):
            items = raw["data"]
            return [response_model.model_validate(item) for item in items], False, len(items)

        return [response_model.model_validate(raw)], False, 1

    def fetch(
        self,
        schema: type[ConveniaSchema],
        filters: BaseFilters | None = None,
        **path_params: Any,
    ) -> list[BaseModel]:
        url = self._build_url(schema.endpoint, path_params)
        params: dict[str, Any] = filters.to_params() if filters else {}

        response = self._get(url, {**params, "paginate": self._page_size, "page": 1})
        self._raise_for_status(response)
        raw = self._safe_json(response)

        if isinstance(raw, dict) and "data" in raw and "success" in raw:
            inner = raw["data"]
        else:
            inner = raw

        items, is_paginated, total = self._parse_page(inner, schema.response_model)

        if not is_paginated or len(items) >= total:
            return items

        total_pages = -(-total // self._page_size)

        for page in range(2, total_pages + 1):
            response = self._get(url, {**params, "paginate": self._page_size, "page": page})
            self._raise_for_status(response)
            raw = self._safe_json(response)

            if isinstance(raw, dict) and "data" in raw and "success" in raw:
                inner = raw["data"]
            else:
                inner = raw

            page_items, _, _ = self._parse_page(inner, schema.response_model)
            items.extend(page_items)

        return items

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ConveniaClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
