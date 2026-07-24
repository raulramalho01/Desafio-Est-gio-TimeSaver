import os
import sqlite3
import sys
from pathlib import Path

from werkzeug.security import generate_password_hash # security algo sha256

from app.config import Config
from app.db import criar_schema


# Our mock-user :P
USUARIO_TESTE = {
    "nome": "admin",
    "email": os.getenv("SEED_USER_EMAIL", "admin@timesaver.com.br"),
    "senha": os.getenv("SEED_USER_PASSWORD", "admin123"),
}


def main() -> int:
    caminho = Path(Config.DATABASE_PATH)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sqlite3.connect(caminho) as conn:

            criar_schema(conn)
            existente = conn.execute(
                "SELECT id FROM usuarios WHERE email = ?", (USUARIO_TESTE["email"],)
            ).fetchone()


            if existente:
                print(f"Usuário {USUARIO_TESTE['email']} já existe. Nada a fazer.")
                return 0
            

            conn.execute(
                "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
                (
                    USUARIO_TESTE["nome"],
                    USUARIO_TESTE["email"],
                    generate_password_hash(USUARIO_TESTE["senha"]),
                ),
            )
            conn.commit()
            
    except sqlite3.Error as exc:
        print(f"Falha ao preparar o banco: {exc}", file=sys.stderr)
        return 1

    print(f"Banco pronto em {caminho}")
    print(f"Usuário de teste: {USUARIO_TESTE['email']} / {USUARIO_TESTE['senha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
