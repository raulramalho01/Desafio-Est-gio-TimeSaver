
# SQLite access
import logging
import sqlite3
from pathlib import Path

from flask import current_app, g
from werkzeug.security import check_password_hash

logger = logging.getLogger(__name__)


class ErroBanco(Exception):
    """Falha ao conectar ou consultar o banco de dados."""


def get_db() -> sqlite3.Connection:
    """Devolve a conexão da request atual, abrindo uma se necessário."""
    if "db" not in g:
        caminho = Path(current_app.config["DATABASE_PATH"])
        try:
            caminho.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(caminho, timeout=5)
            conn.row_factory = sqlite3.Row
            g.db = conn
        except (sqlite3.Error, OSError) as exc:
            logger.error("Falha ao conectar no banco %s: %s", caminho, exc)
            raise ErroBanco("Não foi possível conectar ao banco de dados.") from exc
    return g.db


def close_db(_exception=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def criar_schema(conn: sqlite3.Connection) -> None:
    """Aplica app/schema.sql. Idempotente (CREATE TABLE IF NOT EXISTS)."""
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()


def buscar_usuario_por_login(login: str):
    """Busca por e-mail ou nome de usuário. Retorna sqlite3.Row ou None."""
    try:
        return get_db().execute(
            "SELECT * FROM usuarios WHERE email = ? OR nome = ?",
            (login, login),
        ).fetchone()
    except sqlite3.Error as exc:
        logger.error("Erro ao consultar usuário '%s': %s", login, exc)
        raise ErroBanco("Não foi possível consultar o banco de dados.") from exc


def autenticar(login: str, senha: str):
    """Retorna o usuário se as credenciais conferirem, senão None."""
    if not login or not senha:
        return None
    usuario = buscar_usuario_por_login(login.strip())
    if usuario and check_password_hash(usuario["senha_hash"], senha):
        return usuario
    return None


def registrar_consulta(usuario_id: int, termo: str, resultados: int) -> None:
    """Grava a busca feita pelo usuário. Falha aqui não quebra a tela."""
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO consultas_log (usuario_id, termo, resultados) VALUES (?, ?, ?)",
            (usuario_id, termo, resultados),
        )
        conn.commit()
    except (sqlite3.Error, ErroBanco) as exc:
        logger.warning("Não foi possível registrar a consulta: %s", exc)
