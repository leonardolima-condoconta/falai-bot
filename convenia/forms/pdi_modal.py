"""Modal do Slack para registrar uma ação de PDI.

    from forms.pdi_modal import build_pdi_modal, parse_pdi_submission
    view = build_pdi_modal(conn, slack_user_email)
    client.views_open(trigger_id=trigger_id, view=view)

O select de colaborador traz apenas a equipe direta de quem invocou.
"""
import json
import sqlite3
from typing import Any

from .common import (bloco_contexto, contexto, input_data, input_select, input_texto,
                     opcoes_enum, parse_submission, select_colaborador)


def build_pdi_modal(conn: sqlite3.Connection, slack_user_email: str) -> dict[str, Any]:
    ctx = contexto(conn, slack_user_email)
    if isinstance(ctx, dict):
        return ctx
    lider_id, lider_nome, time = ctx

    return {
        "type": "modal",
        "callback_id": "pdi_submit",
        "private_metadata": json.dumps({"lider_id": lider_id}),
        "title": {"type": "plain_text", "text": "Novo PDI"},
        "submit": {"type": "plain_text", "text": "Salvar"},
        "close": {"type": "plain_text", "text": "Cancelar"},
        "blocks": [
            bloco_contexto(lider_nome, len(time)),
            select_colaborador(time),
            input_texto("competencia_foco", "Competência foco", multiline=False,
                        max_length=200),
            input_texto("gap_evidencia", "Gap e evidência",
                        hint="O que foi observado que justifica esse foco?", optional=True),
            input_select("tipo_acao_id", "Tipo de ação (70-20-10)",
                         opcoes_enum(conn, "tipo_acao_pdi")),
            input_texto("descricao_acao", "Ação combinada"),
            input_data("prazo", "Prazo", optional=True),
            input_select("status_id", "Status", opcoes_enum(conn, "status_acao")),
            input_texto("evidencia_conclusao", "Evidência de conclusão", optional=True),
        ],
    }


def parse_pdi_submission(payload: dict[str, Any]) -> dict[str, Any]:
    """Devolve as chaves de `pdi`. `_meta` é descartado — a tabela não guarda
    quem registrou."""
    dados = parse_submission(payload, inteiros=("tipo_acao_id", "status_id"))
    dados.pop("_meta", None)
    return dados
