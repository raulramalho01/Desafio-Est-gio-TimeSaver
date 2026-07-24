"""API simulada de agendamentos (serviço separado).

Roda em outra porta/container e devolve dados mockados em JSON.
"""
import os

from flask import Flask, jsonify

app = Flask(__name__)

AGENDAMENTOS = [
    {"paciente": "Ana Beatriz Lima", "cpf": "123.456.789-00", "medico": "Dr. Paulo Mendes",
     "especialidade": "Cardiologia", "data": "2026-07-24", "horario": "08:00",
     "convenio": "Unimed", "status": "Confirmado"},
    {"paciente": "Carlos Eduardo Souza", "cpf": "987.654.321-00", "medico": "Dra. Helena Prado",
     "especialidade": "Dermatologia", "data": "2026-07-24", "horario": "09:30",
     "convenio": "Bradesco Saúde", "status": "Aguardando"},
    {"paciente": "Mariana Ferreira", "cpf": "456.789.123-11", "medico": "Dr. Paulo Mendes",
     "especialidade": "Cardiologia", "data": "2026-07-25", "horario": "10:15",
     "convenio": "Particular", "status": "Confirmado"},
    {"paciente": "João Pedro Alves", "cpf": "321.654.987-22", "medico": "Dra. Rita Camargo",
     "especialidade": "Ortopedia", "data": "2026-07-25", "horario": "11:00",
     "convenio": "SulAmérica", "status": "Cancelado"},
    {"paciente": "Fernanda Ribeiro", "cpf": "789.123.456-33", "medico": "Dr. Túlio Nogueira",
     "especialidade": "Pediatria", "data": "2026-07-26", "horario": "14:00",
     "convenio": "Amil", "status": "Confirmado"},
    {"paciente": "Roberto Nunes", "cpf": "159.753.486-44", "medico": "Dra. Helena Prado",
     "especialidade": "Dermatologia", "data": "2026-07-26", "horario": "15:30",
     "convenio": "Unimed", "status": "Reagendado"},
    # Registro incompleto: exercita o descarte de campos ausentes.
    {"paciente": "Registro Incompleto", "cpf": "000.000.000-00", "medico": "",
     "especialidade": "Clínica Geral", "data": "2026-07-27", "horario": "16:00",
     "convenio": "Unimed", "status": "Confirmado"},
]


@app.get("/agendamentos")
def listar():
    return jsonify(agendamentos=AGENDAMENTOS)


@app.get("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")))
