import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

CAMPOS_OBRIGATORIOS = (
    "paciente",
    "cpf",
    "medico",
    "especialidade",
    "data",
    "horario",
    "convenio",
    "status",
)


class ApiIndisponivel(Exception):
    """A API não respondeu (timeout, conexão recusada, erro 5xx)."""


class RespostaInvalida(Exception):
    """A API respondeu, mas o corpo não tem o formato esperado."""


def buscar_agendamentos() -> list[dict]:
    """Busca os agendamentos na API e devolve apenas registros válidos."""
    url = current_app.config["API_URL"]
    timeout = current_app.config["API_TIMEOUT"]
    try:
        resposta = requests.get(url, timeout=timeout)
        resposta.raise_for_status()
    except requests.Timeout as exc:
        logger.error("Timeout de %ss ao chamar %s", timeout, url)
        raise ApiIndisponivel("A API de agendamentos não respondeu a tempo.") from exc
    except requests.RequestException as exc:
        logger.error("Falha na chamada a %s: %s", url, exc)
        raise ApiIndisponivel("A API de agendamentos está indisponível.") from exc

    try:
        corpo = resposta.json()
    except ValueError as exc:
        logger.error("Resposta de %s não é JSON válido", url)
        raise RespostaInvalida("A API retornou um conteúdo inesperado.") from exc

    registros = corpo.get("agendamentos") if isinstance(corpo, dict) else corpo
    if registros is None:
        registros = []
    if not isinstance(registros, list):
        logger.error("Formato inesperado da API: %s", type(registros).__name__)
        raise RespostaInvalida("A API retornou um conteúdo inesperado.")

    return _filtrar_validos(registros)


def _filtrar_validos(registros: list) -> list[dict]:
    """Descarta registros incompletos e registra o motivo no log."""
    validos = []
    for i, item in enumerate(registros):
        if not isinstance(item, dict):
            logger.warning("Registro %s ignorado: não é um objeto", i)
            continue
        faltando = [c for c in CAMPOS_OBRIGATORIOS if not item.get(c)]
        if faltando:
            logger.warning("Registro %s ignorado: campos ausentes %s", i, faltando)
            continue
        validos.append({c: str(item[c]) for c in CAMPOS_OBRIGATORIOS})
    return validos


def filtrar(agendamentos: list[dict], termo: str | None) -> list[dict]:
    """Filtra por paciente, CPF ou médico. Termo vazio devolve tudo."""
    if not termo or not termo.strip():
        return agendamentos
    alvo = _normalizar(termo)
    return [
        a
        for a in agendamentos
        if alvo in _normalizar(a["paciente"])
        or alvo in _normalizar(a["cpf"])
        or alvo in _normalizar(a["medico"])
    ]

