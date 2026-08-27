"""Modal do Slack para registrar a avaliação de um ciclo.

    from forms.avaliacao_modal import build_avaliacao_modal, parse_avaliacao_submission
    view = build_avaliacao_modal(conn, slack_user_email)

As notas alimentam as colunas geradas de `avaliacao` (nota_final, desempenho,
potencial) — o banco calcula, o formulário não.

⚠️ `avaliacao` tem UNIQUE (ciclo_id, colaborador_id). O formulário não consegue
   filtrar quem já foi avaliado, porque o ciclo é escolhido no próprio modal.
   Trate a violação no handler devolvendo response_action: errors — ver README.
"""
import json
import sqlite3
from typing import Any

from .common import (aviso, bloco_contexto, contexto, input_numero, input_select,
                     input_texto, opcao, opcoes_enum, parse_submission,
                     select_colaborador)

# Quantos ciclos oferecer no select, do mais recente para trás.
MAX_CICLOS = 24


def _opcoes_ciclo(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """`ciclo` identifica a rodada por ano+semestre; `nome` é opcional."""
    return [opcao(f"{nome or f'{ano}.{sem}'}{'' if fechado is None else ' (fechado)'}", cid)
            for cid, ano, sem, nome, fechado in conn.execute(
                "SELECT id, ano, semestre, nome, fechado_em FROM ciclo "
                "ORDER BY ano DESC, semestre DESC LIMIT ?", (MAX_CICLOS,))]


def build_avaliacao_modal(conn: sqlite3.Connection, slack_user_email: str) -> dict[str, Any]:
    ctx = contexto(conn, slack_user_email)
    if isinstance(ctx, dict):
        return ctx
    lider_id, lider_nome, time = ctx

    ciclos = _opcoes_ciclo(conn)
    if not ciclos:
        return aviso(
            "Avaliação",
            "Nenhum ciclo avaliativo cadastrado ainda.\n\nO People precisa abrir o ciclo "
            "em `ciclo` antes que as avaliações possam ser registradas.",
        )

    bloco_ciclo = input_select("ciclo_id", "Ciclo", ciclos)
    bloco_ciclo["element"]["initial_option"] = ciclos[0]   # o mais recente

    return {
        "type": "modal",
        "callback_id": "avaliacao_submit",
        "private_metadata": json.dumps({"lider_id": lider_id}),
        "title": {"type": "plain_text", "text": "Avaliação"},
        "submit": {"type": "plain_text", "text": "Salvar"},
        "close": {"type": "plain_text", "text": "Cancelar"},
        "blocks": [
            bloco_contexto(lider_nome, len(time)),
            bloco_ciclo,
            select_colaborador(time),

            {"type": "divider"},
            {
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": "Notas de *1 a 5*, decimais permitidos. A nota final "
                            "(resultados 50% · competências 30% · potencial 20%) e o "
                            "nine box são calculados pelo banco.",
                }],
            },
            input_numero("nota_resultados", "Resultados", 1, 5, decimal=True,
                         hint="O que foi entregue — peso 50%"),
            input_numero("nota_competencias", "Competências", 1, 5, decimal=True,
                         hint="Como foi entregue — peso 30%"),
            input_numero("nota_potencial", "Potencial", 1, 5, decimal=True,
                         hint="Capacidade de assumir escopo maior — peso 20%"),

            {"type": "divider"},
            input_select("recomendacao_id", "Recomendação",
                         opcoes_enum(conn, "recomendacao"), optional=True),
            input_texto("comentarios", "Comentários", optional=True, max_length=3000),
        ],
    }


def parse_avaliacao_submission(payload: dict[str, Any]) -> dict[str, Any]:
    """Devolve as chaves de `avaliacao`. `_meta` é descartado — a tabela não
    guarda quem avaliou."""
    dados = parse_submission(
        payload,
        inteiros=("ciclo_id", "recomendacao_id"),
        decimais=("nota_resultados", "nota_competencias", "nota_potencial"),
    )
    dados.pop("_meta", None)
    return dados
