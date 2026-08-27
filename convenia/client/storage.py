import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from pydantic import BaseModel


# ── Helpers ──────────────────────────────────────────────────────────────────

def _col(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", s).lower().strip("_")


def _flatten(d: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    """Recursively flatten nested dicts. Lists stay as-is (serialized on insert)."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = _col(f"{prefix}_{k}" if prefix else k)
        if isinstance(v, dict):
            out.update(_flatten(v, key))
        else:
            out[key] = v
    return out


def _infer_type(v: Any) -> str:
    if isinstance(v, bool):
        return "INTEGER"
    if isinstance(v, int):
        return "INTEGER"
    if isinstance(v, float):
        return "REAL"
    return "TEXT"


def _serialize(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False, default=str)
    return v


# ── Storage ──────────────────────────────────────────────────────────────────

class ConveniaStorage:
    def __init__(self, path: str | Path = "convenia.db") -> None:
        self._conn = sqlite3.connect(str(path))
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._known_cols: dict[str, set[str]] = {}

    def _existing_cols(self, table: str) -> set[str]:
        cursor = self._conn.execute(f'PRAGMA table_info("{table}")')
        return {row[1] for row in cursor.fetchall()}

    def _ensure_table(self, table: str, sample: dict[str, Any]) -> None:
        existing = self._existing_cols(table)
        if not existing:
            # Only create columns for non-None values so the type is inferred correctly
            col_defs = "\n".join(
                f'    "{k}" {_infer_type(v)},'
                for k, v in sample.items()
                if k != "id" and v is not None
            )
            self._conn.execute(f"""
                CREATE TABLE IF NOT EXISTS "{table}" (
                    "id"       TEXT PRIMARY KEY,
                    {col_defs}
                    "raw"      TEXT,
                    "saved_at" TEXT NOT NULL
                )
            """)
            self._conn.commit()
            existing = self._existing_cols(table)
        self._known_cols[table] = existing

    def _add_missing_cols(self, table: str, flat: dict[str, Any]) -> None:
        known = self._known_cols.get(table) or self._existing_cols(table)
        changed = False
        for k, v in flat.items():
            # Skip id, already-known columns, and None values (type can't be inferred)
            if k == "id" or k in known or v is None:
                continue
            try:
                self._conn.execute(
                    f'ALTER TABLE "{table}" ADD COLUMN "{k}" {_infer_type(v)}'
                )
                known.add(k)
                changed = True
            except sqlite3.OperationalError:
                known.add(k)
        if changed:
            self._conn.commit()
        self._known_cols[table] = known

    def _insert(self, table: str, key: str, flat: dict[str, Any], raw_json: str, now: str) -> None:
        cols = ['"id"']
        vals: list[Any] = [key]
        known = self._known_cols.get(table, set())
        for k, v in flat.items():
            if k == "id" or k not in known:
                continue
            cols.append(f'"{k}"')
            vals.append(_serialize(v))
        cols += ['"raw"', '"saved_at"']
        vals += [raw_json, now]
        ph = ", ".join("?" * len(cols))
        self._conn.execute(
            f'INSERT OR REPLACE INTO "{table}" ({", ".join(cols)}) VALUES ({ph})',
            tuple(vals),
        )

    def _to_flat_and_raw(self, obj: Any) -> tuple[dict[str, Any], str]:
        raw_dict = obj.model_dump() if hasattr(obj, "model_dump") else (obj if isinstance(obj, dict) else dict(obj))
        return _flatten(raw_dict), json.dumps(raw_dict, ensure_ascii=False, default=str)

    # ── Public API ────────────────────────────────────────────────────────

    def save(self, table: str, rows: list[Any]) -> int:
        if not rows:
            return 0
        now = datetime.utcnow().isoformat()
        for i, row in enumerate(rows):
            flat, raw_json = self._to_flat_and_raw(row)
            key = str(flat.get("id", ""))
            if i == 0:
                self._ensure_table(table, flat)
            self._add_missing_cols(table, flat)
            self._insert(table, key, flat, raw_json, now)
        self._conn.commit()
        return len(rows)

    def save_one(self, table: str, key: str, obj: Any) -> None:
        now = datetime.utcnow().isoformat()
        flat, raw_json = self._to_flat_and_raw(obj)
        self._ensure_table(table, flat)
        self._add_missing_cols(table, flat)
        self._insert(table, key, flat, raw_json, now)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ConveniaStorage":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
