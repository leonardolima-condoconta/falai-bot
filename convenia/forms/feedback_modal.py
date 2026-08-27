"""Modal do Slack para registrar um feedback (modelo SCI).

    from forms.feedback_modal import build_feedback_modal, parse_feedback_submission
    view = build_feedback_modal(conn, slack_user_email)

`autor_id` NÃO é campo do formulário: é quem invocou, e sai de
`private_metadata` no parse.
"""
import json
import sqlite3
from typing import Any

from .common import (bloco_contexto, contexto, input_data, input_select, input_texto,
                     opcoes_enum, parse_submission, select_colaborador)


def build_feedback_modal(conn: sqlite3.Connection, slack_user_email: str) -> dict[str, Any]:
    ctx = contexto(conn, slack_user_email)
    if isinstance(ctx, dict):
        return ctx
    lider_id, lider_nome, time = ctx

    return {
        "type": "modal",
        "callback_id": "feedback_submit",
        "private_metadata": json.dumps({"autor_id": lider_id}),
        "title": {"type": "plain_text", "text": "Feedback"},
        "submit": {"type": "plain_text", "text": "Salvar"},
        "close": {"type": "plain_text", "text": "Cancelar"},
        "blocks": [
            bloco_contexto(lider_nome, len(time)),
            select_colaborador(time),
            input_data("data", "Data do feedback"),
            input_select("tipo_id", "Tipo", opcoes_enum(conn, "tipo_feedback")),

            {"type": "divider"},
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": "*Modelo SCI* — descreva a _situação_, o _comportamento_ "
                            "observado e o _impacto_ que ele gerou. Fatos, não rótulos.",
                }],
            },
            input_texto("situacao", "Situação",
                        hint="Quando e onde aconteceu", optional=True),
            input_texto("comportamento", "Comportamento",
                        hint="O que a pessoa fez ou disse, de forma observável", optional=True),
            input_texto("impacto", "Impacto",
                        hint="Que efeito isso teve no time, no cliente ou no resultado",
                        optional=True),

            {"type": "divider"},
            input_texto("acordado", "O que ficou acordado", optional=True),
        ],
    }


def parse_feedback_submission(payload: dict[str, Any]) -> dict[str, Any]:
    """Devolve as chaves de `feedback`, já com `autor_id` de quem invocou."""
    dados = parse_submission(payload, inteiros=("tipo_id",))
    dados["autor_id"] = dados.pop("_meta", {}).get("autor_id")
    return dados
