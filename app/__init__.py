import logging

from flask import Flask, render_template
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.db import close_db


def create_app(config_object: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    from app.blueprints import agenda, auth

    app.register_blueprint(auth.bp)
    app.register_blueprint(agenda.bp)

    app.teardown_appcontext(close_db)
    _registrar_handlers(app)
    _registrar_cli(app)
    return app


def _registrar_handlers(app: Flask) -> None:
    """Nenhuma falha deve chegar ao usuário como stack trace."""

    @app.errorhandler(404)
    def nao_encontrado(_erro):
        return render_template("erro.html", codigo=404,
                               mensagem="Página não encontrada."), 404

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        return render_template(
            "erro.html", codigo=erro.code, mensagem=erro.description
        ), erro.code

    @app.errorhandler(Exception)
    def erro_inesperado(erro):
        app.logger.exception("Erro não tratado: %s", erro)
        return render_template(
            "erro.html",
            codigo=500,
            mensagem="Algo deu errado do nosso lado. Tente novamente em instantes.",
        ), 500


def _registrar_cli(app: Flask) -> None:
    """`flask agendamentos` imprime os dados da API no terminal."""

    @app.cli.command("agendamentos")
    def listar_agendamentos():
        from app.services.agenda_api import (
            ApiIndisponivel, RespostaInvalida, buscar_agendamentos
        )

        try:
            registros = buscar_agendamentos()
        except (ApiIndisponivel, RespostaInvalida) as exc:
            print(f"Erro: {exc}")
            return

        if not registros:
            print("Nenhum agendamento disponível.")
            return

        print(f"{'DATA':<12}{'HORA':<8}{'PACIENTE':<24}{'CPF':<16}"
              f"{'MÉDICO':<24}{'ESPECIALIDADE':<18}{'CONVÊNIO':<16}STATUS")
        for a in registros:
            print(f"{a['data']:<12}{a['horario']:<8}{a['paciente']:<24}{a['cpf']:<16}"
                  f"{a['medico']:<24}{a['especialidade']:<18}{a['convenio']:<16}"
                  f"{a['status']}")
        print(f"\n{len(registros)} agendamento(s).")
