import functools
import logging

from flask import (
    Blueprint, flash, redirect, render_template, request, session, url_for
)

from app.db import ErroBanco, autenticar

logger = logging.getLogger(__name__)
bp = Blueprint("auth", __name__)


def login_obrigatorio(view):
    """Redireciona para o login quem não estiver autenticado."""

    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Faça login para acessar a agenda.", "aviso")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapper


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_informado = request.form.get("login", "")
        senha = request.form.get("senha", "")

        if not login_informado or not senha:
            flash("Informe usuário e senha.", "erro")
            return render_template("login.html", login=login_informado), 400

        try:
            usuario = autenticar(login_informado, senha)
        except ErroBanco as exc:
            logger.error("Login indisponível: %s", exc)
            flash(
                "Não foi possível validar o login agora. Tente novamente em instantes.",
                "erro",
            )
            return render_template("login.html", login=login_informado), 503

        if usuario is None:
            logger.info("Tentativa de login inválida para '%s'", login_informado)
            flash("Usuário ou senha inválidos.", "erro")
            return render_template("login.html", login=login_informado), 401

        session.clear()
        session["usuario_id"] = usuario["id"]
        session["usuario_nome"] = usuario["nome"]
        logger.info("Login bem-sucedido: %s", usuario["email"])
        return redirect(url_for("agenda.index"))

    return render_template("login.html", login="")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sessão encerrada.", "aviso")
    return redirect(url_for("auth.login"))
