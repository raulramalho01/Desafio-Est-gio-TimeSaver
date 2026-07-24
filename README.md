# Agenda Médica

Aplicação web em Flask que autentica um usuário contra um banco SQLite e exibe os
agendamentos médicos em uma tabela Tabulator, com busca por paciente, CPF ou médico.
Os agendamentos vêm de uma API simulada que roda como serviço separado.

## Tecnologias

| Item | Escolha |
|---|---|
| Linguagem / framework | Python 3.12, Flask 3 |
| Banco | SQLite (módulo `sqlite3` da biblioteca padrão) |
| HTTP client | `requests` |
| Tabela | Tabulator 6.3 (via CDN) |
| Servidor | Gunicorn |
| Testes | pytest |
| Containers | Docker + Docker Compose |

## Estrutura

```
app/
├── __init__.py            application factory, handlers de erro, comando de CLI
├── config.py              configuração lida de variáveis de ambiente
├── db.py                  conexão SQLite, autenticação
├── schema.sql             DDL das tabelas (aplicado pelo seed)
├── blueprints/
│   ├── auth.py            login, logout, decorator @login_obrigatorio
│   └── agenda.py          tela principal e endpoint JSON /agendamentos
├── services/
│   └── agenda_api.py      cliente HTTP da API, validação e filtro
└── templates/             base, login, agenda, erro
mock_api/app.py            API simulada (serviço separado)
seed.py                    aplica o schema.sql e cria o usuário de teste
tests/test_app.py          testes automatizados
```

A separação é simples e proposital: *blueprints* só cuidam de request/response,
`services/` fala com o mundo externo, `db.py` fala com o banco. Nenhum SQL ou
`requests.get` aparece dentro de uma rota.

## Como executar com Docker

```bash
cp .env.example .env      # opcional: ajuste SECRET_KEY e credenciais
docker compose up --build
```

Isso sobe dois serviços:

- `web` — aplicação em http://localhost:5000 (roda o seed automaticamente na subida)
- `mock-api` — API simulada em http://localhost:5001/agendamentos

## Como executar sem Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py

# terminal 1
PORT=5001 python mock_api/app.py
# terminal 2
API_URL=http://localhost:5001/agendamentos python wsgi.py
```

## Credenciais de teste

```
usuário: admin@timesaver.com.br   (ou apenas "admin")
senha:   admin123
```

Definidas por `SEED_USER_EMAIL` / `SEED_USER_PASSWORD`. A senha é gravada como hash
(`werkzeug.security.generate_password_hash`), nunca em texto puro.

## Exemplos de uso

**Pela interface** — acesse http://localhost:5000, faça login e use o campo de busca.
A busca aceita nome do paciente, nome do médico e CPF com ou sem pontuação
(`987.654.321-00` e `98765432100` retornam o mesmo registro).

**Pelo terminal** — a aplicação também entrega os dados via CLI:

```bash
flask --app wsgi:app agendamentos
```

```
DATA        HORA    PACIENTE                CPF             MÉDICO ...
2026-07-24  08:00   Ana Beatriz Lima        123.456.789-00  Dr. Paulo Mendes ...
6 agendamento(s).
```

**Pela API interna** (exige sessão autenticada):

```bash
curl -b cookies.txt "http://localhost:5000/agendamentos?q=cardiologia"
# {"dados": [...], "mensagem": null}
```

## Testes

```bash
pytest -q      # 7 testes
```

Cobrem: login válido, login inválido, acesso sem sessão, busca sem correspondência,
busca por CPF sem pontuação, API indisponível e descarte de registro com campo
obrigatório ausente.

## Tratamento de cenários e falhas

| Cenário | Comportamento |
|---|---|
| Credenciais inválidas | HTTP 401, mensagem "Usuário ou senha inválidos." na tela de login; log em nível INFO |
| Campos de login vazios | HTTP 400, "Informe usuário e senha." — não chega a consultar o banco |
| Erro de conexão com o banco | `ErroBanco` capturada no blueprint → HTTP 503 e mensagem "Não foi possível validar o login agora."; log em ERROR |
| Nenhum agendamento na API | Tabela vazia com "Nenhum agendamento disponível no momento." |
| Busca sem correspondência | "Nenhum registro encontrado para *termo*." |
| Busca vazia ou só espaços | Tratada como "sem filtro"; devolve a lista completa, sem erro |
| API indisponível / timeout | `ApiIndisponivel` → HTTP 503, mensagem amigável, tabela vazia; log com a URL e a causa |
| Resposta vazia ou não-JSON | `RespostaInvalida` → HTTP 502, "A API retornou um conteúdo inesperado." |
| Campos obrigatórios ausentes | O registro é descartado e os demais continuam sendo exibidos; log em WARNING com os campos faltantes |
| Qualquer exceção não prevista | `errorhandler(Exception)` → página de erro 500 amigável, stack trace apenas no log |

Nenhum desses caminhos devolve stack trace ou página quebrada ao usuário.

## Decisões técnicas

- **Schema em `app/schema.sql`, não embutido no Python.** O DDL fica legível sozinho
  e o `seed.py` só o aplica. Como todo `CREATE` usa `IF NOT EXISTS`, rodar o seed de
  novo é seguro — o container executa ele a cada subida.
- **`sqlite3` puro em vez de SQLAlchemy.** O modelo tem duas tabelas e nenhuma relação
  complexa. um ORM adicionaria dependência e camada sem ganho real aqui.
- **Endpoint JSON + Tabulator em modo AJAX.** O front chama `/agendamentos?q=...` e
  recebe sempre `{dados, mensagem}`, no sucesso e no erro. Isso mantém o filtro no
  servidor (que é quem fala com a API) e deixa o JavaScript com uma única
  responsabilidade: renderizar.
- **API simulada como serviço separado**, não como função interna. Assim a chamada é
  HTTP de verdade e cenários como timeout e indisponibilidade podem ser testados
  derrubando o container.
- **Exceções de domínio** (`ErroBanco`, `ApiIndisponivel`, `RespostaInvalida`) em vez
  de códigos de retorno: a origem da falha fica explícita e cada camada traduz o erro
  técnico em uma mensagem de usuário no ponto certo.
- **Tabela `consultas_log`** grava as buscas feitas. Atende ao requisito de "estrutura
  para registrar os dados necessários" e falha em silêncio (só WARNING) log não pode
  derrubar a consulta do usuário.
- **Credenciais e URLs vêm do ambiente**, com defaults só para desenvolvimento local.
  O `.env` está no `.gitignore`

## Limitações conhecidas

- O CSS/JS do Tabulator vem de CDN, então a tela precisa de internet para renderizar a
  tabela. Em ambiente fechado bastaria versionar os arquivos em `app/static/`.
- Sem cadastro de usuários pela interface: o usuário de teste vem do `seed.py`.
