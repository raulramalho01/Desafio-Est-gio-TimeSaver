import sqlite3

import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.db import criar_schema
from app.services import agenda_api

AGENDAMENTO = {
    "paciente": "Ana Beatriz Lima", "cpf": "123.456.789-00",
    "medico": "Dr. Paulo Mendes", "especialidade": "Cardiologia",
    "data": "2026-07-24", "horario": "08:00",
    "convenio": "Unimed", "status": "Confirmado",
}


@pytest.fixture
def app(tmp_path):
    banco = tmp_path / "teste.db"
    with sqlite3.connect(banco) as conn:
        criar_schema(conn)
        conn.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (?, ?, ?)",
            ("admin", "admin@timesaver.com.br", generate_password_hash("admin123")),
        )
        conn.commit()

    class TestConfig(Config):
        TESTING = True
        SECRET_KEY = "teste"
        DATABASE_PATH = str(banco)

    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()


def logar(client):
    return client.post(
        "/login",
        data={"login": "admin@timesaver.com.br", "senha": "admin123"},
        follow_redirects=True,
    )


def test_login_valido_leva_para_a_agenda(client):
    resposta = logar(client)
    assert resposta.status_code == 200
    assert "Agenda Médica" in resposta.get_data(as_text=True)


def test_login_invalido_mostra_mensagem_clara(client):
    resposta = client.post("/login", data={"login": "admin@timesaver.com.br",
                                           "senha": "errada"})
    assert resposta.status_code == 401
    assert "Usuário ou senha inválidos." in resposta.get_data(as_text=True)


def test_agenda_exige_login(client):
    resposta = client.get("/", follow_redirects=False)
    assert resposta.status_code == 302
    assert "/login" in resposta.headers["Location"]


def test_busca_sem_correspondencia_informa_ausencia(client, monkeypatch):
    monkeypatch.setattr(agenda_api, "buscar_agendamentos", lambda: [AGENDAMENTO])
    logar(client)
    corpo = client.get("/agendamentos?q=inexistente").get_json()
    assert corpo["dados"] == []
    assert "Nenhum registro encontrado" in corpo["mensagem"]


def test_busca_por_cpf_sem_pontuacao_encontra(client, monkeypatch):
    monkeypatch.setattr(agenda_api, "buscar_agendamentos", lambda: [AGENDAMENTO])
    logar(client)
    corpo = client.get("/agendamentos?q=12345678900").get_json()
    assert len(corpo["dados"]) == 1
    assert corpo["mensagem"] is None


def test_api_indisponivel_responde_503_sem_quebrar(client, monkeypatch):
    def falhar():
        raise agenda_api.ApiIndisponivel("A API de agendamentos está indisponível.")

    monkeypatch.setattr(agenda_api, "buscar_agendamentos", falhar)
    logar(client)
    resposta = client.get("/agendamentos")
    assert resposta.status_code == 503
    assert resposta.get_json()["dados"] == []


def test_registro_com_campo_obrigatorio_ausente_e_descartado():
    incompleto = {**AGENDAMENTO, "medico": ""}
    assert agenda_api._filtrar_validos([AGENDAMENTO, incompleto]) == [AGENDAMENTO]
