"""Modal do Slack para registrar um 1x1.

    from forms.um_a_um_modal import build_1x1_modal, parse_1x1_submission
    view = build_1x1_modal(conn, slack_user_email)

`lider_id` NÃO é campo do formulário: é quem invocou, e sai de
`private_metadata` no parse. Isso também garante o CHECK do schema
(`lider_id <> colaborador_id`), já que o select só traz liderados.
"""
import json
import sqlite3
from typing import Any

from .common import (bloco_contexto, contexto, input_data, input_numero, input_select,
                     input_texto, opcoes_enum, parse_submission, select_colaborador)


def build_1x1_modal(conn: sqlite3.Connection, slack_user_email: str) -> dict[str, Any]:
    ctx = contexto(conn, slack_user_email)
    if isinstance(ctx, dict):
        return ctx
    lider_id, lider_nome, time = ctx

    return {
        "type": "modal",
        "callback_id": "1x1_submit",
        "private_metadata": json.dumps({"lider_id": lider_id}),
        "title": {"type": "plain_text", "text": "Registro de 1x1"},
        "submit": {"type": "plain_text", "text": "Salvar"},
        "close": {"type": "plain_text", "text": "Cancelar"},
        "blocks": [
            bloco_contexto(lider_nome, len(time)),
            select_colaborador(time),
            input_data("data", "Data do 1x1"),
            input_select("formato_id", "Formato", opcoes_enum(conn, "formato")),

            {"type": "divider"},
            input_numero("energia", "Energia", 1, 5,
                         hint="Como a pessoa chega: 1 = esgotada, 5 = com gás de sobra"),
            input_numero("motivacao", "Motivação", 1, 5,
                         hint="1 = desmotivada, 5 = muito motivada"),

            {"type": "divider"},
            input_texto("pauta_liderado", "Pauta trazida pelo liderado", optional=True),
            input_texto("encaminhamentos", "Encaminhamentos", optional=True),

            input_select("feedback_tipo_id", "Tipo de feedback dado",
                         opcoes_enum(conn, "tipo_feedback"), optional=True),
            input_texto("resumo_feedback_sci", "Resumo do feedback (SCI)",
                        hint="Situação · Comportamento · Impacto", optional=True),

            {"type": "divider"},
            input_numero("progresso_pdi_pct", "Progresso do PDI (%)", 0, 100, optional=True),
            input_texto("acoes_acordadas", "Ações acordadas", optional=True),
            input_data("proximo_1x1", "Próximo 1x1", optional=True),
        ],
    }


def parse_1x1_submission(payload: dict[str, Any]) -> dict[str, Any]:
    """Devolve as chaves de `registro_1x1`, já com `lider_id` de quem invocou."""
    dados = parse_submission(
        payload,
        inteiros=("formato_id", "energia", "motivacao", "feedback_tipo_id",
                  "progresso_pdi_pct"),
    )
    dados["lider_id"] = dados.pop("_meta", {}).get("lider_id")
    return dados
