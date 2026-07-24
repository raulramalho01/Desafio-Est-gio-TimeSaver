-- Esquema inicial do banco. 

-- Usuários que podem acessar a agenda.
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nome        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    senha_hash  TEXT    NOT NULL,   -- werkzeug.security, nunca senha em texto puro
    criado_em   TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Registro das buscas feitas na agenda: quem consultou, o que e quantos
-- resultados vieram.
CREATE TABLE IF NOT EXISTS consultas_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id    INTEGER NOT NULL REFERENCES usuarios(id),
    termo         TEXT,
    resultados    INTEGER NOT NULL,
    consultado_em TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_consultas_usuario ON consultas_log (usuario_id);
