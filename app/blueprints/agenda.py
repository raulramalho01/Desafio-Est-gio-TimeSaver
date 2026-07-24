import logging

from flask import Blueprint, jsonify, render_template, request, session

from app.blueprints.auth import login_obrigatorio
from app.db import registrar_consulta
from app.services import agenda_api
from app.services.agenda_api import ApiIndisponivel, RespostaInvalida

logger = logging.getLogger(__name__)
bp = Blueprint("agenda", __name__)


@bp.route("/")
@login_obrigatorio
def index():
    return render_template("agenda.html", usuario=session.get("usuario_nome"))


@bp.route("/agendamentos")
@login_obrigatorio
def dados():
    """Devolve os agendamentos em JSON, já filtrados pelo termo de busca.

    Sempre responde com o mesmo formato ({dados, mensagem}) para o front
    tratar erro e lista vazia da mesma maneira.
    """
    termo = (request.args.get("q") or "").strip()

    try:
        agendamentos = agenda_api.buscar_agendamentos()
    except ApiIndisponivel as exc:
        return jsonify(dados=[], mensagem=str(exc)), 503
    except RespostaInvalida as exc:
        return jsonify(dados=[], mensagem=str(exc)), 502

    resultado = agenda_api.filtrar(agendamentos, termo)
    registrar_consulta(session["usuario_id"], termo, len(resultado))

    mensagem = None
    if not agendamentos:
        mensagem = "Nenhum agendamento disponível no momento."
    elif not resultado:
        mensagem = f"Nenhum registro encontrado para “{termo}”."

    return jsonify(dados=resultado, mensagem=mensagem)
