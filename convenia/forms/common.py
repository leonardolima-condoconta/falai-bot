"""Peças compartilhadas pelos modais de gestão de desempenho.

Todos os quatro formulários (PDI, 1x1, feedback, avaliação) seguem o mesmo
padrão: quem invoca é identificado pelo e-mail do Slack, e o select de
colaborador traz apenas a equipe direta dessa pessoa.
"""
import json
import sqlite3
from typing import Any

# Limites do Block Kit respeitados por todos os builders.
MAX_OPCOES = 100
MAX_TEXTO_OPCAO = 75
MAX_TITULO = 24


def opcao(texto: str, valor: Any) -> dict[str, Any]:
    return {
        "text": {"type": "plain_text", "text": str(texto)[:MAX_TEXTO_OPCAO]},
        "value": str(valor),
    }


def aviso(titulo: str, mensagem: str) -> dict[str, Any]:
    """Modal informativo — melhor que estourar exceção na cara do usuário."""
    return {
        "type": "modal",
        "callback_id": "form_aviso",
        "title": {"type": "plain_text", "text": titulo[:MAX_TITULO]},
        "close": {"type": "plain_text", "text": "Fechar"},
        "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": mensagem}}],
    }


def lider(conn: sqlite3.Connection, email: str) -> tuple[str, str] | None:
    row = conn.execute(
        "SELECT id, name || ' ' || last_name FROM employees "
        "WHERE lower(email) = lower(?) AND is_active = 1",
        (email,),
    ).fetchone()
    return (row[0], row[1]) if row else None


def equipe(conn: sqlite3.Connection, lider_id: str) -> list[tuple[str, str, str]]:
    return conn.execute(
        "SELECT e.id, e.name || ' ' || e.last_name, j.name "
        "FROM employees e JOIN jobs j ON j.id = e.job_id "
        "WHERE e.supervisor_id = ? AND e.is_active = 1 "
        "ORDER BY e.name, e.last_name",
        (lider_id,),
    ).fetchall()


def opcoes_enum(conn: sqlite3.Connection, tabela: str) -> list[dict[str, Any]]:
    """Opções vindas de uma tabela de enum — mudar o enum atualiza o formulário."""
    return [opcao(nome, i)
            for i, nome in conn.execute(f"SELECT id, nome FROM {tabela} ORDER BY id")]


def contexto(conn: sqlite3.Connection, email: str) -> tuple[str, str, list] | dict[str, Any]:
    """Resolve líder + equipe, ou devolve o modal de aviso adequado.

    Retorna (lider_id, lider_nome, equipe) em caso de sucesso, ou um dict de
    view pronto para exibir quando não dá para montar o formulário.
    """
    achado = lider(conn, email)
    if achado is None:
        return aviso(
            "Formulário",
            f"Não encontrei ninguém ativo com o e-mail *{email}* na base da Convenia."
            "\n\nIsso acontece quando o e-mail do Slack difere do cadastrado no RH. "
            "Fale com o People para alinhar os dois.",
        )

    lider_id, lider_nome = achado
    time = equipe(conn, lider_id)
    if not time:
        return aviso(
            "Formulário",
            f"*{lider_nome}*, você não tem liderados diretos na base da Convenia."
            "\n\nSe isso estiver errado, o vínculo de gestor vem do cadastro do RH — "
            "peça a correção lá.",
        )
    if len(time) > MAX_OPCOES:
        return aviso(
            "Formulário",
            f"Sua equipe tem {len(time)} pessoas e o Slack limita a lista a "
            f"{MAX_OPCOES}. Use a interface web.",
        )
    return lider_id, lider_nome, time


def bloco_contexto(lider_nome: str, n: int) -> dict[str, Any]:
    return {
        "type": "context",
        "elements": [{
            "type": "mrkdwn",
            "text": f"Registrando como *{lider_nome}* · {n} liderado(s) direto(s)",
        }],
    }


def select_colaborador(time: list[tuple[str, str, str]]) -> dict[str, Any]:
    return {
        "type": "input",
        "block_id": "colaborador_id",
        "label": {"type": "plain_text", "text": "Colaborador"},
        "element": {
            "type": "static_select",
            "action_id": "valor",
            "placeholder": {"type": "plain_text", "text": "Escolha da sua equipe"},
            "options": [opcao(f"{nome} — {cargo}", eid) for eid, nome, cargo in time],
        },
    }


def input_select(block_id: str, label: str, options: list[dict[str, Any]],
                 optional: bool = False) -> dict[str, Any]:
    bloco: dict[str, Any] = {
        "type": "input",
        "block_id": block_id,
        "label": {"type": "plain_text", "text": label},
        "element": {"type": "static_select", "action_id": "valor", "options": options},
    }
    if optional:
        bloco["optional"] = True
    return bloco


def input_texto(block_id: str, label: str, *, hint: str | None = None,
                multiline: bool = True, optional: bool = False,
                max_length: int = 2000) -> dict[str, Any]:
    bloco: dict[str, Any] = {
        "type": "input",
        "block_id": block_id,
        "label": {"type": "plain_text", "text": label},
        "element": {"type": "plain_text_input", "action_id": "valor",
                    "multiline": multiline, "max_length": max_length},
    }
    if hint:
        bloco["hint"] = {"type": "plain_text", "text": hint}
    if optional:
        bloco["optional"] = True
    return bloco


def input_numero(block_id: str, label: str, minimo: float, maximo: float, *,
                 decimal: bool = False, hint: str | None = None,
                 optional: bool = False) -> dict[str, Any]:
    bloco: dict[str, Any] = {
        "type": "input",
        "block_id": block_id,
        "label": {"type": "plain_text", "text": label},
        "element": {
            "type": "number_input",
            "action_id": "valor",
            "is_decimal_allowed": decimal,
            "min_value": str(minimo),
            "max_value": str(maximo),
        },
    }
    if hint:
        bloco["hint"] = {"type": "plain_text", "text": hint}
    if optional:
        bloco["optional"] = True
    return bloco


def input_data(block_id: str, label: str, optional: bool = False) -> dict[str, Any]:
    bloco: dict[str, Any] = {
        "type": "input",
        "block_id": block_id,
        "label": {"type": "plain_text", "text": label},
        "element": {"type": "datepicker", "action_id": "valor"},
    }
    if optional:
        bloco["optional"] = True
    return bloco


def parse_submission(payload: dict[str, Any], *, inteiros: tuple[str, ...] = (),
                     decimais: tuple[str, ...] = ()) -> dict[str, Any]:
    """Extrai o view_submission no formato das colunas da tabela alvo.

    `selected_option` → value, `datepicker` → data ISO, resto → value.
    String em branco vira None (nunca ''), respeitando o que o schema exige.
    """
    valores = payload["view"]["state"]["values"]
    out: dict[str, Any] = {}
    for block_id, campo in valores.items():
        el = campo["valor"]
        if "selected_option" in el:
            bruto = (el["selected_option"] or {}).get("value")
        elif "selected_date" in el:
            bruto = el["selected_date"]
        else:
            bruto = el.get("value")
        if isinstance(bruto, str):
            bruto = bruto.strip() or None
        out[block_id] = bruto

    for campo in inteiros:
        if out.get(campo) is not None:
            out[campo] = int(float(out[campo]))
    for campo in decimais:
        if out.get(campo) is not None:
            out[campo] = float(out[campo])

    meta = payload["view"].get("private_metadata")
    if meta:
        out["_meta"] = json.loads(meta)
    return out
